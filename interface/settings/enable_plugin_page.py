from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from core.exceptions import NotFoundError
from core.extensibility.loader import DiscoveredPlugin
from core.models import Project, Repo
from core.store import LocalConfigStore, MetadataStore
from interface.shared.widget_helpers import show_exclusive

_DESCRIPTION = (
    "Choose which plugins actually apply to this repo. Unchecked plugins hide "
    "their sidebar tab while this repo is active. Leaving everything checked "
    "(the default for a new repo) applies every plugin, same as before this "
    "setting existed. Saved to the shared Project/Repo registry (Studio)."
)


class EnablePluginPage(QWidget):
    """Per-repo toggle for plugins/studio + plugins/local entries
    (Repo.active_plugin_ids) — distinct from the existing Add-ons concept
    (Repo.enabled_addon_ids, edited in About > Requirement): unlike Add-ons,
    this one actually hides the plugin's sidebar section for repos that
    don't have it checked (see MainWindow._apply_plugin_visibility). Scoped
    to a single repo, so like BrowserLinksSettingsPage it resolves the
    active project/repo itself from local_config_store on refresh()."""

    def __init__(
        self,
        parent=None,
        *,
        store: MetadataStore,
        local_config_store: LocalConfigStore,
        plugin_catalog: list[DiscoveredPlugin],
    ):
        super().__init__(parent)
        self.store = store
        self.local_config_store = local_config_store
        self._plugin_catalog = plugin_catalog
        self._project: Project | None = None
        self._repo: Repo | None = None
        self._loading = False

        self.empty_label = QLabel("Select a repo to see this information.")

        description_label = QLabel(_DESCRIPTION)
        description_label.setWordWrap(True)

        self.list_widget = QListWidget()
        self.list_widget.itemChanged.connect(self._on_item_changed)

        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(description_label)
        content_layout.addWidget(self.list_widget)

        layout = QVBoxLayout(self)
        layout.addWidget(self.empty_label)
        layout.addWidget(self.content_widget)

        self.refresh()

    def refresh(self) -> None:
        project_id = self.local_config_store.active_project_id
        repo_id = self.local_config_store.active_repo_id
        if not project_id or not repo_id:
            self._project = None
            self._repo = None
            show_exclusive(self.empty_label, self.content_widget)
            return
        try:
            self._project = self.store.get_project(project_id)
            self._repo = self.store.get_repo(project_id, repo_id)
        except NotFoundError:
            self._project = None
            self._repo = None
            show_exclusive(self.empty_label, self.content_widget)
            return
        show_exclusive(self.content_widget, self.empty_label)
        self._rebuild_rows()

    def _rebuild_rows(self) -> None:
        # Guard against itemChanged firing while we're programmatically
        # setting check states below (would otherwise re-persist a
        # half-built list on every single addItem call).
        self._loading = True
        self.list_widget.clear()
        if self._repo is not None:
            active_ids = self._repo.active_plugin_ids
            for plugin in self._plugin_catalog:
                checked = not active_ids or plugin.manifest.id in active_ids
                item = QListWidgetItem(plugin.manifest.name)
                item.setData(Qt.UserRole, plugin.manifest.id)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
                self.list_widget.addItem(item)
        self._loading = False

    def _on_item_changed(self, _item: QListWidgetItem) -> None:
        if self._loading or self._project is None or self._repo is None:
            return
        active_ids = [
            self.list_widget.item(row).data(Qt.UserRole)
            for row in range(self.list_widget.count())
            if self.list_widget.item(row).checkState() == Qt.Checked
        ]
        # Every plugin checked is indistinguishable from "unrestricted" for
        # MainWindow._apply_plugin_visibility, but storing [] explicitly
        # here (rather than the full id list) keeps a brand-new plugin
        # added later auto-enabled for repos that never opted out of
        # anything, matching the "unrestricted by default" behavior.
        if len(active_ids) == len(self._plugin_catalog):
            active_ids = []
        self.store.set_repo_active_plugin_ids(self._project.id, self._repo.id, active_ids)
        self._repo.active_plugin_ids = active_ids
