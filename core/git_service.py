from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Callable

from core.exceptions import GitOperationError
from core.models import CommitInfo, RepoStatus

OutputCallback = Callable[[str], None] | None

_FIELD_SEP = "\x1f"


class GitService:
    def __init__(self, git_executable: str | None = None):
        self.git_executable = git_executable or shutil.which("git") or "git"

    def is_cloned(self, local_path: Path) -> bool:
        return (Path(local_path) / ".git").exists()

    def _run_streaming(self, args: list[str], cwd: Path | None, on_output: OutputCallback) -> None:
        process = subprocess.Popen(
            [self.git_executable, *args],
            cwd=str(cwd) if cwd else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None
        # git's progress meter ("Receiving objects: 42% (420/1000)...") uses
        # \r to redraw the same line rather than \n, so splitting only on \n
        # would buffer up every tick until the next real newline and make the
        # log look frozen. Treat \r as a line boundary too for a live feed.
        buffer = ""
        while True:
            char = process.stdout.read(1)
            if char == "":
                break
            if char in ("\n", "\r"):
                if buffer and on_output:
                    on_output(buffer)
                buffer = ""
            else:
                buffer += char
        if buffer and on_output:
            on_output(buffer)
        return_code = process.wait()
        if return_code != 0:
            raise GitOperationError(
                f"git {' '.join(args)} failed with exit code {return_code}"
            )

    def clone(self, git_url: str, dest: Path, on_output: OutputCallback = None) -> None:
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        # --progress forces git to emit its progress meter even though stdout
        # is a pipe, not a terminal (git suppresses it by default otherwise).
        self._run_streaming(["clone", "--progress", git_url, str(dest)], cwd=dest.parent, on_output=on_output)

    def pull(self, local_path: Path, on_output: OutputCallback = None) -> None:
        self._run_streaming(["pull", "--progress"], cwd=Path(local_path), on_output=on_output)

    def open_or_sync(self, git_url: str, dest: Path, on_output: OutputCallback = None) -> str:
        dest = Path(dest)
        if not self.is_cloned(dest):
            self.clone(git_url, dest, on_output=on_output)
            return "cloned"
        self.pull(dest, on_output=on_output)
        return "pulled"

    def _run_capture(self, args: list[str], cwd: Path) -> str:
        result = subprocess.run(
            [self.git_executable, *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise GitOperationError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
        return result.stdout

    def get_latest_commit(self, repo_path: Path) -> CommitInfo | None:
        repo_path = Path(repo_path)
        try:
            output = self._run_capture(
                ["log", "-1", f"--pretty=format:%H{_FIELD_SEP}%an{_FIELD_SEP}%ae{_FIELD_SEP}%aI{_FIELD_SEP}%s"],
                cwd=repo_path,
            )
        except GitOperationError:
            return None
        output = output.strip()
        if not output:
            return None
        hash_, author, email, date, message = output.split(_FIELD_SEP, 4)
        return CommitInfo(hash=hash_, author=author, email=email, date=date, message=message)

    def get_working_tree_status(self, repo_path: Path) -> tuple[list[str], list[str], list[str]]:
        repo_path = Path(repo_path)
        output = self._run_capture(
            ["status", "--porcelain=v1", "--untracked-files=all"], cwd=repo_path
        )
        untracked: list[str] = []
        modified: list[str] = []
        staged: list[str] = []
        for line in output.splitlines():
            if not line:
                continue
            index_status, worktree_status = line[0], line[1]
            path = line[3:]
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            if index_status == "?" and worktree_status == "?":
                untracked.append(path)
                continue
            if index_status not in (" ", "?"):
                staged.append(path)
            if worktree_status not in (" ", "?"):
                modified.append(path)
        return untracked, modified, staged

    def get_status(self, repo_path: Path) -> RepoStatus:
        repo_path = Path(repo_path)
        commit = self.get_latest_commit(repo_path)
        untracked, modified, staged = self.get_working_tree_status(repo_path)
        is_clean = not (untracked or modified or staged)
        return RepoStatus(
            commit=commit,
            untracked=untracked,
            modified=modified,
            staged=staged,
            is_clean=is_clean,
        )
