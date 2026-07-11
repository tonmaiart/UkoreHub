import subprocess

import pytest

from core.exceptions import GitOperationError
from core.git_service import GitService


def _run_git(args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path):
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    _run_git(["init"], cwd=repo_path)
    _run_git(["config", "user.email", "test@example.com"], cwd=repo_path)
    _run_git(["config", "user.name", "Test User"], cwd=repo_path)
    (repo_path / "committed.txt").write_text("hello\n", encoding="utf-8")
    _run_git(["add", "committed.txt"], cwd=repo_path)
    _run_git(["commit", "-m", "Initial commit"], cwd=repo_path)
    return repo_path


def test_get_latest_commit(repo):
    service = GitService()
    commit = service.get_latest_commit(repo)
    assert commit is not None
    assert commit.message == "Initial commit"
    assert commit.author == "Test User"
    assert len(commit.hash) == 40


def test_get_latest_commit_no_commits(tmp_path):
    repo_path = tmp_path / "empty_repo"
    repo_path.mkdir()
    _run_git(["init"], cwd=repo_path)
    service = GitService()
    assert service.get_latest_commit(repo_path) is None


def test_get_working_tree_status(repo):
    (repo / "untracked.txt").write_text("new\n", encoding="utf-8")
    (repo / "committed.txt").write_text("modified\n", encoding="utf-8")
    (repo / "staged.txt").write_text("staged\n", encoding="utf-8")
    _run_git(["add", "staged.txt"], cwd=repo)

    service = GitService()
    untracked, modified, staged = service.get_working_tree_status(repo)

    assert "untracked.txt" in untracked
    assert "committed.txt" in modified
    assert "staged.txt" in staged


def test_get_status_combines(repo):
    (repo / "untracked.txt").write_text("new\n", encoding="utf-8")
    service = GitService()
    status = service.get_status(repo)
    assert status.commit is not None
    assert "untracked.txt" in status.untracked
    assert status.is_clean is False


def test_get_status_not_a_repo(tmp_path):
    not_a_repo = tmp_path / "plain_folder"
    not_a_repo.mkdir()
    service = GitService()
    with pytest.raises(GitOperationError):
        service.get_status(not_a_repo)
