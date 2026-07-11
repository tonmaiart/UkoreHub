import subprocess

import pytest

from core.exceptions import GitOperationError
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


def test_stage_paths(repo):
    (repo / "new.txt").write_text("new\n", encoding="utf-8")
    service = GitService()
    service.stage_paths(repo, ["new.txt"])
    _, _, staged = service.get_working_tree_status(repo)
    assert "new.txt" in staged


def test_stage_paths_empty_list_is_noop(repo):
    service = GitService()
    service.stage_paths(repo, [])  # should not raise


def test_commit(repo):
    (repo / "new.txt").write_text("new\n", encoding="utf-8")
    service = GitService()
    service.stage_paths(repo, ["new.txt"])
    service.commit(repo, "Add new file")
    commit = service.get_latest_commit(repo)
    assert commit.message == "Add new file"


def test_commit_amend(repo):
    service = GitService()
    first_commit = service.get_latest_commit(repo)
    service.commit(repo, "Amended message", amend=True)
    amended = service.get_latest_commit(repo)
    assert amended.message == "Amended message"
    assert amended.hash != first_commit.hash


def test_get_commit_log_pagination(repo):
    service = GitService()
    for i in range(3):
        (repo / f"file{i}.txt").write_text(str(i), encoding="utf-8")
        service.stage_paths(repo, [f"file{i}.txt"])
        service.commit(repo, f"Commit {i}")

    page1 = service.get_commit_log(repo, skip=0, limit=2)
    assert len(page1) == 2
    assert page1[0].message == "Commit 2"  # newest first
    assert page1[1].message == "Commit 1"

    page2 = service.get_commit_log(repo, skip=2, limit=2)
    assert page2[0].message == "Commit 0"
    assert page2[1].message == "Initial commit"


def test_get_commit_log_empty_repo(tmp_path):
    repo_path = tmp_path / "empty_repo"
    _init_repo(repo_path)
    service = GitService()
    assert service.get_commit_log(repo_path) == []


def test_has_unresolved_merge_false_normally(repo):
    service = GitService()
    assert service.has_unresolved_merge(repo) is False


def test_conflict_resolution_flow(tmp_path):
    # Simulate two clones diverging on the same file, then resolve the
    # resulting merge conflict file-by-file (ours/theirs), matching the
    # animation-pipeline "whole file, not line-level" resolution model.
    origin = tmp_path / "origin.git"
    origin.mkdir()
    subprocess.run(["git", "init", "--bare", "-b", "main", str(origin)], check=True, capture_output=True)

    clone_a = tmp_path / "clone_a"
    clone_b = tmp_path / "clone_b"
    subprocess.run(["git", "clone", str(origin), str(clone_a)], check=True, capture_output=True)
    for path in (clone_a,):
        _run_git(["config", "user.email", "a@example.com"], cwd=path)
        _run_git(["config", "user.name", "User A"], cwd=path)

    (clone_a / "shared.txt").write_text("base\n", encoding="utf-8")
    _run_git(["add", "shared.txt"], cwd=clone_a)
    _run_git(["commit", "-m", "base commit"], cwd=clone_a)
    _run_git(["push", "origin", "main"], cwd=clone_a)

    subprocess.run(["git", "clone", str(origin), str(clone_b)], check=True, capture_output=True)
    _run_git(["config", "user.email", "b@example.com"], cwd=clone_b)
    _run_git(["config", "user.name", "User B"], cwd=clone_b)

    (clone_b / "shared.txt").write_text("from B\n", encoding="utf-8")
    _run_git(["add", "shared.txt"], cwd=clone_b)
    _run_git(["commit", "-m", "B changes"], cwd=clone_b)
    _run_git(["push", "origin", "main"], cwd=clone_b)

    (clone_a / "shared.txt").write_text("from A\n", encoding="utf-8")
    _run_git(["add", "shared.txt"], cwd=clone_a)
    _run_git(["commit", "-m", "A changes"], cwd=clone_a)

    service = GitService()
    with pytest.raises(GitOperationError):
        service.pull(clone_a)

    assert service.has_unresolved_merge(clone_a) is True
    conflicted = service.get_conflicted_files(clone_a)
    assert conflicted == ["shared.txt"]

    service.resolve_conflict_file(clone_a, "shared.txt", keep="ours")
    service.complete_merge(clone_a)

    assert service.has_unresolved_merge(clone_a) is False
    assert (clone_a / "shared.txt").read_text(encoding="utf-8") == "from A\n"
