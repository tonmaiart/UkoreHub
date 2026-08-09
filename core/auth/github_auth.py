from __future__ import annotations

import urllib.error
import urllib.request


def fetch_avatar_bytes(username: str) -> bytes | None:
    # Stable public convenience URL — no API auth/rate limit needed, works
    # even for just showing your own avatar without a Client ID configured.
    url = f"https://github.com/{username}.png"
    request = urllib.request.Request(url, headers={"User-Agent": "UkoreHub"}, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.read()
    except urllib.error.URLError:
        return None
