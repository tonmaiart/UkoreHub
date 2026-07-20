from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from core.models import Project, Repo


class BrowserLinkPage(QWidget):
    """One dynamically-created top-level tab per configured Browser Link —
    embeds that link's URL behind a small Back/Forward/Reset toolbar (the
    shared template every Browser Link tab uses). Rebuilt from scratch
    whenever the active repo (or its links) change, see
    interface/main_window.py, so it doesn't need to react to set_repo()
    itself beyond accepting the call.

    `profile` is a single QWebEngineProfile shared across every Browser
    Link tab (constructed once in MainWindow, see
    interface/browser_links/web_engine_profile.py) with persistent, disk-backed cookie
    storage — so logging into e.g. a Notion or Google Sheet link survives
    quitting and relaunching the app instead of needing to log in again
    every session."""

    def __init__(self, url: str, profile: QWebEngineProfile, parent=None):
        super().__init__(parent)
        self._original_url = QUrl(url)

        self.view = QWebEngineView()
        self.view.setPage(QWebEnginePage(profile, self.view))
        self.view.setUrl(self._original_url)

        self.back_button = QPushButton("< Back")
        self.back_button.clicked.connect(self.view.back)
        self.forward_button = QPushButton("Forward >")
        self.forward_button.clicked.connect(self.view.forward)
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self._on_reset)

        toolbar_row = QHBoxLayout()
        toolbar_row.addWidget(self.back_button)
        toolbar_row.addWidget(self.forward_button)
        toolbar_row.addWidget(self.reset_button)
        toolbar_row.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(toolbar_row)
        layout.addWidget(self.view, stretch=1)

    def _on_reset(self) -> None:
        self.view.setUrl(self._original_url)

    def set_repo(self, project: Project | None, repo: Repo | None, workspace_root: str | None) -> None:
        pass
