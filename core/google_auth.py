"""Google OAuth 2.0 login for Desktop app clients — authenticates
core/cloud_sync.py's GcsJsonSync as the logged-in artist's own Google
identity, instead of a service-account key file (the studio's GCP
organization enforces iam.disableServiceAccountKeyCreation, so no
downloadable key can be created at all).

Uses the loopback/local-server flow (RFC 8252) via google-auth-oauthlib's
InstalledAppFlow: opens the system browser to Google's consent page, and a
short-lived local HTTP server catches the redirect — this is Google's own
recommended pattern for a native desktop app with a real browser and
localhost available (as opposed to the Device Authorization flow, meant
for genuinely input-constrained hardware like TVs, which is a clunkier fit
here). The OAuth client must be of type "Desktop app" in Google Cloud
Console (APIs & Services > Credentials). Its client_id/client_secret are
not meaningfully secret for an installed/distributed app (same footing as
the existing github_client_id already stored in data/system_config.json).

Consent screen User Type matters beyond who can log in: an "External"
consent screen that hasn't completed Google's app verification only issues
refresh tokens valid for 7 days (Google's unverified-app policy) — every
artist would be forced to re-run "Login with Google" weekly. "Internal"
(Workspace-only) consent screens aren't subject to this at all, since they
never need verification. If artists need to log in with personal Gmail
accounts outside the studio's Workspace org, External is unavoidable, but
that then means either completing Google's verification for the storage
scope (a real process — privacy policy URL, possibly a demo video) or
accepting the 7-day re-login cadence.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from core.exceptions import GoogleAuthError

AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
GCS_SCOPE = "https://www.googleapis.com/auth/devstorage.read_write"


def run_installed_app_login(client_id: str, client_secret: str) -> str:
    """Blocks until the artist completes login in their browser (or the
    flow times out) — call this off the UI thread. Returns a refresh_token
    (access_type="offline" + prompt="consent" guarantee one is issued even
    on repeat logins) for the caller to persist via GoogleTokenStore;
    core/cloud_sync.py exchanges it for short-lived access tokens as
    needed."""
    if not client_id or not client_secret:
        raise GoogleAuthError("Google OAuth Client ID/Secret not configured — set them in the Studio Setting window.")
    from google_auth_oauthlib.flow import InstalledAppFlow

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": AUTH_URI,
            "token_uri": TOKEN_URL,
            "redirect_uris": ["http://localhost"],
        }
    }
    flow = InstalledAppFlow.from_client_config(client_config, scopes=[GCS_SCOPE])
    try:
        credentials = flow.run_local_server(port=0, access_type="offline", prompt="consent", timeout_seconds=180)
    except Exception as exc:
        raise GoogleAuthError(f"Google login failed: {exc}") from exc
    if not credentials.refresh_token:
        raise GoogleAuthError("Google did not return a refresh token — try logging in again.")
    return credentials.refresh_token


SERVICE_NAME = "UkoreHub"
KEYRING_USERNAME_KEY = "gcs_refresh_token"


class GoogleTokenStore:
    """Stores the Google refresh token via the OS keyring, falling back to
    a gitignored local file (cache/gcs_refresh_token.json) if the keyring
    isn't available — same shape as core/github/token_store.py's
    TokenStore, duplicated rather than shared since that class lives in
    core/github/ (scoped to GitHub only per its own README) and this one
    isn't GitHub-related."""

    def __init__(self, fallback_path: Path):
        self.fallback_path = Path(fallback_path)

    def save_token(self, token: str) -> None:
        try:
            import keyring

            keyring.set_password(SERVICE_NAME, KEYRING_USERNAME_KEY, token)
            if self.fallback_path.exists():
                self.fallback_path.unlink()
        except Exception:
            self._save_fallback(token)

    def _save_fallback(self, token: str) -> None:
        self.fallback_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.fallback_path.with_suffix(self.fallback_path.suffix + ".tmp")
        tmp_path.write_text(json.dumps({"token": token}), encoding="utf-8")
        os.replace(tmp_path, self.fallback_path)

    def load_token(self) -> str | None:
        try:
            import keyring

            token = keyring.get_password(SERVICE_NAME, KEYRING_USERNAME_KEY)
            if token:
                return token
        except Exception:
            pass
        if self.fallback_path.exists():
            data = json.loads(self.fallback_path.read_text(encoding="utf-8"))
            return data.get("token")
        return None

    def clear_token(self) -> None:
        try:
            import keyring

            keyring.delete_password(SERVICE_NAME, KEYRING_USERNAME_KEY)
        except Exception:
            pass
        if self.fallback_path.exists():
            self.fallback_path.unlink()
