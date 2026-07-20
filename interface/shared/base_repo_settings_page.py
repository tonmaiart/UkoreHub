from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from core.exceptions import NotFoundError
from core.models import Project, Repo
from core.store import LocalConfigStore, MetadataStore
from interface.shared.widget_helpers import show_exclusive


class BaseRepoSettingsPage(QWidget):
    """Shared base for a Settings tab that's scoped to a single repo and
    resolves the active project/repo itself from local_config_store, rather
    than waiting for a set_repo() call MainWindow never makes for Settings
    pages (see interface/repo_settings/README.md and
    interface/browser_links/README.md — both domains have a tab built on
    this). Collapses the empty_label/content_widget scaffolding and
    refresh() preamble that LocalRepositoryPage, EnablePluginPage, and
    BrowserLinksSettingsPage each had independently, byte-for-byte
    identical, before 2026-07-20.

    This __init__ leaves content_widget layout-less on purpose — a
    subclass adds exactly one layout onto it in its own __init__ (even a
    scroll-wrapped one, like BrowserLinksSettingsPage's), after calling
    super().__init__(), then calls self.refresh() itself once its content
    widgets actually exist. Override _on_refresh_content() for the
    type-specific rebuild; refresh() itself (the resolve-active-repo +
    NotFoundError + show_exclusive part) should not need overriding."""

    def __init__(self, parent=None, *, store: MetadataStore, local_config_store: LocalConfigStore):
        super().__init__(parent)
        self.store = store
        self.local_config_store = local_config_store
        self._project: Project | None = None
        self._repo: Repo | None = None

        self.empty_label = QLabel("Select a repo to see this information.")
        self.content_widget = QWidget()

        layout = QVBoxLayout(self)
        layout.addWidget(self.empty_label)
        layout.addWidget(self.content_widget)

    def refresh(self) -> None:
        """Re-resolves the active project/repo from local_config_store and,
        on success, calls _on_refresh_content() for the subclass's own
        rebuild. Called on construction and on every
        SettingsTabSpec.on_activated (see
        interface/builtin_settings_tabs.py's shared _trigger_refresh)."""
        project_id = self.local_config_store.active_project_id
        repo_id = self.local_config_store.active_repo_id
        if not project_id or not repo_id:
            self._invalidate()
            return
        try:
            self._project = self.store.get_project(project_id)
            self._repo = self.store.get_repo(project_id, repo_id)
        except NotFoundError:
            self._invalidate()
            return
        show_exclusive(self.content_widget, self.empty_label)
        self._on_refresh_content()

    def _invalidate(self) -> None:
        self._project = None
        self._repo = None
        show_exclusive(self.empty_label, self.content_widget)

    def _on_refresh_content(self) -> None:
        """Override to rebuild content_widget's own content once
        self._project/self._repo are known-good. No-op by default."""
