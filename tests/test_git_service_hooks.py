import subprocess

import pytest

from core.exceptions import GitOperationError
from core.extensibility.hooks import GitHookContext, GitHookEvent, HookRegistry
from core.git_service import GitService


def _run_git(args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _init_repo(path):
    path.mkdir(parents=True, exist_ok=True)
    _run_git(["init", "-b", "main"], cwd=path)
    _run_git(["config", "user.email", "test@example.com"], cwd=path)
    _run_git(["config", "user.name", "Test User"], cwd=path)


@pytest.fixture
def repo(tmp_path):
    repo_path = tmp_path / "repo"
    _init_repo(repo_path)
    (repo_path / "committed.txt").write_text("hello\n", encoding="utf-8")
    _run_git(["add", "committed.txt"], cwd=repo_path)
    _run_git(["commit", "-m", "Initial commit"], cwd=repo_path)
    return repo_path


@pytest.fixture
def cloned_repo(tmp_path):
    """A bare origin plus a working clone with one pushed commit, so pull()
    and push() have something real to talk to."""
    origin = tmp_path / "origin.git"
    origin.mkdir()
    subprocess.run(["git", "init", "--bare", "-b", "main", str(origin)], check=True, capture_output=True)

    clone = tmp_path / "clone"
    subprocess.run(["git", "clone", str(origin), str(clone)], check=True, capture_output=True)
    _run_git(["config", "user.email", "a@example.com"], cwd=clone)
    _run_git(["config", "user.name", "A"], cwd=clone)
    (clone / "f.txt").write_text("x\n", encoding="utf-8")
    _run_git(["add", "f.txt"], cwd=clone)
    _run_git(["commit", "-m", "init"], cwd=clone)
    _run_git(["push", "origin", "main"], cwd=clone)
    return origin, clone


def test_commit_fires_before_then_after_with_context(repo):
    hooks = HookRegistry()
    order = []
    hooks.subscribe(GitHookEvent.BEFORE_COMMIT, lambda ctx: order.append(("before", ctx)))
    hooks.subscribe(GitHookEvent.AFTER_COMMIT, lambda ctx: order.append(("after", ctx)))
    service = GitService(hooks=hooks)
    context = GitHookContext(project=None, repo=None, repo_path=repo)

    (repo / "new.txt").write_text("new\n", encoding="utf-8")
    service.stage_paths(repo, ["new.txt"])
    service.commit(repo, "Add new file", context=context)

    assert [name for name, _ in order] == ["before", "after"]
    assert order[0][1] is context
    assert order[1][1] is context


def test_commit_failure_fires_commit_failed_and_still_raises(repo):
    hooks = HookRegistry()
    failed = []
    after = []
    hooks.subscribe(GitHookEvent.COMMIT_FAILED, lambda ctx: failed.append(ctx))
    hooks.subscribe(GitHookEvent.AFTER_COMMIT, lambda ctx: after.append(ctx))
    service = GitService(hooks=hooks)
    context = GitHookContext(project=None, repo=None, repo_path=repo)

    # Nothing staged and an empty message — git refuses this commit.
    with pytest.raises(GitOperationError):
        service.commit(repo, "", context=context)

    assert len(failed) == 1
    assert after == []


def test_commit_without_context_does_not_fire_hooks(repo):
    hooks = HookRegistry()
    calls = []
    hooks.subscribe(GitHookEvent.AFTER_COMMIT, lambda ctx: calls.append(ctx))
    service = GitService(hooks=hooks)

    (repo / "new.txt").write_text("new\n", encoding="utf-8")
    service.stage_paths(repo, ["new.txt"])
    service.commit(repo, "Add new file")  # no context= passed

    assert calls == []


def test_pull_and_push_fire_before_after(cloned_repo):
    _origin, clone = cloned_repo
    hooks = HookRegistry()
    order = []
    for event in (GitHookEvent.BEFORE_PULL, GitHookEvent.AFTER_PULL, GitHookEvent.BEFORE_PUSH, GitHookEvent.AFTER_PUSH):
        hooks.subscribe(event, lambda ctx, e=event: order.append(e))
    service = GitService(hooks=hooks)
    context = GitHookContext(project=None, repo=None, repo_path=clone)

    service.pull(clone, context=context)

    (clone / "another.txt").write_text("y\n", encoding="utf-8")
    _run_git(["add", "another.txt"], cwd=clone)
    _run_git(["commit", "-m", "another"], cwd=clone)
    service.push(clone, context=context)

    assert order == [
        GitHookEvent.BEFORE_PULL,
        GitHookEvent.AFTER_PULL,
        GitHookEvent.BEFORE_PUSH,
        GitHookEvent.AFTER_PUSH,
    ]


def test_clone_fires_before_then_after(tmp_path, cloned_repo):
    origin, _clone = cloned_repo
    hooks = HookRegistry()
    order = []
    hooks.subscribe(GitHookEvent.BEFORE_CLONE, lambda ctx: order.append("before"))
    hooks.subscribe(GitHookEvent.AFTER_CLONE, lambda ctx: order.append("after"))
    service = GitService(hooks=hooks)
    dest = tmp_path / "fresh_clone"
    context = GitHookContext(project=None, repo=None, repo_path=dest)

    service.clone(str(origin), dest, context=context)

    assert order == ["before", "after"]
    assert (dest / "f.txt").exists()


def test_clone_failure_fires_clone_failed(tmp_path):
    hooks = HookRegistry()
    failed = []
    hooks.subscribe(GitHookEvent.CLONE_FAILED, lambda ctx: failed.append(ctx))
    service = GitService(hooks=hooks)
    dest = tmp_path / "nowhere"
    context = GitHookContext(project=None, repo=None, repo_path=dest)

    with pytest.raises(GitOperationError):
        service.clone(str(tmp_path / "does-not-exist.git"), dest, context=context)

    assert len(failed) == 1
