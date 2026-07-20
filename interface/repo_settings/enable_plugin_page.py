from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QVBoxLayout

from core.extensibility.loader import DiscoveredPlugin
from core.store import LocalConfigStore, MetadataStore
from interface.shared.base_repo_settings_page import BaseRepoSettingsPage

_DESCRIPTION = (
    "Choose which plugins actually apply to this repo. Unchecked plugins hide "
    "their sidebar tab while this repo is active. Leaving everything checked "
    "(the default for a new repo) applies every plugin, same as before this "
    "setting existed. Saved to the shared Project/Repo registry (Studio). "
    "Core plugins (marked below) can't be unchecked — hiding them would remove "
    "the only way to do something this app needs (e.g. switching the active "
    "repo at all), not just an optional feature."
)


class EnablePluginPage(BaseRepoSettingsPage):
    """Per-repo toggle for plugins/studio + plugins/local entries
    (Repo.active_plugin_ids) — distinct from the existing Add-ons concept
    (Repo.enabled_addon_ids, edited in About > Requirement): unlike Add-ons,
    this one actually hides the plugin's sidebar section for repos that
    don't have it checked (see MainWindow._apply_plugin_visibility) — except
    a plugin flagged manifest.json "core": true (PluginManifest.core), which
    always renders checked and disabled here and is never actually hideable
    regardless of what ends up in active_plugin_ids. Active-repo resolution
    + refresh() preamble live in BaseRepoSettingsPage (interface/shared/)."""

    def __init__(
        self,
        parent=None,
        *,
        store: MetadataStore,
        local_config_store: LocalConfigStore,
        plugin_catalog: list[DiscoveredPlugin],
    ):
        super().__init__(parent, store=store, local_config_store=local_config_store)
        self._plugin_catalog = plugin_catalog
        self._loading = False

        description_label = QLabel(_DESCRIPTION)
        description_label.setWordWrap(True)

        self.list_widget = QListWidget()
        self.list_widget.itemChanged.connect(self._on_item_changed)

        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(description_label)
        content_layout.addWidget(self.list_widget)

        self.refresh()

    def _on_refresh_content(self) -> None:
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
                is_core = plugin.manifest.core
                checked = is_core or not active_ids or plugin.manifest.id in active_ids
                label = f"{plugin.manifest.name} (core — always enabled)" if is_core else plugin.manifest.name
                item = QListWidgetItem(label)
                item.setData(Qt.UserRole, plugin.manifest.id)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                if is_core:
                    # Rendered checked but not interactive — see
                    # MainWindow._apply_plugin_visibility, which forces a
                    # core plugin's section visible regardless of what ends
                    # up in active_plugin_ids anyway, but this keeps the
                    # persisted list itself honest and the UI from
                    # suggesting a toggle that wouldn't do anything.
                    item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
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
