from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from core_api import DiscoveredPlugin, GitOperationError, GitService, LocalConfigStore, MetadataStore, PluginManifest, plugin_source
from interface.shared.base_repo_settings_page import BaseRepoSettingsPage
from interface.shared.requirements_tree_widget import RequirementsTreeWidget
from interface.shared.widget_helpers import wrap_scrollable

# Matches plugins/core/ExternalPluginManager/catalog_store.py's _CATALOG_KEY and
# PLUGIN_ID by convention (agreeing on a plugin_id + JSON shape inside
# Project.plugin_data), not by importing that plugin's source — see
# developer/app/docs/plugins-guide.md's "Sharing data with another plugin".
_EXTERNAL_PLUGINS_ID = "external_plugins"
_EXTERNAL_CATALOG_KEY = "catalog"
_NOT_CLONED_SUFFIX = " (not installed — check to clone)"
_PENDING_RESTART_SUFFIX = " (installed — restart UkoreHub to activate)"
_BROKEN_CLONE_SUFFIX = " (broken clone — fix via Settings > Developer > External Plugins)"

_PLUGIN_DESCRIPTION = (
    "Choose which plugins actually apply to this repo. Core plugins are "
    "always on — hiding them would remove functionality this app needs "
    "everywhere (e.g. switching the active repo at all), not just an "
    "optional feature — so there's nothing to toggle. External plugins "
    "are opt-in: off by default, check one only if this repo actually "
    "needs it. Saved to the shared Project/Repo registry (Studio)."
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
      split into two lists by core.extensibility.loader.plugin_source()
      instead of one flat checklist (see MainWindow._apply_plugin_visibility
      for the full precedence this mirrors), laid out as two columns in
      one QHBoxLayout row:
      - Core (plugins/core/) — always on for every repo, no checkbox and no
        per-repo opt-out (2026-08-04): anything left in plugins/core/ is
        meant to be universal app-level functionality now that anything
        repo-specific (Maya tools, ...) lives under cache/plugins/ instead.
      - External (cache/plugins/, its own separate git clone) — opt-in,
        unchecked by default, persisted to Repo.required_plugin_ids. Lists
        every "repo"-source plugin discover_plugins() finds cloned on this
        machine, plus every entry in the active Project's own
        plugins/core/ExternalPluginManager/ catalog
        (Project.plugin_data["external_plugins"]["catalog"]) that isn't
        cloned/discovered yet. Was a studio-wide catalog with a brief,
        reverted 2026-08-10 attempt at a per-project selection filter on
        top of it — see developer/app/docs/plugins/ExternalPluginManager.md
        for why the filter
        version failed (catalog entries added before the filter existed
        had no way back into a project's selection once the manual toggle
        that set it was removed). Moving the catalog itself into
        Project.plugin_data replaces that filter outright: each project
        now has its own catalog rather than a shared one with a selection
        overlay, so this class of bug has no filter left to have.

        A catalogued-but-not-yet-cloned entry is checkable — checking it
        clones it immediately (via GitService, into plugins_root, no
        confirmation prompt) and marks it required, rather than sending the
        user to Settings > Developer > External Plugins to clone it by hand
        first. Since plugin discovery/registration only ever runs once at
        app startup, a plugin cloned mid-session still needs a restart
        before it actually loads — see _add_pending_external_items and
        _on_catalog_entry_checked.
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
        git_service: GitService,
        plugins_root: Path,
    ):
        super().__init__(parent, store=store, local_config_store=local_config_store)
        self._plugin_catalog = plugin_catalog
        self._git_service = git_service
        self._plugins_root = Path(plugins_root)
        self._plugin_by_id = {plugin.manifest.id: plugin for plugin in plugin_catalog}
        self._item_by_plugin_id: dict[str, QListWidgetItem] = {}
        self._requirements_tree: RequirementsTreeWidget | None = None
        self._loading_plugins = False

        self._requirements_group = QGroupBox("Program Requirements")
        self._requirements_layout = QVBoxLayout(self._requirements_group)

        plugin_description = QLabel(_PLUGIN_DESCRIPTION)
        plugin_description.setWordWrap(True)

        self._core_list = QListWidget()
        self._external_list = QListWidget()
        self._external_list.itemChanged.connect(self._on_plugin_item_changed)

        core_group = QGroupBox("Core Plugin")
        core_layout = QVBoxLayout(core_group)
        core_layout.addWidget(self._core_list)

        external_group = QGroupBox("External Plugin")
        external_layout = QVBoxLayout(external_group)
        external_layout.addWidget(self._external_list)

        plugin_columns = QHBoxLayout()
        plugin_columns.addWidget(core_group)
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
        self._external_list.clear()
        self._item_by_plugin_id = {}
        if self._repo is not None:
            required_ids = self._repo.required_plugin_ids
            discovered_repo_folders: set[str] = set()
            for plugin in self._plugin_catalog:
                source = plugin_source(plugin)
                if source == "core":
                    self._core_list.addItem(QListWidgetItem(plugin.manifest.name))
                    continue
                # source == "repo" (External) — every discovered one is a
                # choice, whether or not it's currently required.
                discovered_repo_folders.add(plugin.dir_path.name)
                self._add_plugin_item(self._external_list, plugin, required_ids)
            self._add_pending_external_items(discovered_repo_folders, required_ids)
        self._loading_plugins = False

    def _add_plugin_item(self, target_list: QListWidget, plugin: DiscoveredPlugin, required_ids: list[str]) -> None:
        item = QListWidgetItem(plugin.manifest.name + self._requires_label(plugin))
        item.setData(Qt.UserRole, plugin.manifest.id)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Checked if plugin.manifest.id in required_ids else Qt.Unchecked)
        target_list.addItem(item)
        self._item_by_plugin_id[plugin.manifest.id] = item

    def _requires_label(self, plugin: DiscoveredPlugin) -> str:
        """' — requires: X, Y', resolving each required id to its
        discovered manifest name via self._plugin_by_id (built from the
        full plugin_catalog at construction, so this covers Core/External
        requirements alike) — '' if plugin.manifest.requires is
        empty. Always visible (not just on check, unlike the
        _confirm_and_enable_requirements prompt below) so a dependency is
        known before you check anything."""
        if not plugin.manifest.requires:
            return ""
        names = [
            self._plugin_by_id[req_id].manifest.name if req_id in self._plugin_by_id else req_id
            for req_id in plugin.manifest.requires
        ]
        return f" — requires: {', '.join(names)}"

    def _add_pending_external_items(self, discovered_repo_folders: set[str], required_ids: list[str]) -> None:
        """A studio-wide catalog entry (plugins/core/ExternalPluginManager/) that
        this session's plugin discovery hasn't picked up (see loader.py's
        discover_plugins, run once at app startup) — split by actual on-disk
        state, since "not discovered yet" covers three different situations:
        - Not cloned at all: checkable — checking it clones it right here
          (see _on_catalog_entry_checked) instead of sending the user to
          Settings > Project > External Plugin Manager first.
        - Cloned (by this flow or by hand) but not yet discovered this
          session: shown disabled with its current required-for-this-repo
          state, since there's nothing left to do but restart.
        - A broken .git directory (GitService.is_cloned true, is_repo_root
          false — see developer/app/docs/plugins/ExternalPluginManager.md's
          "Why is_repo_root, not just is_cloned"): shown disabled, pointing
          at External Plugin Manager to fix it rather than silently treating
          it as installed."""
        for entry in sorted(self._read_external_catalog(), key=lambda e: e["name"]):
            if entry["folder_name"] in discovered_repo_folders:
                continue
            local_path = self._plugins_root / entry["folder_name"]
            if not self._git_service.is_cloned(local_path):
                item = QListWidgetItem(entry["name"] + _NOT_CLONED_SUFFIX)
                item.setData(Qt.UserRole + 1, entry["id"])
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
                self._external_list.addItem(item)
                continue
            if not self._git_service.is_repo_root(local_path):
                item = QListWidgetItem(entry["name"] + _BROKEN_CLONE_SUFFIX)
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
                self._external_list.addItem(item)
                continue
            manifest = self._read_manifest_if_cloned(entry["folder_name"])
            label = manifest.name if manifest is not None else entry["name"]
            item = QListWidgetItem(label + _PENDING_RESTART_SUFFIX)
            item.setFlags((item.flags() | Qt.ItemIsUserCheckable) & ~Qt.ItemIsEnabled)
            is_required = manifest is not None and manifest.id in required_ids
            item.setCheckState(Qt.Checked if is_required else Qt.Unchecked)
            self._external_list.addItem(item)

    def _read_manifest_if_cloned(self, folder_name: str) -> PluginManifest | None:
        """A raw manifest.json read/parse only — never imports or executes
        the plugin's entry_point (unlike loader.discover_plugins), since
        running a plugin's code mid-session outside the normal one-shot
        startup flow is out of scope here. Used right after cloning (to
        learn the real plugin id to mark required) and for a folder cloned
        earlier this session that's still awaiting restart."""
        manifest_path = self._plugins_root / folder_name / "manifest.json"
        if not manifest_path.exists():
            return None
        try:
            return PluginManifest.from_dict(json.loads(manifest_path.read_text(encoding="utf-8")))
        except (OSError, ValueError, KeyError):
            return None

    def _read_external_catalog(self) -> list[dict]:
        """The active Project's own External Plugin Manager catalog (see
        plugins/core/ExternalPluginManager/catalog_store.py) — read straight
        from self.store on every call, no caching, so an edit made on the
        External Plugin Manager settings tab earlier in the same session is
        picked up the next time this tab is opened."""
        if self._project is None:
            return []
        plugin_data = self.store.get_project_plugin_data(self._project.id, _EXTERNAL_PLUGINS_ID)
        return plugin_data.get(_EXTERNAL_CATALOG_KEY, [])

    def _on_catalog_entry_checked(self, item: QListWidgetItem, entry_id: str) -> None:
        """Handles a check-state change on a not-yet-cloned catalog entry
        row (see _add_pending_external_items) — the only state such a row
        can be in, so unchecking it (e.g. immediately after a failed clone
        reverts it below) needs no persistence of its own; there was never
        anything installed or required to undo."""
        if item.checkState() != Qt.Checked:
            return

        entry = next((e for e in self._read_external_catalog() if e.get("id") == entry_id), None)
        if entry is None:
            self._set_item_checked(item, False)
            return

        git_url = entry.get("git_url", "")
        if not git_url:
            QMessageBox.warning(
                self,
                "Clone Plugin",
                f"'{entry['name']}' has no Git URL set — edit it via "
                "Settings > Developer > External Plugins first.",
            )
            self._set_item_checked(item, False)
            return

        local_path = self._plugins_root / entry["folder_name"]
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self._git_service.clone(git_url, local_path)
        except GitOperationError as exc:
            QMessageBox.warning(self, "Clone Plugin", str(exc))
            self._set_item_checked(item, False)
            return
        finally:
            QApplication.restoreOverrideCursor()

        manifest = self._read_manifest_if_cloned(entry["folder_name"])
        if manifest is None:
            QMessageBox.warning(
                self,
                "Clone Plugin",
                f"Cloned '{entry['name']}', but its manifest.json is missing or invalid.",
            )
            self._rebuild_plugin_lists()
            return

        required_ids = list(self._repo.required_plugin_ids)
        if manifest.id not in required_ids:
            required_ids.append(manifest.id)
            self.store.set_repo_required_plugin_ids(self._project.id, self._repo.id, required_ids)
            self._repo.required_plugin_ids = required_ids

        QMessageBox.information(
            self,
            "Clone Plugin",
            f"Cloned '{manifest.name}'. It's marked as required for this repo — "
            "restart UkoreHub for it to actually load.",
        )
        self._rebuild_plugin_lists()

    def _on_plugin_item_changed(self, item: QListWidgetItem) -> None:
        if self._loading_plugins or self._project is None or self._repo is None:
            return

        entry_id = item.data(Qt.UserRole + 1)
        if entry_id is not None:
            self._on_catalog_entry_checked(item, entry_id)
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
        always-on Core plugin plus every checked External item."""
        enabled = {plugin.manifest.id for plugin in self._plugin_catalog if plugin_source(plugin) == "core"}
        enabled.update(
            item.data(Qt.UserRole)
            for row in range(self._external_list.count())
            if (item := self._external_list.item(row)).checkState() == Qt.Checked
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
            item.data(Qt.UserRole)
            for row in range(self._external_list.count())
            if (item := self._external_list.item(row)).checkState() == Qt.Checked and item.data(Qt.UserRole)
        ]
        self.store.set_repo_required_plugin_ids(self._project.id, self._repo.id, required_ids)
        self._repo.required_plugin_ids = required_ids
