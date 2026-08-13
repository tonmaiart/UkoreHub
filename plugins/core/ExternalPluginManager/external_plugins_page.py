from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from plugin_api import (
    DiscoveredPlugin,
    GitOperationError,
    GitService,
    UkoreHubError,
    confirm_action,
    open_in_file_explorer,
    plugin_source,
)
from plugins.core.ExternalPluginManager import sync_engine
from plugins.core.ExternalPluginManager.catalog_entry_dialog import CatalogEntryDialog
from plugins.core.ExternalPluginManager.catalog_store import CatalogEntry, ExternalPluginCatalog
from plugins.core.ExternalPluginManager.last_check_store import LastCheckedStore
from plugins.core.ExternalPluginManager.sync_status_store import ExternalPluginSyncStatusStore

# The 5 canonical status buckets shown in the Status column (each has its own
# icon, built once in __init__ — see _status_icons). Anything more specific
# (ahead/behind counts, conflict/broken-git instructions, auto-sync failure
# messages) goes in the Detail column instead of being its own bucket.
_ERROR = "Error"
_NOT_CLONE = "Not Clone"
_MODIFIED = "Modified"
_UPDATE_NEEDED = "Update Needed"
_UP_TO_DATE = "Up to date"
_CHECKING = "Checking..."

_BROKEN_GIT_DETAIL = "Broken .git directory (not a valid clone) — delete the folder and Clone again."
_PENDING_RESTART_DETAIL = "Cloned/updated this session — restart UkoreHub to load it."


def _format_relative(iso_str: str) -> str:
    """"Never" for an entry with no last-check record yet; "Just now" / "N
    minute(s)/hour(s)/day(s) ago" otherwise. No existing "ago" helper exists
    anywhere else in this codebase — nearest precedent is project_editor/
    project_graph_view.py's _format_last_synced, which does absolute
    timestamps instead and falls back to "Never" the same way on empty/parse
    failure, which this mirrors."""
    if not iso_str:
        return "Never"
    try:
        checked = datetime.fromisoformat(iso_str)
    except ValueError:
        return iso_str
    if checked.tzinfo is None:
        checked = checked.replace(tzinfo=timezone.utc)
    seconds = (datetime.now(timezone.utc) - checked).total_seconds()
    if seconds < 60:
        return "Just now"
    minutes = int(seconds // 60)
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    hours = int(seconds // 3600)
    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    days = int(seconds // 86400)
    return f"{days} day{'s' if days != 1 else ''} ago"


@dataclass
class _Row:
    entry: CatalogEntry
    status: str
    detail: str = ""
    checked_at: str = ""


class ExternalPluginsPage(QWidget):
    """Settings > Project tab: every cache/plugins/ repo plugin the active
    Project's own catalog declares (Project.plugin_data["external_plugins"]
    ["catalog"], core/models.py), whether it's behind its remote, and
    Clone/Update Selected actions. See this plugin's own README for why this
    page's own manual actions run synchronously (with a wait cursor) instead
    of a background QThread — the separate auto-sync engine (below) does use
    one.

    The table has 4 columns (Name, Status, Detail, Last Checked). Status is
    one of 5 canonical buckets (Error / Not Clone / Modified / Update Needed
    / Up to date), each with its own QStyle icon; Detail carries the
    specific reason (ahead/behind counts, conflict/broken-git instructions,
    auto-sync failure text). "Check for Status" is a network call (fetch +
    ahead/behind), so its result — bucket + detail + timestamp — is cached
    per entry (last_check_store, per-machine) and re-shown by the fast,
    local-only refresh_list() on every reopen, instead of reverting to a
    bare "Up to date" until the next explicit check. It also runs
    git_service.safe_untrack_and_clean_ignored() first on each row as a
    guard against files matching .gitignore ending up tracked (local
    untrack + commit only — never pushes).

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

    The table supports multi-selection: "Update Selected" and "Check for
    Status" both operate over every selected row; "Check for Status" with
    nothing selected falls back to checking every row (its old, single
    default behavior). Add/Edit/Delete/Clone/Open Git Directory/Bulk Push
    stay single-entry actions, guarded to require exactly one selected row.

    Entries the active repo currently requires are also cloned/updated
    automatically at app start and on repo switch, off the UI thread — see
    sync_engine.py/sync_worker.py and this plugin's own README's "Auto-sync
    engine". sync_status_store carries that background engine's last result
    for each entry across Settings-dialog opens (a merge conflict or a
    failed auto-clone/-update surfaces as the Error bucket), so a stuck
    plugin shows up here even if this tab was never opened while the sync
    itself ran."""

    def __init__(
        self,
        parent=None,
        *,
        git_service: GitService,
        plugins_root: Path,
        catalog: ExternalPluginCatalog,
        plugin_catalog: list[DiscoveredPlugin],
        sync_status_store: ExternalPluginSyncStatusStore,
        last_check_store: LastCheckedStore,
    ):
        super().__init__(parent)
        self.git_service = git_service
        self.plugins_root = Path(plugins_root)
        self.catalog = catalog
        self.sync_status_store = sync_status_store
        self.last_check_store = last_check_store
        self._plugin_by_id = {plugin.manifest.id: plugin for plugin in plugin_catalog}
        self._plugin_by_folder = {
            plugin.dir_path.name: plugin for plugin in plugin_catalog if plugin_source(plugin) == "repo"
        }
        self._rows: list[_Row] = []
        self._status_icons = {
            _ERROR: self.style().standardIcon(QStyle.SP_MessageBoxWarning),
            _NOT_CLONE: self.style().standardIcon(QStyle.SP_TitleBarMaxButton),
            _MODIFIED: self.style().standardIcon(QStyle.SP_MessageBoxInformation),
            _UPDATE_NEEDED: self.style().standardIcon(QStyle.SP_ArrowDown),
            _UP_TO_DATE: self.style().standardIcon(QStyle.SP_DialogApplyButton),
        }

        description = QLabel(
            "External (repo) plugins declared for this project — cloned into cache/plugins/ or not yet. "
            "Add one that hasn't been cloned here yet, then Clone it; use Check for Status to see which "
            "cloned ones are behind their remote (also untracks any accidentally-tracked .gitignore'd files "
            "along the way — local commit only, never pushed). Select multiple rows to Update Selected or "
            "Check for Status together; with nothing selected, Check for Status checks every row. Every "
            "entry here is offered as a choice on this project's Requirements & Plugins tab. Entries a repo "
            "currently requires clone/update themselves at app start and on repo switch — an Error status "
            "here can mean an automatic update hit a merge conflict and needs a dev to resolve it by hand "
            "(Open Git Directory)."
        )
        description.setWordWrap(True)

        self.table_widget = QTableWidget(0, 5)
        self.table_widget.setHorizontalHeaderLabels(["Name", "Requires", "Status", "Detail", "Last Checked"])
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        add_btn = QPushButton("Add")
        edit_btn = QPushButton("Edit")
        delete_btn = QPushButton("Delete")
        clone_btn = QPushButton("Clone")
        pull_btn = QPushButton("Update Selected")
        pull_btn.setToolTip("Pull from the remote for every selected plugin (or select one).")

        check_btn = QPushButton("Check for Status")
        check_btn.setToolTip("Check status for selected plugins, or every plugin if nothing is selected.")

        open_dir_btn = QPushButton("Open Selected Cloned Directory")
        open_dir_btn.setToolTip("Open the directory of the selected cloned plugin.")

        stage_push_btn = QPushButton("Bulk Push")
        stage_push_btn.setToolTip(
            "Stage untracked/modified changes (or push already-committed local work) for the "
            "selected plugin — enabled only when its Status is 'Modified'."
        )
        stage_push_btn.setEnabled(False)
        self.stage_push_btn = stage_push_btn

        add_btn.clicked.connect(self._on_add)
        edit_btn.clicked.connect(self._on_edit)
        delete_btn.clicked.connect(self._on_delete)
        clone_btn.clicked.connect(self._on_clone)
        pull_btn.clicked.connect(self._on_pull)
        check_btn.clicked.connect(self._on_check_for_updates)
        open_dir_btn.clicked.connect(self._on_open_git_directory)
        stage_push_btn.clicked.connect(self._on_stage_untracked_and_push)
        self.table_widget.itemSelectionChanged.connect(self._update_stage_push_enabled)

        button_row = QHBoxLayout()
        for button in (add_btn, edit_btn, delete_btn, clone_btn, pull_btn, check_btn, open_dir_btn, stage_push_btn):
            button_row.addWidget(button)
        button_row.addStretch()

        layout = QVBoxLayout(self)
        layout.addWidget(description)
        layout.addLayout(button_row)
        layout.addWidget(self.table_widget)

        self.refresh_list()

    # -- listing --------------------------------------------------------------

    def refresh_list(self) -> None:
        """Fast, local-only pass over this project's own catalog entries.
        No network calls — Check for Status does those on demand, caching
        its result (last_check_store) so this fast pass can still show the
        last known Update Needed/Up to date distinction instead of losing
        it every time the tab reopens."""
        self._rows = [self._local_status(entry) for entry in self.catalog.list_entries()]
        self._render()

    def _local_status(self, entry: CatalogEntry) -> _Row:
        """Live, local-only checks first (cheap, always fresh) — sync_status
        is only ever consulted as a fallback within the branch it actually
        applies to, never as a blanket first check, so a stale persisted
        error can never override a real, current, local git state (see
        this plugin's own README for the bug that ordering avoids)."""
        local_path = self.plugins_root / entry.folder_name
        sync_status = self.sync_status_store.get(entry.id)

        if not self.git_service.is_cloned(local_path):
            if sync_status is not None and sync_status.status == sync_engine.STATUS_ERROR:
                return _Row(entry, _NOT_CLONE, f"Last auto-clone attempt failed: {sync_status.message}")
            return _Row(entry, _NOT_CLONE)
        if not self.git_service.is_repo_root(local_path):
            return _Row(entry, _ERROR, _BROKEN_GIT_DETAIL)
        if self.git_service.has_unresolved_merge(local_path):
            message = sync_status.message if sync_status is not None else ""
            return _Row(entry, _ERROR, message or "Merge conflict — resolve it in the clone (Open Git Directory).")

        try:
            untracked, modified, staged = self.git_service.get_working_tree_status(local_path)
        except Exception:
            return _Row(entry, _ERROR, "Failed to read working tree status.")
        if untracked or modified or staged:
            return _Row(entry, _MODIFIED, self._changes_detail(untracked, modified, staged))

        if sync_status is not None and sync_status.status == sync_engine.STATUS_ERROR:
            return _Row(entry, _ERROR, f"Auto-update failed: {sync_status.message}")

        if entry.folder_name not in self._plugin_by_folder:
            return _Row(entry, _UP_TO_DATE, _PENDING_RESTART_DETAIL)

        cached = self.last_check_store.get(entry.id)
        if cached is not None:
            return _Row(entry, cached.status, cached.detail, cached.checked_at)
        return _Row(entry, _UP_TO_DATE)

    @staticmethod
    def _changes_detail(untracked: list[str], modified: list[str], staged: list[str]) -> str:
        parts = []
        if modified:
            parts.append(f"{len(modified)} modified")
        if staged:
            parts.append(f"{len(staged)} staged")
        if untracked:
            parts.append(f"{len(untracked)} untracked")
        return ", ".join(parts) + " file(s)"

    def _render(self) -> None:
        selected_folders = {
            item.data(Qt.UserRole) for item in self.table_widget.selectedItems() if item.column() == 0
        }
        self.table_widget.setRowCount(0)
        self.table_widget.setRowCount(len(self._rows))
        for row_index, row in enumerate(self._rows):
            name_item = QTableWidgetItem(row.entry.name)
            name_item.setData(Qt.UserRole, row.entry.folder_name)
            name_item.setData(Qt.UserRole + 1, row.entry.id)

            status_item = QTableWidgetItem(row.status)
            icon = self._status_icons.get(row.status)
            if icon is not None:
                status_item.setIcon(icon)

            self.table_widget.setItem(row_index, 0, name_item)
            self.table_widget.setItem(row_index, 1, QTableWidgetItem(self._requires_label(row.entry)))
            self.table_widget.setItem(row_index, 2, status_item)
            self.table_widget.setItem(row_index, 3, QTableWidgetItem(row.detail))
            self.table_widget.setItem(row_index, 4, QTableWidgetItem(_format_relative(row.checked_at)))

            if row.entry.folder_name in selected_folders:
                self.table_widget.selectRow(row_index)

    def _requires_label(self, entry: CatalogEntry) -> str:
        """'X, Y' if this entry is cloned and its manifest declares
        requirements; '' (unknown) if it isn't cloned yet — there's no
        manifest to read until then."""
        plugin = self._plugin_by_folder.get(entry.folder_name)
        if plugin is None or not plugin.manifest.requires:
            return ""
        names = [
            self._plugin_by_id[req_id].manifest.name if req_id in self._plugin_by_id else req_id
            for req_id in plugin.manifest.requires
        ]
        return ", ".join(names)

    def _selected_rows(self) -> list[_Row]:
        folder_names = {
            item.data(Qt.UserRole) for item in self.table_widget.selectedItems() if item.column() == 0
        }
        return [row for row in self._rows if row.entry.folder_name in folder_names]

    def _selected_row(self) -> _Row | None:
        rows = self._selected_rows()
        if len(rows) != 1:
            return None
        return rows[0]

    def _update_stage_push_enabled(self) -> None:
        """Bulk Push is only meaningful on a Modified entry — reuses the
        same row.status the Status column already shows (computed in
        _local_status/_format_status, which counts both working-tree
        changes and unpushed-but-committed work as Modified) instead of a
        separate check here."""
        row = self._selected_row()
        self.stage_push_btn.setEnabled(row is not None and row.status == _MODIFIED)

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
            QMessageBox.information(self, "Edit", "Select exactly one entry first.")
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
            QMessageBox.information(self, "Delete", "Select exactly one entry first.")
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
        .git directory (see the ukorehub-core skill) can never be mistaken
        for a usable clone and have a git command silently run against
        whatever real repo git's discovery walks up to instead."""
        if not self.git_service.is_cloned(local_path):
            QMessageBox.information(self, title, "Not cloned yet — use Clone first.")
            return False
        if not self.git_service.is_repo_root(local_path):
            QMessageBox.warning(self, title, _BROKEN_GIT_DETAIL)
            return False
        return True

    def _on_clone(self) -> None:
        row = self._selected_row()
        if row is None:
            QMessageBox.information(self, "Clone", "Select exactly one entry first.")
            return
        local_path = self.plugins_root / row.entry.folder_name
        if self.git_service.is_cloned(local_path):
            message = "Already cloned — use Update Selected instead." if self.git_service.is_repo_root(
                local_path
            ) else _BROKEN_GIT_DETAIL
            QMessageBox.information(self, "Clone", message)
            return
        if not row.entry.git_url:
            QMessageBox.warning(self, "Clone", "This entry has no Git URL set — edit it first.")
            return

        def action() -> None:
            self.git_service.clone(row.entry.git_url, local_path)
            # A successful manual Clone clears any stale conflict/error the
            # background auto-sync engine had recorded for this entry —
            # otherwise an old auto-clone failure would keep showing Error
            # here even though this fresh clone is fine (manual Pull already
            # clears this on success; Clone needs the same treatment).
            if row.entry.id:
                self.sync_status_store.clear(row.entry.id)

        self._run_with_wait_cursor(action, "Clone")

    def _on_pull(self) -> None:
        rows = self._selected_rows()
        if not rows:
            QMessageBox.information(self, "Update Selected", "Select at least one entry first.")
            return

        problems: list[str] = []

        def action() -> None:
            for row in rows:
                local_path = self.plugins_root / row.entry.folder_name
                if not self.git_service.is_cloned(local_path):
                    problems.append(f"{row.entry.name}: not cloned yet — use Clone first.")
                    continue
                if not self.git_service.is_repo_root(local_path):
                    problems.append(f"{row.entry.name}: {_BROKEN_GIT_DETAIL}")
                    continue
                try:
                    self.git_service.pull(local_path)
                except GitOperationError as exc:
                    problems.append(f"{row.entry.name}: {exc}")
                    continue
                # See _on_clone's own comment — a successful manual Pull
                # clears any stale conflict/error the background auto-sync
                # engine had recorded, so it doesn't linger until the next
                # auto-sync run happens to touch this same entry again.
                if row.entry.id:
                    self.sync_status_store.clear(row.entry.id)

        self._run_with_wait_cursor(action, "Update Selected")
        if problems:
            QMessageBox.warning(self, "Update Selected", "\n".join(problems))

    def _on_open_git_directory(self) -> None:
        row = self._selected_row()
        if row is None:
            QMessageBox.information(self, "Open Git Directory", "Select exactly one entry first.")
            return
        local_path = self.plugins_root / row.entry.folder_name
        if not self.git_service.is_cloned(local_path):
            QMessageBox.information(self, "Open Git Directory", "Not cloned yet — use Clone first.")
            return
        open_in_file_explorer(local_path)

    def _on_stage_untracked_and_push(self) -> None:
        row = self._selected_row()
        if row is None or row.status != _MODIFIED:
            QMessageBox.information(self, "Bulk Push", "Select a 'Modified' entry first.")
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
        message: str | None = None

        if all_changed_paths:
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
        else:
            # Modified with an empty working tree means commit(s) already
            # made locally but not pushed yet (the "N commit(s) ahead — not
            # pushed" case _format_status also buckets as Modified) —
            # nothing left to stage/commit, just push.
            confirmed = confirm_action(
                self, "Bulk Push", f"Push existing local commit(s) in '{row.entry.name}'?"
            )
            if not confirmed:
                return

        def action() -> None:
            if all_changed_paths:
                # ถ้ามีไฟล์ untracked หรือ modified ให้สั่ง stage เพิ่มเติม (ส่วนที่ staged อยู่แล้วคำสั่ง add จะไม่กระทบอะไร)
                if untracked or modified:
                    self.git_service.stage_paths(local_path, list(set(untracked + modified)))
                self.git_service.commit(local_path, message)
            self.git_service.push(local_path)
            # Drop any stale "Modified"/"N commit(s) ahead" result cached
            # from a previous Check for Status — otherwise _local_status
            # keeps showing it after this push already resolved it, since a
            # clean working tree falls back to this cache (see
            # ExternalPluginManager.md's Bulk Push entry).
            if row.entry.id:
                self.last_check_store.clear(row.entry.id)

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
        """Runs over the current selection, or every row if nothing is
        selected (preserves the old single "check everything" default).
        Each cloned+valid row gets safe_untrack_and_clean_ignored() first
        (local untrack + commit only, never pushes — the guard that used to
        be the separate "Gitignore Update All" button) before the network
        fetch, then its result is written to last_check_store so it survives
        a Settings reopen instead of reverting to a bare "Up to date"."""
        rows = self._selected_rows() or self._rows
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            for row in rows:
                local_path = self.plugins_root / row.entry.folder_name
                if not self.git_service.is_cloned(local_path):
                    row.status, row.detail = _NOT_CLONE, ""
                    continue
                if not self.git_service.is_repo_root(local_path):
                    row.status, row.detail = _ERROR, _BROKEN_GIT_DETAIL
                    continue
                if self.git_service.has_unresolved_merge(local_path):
                    refreshed = self._local_status(row.entry)
                    row.status, row.detail, row.checked_at = refreshed.status, refreshed.detail, refreshed.checked_at
                    continue

                row.status, row.detail = _CHECKING, ""
                self._render()
                QApplication.processEvents()

                self.git_service.safe_untrack_and_clean_ignored(local_path)

                try:
                    self.git_service.fetch(local_path)
                    ahead_behind = self.git_service.get_ahead_behind(local_path)
                    untracked, modified, staged = self.git_service.get_working_tree_status(local_path)
                except GitOperationError as exc:
                    row.status, row.detail = _ERROR, f"Check failed: {exc}"
                    self._render()
                    QApplication.processEvents()
                    continue

                status, detail = self._format_status(
                    ahead_behind,
                    untracked_count=len(untracked),
                    modified_count=len(modified),
                    staged_count=len(staged),
                )
                row.status, row.detail = status, detail
                if row.entry.id:
                    self.last_check_store.set(row.entry.id, status, detail)
                    cached = self.last_check_store.get(row.entry.id)
                    row.checked_at = cached.checked_at if cached is not None else row.checked_at
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
    ) -> tuple[str, str]:
        changes = []
        if modified_count:
            changes.append(f"{modified_count} modified")
        if staged_count:
            changes.append(f"{staged_count} staged")
        if untracked_count:
            changes.append(f"{untracked_count} untracked")

        ahead, behind = ahead_behind if ahead_behind is not None else (0, 0)

        # Local changes and unpushed commits both need the same remedy
        # (push local work — Bulk Push), so both take priority over a pure
        # "behind" state, which just needs a Pull instead.
        if changes or ahead > 0:
            detail_bits = []
            if changes:
                detail_bits.append(", ".join(changes) + " file(s)")
            if ahead > 0:
                detail_bits.append(f"{ahead} commit(s) ahead — not pushed")
            return _MODIFIED, "; ".join(detail_bits)

        if ahead_behind is None:
            return _UPDATE_NEEDED, "No upstream configured"
        if behind > 0:
            return _UPDATE_NEEDED, f"{behind} commit(s) behind"
        return _UP_TO_DATE, ""
