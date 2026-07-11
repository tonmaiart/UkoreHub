from __future__ import annotations

import os
import shutil
import subprocess
import urllib.parse
from pathlib import Path
from typing import Callable

from core.exceptions import GitOperationError
from core.models import CommitInfo, RepoStatus

OutputCallback = Callable[[str], None] | None

_FIELD_SEP = "\x1f"

_GITHUB_TOKEN_ENV_VAR = "UKOREHUB_GITHUB_TOKEN"
_GITHUB_HOSTS = {"github.com", "www.github.com"}


def _non_interactive_env(extra: dict | None = None) -> dict:
    """Environment that makes git fail fast with a visible error instead of
    silently hanging forever waiting for a username/password/passphrase on a
    terminal nobody is watching (the classic "clone just sits there" trap
    when git is launched from a GUI app with no real TTY to prompt on)."""
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    ssh_command = env.get("GIT_SSH_COMMAND", "ssh")
    env["GIT_SSH_COMMAND"] = f"{ssh_command} -o BatchMode=yes"
    if extra:
        env.update(extra)
    return env


class GitService:
    def __init__(self, git_executable: str | None = None):
        self.git_executable = git_executable or shutil.which("git") or "git"
        self._github_token: str | None = None

    def set_github_token(self, token: str | None) -> None:
        """Token from the app's GitHub login (see interface/main_window.py),
        used to authenticate github.com HTTPS clone/pull for private repos
        without needing a separate credential setup. Never touches SSH URLs
        or non-GitHub hosts — those still rely on the user's own system git
        credentials exactly as before."""
        self._github_token = token

    def _github_auth_args_and_env(self, git_url: str) -> tuple[list[str], dict]:
        if not self._github_token:
            return [], {}
        parsed = urllib.parse.urlparse(git_url)
        if parsed.scheme != "https" or parsed.hostname not in _GITHUB_HOSTS:
            return [], {}
        # Credentials are passed via an environment variable, never on the
        # command line or written to disk, so they can't leak through `ps aux`
        # or a leftover temp file.
        helper = f'!f() {{ echo username=x-access-token; echo "password=${_GITHUB_TOKEN_ENV_VAR}"; }}; f'
        return ["-c", f"credential.helper={helper}"], {_GITHUB_TOKEN_ENV_VAR: self._github_token}

    def is_cloned(self, local_path: Path) -> bool:
        return (Path(local_path) / ".git").exists()

    def _run_streaming(
        self, args: list[str], cwd: Path | None, on_output: OutputCallback, extra_env: dict | None = None
    ) -> None:
        process = subprocess.Popen(
            [self.git_executable, *args],
            cwd=str(cwd) if cwd else None,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=_non_interactive_env(extra_env),
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
        auth_args, auth_env = self._github_auth_args_and_env(git_url)
        # --progress forces git to emit its progress meter even though stdout
        # is a pipe, not a terminal (git suppresses it by default otherwise).
        self._run_streaming(
            [*auth_args, "clone", "--progress", git_url, str(dest)],
            cwd=dest.parent,
            on_output=on_output,
            extra_env=auth_env,
        )

    def pull(self, local_path: Path, on_output: OutputCallback = None) -> None:
        # Read the remote URL from the repo itself so the same github.com
        # credential check applies whether it was cloned via HTTPS or SSH.
        try:
            remote_url = self._run_capture(["remote", "get-url", "origin"], cwd=Path(local_path)).strip()
        except GitOperationError:
            remote_url = ""
        auth_args, auth_env = self._github_auth_args_and_env(remote_url)
        self._run_streaming(
            [*auth_args, "pull", "--progress"], cwd=Path(local_path), on_output=on_output, extra_env=auth_env
        )

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
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            env=_non_interactive_env(),
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
