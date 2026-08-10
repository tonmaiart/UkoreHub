from __future__ import annotations

from PySide6.QtWidgets import QLabel

_DOT_SIZE = 10


class RepoStatusDot(QLabel):
    """Small colored circle shown at the right edge of the Submit tab's own
    sidebar row (see SectionSpec.trailing_widget_factory in
    interface/section_registry.py — plugin.py hands this widget to it). Hidden
    ("loading") while no verified status is currently known; RepoGitStatusPage
    updates the color directly via set_state, SectionTabList only lays it out.

    States (see RepoGitStatusPage._on_status_ready / refresh_status /
    _on_freshness_expired for what drives each one):
    - "loading": a status check is in flight, or the last one is more than
      10 minutes stale — hidden, no color.
    - "dirty": the working tree has modified/staged changes pending —
      yellow (interface.theme's warning color).
    - "fresh": the working tree was clean the last time it was checked, and
      that check happened within the last 10 minutes — blue (interface.theme's
      accent color).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("submitStatusDot")
        self.setFixedSize(_DOT_SIZE, _DOT_SIZE)
        self.set_state("loading")

    def set_state(self, state: str) -> None:
        if state == "loading":
            self.setVisible(False)
            return
        self.setProperty("state", state)
        self.setVisible(True)
        self.style().unpolish(self)
        self.style().polish(self)
