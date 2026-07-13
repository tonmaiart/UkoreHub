from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

COMMITS_API_URL = "https://api.github.com/repos/{owner}/{repo}/commits"


class GitHubCommitsApiError(Exception):
    pass


def fetch_commits_for_path(owner: str, repo: str, path: str, token: str | None, limit: int = 30) -> list[dict]:
    params = {"per_page": str(limit)}
    if path:
        params["path"] = path
    url = COMMITS_API_URL.format(owner=owner, repo=repo) + "?" + urllib.parse.urlencode(params)
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "UkoreHub"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise GitHubCommitsApiError(str(exc)) from exc
    if not isinstance(data, list):
        raise GitHubCommitsApiError(f"Unexpected response: {data}")
    return data


def download_bytes(url: str) -> bytes | None:
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return response.read()
    except (urllib.error.URLError, TimeoutError):
        return None
