# core/github/

Everything that talks to GitHub. No PySide6/Qt imports here (same Qt-free
rule as the rest of `core/`).

- `auth.py` — GitHub OAuth Device Flow: request a device code, poll for a
  token, fetch the authenticated username, fetch an avatar's raw bytes.
- `commits_api.py` — REST calls against `api.github.com` for a path's commit
  history (used as the preferred data source before falling back to local
  `git log` — see `core/git_service.py`).
- `token_store.py` — stores the GitHub token via the OS keyring, falling
  back to a gitignored local file (`data/github_token.json`) if the keyring
  isn't available.
- `repo_access.py` — `check_repo_access(owner, repo, token)`: a lightweight
  `GET /repos/{owner}/{repo}` used to predict whether a clone would succeed
  *before* attempting one, so a private repo the current GitHub account
  can't see fails fast with a clear "contact your admin" message instead of
  git's own opaque clone error. Called from
  `plugins/core/submit/repo_git_status_page.py` only when a repo hasn't
  been cloned locally yet.

None of these four files import each other or import from anywhere else in
`core/` except `core/exceptions.py` (`GitHubAuthError`).
