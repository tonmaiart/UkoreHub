"""Syncs shared studio JSON stores (data/projects.json, data/programs.json,
data/system_config.json, data/plugins/core/*.json) to/from Cloudflare R2 —
the replacement for the old "git pull carries data/ along with the app
code" model, which broke whenever a machine had an uncommitted local edit
(see developer/bug-history/README.md).

Deliberately isolated in its own module: never import this from
core/storage/metadata_store.py, core/storage/config_store.py, or
core/extensibility/config_store.py — those get vendored (copy-pasted, not
imported) into developer/launcher/launcher_build/core/ for
UkoreHubLauncher.exe's own build, and boto3 has no business ending up in
that PyInstaller bundle. Only launcher.py and interface/plugin_api.py (the
unfrozen app, run via plain python(w).exe) import this.

Authenticates with a single shared static R2 API key (Account ID + Access
Key ID + Secret Access Key) baked into UkoreHubLauncher.exe and passed to
launcher.py purely via UKOREHUB_R2_* environment variables — never stored
in any JSON file (see developer/launcher/launcher_build/r2_credentials.py,
gitignored). Every artist gets equal read/write access; there is no
per-user login step, unlike the old Google OAuth model.
"""
from __future__ import annotations

from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from core.exceptions import ConflictError


# Every R2 call below gets an explicit timeout — a stalled connection (bad
# network, a slow DNS resolution, a firewall silently dropping packets)
# would otherwise hang forever. These calls run synchronously on whatever
# thread calls pull()/push() — today that's the Qt UI thread (launcher.py's
# startup pull, and every store save afterwards — e.g.
# SystemConfigStore.save(), or MetadataStore's per-index/per-project saves)
# — so an unbounded hang freezes the whole app, not just the sync.
_TIMEOUT_SECONDS = 20

# R2/S3 report a rejected conditional write (IfMatch/IfNoneMatch) under two
# different shapes depending on which layer answers — GCS always used plain
# HTTP 412; AWS's newer S3 conditional-write feature uses 409
# "ConditionalRequestConflict" instead, and Cloudflare R2's exact behavior
# isn't documented precisely enough to assume just one. Checked against
# both the error Code and the raw HTTP status so either shape is caught.
_CONFLICT_ERROR_CODES = {"PreconditionFailed", "ConditionalRequestConflict"}
_CONFLICT_STATUS_CODES = {409, 412}


class R2JsonSync:
    """One instance per app run, shared across every synced store. Tracks
    the last-seen ETag per blob so push() can send a conditional-write
    precondition (If-Match/If-None-Match) instead of blindly overwriting
    whatever another machine wrote in the meantime.

    Unlike the old GCS engine, there is no separate anonymous/authenticated
    split — a single shared key means an instance is either fully
    read/write capable or (see launcher.py's _build_cloud_sync) never
    constructed at all."""

    def __init__(self, account_id: str, access_key_id: str, secret_access_key: str, bucket_name: str):
        endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            config=Config(
                signature_version="s3v4",
                connect_timeout=_TIMEOUT_SECONDS,
                read_timeout=_TIMEOUT_SECONDS,
            ),
        )
        self._bucket = bucket_name
        self._etags: dict[str, str | None] = {}

    def pull(self, blob_name: str, local_path: Path) -> str | None:
        """Downloads blob_name to local_path, returns its ETag. If the
        blob doesn't exist yet (fresh studio setup, nobody has pushed this
        blob before), leaves local_path untouched and returns None — the
        next push() for this blob_name will be create-only."""
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=blob_name)
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code in ("NoSuchKey", "404"):
                self._etags[blob_name] = None
                return None
            raise
        body = response["Body"].read()
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(body)
        etag = response["ETag"]
        self._etags[blob_name] = etag
        return etag

    def push(self, blob_name: str, local_path: Path) -> None:
        """Uploads local_path's current bytes to blob_name, conditioned on
        the ETag last seen by pull() (or a create-only precondition if
        pull() never saw this blob). On a rejected conditional write
        (someone else wrote a newer version first), re-pulls the latest
        into local_path and raises ConflictError instead of clobbering
        it."""
        last_etag = self._etags.get(blob_name)
        put_kwargs = {"IfMatch": last_etag} if last_etag is not None else {"IfNoneMatch": "*"}
        try:
            response = self._client.put_object(
                Bucket=self._bucket,
                Key=blob_name,
                Body=local_path.read_bytes(),
                **put_kwargs,
            )
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            status_code = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            if error_code in _CONFLICT_ERROR_CODES or status_code in _CONFLICT_STATUS_CODES:
                self.pull(blob_name, local_path)
                raise ConflictError(
                    f"'{blob_name}' was updated elsewhere first — reloaded the latest version."
                ) from None
            raise
        self._etags[blob_name] = response["ETag"]

    def delete(self, blob_name: str) -> None:
        """Removes blob_name from the bucket entirely — used when a project
        is deleted, so its per-project blob doesn't linger forever. S3-
        compatible delete is idempotent (a blob that's already gone is not
        an error)."""
        self._client.delete_object(Bucket=self._bucket, Key=blob_name)
        self._etags.pop(blob_name, None)
