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


def run_git(args: list[str], cwd: Path) -> str:
    """Bare, synchronous `git <args>` against `cwd` — used for whole-tree
    operations on UkoreHub's own install (this repo), as opposed to
    core/git_service.py's GitService which is built around cloning/syncing
    arbitrary *studio project* repos with token auth and hooks."""
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
    run_git(["fetch"], cwd=repo_root)
    local_head = run_git(["rev-parse", "HEAD"], cwd=repo_root)
    upstream_head = run_git(["rev-parse", "@{u}"], cwd=repo_root)
    return local_head != upstream_head


def _untrack_paths_deleted_upstream(repo_root: Path) -> None:
    """Best-effort: `git rm --cached` every path tracked at HEAD but no
    longer present at @{u} — leaves the actual file on disk untouched,
    only drops it from git's index. Same reasoning/near-duplicate as
    developer/packaging/updater.py's identically-named helper — see its
    docstring. A file the running app writes to directly with no commit
    step (e.g. data/projects.json before it moved to cloud sync, see
    developer/bug-history/2026-08-09-shared-data-git-pull-conflict.md) is
    always "locally modified" from git's point of view, so an incoming
    pull that stops tracking that same file gets refused with "local
    changes would be overwritten by merge" instead of just applying the
    deletion."""
    deleted = run_git(["diff", "--name-only", "--diff-filter=D", "HEAD", "@{u}"], cwd=repo_root)
    for path in deleted.splitlines():
        if not path:
            continue
        try:
            run_git(["rm", "--cached", "--ignore-unmatch", "-r", path], cwd=repo_root)
        except GitOperationError:
            pass  # best-effort — the retried pull below still surfaces a real remaining conflict


def pull_update(repo_root: Path = REPO_ROOT) -> None:
    try:
        run_git(["pull"], cwd=repo_root)
    except GitOperationError as exc:
        if "would be overwritten by merge" not in str(exc):
            raise
        _untrack_paths_deleted_upstream(repo_root)
        run_git(["pull"], cwd=repo_root)
