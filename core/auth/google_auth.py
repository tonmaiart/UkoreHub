"""Google OAuth 2.0 login for Desktop app clients — authenticates
core/vcs/cloud_sync.py's GcsJsonSync as the logged-in artist's own Google
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

from core.exceptions import GoogleAuthError

AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
GCS_SCOPE = "https://www.googleapis.com/auth/devstorage.read_write"


def run_installed_app_login(client_id: str, client_secret: str) -> str:
    """Blocks until the artist completes login in their browser (or the
    flow times out) — call this off the UI thread. Returns a refresh_token
    (access_type="offline" + prompt="consent" guarantee one is issued even
    on repeat logins) for the caller to persist via
    core/auth/token_store.py's SecureTokenStore; core/vcs/cloud_sync.py
    exchanges it for short-lived access tokens as needed."""
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
