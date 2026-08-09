# core/auth/

Token storage and login helpers, for both GitHub and Google — no
PySide6/Qt imports here.

- `token_store.py` — `SecureTokenStore(service_name, key_name,
  fallback_path, token_label=...)`: stores a single token via the OS
  keyring, falling back to a gitignored local JSON file if the keyring
  isn't available. Raises `TokenStoreFallbackUsed` (after the token is
  already safely saved to the fallback file) so the caller can warn the
  artist their token landed in plaintext — every `save_token()` call site
  should catch this. One shared class for both credential types: GitHub's
  (`UkoreCore.github_tokens`, keyed `"github_access_token"`,
  `cache/github_token.json`) and Google's (`UkoreCore.google_tokens`,
  keyed `"gcs_refresh_token"`, `cache/gcs_refresh_token.json`).
- `github_auth.py` — `fetch_avatar_bytes(username)`: moved from the old
  `core/github/auth.py` (GitHub login itself — device code request/poll/
  username fetch — moved entirely to the separate `UkoreHubLauncher` repo;
  the rest of `core/github/auth.py` had no live call site left in this repo
  and was deleted, along with the rest of `core/github/`).
- `google_auth.py` — `run_installed_app_login(client_id, client_secret)`:
  Google OAuth 2.0 login via `google-auth-oauthlib`'s `InstalledAppFlow`
  loopback/local-server flow (opens the system browser, blocks until the
  artist finishes) — the Google-recommended pattern for a native desktop
  app. Each artist authenticates as their own Google identity to use
  `core/vcs/cloud_sync.py`'s `GcsJsonSync`, since the studio's GCP org
  blocks service-account key creation
  (`iam.disableServiceAccountKeyCreation`).

`core/github/` no longer exists — it held only the GitHub-login-specific
functions (`request_device_code`, `poll_for_token`, `fetch_username`) that
had no live call site left in this repo (GitHub login moved entirely to the
separate `UkoreHubLauncher` repo), and was deleted as dead code.
