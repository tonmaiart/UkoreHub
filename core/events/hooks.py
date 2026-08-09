from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable

from core.models import Project, Repo


class GitHookEvent(str, Enum):
    BEFORE_CLONE = "before_clone"
    AFTER_CLONE = "after_clone"
    CLONE_FAILED = "clone_failed"
    BEFORE_PULL = "before_pull"
    AFTER_PULL = "after_pull"
    PULL_FAILED = "pull_failed"
    BEFORE_PUSH = "before_push"
    AFTER_PUSH = "after_push"
    PUSH_FAILED = "push_failed"
    BEFORE_COMMIT = "before_commit"
    AFTER_COMMIT = "after_commit"
    COMMIT_FAILED = "commit_failed"
    REPO_SELECTED = "repo_selected"
    APP_STARTED = "app_started"


@dataclass
class GitHookContext:
    project: Project | None
    repo: Repo | None
    repo_path: Path
    extra: dict = field(default_factory=dict)


HookHandler = Callable[[GitHookContext], None]


class HookRegistry:
    """Plain-Python pub/sub — deliberately not a QObject so core/ stays
    importable and testable without a QApplication."""

    def __init__(self) -> None:
        self._handlers: dict[GitHookEvent, list[HookHandler]] = {}

    def subscribe(self, event: GitHookEvent, handler: HookHandler) -> None:
        self._handlers.setdefault(event, []).append(handler)

    def fire(self, event: GitHookEvent, context: GitHookContext) -> list[Exception]:
        """Calls every handler subscribed to `event`, each isolated in its
        own try/except — one broken plugin handler must never break a git
        operation for everyone else. Returns the exceptions it swallowed so
        the caller can log them."""
        failures: list[Exception] = []
        for handler in self._handlers.get(event, []):
            try:
                handler(context)
            except Exception as exc:  # noqa: BLE001 - intentionally broad, plugin isolation
                failures.append(exc)
        return failures
