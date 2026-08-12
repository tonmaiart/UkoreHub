from __future__ import annotations

import getpass
import json
import re
from pathlib import Path

_FILENAME_TEMPLATE = "last_opened_{repo_id}_{username}.json"
_SAFE_USERNAME_PATTERN = re.compile(r"[^A-Za-z0-9_-]+")


def _safe_username() -> str:
    try:
        username = getpass.getuser()
    except Exception:
        return "unknown"
    return _SAFE_USERNAME_PATTERN.sub("_", username) or "unknown"


class LastOpenedStore:
    def __init__(self, repo_root: Path, cache_dir: Path, repo_id: str, max_entries: int = 20):
        self.repo_root = Path(repo_root)
        self.max_entries = max_entries
        
        # บังคับใช้ cache_dir ที่ส่งมาจากภายนอกเท่านั้น (จะไม่คำนวณแบบ Hardcode อีกต่อไป)
        explorer_cache_root = Path(cache_dir) / "explorer"
        
        self._config_path = explorer_cache_root / _FILENAME_TEMPLATE.format(
            repo_id=_SAFE_USERNAME_PATTERN.sub("_", repo_id), 
            username=_safe_username()
        )
        self._relpaths: list[str] = self._load()
        
    def _load(self) -> list[str]:
        if not self._config_path.is_file():
            return []
        try:
            data = json.loads(self._config_path.read_text(encoding="utf-8"))
            return list(data.get("last_opened", []))
        except Exception:
            return []

    def _save(self) -> None:
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        self._config_path.write_text(
            json.dumps({"last_opened": self._relpaths}, indent=4), encoding="utf-8"
        )

    def get_last_opened(self) -> list[Path]:
        still_valid = []
        paths = []
        for rel in self._relpaths:
            abs_path = self.repo_root / rel
            if abs_path.exists():
                still_valid.append(rel)
                paths.append(abs_path)
        if still_valid != self._relpaths:
            self._relpaths = still_valid
            self._save()
        return paths

    def add(self, abs_path: Path) -> list[Path]:
        try:
            rel = str(Path(abs_path).relative_to(self.repo_root))
        except ValueError:
            return self.get_last_opened()
        if rel in self._relpaths:
            self._relpaths.remove(rel)
        self._relpaths.insert(0, rel)
        self._relpaths = self._relpaths[: self.max_entries]
        self._save()
        return self.get_last_opened()