from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from core.models import Project, Repo


@dataclass
class AppLifecycleContext:
    project: Project | None
    repo: Repo | None
    repo_path: Path
    extra: dict = field(default_factory=dict)


AppLifecycleHandler = Callable[[AppLifecycleContext], None]


class AppLifecycleHooks:
    """Fixed, three-point plugin lifecycle — on_app_start, on_repo_changed,
    on_app_close — replacing the old open-ended GitHookEvent pub/sub (14
    event keys spanning before/after clone/pull/push/commit plus these same
    three). That granular git-operation half had zero subscribers anywhere
    in plugins/ (removed along with it, see core/vcs/git_service.py, which
    no longer fires anything at all); the three app-lifecycle events are
    the ones interface/main_window.py always fired and are kept as the
    entire surface. Each is a plain list of handlers, isolated the same way
    the old HookRegistry.fire was — one broken plugin handler must never
    break another's, or the app-level event it was reacting to."""

    def __init__(self) -> None:
        self._on_app_start: list[AppLifecycleHandler] = []
        self._on_repo_changed: list[AppLifecycleHandler] = []
        self._on_app_close: list[AppLifecycleHandler] = []

    def subscribe_app_start(self, handler: AppLifecycleHandler) -> None:
        self._on_app_start.append(handler)

    def subscribe_repo_changed(self, handler: AppLifecycleHandler) -> None:
        self._on_repo_changed.append(handler)

    def subscribe_app_close(self, handler: AppLifecycleHandler) -> None:
        self._on_app_close.append(handler)

    def fire_app_start(self, context: AppLifecycleContext) -> list[Exception]:
        return self._fire(self._on_app_start, context)

    def fire_repo_changed(self, context: AppLifecycleContext) -> list[Exception]:
        return self._fire(self._on_repo_changed, context)

    def fire_app_close(self, context: AppLifecycleContext) -> list[Exception]:
        return self._fire(self._on_app_close, context)

    @staticmethod
    def _fire(handlers: list[AppLifecycleHandler], context: AppLifecycleContext) -> list[Exception]:
        failures: list[Exception] = []
        for handler in handlers:
            try:
                handler(context)
            except Exception as exc:  # noqa: BLE001 - intentionally broad, plugin isolation
                failures.append(exc)
        return failures
