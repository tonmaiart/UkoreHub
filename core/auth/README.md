# core/auth/

Token storage and login helpers, for GitHub — no PySide6/Qt imports here.
There is no cloud-sync login anymore: `core/vcs/cloud_sync.py`'s `R2JsonSync`
authenticates with a single shared static Cloudflare R2 key baked into
`UkoreHubLauncher.exe` (see the `ukorehub-cloud-sync` skill), not a
per-artist credential, so nothing in this folder is involved in cloud sync.

- `token_store.py` — `SecureTokenStore(service_name, key_name,
  fallback_path, token_label=...)`: stores a single token via the OS
  keyring, falling back to a gitignored local JSON file if the keyring
  isn't available. Raises `TokenStoreFallbackUsed` (after the token is
  already safely saved to the fallback file) so the caller can warn the
  artist their token landed in plaintext — every `save_token()` call site
  should catch this. Generic enough to store more than one credential type
  (constructor takes the service/key name and fallback path); currently
  only used for GitHub's (`UkoreCore.github_tokens`, keyed
  `"github_access_token"`, `cache/github_token.json`).
- `github_auth.py` — `fetch_avatar_bytes(username)`: moved from the old
  `core/github/auth.py` (GitHub login itself — device code request/poll/
  username fetch — moved entirely to the separate `UkoreHubLauncher` repo;
  the rest of `core/github/auth.py` had no live call site left in this repo
  and was deleted, along with the rest of `core/github/`).

`core/github/` no longer exists — it held only the GitHub-login-specific
functions (`request_device_code`, `poll_for_token`, `fetch_username`) that
had no live call site left in this repo (GitHub login moved entirely to the
separate `UkoreHubLauncher` repo), and was deleted as dead code.
