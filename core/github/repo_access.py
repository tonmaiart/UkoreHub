from __future__ import annotations

import urllib.error
import urllib.request

from core.exceptions import GitHubAuthError

REPO_API_URL = "https://api.github.com/repos/{owner}/{repo}"


def check_repo_access(owner: str, repo: str, token: str | None) -> bool:
    """True if the given token (or anonymous, if None) can see this repo's
    metadata — good enough to predict whether a clone would succeed, without
    actually attempting one. GitHub returns 404 (not 403) for a private repo
    the caller can't see, same status as a genuinely nonexistent repo, so
    both cases return False here; callers should treat False as "can't
    clone", not as proof the repo doesn't exist."""
    url = REPO_API_URL.format(owner=owner, repo=repo)
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "UkoreHub"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=15):
            return True
    except urllib.error.HTTPError as exc:
        if exc.code in (403, 404):
            return False
        raise GitHubAuthError(f"GitHub API error checking repo access: {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise GitHubAuthError(f"Network error contacting GitHub: {exc}") from exc
