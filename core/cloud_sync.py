"""Syncs shared studio JSON stores (data/projects.json, data/programs.json,
data/system_config.json, data/plugins/core/*.json) to/from Google Cloud
Storage — the replacement for the old "git pull carries data/ along with
the app code" model, which broke whenever a machine had an uncommitted
local edit (see developer/bug-history/README.md).

Deliberately isolated in its own module: never import this from
core/store.py, core/program_store.py, or core/extensibility/config_store.py
— those are reachable from updater.py (UkoreHubLauncher repo)'s import graph
(the frozen UkoreHub.exe), and google-cloud-storage has no business being
bundled into that pre-launch exe. Only launcher.py and
interface/plugin_api.py (the unfrozen app, run via plain python(w).exe)
import this.

Authenticates as the logged-in artist's own Google identity (via
core/google_auth.py's OAuth device flow), not a service-account key file —
the studio's GCP organization enforces
iam.disableServiceAccountKeyCreation, so no downloadable key can exist at
all. See developer/bug-history/ for context.

The bucket is public-read (`allUsers` granted `Storage Object Viewer` at
the bucket level, outside this codebase — see
developer/bug-history/README.md for the studio's reasoning). That means
pull() works for every artist with no Google login at all: GcsJsonSync
falls back to an anonymous client whenever no refresh_token is available.
push() still requires the authenticated per-user OAuth credential — the
bucket was deliberately never made public-write, since these blobs
(programs.json in particular) hold paths UkoreHub launches as real
executables, so an anonymous writer could plant an arbitrary command for
every synced machine to run.
"""
from __future__ import annotations

from pathlib import Path

from google.api_core.exceptions import NotFound, PreconditionFailed
from google.cloud import storage
from google.oauth2.credentials import Credentials

from core.exceptions import ConflictError, GoogleAuthError
from core.google_auth import GCS_SCOPE, TOKEN_URL


# Every GCS call below gets this timeout explicitly — google-cloud-storage
# has no default timeout of its own, so a stalled connection (bad network,
# a slow first-time credential refresh, a firewall silently dropping
# packets) would otherwise hang forever. These calls run synchronously on
# whatever thread calls pull()/push() — today that's the Qt UI thread
# (launcher.py's startup pull, and every store.save() afterwards) — so an
# unbounded hang freezes the whole app, not just the sync.
_TIMEOUT_SECONDS = 20


class GcsJsonSync:
    """One instance per app run, shared across every synced store. Tracks
    the last-seen object generation per blob so push() can send an
    optimistic-concurrency precondition instead of blindly overwriting
    whatever another machine wrote in the meantime.

    refresh_token may be None — the bucket is public-read, so a machine
    that hasn't done the Google login yet still gets a working pull() via
    an anonymous client. can_push reflects whether this instance was built
    with real credentials; push() raises GoogleAuthError up front instead
    of making a doomed anonymous write request against a public-read-only
    bucket. Needs client_id/client_secret too, not just refresh_token — on
    a machine where launcher.py's _build_cloud_sync fell back to
    data/system_config.default.json (a fresh machine with no local
    system_config.json yet, but one that already has a cached refresh
    token from a previous login), that file deliberately omits the OAuth
    client fields, so refresh_token alone isn't enough to build valid
    Credentials. Missing either falls back to the anonymous client for
    this run; the next run picks up the real client_id/secret once the
    first pull() has cached the full system_config.json locally."""

    def __init__(self, bucket_name: str, project_id: str | None, client_id: str | None, client_secret: str | None, refresh_token: str | None):
        self.can_push = bool(refresh_token and client_id and client_secret)
        if self.can_push:
            credentials = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri=TOKEN_URL,
                client_id=client_id,
                client_secret=client_secret,
                scopes=[GCS_SCOPE],
            )
            client = storage.Client(project=project_id, credentials=credentials)
        else:
            client = storage.Client.create_anonymous_client()
        self._bucket = client.bucket(bucket_name)
        self._generations: dict[str, int] = {}

    def pull(self, blob_name: str, local_path: Path) -> int:
        """Downloads blob_name to local_path, returns its generation. If the
        blob doesn't exist yet (fresh studio setup, nobody has pushed this
        blob before), leaves local_path untouched and returns 0 — the next
        push() for this blob_name will be create-only."""
        blob = self._bucket.blob(blob_name)
        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            blob.reload(timeout=_TIMEOUT_SECONDS)
            blob.download_to_filename(str(local_path), timeout=_TIMEOUT_SECONDS)
        except NotFound:
            self._generations[blob_name] = 0
            return 0
        self._generations[blob_name] = blob.generation
        return blob.generation

    def push(self, blob_name: str, local_path: Path) -> None:
        """Uploads local_path's current bytes to blob_name, conditioned on
        the generation last seen by pull() (or 0 — create-only — if pull()
        never saw this blob). On a 412 Precondition Failed (someone else
        wrote a newer generation first), re-pulls the latest into
        local_path and raises ConflictError instead of clobbering it."""
        if not self.can_push:
            raise GoogleAuthError(
                "Not logged in with Google — sign in via the Studio Setting window to save shared changes."
            )
        blob = self._bucket.blob(blob_name)
        if_generation_match = self._generations.get(blob_name, 0)
        try:
            blob.upload_from_filename(str(local_path), if_generation_match=if_generation_match, timeout=_TIMEOUT_SECONDS)
        except PreconditionFailed:
            self.pull(blob_name, local_path)
            raise ConflictError(
                f"'{blob_name}' was updated elsewhere first — reloaded the latest version."
            ) from None
        self._generations[blob_name] = blob.generation
