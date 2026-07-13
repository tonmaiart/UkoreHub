from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from core.exceptions import GitOperationError
from core.git_service import _non_interactive_env

REPO_ROOT = Path(__file__).resolve().parent.parent

# See core/git_service.py's identical constant — avoids a console flash
# behind the GUI on every self-update git fetch/pull.
_NO_WINDOW_FLAGS = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


def _git(args: list[str], cwd: Path) -> str:
    git_executable = shutil.which("git") or "git"
    result = subprocess.run(
        [git_executable, *args],
        cwd=str(cwd),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        env=_non_interactive_env(),
        creationflags=_NO_WINDOW_FLAGS,
    )
    if result.returncode != 0:
        raise GitOperationError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def check_for_update(repo_root: Path = REPO_ROOT) -> bool:
    _git(["fetch"], cwd=repo_root)
    local_head = _git(["rev-parse", "HEAD"], cwd=repo_root)
    upstream_head = _git(["rev-parse", "@{u}"], cwd=repo_root)
    return local_head != upstream_head


def pull_update(repo_root: Path = REPO_ROOT) -> None:
    _git(["pull"], cwd=repo_root)
