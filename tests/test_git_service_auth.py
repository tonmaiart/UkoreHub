from core.git_service import GitService, _non_interactive_env


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


def test_non_interactive_env_disables_prompts_but_accepts_new_ssh_hosts():
    env = _non_interactive_env()
    assert env["GIT_TERMINAL_PROMPT"] == "0"
    # BatchMode=yes alone would also swallow the one-time "accept this
    # host's fingerprint?" SSH prompt, permanently breaking every SSH clone
    # on a machine that has never connected to the host before ("Host key
    # verification failed") — accept-new must be present alongside it.
    assert "-o BatchMode=yes" in env["GIT_SSH_COMMAND"]
    assert "-o StrictHostKeyChecking=accept-new" in env["GIT_SSH_COMMAND"]


def test_non_interactive_env_preserves_existing_ssh_command():
    env = _non_interactive_env(extra={"GIT_SSH_COMMAND": "custom-ssh-wrapper"})
    # extra overrides GIT_SSH_COMMAND wholesale (matches existing behavior
    # for any key in `extra`) rather than being appended to the computed one.
    assert env["GIT_SSH_COMMAND"] == "custom-ssh-wrapper"
