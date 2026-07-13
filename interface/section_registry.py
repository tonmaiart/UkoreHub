from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtWidgets import QWidget

from core.exceptions import ValidationError


@dataclass(frozen=True)
class SectionSpec:
    key: str
    label: str
    order: int
    page_factory: Callable[[], QWidget]
    # Optional: given the constructed page, return any background QThread
    # workers it owns, so MainWindow.closeEvent can terminate them safely
    # without needing to know a plugin page's internals.
    background_threads: Callable[[QWidget], list] | None = None
    # False (default): page is shown inside the shared sidebar + content
    # stack (Repo, About). True: page gets its own full-width top-level view
    # with no sidebar (Explorer, Submit) — see main_window.py's view_stack
    # construction.
    standalone: bool = False


class SectionRegistry:
    """Open, ordered replacement for the old closed SectionKey enum — both
    built-in and plugin-provided sidebar sections register into the same
    collection."""

    def __init__(self) -> None:
        self._specs: dict[str, SectionSpec] = {}

    def register(self, spec: SectionSpec) -> None:
        if spec.key in self._specs:
            raise ValidationError(f"Section key '{spec.key}' is already registered")
        self._specs[spec.key] = spec

    def ordered(self) -> list[SectionSpec]:
        return sorted(self._specs.values(), key=lambda spec: (spec.order, spec.key))
