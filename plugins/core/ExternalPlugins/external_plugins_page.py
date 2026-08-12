from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.exceptions import GitOperationError, UkoreHubError
from core.extensibility.loader import DiscoveredPlugin, plugin_source
from core.vcs.git_service import GitService
from core.os_utils import open_in_file_explorer
from interface.shared.widget_helpers import confirm_action
from plugins.core.ExternalPlugins import sync_engine
from plugins.core.ExternalPlugins.catalog_entry_dialog import CatalogEntryDialog
from plugins.core.ExternalPlugins.catalog_store import CatalogEntry, ExternalPluginCatalog
from plugins.core.ExternalPlugins.sync_status_store import ExternalPluginSyncStatusStore

_NOT_CLONED = "Not cloned"
_NOT_CHECKED = "Not checked yet"
_BROKEN_GIT = "Broken .git directory (not a valid clone) — delete the folder and Clone again"
_UPDATE_CONFLICT = "⚠ Update Conflict"
_PENDING_RESTART = "Pending Restart — cloned/updated this session, restart UkoreHub to load it"


@dataclass
class _Row:
    entry: CatalogEntry
    status: str


class ExternalPluginsPage(QWidget):
    """Settings > Project tab: every cache/plugins/ repo plugin the active
    Project's own catalog declares (Project.plugin_data["external_plugins"]
    ["catalog"], core/models.py), whether it's behind its remote, and
    Clone/Pull actions. See this plugin's own README for why this page's
    own manual actions run synchronously (with a wait cursor) instead of a
    background QThread — the separate auto-sync engine (below) does use
    one.

    Only entries actually in this Project's catalog are listed — no
    auto-detected "(not catalogued)" rows for an already-cloned
    cache/plugins/ folder the catalog doesn't mention. An entry must be
    added here explicitly before anything else (Requirements & Plugins,
    the auto-sync engine) can see it.

    Each row also shows its own manifest's `requires` (only known once the
    entry is actually cloned — resolved via `plugin_catalog`, the same
    discover_plugins() result the rest of the app uses, so no manual
    manifest.json parsing here). An entry that isn't cloned yet shows no
    requires text — there's no manifest to read until it is.

    This page manages the active Project's catalog itself (Add/Edit/
    Delete/Clone/Pull/Check for Updates); every catalogued entry is a
    choice on that same project's Requirements & Plugins tab — see this
    plugin's own README.

    Entries the active repo currently requires are also cloned/updated
    automatically at app start and on repo switch, off the UI thread — see
    sync_engine.py/sync_worker.py and this plugin's own README's "Auto-sync
    engine". sync_status_store carries that background engine's last result
    for each entry across Settings-dialog opens (Update Conflict / a failed
    auto-clone/-update), so a stuck plugin shows up here even if this tab
    was never opened while the sync itself ran."""

    def __init__(
        self,
        parent=None,
        *,
        git_service: GitService,
        plugins_root: Path,
        catalog: ExternalPluginCatalog,
        plugin_catalog: list[DiscoveredPlugin],
        sync_status_store: ExternalPluginSyncStatusStore,
    ):
        super().__init__(parent)
        self.git_service = git_service
        self.plugins_root = Path(plugins_root)
        self.catalog = catalog
        self.sync_status_store = sync_status_store
        self._plugin_by_id = {plugin.manifest.id: plugin for plugin in plugin_catalog}
        self._plugin_by_folder = {
            plugin.dir_path.name: plugin for plugin in plugin_catalog if plugin_source(plugin) == "repo"
        }
        self._rows: list[_Row] = []

        description = QLabel(
            "External (repo) plugins declared for this project — cloned into cache/plugins/ or not yet. "
            "Add one that hasn't been cloned here yet, then Clone it; use Check for Updates to see which "
            "cloned ones are behind their remote. Every entry here is offered as a choice on this project's "
            "Requirements & Plugins tab. Entries a repo currently requires clone/update themselves at app "
            "start and on repo switch — Update Conflict here means an automatic update hit a merge conflict "
            "and needs a dev to resolve it by hand (Open Git Directory)."
        )
        description.setWordWrap(True)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)

        add_btn = QPushButton("Add")
        edit_btn = QPushButton("Edit")
        delete_btn = QPushButton("Delete")
        clone_btn = QPushButton("Clone")
        pull_btn = QPushButton("Update Selected")
        pull_btn.setToolTip("Pull from the remote for the selected plugin.")

        check_btn = QPushButton("Check for Status")
        check_btn.setToolTip("Check the status of all external plugin.")

        open_dir_btn = QPushButton("Open Selected Cloned Directory")
        open_dir_btn.setToolTip("Open the directory of the selected cloned plugin.")

        stage_push_btn = QPushButton("Bulk Push")
        stage_push_btn.setToolTip("Stage untracked,modified changes and push to the remote for the selected plugin.")

        ignore_update_btn = QPushButton("Gitignore Update All")
        ignore_update_btn.setToolTip("ลบไฟล์ทั้งหมดที่ตรงกับกฎ .gitignore ออกจากการ Track ของ Git (Untrack)")
        ignore_update_btn.clicked.connect(self._on_gitignore_update)

        add_btn.clicked.connect(self._on_add)
        edit_btn.clicked.connect(self._on_edit)
        delete_btn.clicked.connect(self._on_delete)
        clone_btn.clicked.connect(self._on_clone)
        pull_btn.clicked.connect(self._on_pull)
        check_btn.clicked.connect(self._on_check_for_updates)
        open_dir_btn.clicked.connect(self._on_open_git_directory)
        stage_push_btn.clicked.connect(self._on_stage_untracked_and_push)

        button_row = QHBoxLayout()
        for button in (add_btn, edit_btn, delete_btn, clone_btn, pull_btn, check_btn, open_dir_btn, stage_push_btn,ignore_update_btn):
            button_row.addWidget(button)
        button_row.addStretch()

        layout = QVBoxLayout(self)
        layout.addWidget(description)
        layout.addLayout(button_row)
        layout.addWidget(self.list_widget)

        self.refresh_list()

    # -- listing --------------------------------------------------------------

    def refresh_list(self) -> None:
        """Fast, local-only pass over this project's own catalog entries.
        No network calls — Check for Updates does those on demand. No
        disk scan for un-catalogued cache/plugins/ folders anymore — an
        entry has to be added to the catalog before it shows up here."""
        self._rows = [_Row(entry=entry, status=self._local_status(entry)) for entry in self.catalog.list_entries()]
        self._render()

    def _local_status(self, entry: CatalogEntry) -> str:
        """Fast, local-only status for one row — folded in with whatever
        the background auto-sync engine (sync_engine.py) last recorded for
        this entry in sync_status_store, so a conflict/failure it hit while
        this tab was closed still shows up the next time it's opened."""
        local_path = self.plugins_root / entry.folder_name
        sync_status = self.sync_status_store.get(entry.id)

        if not self.git_service.is_cloned(local_path):
            if sync_status is not None and sync_status.status == sync_engine.STATUS_ERROR:
                return f"{_NOT_CLONED} — last auto-clone attempt failed: {sync_status.message}"
            return _NOT_CLONED
        if not self.git_service.is_repo_root(local_path):
            return _BROKEN_GIT
        if self.git_service.has_unresolved_merge(local_path):
            message = sync_status.message if sync_status is not None else ""
            return f"{_UPDATE_CONFLICT}{f' — {message}' if message else ''}"
        
        # เช็กสถานะไฟล์ในเครื่อง (Untracked, Modified, Staged) แบบรวดเร็วตอนโหลดตาราง
        try:
            untracked, modified, staged = self.git_service.get_working_tree_status(local_path)
            if untracked or modified or staged:
                changes = []
                if modified:
                    changes.append(f"{len(modified)} modified")
                if staged:
                    changes.append(f"{len(staged)} staged")
                if untracked:
                    changes.append(f"{len(untracked)} untracked")
                return f"Not up to date — {', '.join(changes)} file(s)"
        except Exception:
            pass

        if entry.folder_name not in self._plugin_by_folder:
            return _PENDING_RESTART
        if sync_status is not None and sync_status.status == sync_engine.STATUS_ERROR:
            return f"Auto-update failed: {sync_status.message}"
        return _NOT_CHECKED
    def _render(self) -> None:
        selected_folder = self._selected_row().entry.folder_name if self._selected_row() else None
        self.list_widget.clear()
        for row in self._rows:
            label = f"{row.entry.name}{self._requires_label(row.entry)} — {row.status}"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, row.entry.folder_name)
            item.setData(Qt.UserRole + 1, row.entry.id)
            self.list_widget.addItem(item)
            if row.entry.folder_name == selected_folder:
                item.setSelected(True)
                self.list_widget.setCurrentItem(item)

    def _requires_label(self, entry: CatalogEntry) -> str:
        """' — requires: X, Y' if this entry is cloned and its manifest
        declares requirements; '' (unknown) if it isn't cloned yet — there's
        no manifest to read until then."""
        plugin = self._plugin_by_folder.get(entry.folder_name)
        if plugin is None or not plugin.manifest.requires:
            return ""
        names = [
            self._plugin_by_id[req_id].manifest.name if req_id in self._plugin_by_id else req_id
            for req_id in plugin.manifest.requires
        ]
        return f" — requires: {', '.join(names)}"

    def _selected_row(self) -> _Row | None:
        items = self.list_widget.selectedItems()
        if not items:
            return None
        folder_name = items[0].data(Qt.UserRole)
        for row in self._rows:
            if row.entry.folder_name == folder_name:
                return row
        return None

    # -- catalog CRUD -----------------------------------------------------------

    def _on_add(self) -> None:
        dialog = CatalogEntryDialog(self)
        if dialog.exec():
            try:
                self.catalog.add_entry(dialog.name(), dialog.git_url(), dialog.folder_name())
            except UkoreHubError as exc:
                QMessageBox.warning(self, "Add External Plugin", str(exc))
                return
            self.refresh_list()

    def _on_edit(self) -> None:
        row = self._selected_row()
        if row is None:
            QMessageBox.information(self, "Edit", "Select an entry first.")
            return
        entry = row.entry
        dialog = CatalogEntryDialog(self, name=entry.name, git_url=entry.git_url, folder_name=entry.folder_name)
        if not dialog.exec():
            return
        try:
            self.catalog.edit_entry(
                entry.id, name=dialog.name(), git_url=dialog.git_url(), folder_name=dialog.folder_name()
            )
        except UkoreHubError as exc:
            QMessageBox.warning(self, "Edit External Plugin", str(exc))
            return
        self.refresh_list()

    def _on_delete(self) -> None:
        row = self._selected_row()
        if row is None:
            QMessageBox.information(self, "Delete", "Select an entry first.")
            return
        confirmed = confirm_action(
            self,
            "Delete External Plugin",
            f"Remove '{row.entry.name}' from this project's External Plugins catalog?\n\n"
            "This only removes the catalog entry — any already-cloned folder on disk is left untouched.",
        )
        if confirmed:
            self.catalog.delete_entry(row.entry.id)
            self.refresh_list()

    # -- clone / pull -----------------------------------------------------------

    def _require_valid_clone(self, local_path: Path, title: str) -> bool:
        """Gate for anything about to run a real git command against
        local_path — is_repo_root(), not is_cloned(), so a broken/empty
        .git directory (see bug-history 2026-08-08) can never be mistaken
        for a usable clone and have a git command silently run against
        whatever real repo git's discovery walks up to instead."""
        if not self.git_service.is_cloned(local_path):
            QMessageBox.information(self, title, "Not cloned yet — use Clone first.")
            return False
        if not self.git_service.is_repo_root(local_path):
            QMessageBox.warning(self, title, _BROKEN_GIT)
            return False
        return True

    def _on_clone(self) -> None:
        row = self._selected_row()
        if row is None:
            QMessageBox.information(self, "Clone", "Select an entry first.")
            return
        local_path = self.plugins_root / row.entry.folder_name
        if self.git_service.is_cloned(local_path):
            message = "Already cloned — use Pull instead." if self.git_service.is_repo_root(local_path) else _BROKEN_GIT
            QMessageBox.information(self, "Clone", message)
            return
        if not row.entry.git_url:
            QMessageBox.warning(self, "Clone", "This entry has no Git URL set — edit it first.")
            return
        self._run_with_wait_cursor(lambda: self.git_service.clone(row.entry.git_url, local_path), "Clone")

    def _on_pull(self) -> None:
        row = self._selected_row()
        if row is None:
            QMessageBox.information(self, "Pull", "Select an entry first.")
            return
        local_path = self.plugins_root / row.entry.folder_name
        if not self._require_valid_clone(local_path, "Pull"):
            return

        def action() -> None:
            self.git_service.pull(local_path)
            # A successful manual Pull clears any stale conflict/error the
            # background auto-sync engine had recorded — otherwise the
            # Update Conflict badge would linger until the next auto-sync
            # run happens to touch this same entry again.
            if row.entry.id:
                self.sync_status_store.clear(row.entry.id)

        self._run_with_wait_cursor(action, "Pull")

    def _on_open_git_directory(self) -> None:
        row = self._selected_row()
        if row is None:
            QMessageBox.information(self, "Open Git Directory", "Select an entry first.")
            return
        local_path = self.plugins_root / row.entry.folder_name
        if not self.git_service.is_cloned(local_path):
            QMessageBox.information(self, "Open Git Directory", "Not cloned yet — use Clone first.")
            return
        open_in_file_explorer(local_path)

    def _on_stage_untracked_and_push(self) -> None:
        row = self._selected_row()
        if row is None:
            QMessageBox.information(self, "Bulk Push", "Select an entry first.")
            return
        local_path = self.plugins_root / row.entry.folder_name
        if not self._require_valid_clone(local_path, "Bulk Push"):
            return
        
        try:
            untracked, modified, staged = self.git_service.get_working_tree_status(local_path)
        except GitOperationError as exc:
            QMessageBox.warning(self, "Bulk Push", str(exc))
            return
        
        # รวมไฟล์ทั้ง Untracked, Modified และ Staged เข้าด้วยกัน
        all_changed_paths = list(set(untracked + modified + staged))

        if not all_changed_paths:
            QMessageBox.information(self, "Bulk Push", "No changes (untracked, modified, or staged files) to push.")
            return

        confirmed = confirm_action(
            self,
            "Bulk Push",
            f"Stage/Push {len(all_changed_paths)} file(s), commit, and push in '{row.entry.name}'?",
        )
        if not confirmed:
            return

        message, ok = QInputDialog.getMultiLineText(
            self, "Commit Message", "Commit message:", f"Update plugin files ({len(all_changed_paths)} files)"
        )
        if not ok or not message.strip():
            return

        def action() -> None:
            # ถ้ามีไฟล์ untracked หรือ modified ให้สั่ง stage เพิ่มเติม (ส่วนที่ staged อยู่แล้วคำสั่ง add จะไม่กระทบอะไร)
            if untracked or modified:
                self.git_service.stage_paths(local_path, list(set(untracked + modified)))
            self.git_service.commit(local_path, message)
            self.git_service.push(local_path)

        self._run_with_wait_cursor(action, "Bulk Push")
    def _run_with_wait_cursor(self, action, title: str) -> None:
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            action()
        except GitOperationError as exc:
            QMessageBox.warning(self, title, str(exc))
        finally:
            QApplication.restoreOverrideCursor()
        self.refresh_list()


    def _on_check_for_updates(self) -> None:
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            for row in self._rows:
                local_path = self.plugins_root / row.entry.folder_name
                if not self.git_service.is_cloned(local_path):
                    row.status = _NOT_CLONED
                    continue
                if not self.git_service.is_repo_root(local_path):
                    row.status = _BROKEN_GIT
                    continue
                if self.git_service.has_unresolved_merge(local_path):
                    row.status = self._local_status(row.entry)
                    continue

                row.status = "Checking..."
                self._render()
                QApplication.processEvents()

                try:
                    self.git_service.fetch(local_path)
                    ahead_behind = self.git_service.get_ahead_behind(local_path)
                    untracked, modified, staged = self.git_service.get_working_tree_status(local_path)
                except GitOperationError as exc:
                    row.status = f"Check failed: {exc}"
                    continue

                row.status = self._format_status(
                    ahead_behind,
                    untracked_count=len(untracked),
                    modified_count=len(modified),
                    staged_count=len(staged),
                )
                self._render()
                QApplication.processEvents()
        finally:
            QApplication.restoreOverrideCursor()
        self._render()

    @staticmethod
    def _format_status(
        ahead_behind: tuple[int, int] | None,
        untracked_count: int = 0,
        modified_count: int = 0,
        staged_count: int = 0,
    ) -> str:
        if ahead_behind is None:
            base = "No upstream (nothing pushed yet)"
        else:
            ahead, behind = ahead_behind
            if ahead == 0 and behind == 0:
                base = "Up to date"
            elif behind > 0 and ahead == 0:
                base = f"{behind} commit(s) behind"
            elif ahead > 0 and behind == 0:
                base = f"{ahead} commit(s) ahead (not pushed)"
            else:
                base = f"Diverged (ahead {ahead}, behind {behind})"

        changes = []
        if modified_count > 0:
            changes.append(f"{modified_count} modified")
        if staged_count > 0:
            changes.append(f"{staged_count} staged")
        if untracked_count > 0:
            changes.append(f"{untracked_count} untracked")

        if changes:
            if base == "Up to date":
                base = "Not up to date"
            return f"{base} — {', '.join(changes)} file(s)"

        return base

    def _on_gitignore_update(self) -> None:
        row = self._selected_row()
        if row is None:
            QMessageBox.information(self, "Gitignore Update", "Select an entry first.")
            return
        local_path = self.plugins_root / row.entry.folder_name
        if not self._require_valid_clone(local_path, "Gitignore Update"):
            return

        confirmed = confirm_action(
            self,
            "Gitignore Update",
            f"ต้องการ Untrack ไฟล์ทั้งหมดที่เข้าข่าย .gitignore ใน '{row.entry.name}' ใช่หรือไม่?\n\n(ไฟล์จริงในเครื่องจะไม่ถูกลบ)",
        )
        if not confirmed:
            return

        def action() -> None:
            # ลบส่วนตั้งค่า username / email ชั่วคราวออกไปได้เลย
            # เพราะระบบหลักตั้งค่า user.name / user.email ให้ Repo นี้เรียบร้อยแล้ว
            self.git_service.untrack_ignored_files(local_path)
            self.git_service.commit(local_path, "Untrack gitignored files")
            self.git_service.push(local_path)

        self._run_with_wait_cursor(action, "Gitignore Update")