from __future__ import annotations

import json
import os
from pathlib import Path

SERVICE_NAME = "UkoreHub"


class TokenStoreFallbackUsed(Exception):
    """Raised (after the token is safely saved) to tell the UI to warn the
    user their token landed in a plaintext local file instead of the OS
    keyring."""


class SecureTokenStore:
    """Stores a single token via the OS keyring, falling back to a
    gitignored local file if the keyring isn't available. Merges what used
    to be two near-identical classes (GitHub's TokenStore and Google's
    GoogleTokenStore) — same keyring service name, different key/fallback
    path per token type, distinguished by `token_label` in the fallback
    warning message."""

    def __init__(self, service_name: str, key_name: str, fallback_path: Path, *, token_label: str = "access"):
        self.service_name = service_name
        self.key_name = key_name
        self.fallback_path = Path(fallback_path)
        self.token_label = token_label

    def save_token(self, token: str) -> None:
        try:
            import keyring

            keyring.set_password(self.service_name, self.key_name, token)
            if self.fallback_path.exists():
                self.fallback_path.unlink()
            return
        except Exception:
            self._save_fallback(token)
            raise TokenStoreFallbackUsed(
                f"Secure system keyring unavailable — storing your {self.token_label} token in a "
                f"local file at {self.fallback_path}. Do not share this file."
            )

    def _save_fallback(self, token: str) -> None:
        self.fallback_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.fallback_path.with_suffix(self.fallback_path.suffix + ".tmp")
        tmp_path.write_text(json.dumps({"token": token}), encoding="utf-8")
        os.replace(tmp_path, self.fallback_path)

    def load_token(self) -> str | None:
        try:
            import keyring

            token = keyring.get_password(self.service_name, self.key_name)
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

            keyring.delete_password(self.service_name, self.key_name)
        except Exception:
            pass
        if self.fallback_path.exists():
            self.fallback_path.unlink()
