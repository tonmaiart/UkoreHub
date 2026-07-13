from pathlib import Path

from core.extensibility.hooks import GitHookContext, GitHookEvent, HookRegistry


def _context(tmp_path) -> GitHookContext:
    return GitHookContext(project=None, repo=None, repo_path=Path(tmp_path))


def test_subscribe_and_fire_calls_handler(tmp_path):
    registry = HookRegistry()
    received = []
    registry.subscribe(GitHookEvent.AFTER_COMMIT, received.append)

    context = _context(tmp_path)
    failures = registry.fire(GitHookEvent.AFTER_COMMIT, context)

    assert received == [context]
    assert failures == []


def test_fire_with_no_subscribers_is_noop(tmp_path):
    registry = HookRegistry()
    assert registry.fire(GitHookEvent.AFTER_COMMIT, _context(tmp_path)) == []


def test_multiple_handlers_all_run(tmp_path):
    registry = HookRegistry()
    calls = []
    registry.subscribe(GitHookEvent.AFTER_PUSH, lambda ctx: calls.append("a"))
    registry.subscribe(GitHookEvent.AFTER_PUSH, lambda ctx: calls.append("b"))

    registry.fire(GitHookEvent.AFTER_PUSH, _context(tmp_path))

    assert calls == ["a", "b"]


def test_handler_exception_is_isolated_and_collected(tmp_path):
    registry = HookRegistry()
    calls = []

    def broken(_ctx):
        raise RuntimeError("boom")

    registry.subscribe(GitHookEvent.AFTER_PULL, broken)
    registry.subscribe(GitHookEvent.AFTER_PULL, lambda ctx: calls.append("still runs"))

    failures = registry.fire(GitHookEvent.AFTER_PULL, _context(tmp_path))

    assert calls == ["still runs"]
    assert len(failures) == 1
    assert isinstance(failures[0], RuntimeError)


def test_events_are_isolated_from_each_other(tmp_path):
    registry = HookRegistry()
    calls = []
    registry.subscribe(GitHookEvent.BEFORE_COMMIT, lambda ctx: calls.append("before"))
    registry.subscribe(GitHookEvent.AFTER_COMMIT, lambda ctx: calls.append("after"))

    registry.fire(GitHookEvent.BEFORE_COMMIT, _context(tmp_path))

    assert calls == ["before"]
