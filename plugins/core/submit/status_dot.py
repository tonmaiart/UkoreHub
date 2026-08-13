from __future__ import annotations

from PySide6.QtWidgets import QLabel, QStyle

_DOT_SIZE = 14


class RepoStatusDot(QLabel):
    """Small status icon shown at the right edge of the Submit tab's own
    sidebar row (see SectionSpec.trailing_widget_factory in
    plugin_api/registries/section_registry.py — plugin.py hands this widget to it). Hidden
    ("loading") while no verified status is currently known; RepoGitStatusPage
    updates the icon directly via set_state, SectionTabList only lays it out.

    States (see RepoGitStatusPage._on_status_ready / refresh_status /
    _on_freshness_expired for what drives each one):
    - "loading": a status check is in flight, or the last one is more than
      10 minutes stale — hidden, no icon.
    - "dirty": the working tree has modified/staged changes pending —
      QStyle.SP_MessageBoxWarning.
    - "fresh": the working tree was clean the last time it was checked, and
      that check happened within the last 10 minutes — QStyle.SP_DialogApplyButton.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(_DOT_SIZE, _DOT_SIZE)
        self.set_state("loading")

    def set_state(self, state: str) -> None:
        if state == "loading":
            self.setVisible(False)
            return
        standard_icon = QStyle.SP_MessageBoxWarning if state == "dirty" else QStyle.SP_DialogApplyButton
        icon = self.style().standardIcon(standard_icon)
        self.setPixmap(icon.pixmap(_DOT_SIZE, _DOT_SIZE))
        self.setToolTip("Uncommitted changes" if state == "dirty" else "Up to date")
        self.setVisible(True)
