from core.git_service import GitService


def test_no_auth_args_when_no_token():
    service = GitService()
    args, env = service._github_auth_args_and_env("https://github.com/owner/repo.git")
    assert args == []
    assert env == {}


def test_no_auth_args_for_non_github_host():
    service = GitService()
    service.set_github_token("abc123")
    args, env = service._github_auth_args_and_env("https://gitlab.com/owner/repo.git")
    assert args == []
    assert env == {}


def test_no_auth_args_for_ssh_url():
    service = GitService()
    service.set_github_token("abc123")
    args, env = service._github_auth_args_and_env("git@github.com:owner/repo.git")
    assert args == []
    assert env == {}


def test_auth_args_for_github_https_with_token():
    service = GitService()
    service.set_github_token("abc123")
    args, env = service._github_auth_args_and_env("https://github.com/owner/repo.git")
    assert args[0] == "-c"
    assert "credential.helper=" in args[1]
    assert len(env) == 1
    (env_var_name, env_var_value), = env.items()
    assert env_var_value == "abc123"
    # the token value itself must never appear in the argv-visible helper string
    assert "abc123" not in args[1]
    assert env_var_name in args[1]


def test_set_github_token_none_clears_it():
    service = GitService()
    service.set_github_token("abc123")
    service.set_github_token(None)
    args, env = service._github_auth_args_and_env("https://github.com/owner/repo.git")
    assert args == []
    assert env == {}
