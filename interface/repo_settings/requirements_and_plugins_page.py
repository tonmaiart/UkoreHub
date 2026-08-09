from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from core.extensibility.loader import DiscoveredPlugin, plugin_source
from core.store import LocalConfigStore, MetadataStore
from interface.shared.base_repo_settings_page import BaseRepoSettingsPage
from interface.shared.requirements_tree_widget import RequirementsTreeWidget
from interface.shared.widget_helpers import wrap_scrollable

_PLUGIN_DESCRIPTION = (
    "Choose which plugins actually apply to this repo. Core plugins are "
    "always on — hiding them would remove functionality this app needs "
    "everywhere (e.g. switching the active repo at all), not just an "
    "optional feature — so there's nothing to toggle. Internal and "
    "External plugins are opt-in: off by default, check one only if this "
    "repo actually needs it. Saved to the shared Project/Repo registry "
    "(Studio)."
)


class RequirementsAndPluginsPage(BaseRepoSettingsPage):
    """Active repo's "Requirements & Plugins" tab — merges what used to be
    two separate CATEGORY_REPO tabs (Requirements, owned by
    plugins/core/project_editor/, and Enable Plugin, owned by this folder)
    into one, per the user's 2026-08-04 request. Two sections stacked
    vertically inside a wrap_scrollable() scroll area (2026-08-05, so the
    Program Requirements tree plus three plugin lists don't cram into
    whatever height the "Repository Setting..." popup happens to have):
    - Program Requirements — the same RequirementsTreeWidget RepoDialog
      shows at Add-Repo time (interface/shared/requirements_tree_widget.py),
      hosted here so an *existing* repo's required Programs (+ pinned
      version for a multi-version Program) can be edited too.
    - Enable Plugin — every discovered plugin's sidebar section visibility,
      split into three lists by core.extensibility.loader.plugin_source()
      instead of one flat checklist (see MainWindow._apply_plugin_visibility
      for the full precedence this mirrors), laid out as three columns in
      one QHBoxLayout row (2026-08-05, was stacked vertically) rather than
      one column each:
      - Core (plugins/core/) — always on for every repo, no checkbox and no
        per-repo opt-out (2026-08-04): anything left in plugins/core/ is
        meant to be universal app-level functionality now that anything
        repo-specific (Maya tools, ...) lives under repo_internal/ instead.
      - Internal (plugins/repo_internal/) — opt-in, unchecked by default,
        persisted to Repo.required_plugin_ids.
      - External (cache/plugins/, its own separate git clone) — opt-in,
        same as Internal, same Repo.required_plugin_ids list.
    Self-persists on every check-state change, same convention as every
    other repo-settings tab — no separate Save button. Active-repo
    resolution + refresh() preamble live in BaseRepoSettingsPage
    (interface/shared/).

    Cross-plugin `PluginManifest.requires` (2026-08-05) is enforced here,
    not in core.extensibility.loader — checking a plugin whose requirements
    aren't all enabled yet prompts to enable the (transitive) closure of
    those requirements along with it; unchecking a plugin that some other
    still-enabled plugin (including an always-on Core one) requires prompts
    a "this will break X" warning first. Either dialog can be declined,
    which reverts just that one checkbox and changes nothing."""

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
        self._plugin_by_id = {plugin.manifest.id: plugin for plugin in plugin_catalog}
        self._item_by_plugin_id: dict[str, QListWidgetItem] = {}
        self._requirements_tree: RequirementsTreeWidget | None = None
        self._loading_plugins = False

        self._requirements_group = QGroupBox("Program Requirements")
        self._requirements_layout = QVBoxLayout(self._requirements_group)

        plugin_description = QLabel(_PLUGIN_DESCRIPTION)
        plugin_description.setWordWrap(True)

        self._core_list = QListWidget()
        self._internal_list = QListWidget()
        self._internal_list.itemChanged.connect(self._on_plugin_item_changed)
        self._external_list = QListWidget()
        self._external_list.itemChanged.connect(self._on_plugin_item_changed)

        core_group = QGroupBox("Core Plugin")
        core_layout = QVBoxLayout(core_group)
        core_layout.addWidget(self._core_list)

        internal_group = QGroupBox("Internal Plugin")
        internal_layout = QVBoxLayout(internal_group)
        internal_layout.addWidget(self._internal_list)

        external_group = QGroupBox("External Plugin")
        external_layout = QVBoxLayout(external_group)
        external_layout.addWidget(self._external_list)

        plugin_columns = QHBoxLayout()
        plugin_columns.addWidget(core_group)
        plugin_columns.addWidget(internal_group)
        plugin_columns.addWidget(external_group)

        plugin_group = QGroupBox("Enable Plugin")
        plugin_layout = QVBoxLayout(plugin_group)
        plugin_layout.addWidget(plugin_description)
        plugin_layout.addLayout(plugin_columns)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(self._requirements_group)
        content_layout.addWidget(plugin_group)

        scroll = wrap_scrollable(content)

        content_wrap_layout = QVBoxLayout(self.content_widget)
        content_wrap_layout.setContentsMargins(0, 0, 0, 0)
        content_wrap_layout.addWidget(scroll)

        self.refresh()

    def _on_refresh_content(self) -> None:
        self._rebuild_requirements_tree()
        self._rebuild_plugin_lists()

    def _rebuild_requirements_tree(self) -> None:
        if self._requirements_tree is not None:
            self._requirements_layout.removeWidget(self._requirements_tree)
            self._requirements_tree.deleteLater()
            self._requirements_tree = None
        if self._repo is None or self._project is None:
            return
        self._requirements_tree = RequirementsTreeWidget(
            store=self.store,
            project_id=self._project.id,
            selected_program_ids=self._repo.required_program_ids,
            selected_program_version_pins=self._repo.program_version_pins,
        )
        self._requirements_tree.itemChanged.connect(self._on_requirements_tree_changed)
        self._requirements_layout.addWidget(self._requirements_tree)

    def _on_requirements_tree_changed(self, _item, _column) -> None:
        if self._project is None or self._repo is None or self._requirements_tree is None:
            return
        program_ids = self._requirements_tree.selected_program_ids()
        pins = self._requirements_tree.selected_program_version_pins()
        self.store.set_repo_requirements(self._project.id, self._repo.id, program_ids)
        self.store.set_repo_program_version_pins(self._project.id, self._repo.id, pins)
        self._repo.required_program_ids = program_ids
        self._repo.program_version_pins = pins

    def _rebuild_plugin_lists(self) -> None:
        # Guard against itemChanged firing while we're programmatically
        # setting check states below (would otherwise re-persist a
        # half-built list on every single addItem call).
        self._loading_plugins = True
        self._core_list.clear()
        self._internal_list.clear()
        self._external_list.clear()
        self._item_by_plugin_id = {}
        if self._repo is not None:
            required_ids = self._repo.required_plugin_ids
            for plugin in self._plugin_catalog:
                source = plugin_source(plugin)
                if source == "core":
                    self._core_list.addItem(QListWidgetItem(plugin.manifest.name))
                    continue
                target_list = self._internal_list if source == "repo_internal" else self._external_list
                item = QListWidgetItem(plugin.manifest.name)
                item.setData(Qt.UserRole, plugin.manifest.id)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked if plugin.manifest.id in required_ids else Qt.Unchecked)
                target_list.addItem(item)
                self._item_by_plugin_id[plugin.manifest.id] = item
        self._loading_plugins = False

    def _on_plugin_item_changed(self, item: QListWidgetItem) -> None:
        if self._loading_plugins or self._project is None or self._repo is None:
            return
        plugin_id = item.data(Qt.UserRole)
        if plugin_id is None:
            return

        if item.checkState() == Qt.Checked:
            if not self._confirm_and_enable_requirements(plugin_id):
                self._set_item_checked(item, False)
                return
        else:
            if not self._confirm_disable(plugin_id):
                self._set_item_checked(item, True)
                return

        self._persist_required_plugin_ids()

    def _set_item_checked(self, item: QListWidgetItem, checked: bool) -> None:
        # Guarded so this programmatic change doesn't re-enter
        # _on_plugin_item_changed (it fires itemChanged same as a user click).
        self._loading_plugins = True
        item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
        self._loading_plugins = False

    def _enabled_plugin_ids(self) -> set[str]:
        """Plugin ids currently in effect for the repo being edited: every
        always-on Core plugin plus every checked Internal/External item."""
        enabled = {plugin.manifest.id for plugin in self._plugin_catalog if plugin_source(plugin) == "core"}
        enabled.update(
            item.data(Qt.UserRole)
            for lst in (self._internal_list, self._external_list)
            for row in range(lst.count())
            if (item := lst.item(row)).checkState() == Qt.Checked
        )
        return enabled

    def _requires_closure(self, plugin_id: str) -> list[str]:
        """Transitive requirement ids for plugin_id (not including
        plugin_id itself), deepest-first. Ids that aren't in the discovered
        plugin catalog are silently skipped — nothing to enable for a
        requirement that doesn't exist."""
        seen: set[str] = set()
        ordered: list[str] = []

        def visit(pid: str) -> None:
            plugin = self._plugin_by_id.get(pid)
            if plugin is None:
                return
            for req_id in plugin.manifest.requires:
                if req_id in seen:
                    continue
                seen.add(req_id)
                visit(req_id)
                ordered.append(req_id)

        visit(plugin_id)
        return ordered

    def _confirm_and_enable_requirements(self, plugin_id: str) -> bool:
        """Called after `plugin_id`'s own checkbox is already checked.
        Returns False (caller should revert) only if the user declines to
        also enable its unmet requirements; True if there was nothing to
        enable or the user agreed."""
        enabled = self._enabled_plugin_ids()
        missing_ids = [req_id for req_id in self._requires_closure(plugin_id) if req_id not in enabled]
        missing_items = [self._item_by_plugin_id[req_id] for req_id in missing_ids if req_id in self._item_by_plugin_id]
        if not missing_items:
            return True

        plugin_name = self._plugin_by_id[plugin_id].manifest.name
        names = "\n".join(f"- {self._plugin_by_id[req_id].manifest.name}" for req_id in missing_ids if req_id in self._plugin_by_id)
        confirm = QMessageBox.question(
            self,
            "Enable Required Plugins",
            f"'{plugin_name}' requires the following plugin(s), currently disabled for this repo:\n\n"
            f"{names}\n\nEnable them along with '{plugin_name}'?",
        )
        if confirm != QMessageBox.Yes:
            return False

        for req_item in missing_items:
            self._set_item_checked(req_item, True)
        return True

    def _confirm_disable(self, plugin_id: str) -> bool:
        """Called after `plugin_id`'s own checkbox is already unchecked.
        Returns False (caller should revert) only if the user declines to
        proceed after being warned some other still-enabled plugin requires
        it; True if nothing depends on it or the user confirmed anyway."""
        enabled = self._enabled_plugin_ids()
        dependents = [
            plugin.manifest.name
            for plugin in self._plugin_catalog
            if plugin.manifest.id in enabled and plugin_id in plugin.manifest.requires
        ]
        if not dependents:
            return True

        plugin_name = self._plugin_by_id[plugin_id].manifest.name
        names = "\n".join(f"- {name}" for name in dependents)
        confirm = QMessageBox.question(
            self,
            "Disable Plugin",
            f"Disabling '{plugin_name}' will break the following plugin(s), which require it:\n\n"
            f"{names}\n\nDisable '{plugin_name}' anyway?",
        )
        return confirm == QMessageBox.Yes

    def _persist_required_plugin_ids(self) -> None:
        required_ids = [
            self._internal_list.item(row).data(Qt.UserRole)
            for row in range(self._internal_list.count())
            if self._internal_list.item(row).checkState() == Qt.Checked
        ] + [
            self._external_list.item(row).data(Qt.UserRole)
            for row in range(self._external_list.count())
            if self._external_list.item(row).checkState() == Qt.Checked
        ]
        self.store.set_repo_required_plugin_ids(self._project.id, self._repo.id, required_ids)
        self._repo.required_plugin_ids = required_ids
