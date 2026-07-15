from __future__ import annotations

import os
import shutil
import subprocess
import sys
import urllib.parse
from pathlib import Path
from typing import Callable

from core.exceptions import GitOperationError
from core.extensibility.hooks import GitHookContext, GitHookEvent, HookRegistry
from core.models import CommitInfo, RepoStatus

OutputCallback = Callable[[str], None] | None

_FIELD_SEP = "\x1f"

# Every git subprocess call passes this so Windows doesn't briefly flash a
# console window behind the GUI (git.exe is a console app; the parent
# process here has none). No-op on non-Windows.
_NO_WINDOW_FLAGS = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

_GITHUB_TOKEN_ENV_VAR = "UKOREHUB_GITHUB_TOKEN"
_GITHUB_HOSTS = {"github.com", "www.github.com"}


def _non_interactive_env(extra: dict | None = None) -> dict:
    """Environment that makes git fail fast with a visible error instead of
    silently hanging forever waiting for a username/password/passphrase on a
    terminal nobody is watching (the classic "clone just sits there" trap
    when git is launched from a GUI app with no real TTY to prompt on).

    BatchMode=yes disables every SSH prompt, including the normal one-time
    "accept this host's fingerprint?" prompt shown the first time you SSH
    to a new host — without StrictHostKeyChecking=accept-new, a machine
    that has never SSH'd to github.com before fails every SSH clone with
    "Host key verification failed" and there is no prompt for the user to
    ever get past. accept-new auto-trusts a *new* host's key (standard
    practice for non-interactive/CI git clients) while still strictly
    verifying hosts already in known_hosts, so it doesn't weaken protection
    against a host's key actually changing later (unlike
    StrictHostKeyChecking=no, which disables verification permanently)."""
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    ssh_command = env.get("GIT_SSH_COMMAND", "ssh")
    env["GIT_SSH_COMMAND"] = f"{ssh_command} -o BatchMode=yes -o StrictHostKeyChecking=accept-new"
    if extra:
        env.update(extra)
    return env


class GitService:
    def __init__(self, git_executable: str | None = None, hooks: HookRegistry | None = None):
        self.git_executable = git_executable or shutil.which("git") or "git"
        self._github_token: str | None = None
        self._hooks = hooks

    def _fire(self, event: GitHookEvent, context: GitHookContext | None) -> None:
        if self._hooks is None or context is None:
            return
        self._hooks.fire(event, context)

    def set_github_token(self, token: str | None) -> None:
        """Token from the app's GitHub login (see interface/main_window.py),
        used to authenticate github.com HTTPS clone/pull for private repos
        without needing a separate credential setup. Never touches SSH URLs
        or non-GitHub hosts — those still rely on the user's own system git
        credentials exactly as before."""
        self._github_token = token

    def get_github_token(self) -> str | None:
        return self._github_token

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

    def get_current_branch(self, repo_path: Path) -> str:
        return self._run_capture(["rev-parse", "--abbrev-ref", "HEAD"], cwd=Path(repo_path)).strip()

    def has_upstream(self, repo_path: Path) -> bool:
        """False for a repo cloned from a brand-new/empty remote: there is
        no `origin/<branch>` yet for the local branch to track, since
        nothing has ever been pushed. `pull`/`push` use this to treat that
        case as "nothing to pull, first push needs --set-upstream" instead
        of failing on git's usual "no such ref was fetched"/"no upstream
        branch" errors, which otherwise block ever completing the first
        sync of a new repo."""
        try:
            self._run_capture(
                ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], cwd=Path(repo_path)
            )
            return True
        except GitOperationError:
            return False

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
            creationflags=_NO_WINDOW_FLAGS,
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

    def clone(
        self, git_url: str, dest: Path, on_output: OutputCallback = None, *, context: GitHookContext | None = None
    ) -> None:
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        auth_args, auth_env = self._github_auth_args_and_env(git_url)
        self._fire(GitHookEvent.BEFORE_CLONE, context)
        try:
            # --progress forces git to emit its progress meter even though
            # stdout is a pipe, not a terminal (git suppresses it by default
            # otherwise).
            self._run_streaming(
                [*auth_args, "clone", "--progress", git_url, str(dest)],
                cwd=dest.parent,
                on_output=on_output,
                extra_env=auth_env,
            )
        except GitOperationError:
            self._fire(GitHookEvent.CLONE_FAILED, context)
            raise
        self._fire(GitHookEvent.AFTER_CLONE, context)

    def pull(
        self, local_path: Path, on_output: OutputCallback = None, *, context: GitHookContext | None = None
    ) -> None:
        # Read the remote URL from the repo itself so the same github.com
        # credential check applies whether it was cloned via HTTPS or SSH.
        try:
            remote_url = self._run_capture(["remote", "get-url", "origin"], cwd=Path(local_path)).strip()
        except GitOperationError:
            remote_url = ""
        auth_args, auth_env = self._github_auth_args_and_env(remote_url)
        self._fire(GitHookEvent.BEFORE_PULL, context)
        if not self.has_upstream(Path(local_path)):
            # Remote has no commits yet (repo was cloned empty, or nothing
            # has been pushed since) — there's no `origin/<branch>` to merge
            # with, so a real `git pull` would only fail with "no such ref
            # was fetched". Nothing to pull; let the caller push first.
            if on_output:
                on_output("Nothing to pull yet (remote has no commits).")
            self._fire(GitHookEvent.AFTER_PULL, context)
            return
        try:
            # --no-rebase: explicitly request a merge (not rebase)
            # reconciliation. Without this, modern git refuses to pull at all
            # on diverged branches ("Need to specify how to reconcile
            # divergent branches") unless the user has a global
            # pull.rebase/pull.ff default configured — we can't rely on that
            # being set, and our conflict-resolution workflow below is built
            # around a real merge commit, not a rebase.
            self._run_streaming(
                [*auth_args, "pull", "--no-rebase", "--progress"],
                cwd=Path(local_path),
                on_output=on_output,
                extra_env=auth_env,
            )
        except GitOperationError:
            self._fire(GitHookEvent.PULL_FAILED, context)
            raise
        self._fire(GitHookEvent.AFTER_PULL, context)

    def open_or_sync(
        self, git_url: str, dest: Path, on_output: OutputCallback = None, *, context: GitHookContext | None = None
    ) -> str:
        dest = Path(dest)
        if not self.is_cloned(dest):
            self.clone(git_url, dest, on_output=on_output, context=context)
            return "cloned"
        self.pull(dest, on_output=on_output, context=context)
        return "pulled"

    def push(
        self, local_path: Path, on_output: OutputCallback = None, *, context: GitHookContext | None = None
    ) -> None:
        local_path = Path(local_path)
        try:
            remote_url = self._run_capture(["remote", "get-url", "origin"], cwd=local_path).strip()
        except GitOperationError:
            remote_url = ""
        auth_args, auth_env = self._github_auth_args_and_env(remote_url)
        push_args = ["push", "--progress"]
        if not self.has_upstream(local_path):
            # First push to a remote that had no commits when it was cloned:
            # plain `git push` fails with "no upstream branch" since nothing
            # was ever fetched to configure tracking against. --set-upstream
            # both creates the branch on the remote and wires up tracking so
            # every later pull/push on this repo is a normal one.
            push_args += ["--set-upstream", "origin", self.get_current_branch(local_path)]
        self._fire(GitHookEvent.BEFORE_PUSH, context)
        try:
            self._run_streaming(
                [*auth_args, *push_args], cwd=local_path, on_output=on_output, extra_env=auth_env
            )
        except GitOperationError:
            self._fire(GitHookEvent.PUSH_FAILED, context)
            raise
        self._fire(GitHookEvent.AFTER_PUSH, context)

    def stage_paths(self, repo_path: Path, paths: list[str]) -> None:
        if not paths:
            return
        self._run_capture(["add", "--", *paths], cwd=Path(repo_path))

    def unstage_paths(self, repo_path: Path, paths: list[str]) -> None:
        if not paths:
            return
        self._run_capture(["reset", "HEAD", "--", *paths], cwd=Path(repo_path))

    def get_commit_files(self, repo_path: Path, commit_hash: str) -> list[str]:
        """Relative paths of every file changed in a single commit. --root
        is required for this to return anything on a repo's very first
        commit (no parent to diff against otherwise)."""
        try:
            output = self._run_capture(
                ["diff-tree", "--no-commit-id", "--name-only", "-r", "--root", commit_hash],
                cwd=Path(repo_path),
            )
        except GitOperationError:
            return []
        return [line for line in output.splitlines() if line]

    def revert_paths(self, repo_path: Path, *, modified_paths: list[str], untracked_paths: list[str]) -> None:
        """Discards working-tree changes. Tracked/modified files are reset to
        HEAD via checkout; untracked files have no HEAD version to reset to,
        so they're removed instead via git clean."""
        repo_path = Path(repo_path)
        if modified_paths:
            self._run_capture(["checkout", "--", *modified_paths], cwd=repo_path)
        if untracked_paths:
            self._run_capture(["clean", "-f", "--", *untracked_paths], cwd=repo_path)

    def commit(
        self, repo_path: Path, message: str, amend: bool = False, *, context: GitHookContext | None = None
    ) -> None:
        args = ["commit"]
        message = message.strip()
        if amend:
            args.append("--amend")
            if message:
                args += ["-m", message]
            else:
                args.append("--no-edit")
        else:
            args += ["-m", message]
        self._fire(GitHookEvent.BEFORE_COMMIT, context)
        try:
            self._run_capture(args, cwd=Path(repo_path))
        except GitOperationError:
            self._fire(GitHookEvent.COMMIT_FAILED, context)
            raise
        self._fire(GitHookEvent.AFTER_COMMIT, context)

    def has_unresolved_merge(self, repo_path: Path) -> bool:
        return (Path(repo_path) / ".git" / "MERGE_HEAD").exists()

    _CONFLICT_CODES = {"UU", "AA", "DD", "AU", "UA", "UD", "DU"}

    def get_conflicted_files(self, repo_path: Path) -> list[str]:
        output = self._run_capture(["status", "--porcelain=v1"], cwd=Path(repo_path))
        conflicted = []
        for line in output.splitlines():
            if not line:
                continue
            if line[:2] in self._CONFLICT_CODES:
                conflicted.append(line[3:])
        return conflicted

    def resolve_conflict_file(self, repo_path: Path, file_path: str, keep: str) -> None:
        side = "--ours" if keep == "ours" else "--theirs"
        repo_path = Path(repo_path)
        self._run_capture(["checkout", side, "--", file_path], cwd=repo_path)
        self._run_capture(["add", "--", file_path], cwd=repo_path)

    def complete_merge(self, repo_path: Path) -> None:
        self._run_capture(["commit", "--no-edit"], cwd=Path(repo_path))

    def get_commit_log(self, repo_path: Path, skip: int = 0, limit: int = 30) -> list[CommitInfo]:
        try:
            output = self._run_capture(
                [
                    "log",
                    f"--skip={skip}",
                    f"--max-count={limit}",
                    f"--pretty=format:%H{_FIELD_SEP}%an{_FIELD_SEP}%ae{_FIELD_SEP}%aI{_FIELD_SEP}%s",
                ],
                cwd=Path(repo_path),
            )
        except GitOperationError:
            return []
        commits = []
        for line in output.splitlines():
            if not line:
                continue
            hash_, author, email, date, message = line.split(_FIELD_SEP, 4)
            commits.append(CommitInfo(hash=hash_, author=author, email=email, date=date, message=message))
        return commits

    def get_commit_log_for_path(self, repo_path: Path, relative_path: str, limit: int = 30) -> list[CommitInfo]:
        args = [
            "log",
            f"--max-count={limit}",
            f"--pretty=format:%H{_FIELD_SEP}%an{_FIELD_SEP}%ae{_FIELD_SEP}%aI{_FIELD_SEP}%s",
        ]
        # An empty pathspec is invalid ("fatal: empty string is not a valid
        # pathspec") — omit it entirely to mean "whole repo" (viewing the
        # repo root), only scope to a path when one was actually given.
        if relative_path:
            args += ["--", relative_path]
        try:
            output = self._run_capture(args, cwd=Path(repo_path))
        except GitOperationError:
            return []
        commits = []
        for line in output.splitlines():
            if not line:
                continue
            hash_, author, email, date, message = line.split(_FIELD_SEP, 4)
            commits.append(CommitInfo(hash=hash_, author=author, email=email, date=date, message=message))
        return commits

    def get_github_owner_repo(self, repo_path: Path) -> tuple[str, str] | None:
        """Parses `origin`'s URL for an owner/repo pair, handling both SSH
        (git@github.com:owner/repo.git) and HTTPS (https://github.com/owner/repo.git)
        forms. Returns None if origin isn't a github.com remote at all."""
        try:
            remote_url = self._run_capture(["remote", "get-url", "origin"], cwd=Path(repo_path)).strip()
        except GitOperationError:
            return None
        return self.parse_github_owner_repo(remote_url)

    @staticmethod
    def parse_github_owner_repo(git_url: str) -> tuple[str, str] | None:
        """Same parsing as get_github_owner_repo, but on a raw URL string
        instead of a local repo's `origin` — usable before a repo is even
        cloned (e.g. Repo.git_url straight from the metadata store)."""
        remote_url = git_url[: -len(".git")] if git_url.endswith(".git") else git_url
        if remote_url.startswith("git@github.com:"):
            path = remote_url[len("git@github.com:") :]
        else:
            parsed = urllib.parse.urlparse(remote_url)
            if parsed.hostname not in _GITHUB_HOSTS:
                return None
            path = parsed.path.lstrip("/")
        parts = path.split("/")
        if len(parts) != 2 or not all(parts):
            return None
        return parts[0], parts[1]

    def _run_capture(self, args: list[str], cwd: Path) -> str:
        result = subprocess.run(
            [self.git_executable, *args],
            cwd=str(cwd),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            env=_non_interactive_env(),
            creationflags=_NO_WINDOW_FLAGS,
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
