import subprocess

import pytest

from core.git_service import GitService


def _run_git(args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _init_repo_with_remote(path, remote_url):
    path.mkdir(parents=True, exist_ok=True)
    _run_git(["init", "-b", "main"], cwd=path)
    _run_git(["config", "user.email", "test@example.com"], cwd=path)
    _run_git(["config", "user.name", "Test User"], cwd=path)
    _run_git(["remote", "add", "origin", remote_url], cwd=path)


def test_get_github_owner_repo_https(tmp_path):
    repo_path = tmp_path / "repo"
    _init_repo_with_remote(repo_path, "https://github.com/octocat/Hello-World.git")
    service = GitService()
    assert service.get_github_owner_repo(repo_path) == ("octocat", "Hello-World")


def test_get_github_owner_repo_ssh(tmp_path):
    repo_path = tmp_path / "repo"
    _init_repo_with_remote(repo_path, "git@github.com:octocat/Hello-World.git")
    service = GitService()
    assert service.get_github_owner_repo(repo_path) == ("octocat", "Hello-World")


def test_get_github_owner_repo_https_no_dotgit_suffix(tmp_path):
    repo_path = tmp_path / "repo"
    _init_repo_with_remote(repo_path, "https://github.com/octocat/Hello-World")
    service = GitService()
    assert service.get_github_owner_repo(repo_path) == ("octocat", "Hello-World")


def test_get_github_owner_repo_non_github_host(tmp_path):
    repo_path = tmp_path / "repo"
    _init_repo_with_remote(repo_path, "https://gitlab.com/octocat/Hello-World.git")
    service = GitService()
    assert service.get_github_owner_repo(repo_path) is None


def test_get_github_owner_repo_no_remote(tmp_path):
    repo_path = tmp_path / "repo"
    repo_path.mkdir(parents=True)
    _run_git(["init", "-b", "main"], cwd=repo_path)
    service = GitService()
    assert service.get_github_owner_repo(repo_path) is None


@pytest.fixture
def repo_with_commits(tmp_path):
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    _run_git(["init", "-b", "main"], cwd=repo_path)
    _run_git(["config", "user.email", "test@example.com"], cwd=repo_path)
    _run_git(["config", "user.name", "Test User"], cwd=repo_path)
    (repo_path / "a.txt").write_text("a\n", encoding="utf-8")
    (repo_path / "b.txt").write_text("b\n", encoding="utf-8")
    _run_git(["add", "a.txt", "b.txt"], cwd=repo_path)
    _run_git(["commit", "-m", "Add a and b"], cwd=repo_path)
    (repo_path / "a.txt").write_text("a2\n", encoding="utf-8")
    _run_git(["add", "a.txt"], cwd=repo_path)
    _run_git(["commit", "-m", "Update a only"], cwd=repo_path)
    return repo_path


def test_get_commit_log_for_path_scopes_to_file(repo_with_commits):
    service = GitService()
    a_commits = service.get_commit_log_for_path(repo_with_commits, "a.txt")
    b_commits = service.get_commit_log_for_path(repo_with_commits, "b.txt")
    assert [c.message for c in a_commits] == ["Update a only", "Add a and b"]
    assert [c.message for c in b_commits] == ["Add a and b"]


def test_get_commit_log_for_path_empty_repo(tmp_path):
    repo_path = tmp_path / "empty_repo"
    repo_path.mkdir()
    _run_git(["init", "-b", "main"], cwd=repo_path)
    service = GitService()
    assert service.get_commit_log_for_path(repo_path, "nope.txt") == []


def test_get_commit_log_for_path_empty_string_means_whole_repo(repo_with_commits):
    # "" represents "viewing the repo root" (no path filter) — git treats an
    # empty pathspec as an error, so this must NOT be passed through literally.
    service = GitService()
    commits = service.get_commit_log_for_path(repo_with_commits, "")
    assert [c.message for c in commits] == ["Update a only", "Add a and b"]
