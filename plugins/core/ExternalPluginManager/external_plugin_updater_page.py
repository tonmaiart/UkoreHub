from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import QFile, QObject, QRunnable, Qt, QThreadPool, Signal
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHeaderView,
    QInputDialog,
    QMenu,
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
    confirm_action,
    open_in_file_explorer,
    plugin_source,
)
from plugins.core.ExternalPluginManager import sync_engine
from plugins.core.ExternalPluginManager.catalog_store import CatalogEntry, ExternalPluginCatalog
from plugins.core.ExternalPluginManager.last_check_store import LastCheckedStore
from plugins.core.ExternalPluginManager.sync_status_store import ExternalPluginSyncStatusStore

# Same 5 canonical status buckets as external_plugins_page.py used to show
# before the split — see this plugin's own doc.
_ERROR = "Error"
_NOT_CLONE = "Not Clone"
_MODIFIED = "Modified"
_UPDATE_NEEDED = "Update Needed"
_UP_TO_DATE = "Up to date"
_CHECKING = "Checking..."

_BROKEN_GIT_DETAIL = "Broken .git directory (not a valid clone) — delete the folder and Clone again."
_PENDING_RESTART_DETAIL = "Cloned/updated this session — restart UkoreHub to load it."

_UI_FILE = Path(__file__).resolve().parent / "ExternalPluginUpdaterWindow.ui"

# One shared pool for this page's parallel "Check for Status" runs — each
# catalog entry lives in its own cache/plugins/<folder> clone, so running
# several fetches concurrently is safe (no two tasks ever touch the same
# folder in the same run). Capped rather than unbounded so a large catalog
# doesn't spawn dozens of git subprocesses at once.
_MAX_PARALLEL_CHECKS = 8


def _format_relative(iso_str: str) -> str:
    """"Never" for an entry with no last-check record yet; "Just now" / "N
    minute(s)/hour(s)/day(s) ago" otherwise."""
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

    # Local changes and unpushed commits both need the same remedy (push
    # local work — Bulk Push), so both take priority over a pure "behind"
    # state, which just needs an update instead.
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


@dataclass
class _Row:
    entry: CatalogEntry
    status: str
    detail: str = ""
    checked_at: str = ""


class _StatusCheckSignals(QObject):
    """Lives on the main thread (owned by the page) — a _StatusCheckTask
    running on a QThreadPool worker thread only ever emits through this,
    never touches a Qt widget itself. Qt auto-queues the emit onto the
    receiver's (main) thread, so no locking is needed on the page side."""

    finished = Signal(str, str, str)  # entry_id, status, detail


class _StatusCheckTask(QRunnable):
    """One catalog entry's "Check for Status" network call, run on a
    QThreadPool worker thread so many entries can be checked in parallel
    instead of one at a time. Mirrors sync_engine.sync_entry's read-only
    fetch + ahead/behind + working-tree checks, but never clones/pulls/
    force-syncs anything itself."""

    def __init__(self, git_service: GitService, local_path: Path, entry_id: str, signals: _StatusCheckSignals):
        super().__init__()
        self._git_service = git_service
        self._local_path = local_path
        self._entry_id = entry_id
        self._signals = signals

    def run(self) -> None:
        try:
            self._git_service.safe_untrack_and_clean_ignored(self._local_path)
            self._git_service.fetch(self._local_path)
            ahead_behind = self._git_service.get_ahead_behind(self._local_path)
            untracked, modified, staged = self._git_service.get_working_tree_status(self._local_path)
        except GitOperationError as exc:
            self._signals.finished.emit(self._entry_id, _ERROR, f"Check failed: {exc}")
            return
        status, detail = _format_status(
            ahead_behind, untracked_count=len(untracked), modified_count=len(modified), staged_count=len(staged)
        )
        self._signals.finished.emit(self._entry_id, status, detail)


class ExternalPluginUpdaterPage(QWidget):
    """Settings > Account tab (CATEGORY_GENERAL, label "Plugins" — see
    plugin.py's register()), alongside the built-in "Account" tab: shows
    every cache/plugins/ repo plugin this Project's External Plugins
    catalog declares, whether it's behind its remote, and two toolbar
    actions:

    - "Check for Status" runs every row's fetch/ahead-behind check in
      parallel on a QThreadPool (see _StatusCheckTask) instead of one at a
      time, so a large catalog doesn't make the user wait on N sequential
      network round-trips.
    - "Update All" force-updates every catalog entry — no selection
      needed — the same escape hatch external_plugins_page.py used to call
      "Force Update Selected" (not cloned -> Clone; broken .git -> delete +
      re-clone; otherwise -> GitService.force_sync, i.e. fetch + reset
      --hard + clean -fd), confirmed once up front since it discards local
      changes/unpushed commits.

    Clone / Unclone / Open Directory / Bulk Push are no longer toolbar
    buttons — they're a right-click context menu on the row they apply to
    (_on_context_menu), each enabled/disabled based on that row's current
    clone/status state, same guards the old single-selection buttons used.

    "Check for Status" and "Update All" never run concurrently with each
    other or with a context-menu action — both would mean two git commands
    racing on the same cache/plugins/<folder> clone. See self._busy."""

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
        # Only used to tell "cloned but not yet discovered this session"
        # apart from a real up-to-date row (see _local_status's
        # _PENDING_RESTART_DETAIL branch) — the Requires column itself lives
        # on the Manager page now, not here.
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

        self._busy = False
        self._thread_pool = QThreadPool()
        self._thread_pool.setMaxThreadCount(_MAX_PARALLEL_CHECKS)
        self._check_signals = _StatusCheckSignals()
        self._check_signals.finished.connect(self._on_status_check_result)
        self._pending_checks = 0

        # UI is authored in Qt Designer and loaded at runtime, same
        # QUiLoader pattern external_plugins_page.py uses for its own
        # ExternalPluginManagerWindow.ui.
        loader = QUiLoader()
        ui_file = QFile(str(_UI_FILE))
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, self)
        ui_file.close()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ui)

        find = self.ui.findChild
        self.table_widget: QTableWidget = find(QTableWidget, "tableWidget_external_plugin_repo")
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(["Name", "Status", "Detail", "Last Checked"])
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_widget.customContextMenuRequested.connect(self._on_context_menu)
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        self.check_btn: QPushButton = find(QPushButton, "pushButton_check_for_status")
        self.check_btn.setToolTip("Check every plugin's status against its remote, in parallel.")
        self.check_btn.clicked.connect(self._on_check_for_status)

        self.update_btn: QPushButton = find(QPushButton, "pushButton_update_all")
        self.update_btn.setToolTip(
            "Force-update every plugin to exactly match its remote — discards any local "
            "changes/unpushed commits, no selection needed."
        )
        self.update_btn.clicked.connect(self._on_update_all)

        self.refresh_list()

    # -- listing --------------------------------------------------------------

    def refresh_list(self) -> None:
        """Fast, local-only pass over this project's own catalog entries —
        see _local_status. No network calls; "Check for Status" does those
        on demand."""
        self._rows = [self._local_status(entry) for entry in self.catalog.list_entries()]
        self._render()

    def _local_status(self, entry: CatalogEntry) -> _Row:
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
            return _Row(entry, _ERROR, message or "Merge conflict — resolve it in the clone (Open Directory).")

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
        selected_ids = {item.data(Qt.UserRole + 1) for item in self.table_widget.selectedItems() if item.column() == 0}
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
            self.table_widget.setItem(row_index, 1, status_item)
            self.table_widget.setItem(row_index, 2, QTableWidgetItem(row.detail))
            self.table_widget.setItem(row_index, 3, QTableWidgetItem(_format_relative(row.checked_at)))

            if row.entry.id in selected_ids:
                self.table_widget.selectRow(row_index)

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.check_btn.setEnabled(not busy)
        self.update_btn.setEnabled(not busy)

    # -- Check for Status (parallel) -------------------------------------------

    def _on_check_for_status(self) -> None:
        if self._busy or not self._rows:
            return

        checkable: list[_Row] = []
        for row in self._rows:
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
            checkable.append(row)
        self._render()

        if not checkable:
            return

        self._set_busy(True)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self._pending_checks = len(checkable)
        for row in checkable:
            local_path = self.plugins_root / row.entry.folder_name
            task = _StatusCheckTask(self.git_service, local_path, row.entry.id, self._check_signals)
            self._thread_pool.start(task)

    def _on_status_check_result(self, entry_id: str, status: str, detail: str) -> None:
        for row in self._rows:
            if row.entry.id == entry_id:
                row.status, row.detail = status, detail
                if status != _ERROR:
                    self.last_check_store.set(entry_id, status, detail)
                    cached = self.last_check_store.get(entry_id)
                    row.checked_at = cached.checked_at if cached is not None else row.checked_at
                break

        self._pending_checks -= 1
        self._render()
        if self._pending_checks <= 0:
            QApplication.restoreOverrideCursor()
            self._set_busy(False)

    # -- Update All (force update every entry) ---------------------------------

    def _on_update_all(self) -> None:
        if self._busy:
            return
        rows = list(self._rows)
        if not rows:
            QMessageBox.information(self, "Update All", "No External Plugins in this project's catalog yet.")
            return
        plural = "entry" if len(rows) == 1 else "entries"
        if not confirm_action(
            self,
            "Update All",
            f"This force-updates every External Plugin in this project's catalog ({len(rows)} {plural}), "
            "discarding ALL local changes and unpushed commits and resetting each to exactly match its "
            "remote branch. This cannot be undone. Continue?",
        ):
            return

        problems: list[str] = []

        def action() -> None:
            for row in rows:
                local_path = self.plugins_root / row.entry.folder_name
                if not self.git_service.is_cloned(local_path) or not self.git_service.is_repo_root(local_path):
                    if self.git_service.is_cloned(local_path):
                        try:
                            shutil.rmtree(local_path)
                        except OSError as exc:
                            problems.append(f"{row.entry.name}: could not remove broken clone: {exc}")
                            continue
                    if not row.entry.git_url:
                        problems.append(f"{row.entry.name}: no Git URL set — edit it in External Plugin Manager.")
                        continue
                    try:
                        self.git_service.clone(row.entry.git_url, local_path)
                    except GitOperationError as exc:
                        problems.append(f"{row.entry.name}: {exc}")
                        continue
                else:
                    try:
                        self.git_service.force_sync(local_path)
                    except GitOperationError as exc:
                        problems.append(f"{row.entry.name}: {exc}")
                        continue
                if row.entry.id:
                    self.sync_status_store.clear(row.entry.id)
                    self.last_check_store.clear(row.entry.id)

        self._run_with_wait_cursor(action)
        if problems:
            QMessageBox.warning(self, "Update All", "\n".join(problems))

    # -- right-click context menu (Clone / Unclone / Open Directory / Bulk Push)

    def _on_context_menu(self, pos) -> None:
        if self._busy:
            return
        index = self.table_widget.indexAt(pos)
        if not index.isValid():
            return
        row_index = index.row()
        self.table_widget.selectRow(row_index)
        row = self._rows[row_index]
        local_path = self.plugins_root / row.entry.folder_name
        is_cloned = self.git_service.is_cloned(local_path)

        menu = QMenu(self)
        clone_action = menu.addAction("Clone")
        clone_action.setEnabled(not is_cloned)
        unclone_action = menu.addAction("Unclone")
        unclone_action.setEnabled(is_cloned)
        open_dir_action = menu.addAction("Open Directory")
        open_dir_action.setEnabled(is_cloned)
        bulk_push_action = menu.addAction("Bulk Push")
        bulk_push_action.setEnabled(row.status == _MODIFIED)

        chosen = menu.exec(self.table_widget.viewport().mapToGlobal(pos))
        if chosen is clone_action:
            self._on_clone(row)
        elif chosen is unclone_action:
            self._on_unclone(row)
        elif chosen is open_dir_action:
            self._on_open_git_directory(row)
        elif chosen is bulk_push_action:
            self._on_stage_untracked_and_push(row)

    def _on_clone(self, row: _Row) -> None:
        local_path = self.plugins_root / row.entry.folder_name
        if self.git_service.is_cloned(local_path):
            return
        if not row.entry.git_url:
            QMessageBox.warning(self, "Clone", "This entry has no Git URL set — edit it in External Plugin Manager.")
            return

        def action() -> None:
            self.git_service.clone(row.entry.git_url, local_path)
            if row.entry.id:
                self.sync_status_store.clear(row.entry.id)

        self._run_with_wait_cursor(action)

    def _on_unclone(self, row: _Row) -> None:
        """Deletes the selected entry's local clone from disk — the catalog
        entry itself stays and can be Cloned again later."""
        local_path = self.plugins_root / row.entry.folder_name
        if not self.git_service.is_cloned(local_path):
            return
        if not confirm_action(
            self,
            "Unclone",
            f"Delete the local clone of '{row.entry.name}' at:\n{local_path}\n\n"
            "This removes the folder from disk — any uncommitted changes are lost. "
            "The catalog entry itself stays and can be cloned again later.",
        ):
            return
        try:
            shutil.rmtree(local_path)
        except OSError as exc:
            QMessageBox.warning(
                self,
                "Unclone",
                f"Could not remove '{local_path}':\n{exc}\n\n"
                "Make sure no program (Explorer, an editor, ...) has a file open in it.",
            )
            self.refresh_list()
            return
        if row.entry.id:
            self.sync_status_store.clear(row.entry.id)
            self.last_check_store.clear(row.entry.id)
        self.refresh_list()

    def _on_open_git_directory(self, row: _Row) -> None:
        local_path = self.plugins_root / row.entry.folder_name
        if not self.git_service.is_cloned(local_path):
            return
        open_in_file_explorer(local_path)

    def _on_stage_untracked_and_push(self, row: _Row) -> None:
        if row.status != _MODIFIED:
            return
        local_path = self.plugins_root / row.entry.folder_name
        if not self.git_service.is_cloned(local_path):
            QMessageBox.information(self, "Bulk Push", "Not cloned yet — use Clone first.")
            return
        if not self.git_service.is_repo_root(local_path):
            QMessageBox.warning(self, "Bulk Push", _BROKEN_GIT_DETAIL)
            return

        try:
            untracked, modified, staged = self.git_service.get_working_tree_status(local_path)
        except GitOperationError as exc:
            QMessageBox.warning(self, "Bulk Push", str(exc))
            return

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
            # made locally but not pushed yet — nothing left to
            # stage/commit, just push.
            confirmed = confirm_action(self, "Bulk Push", f"Push existing local commit(s) in '{row.entry.name}'?")
            if not confirmed:
                return

        def action() -> None:
            if all_changed_paths:
                if untracked or modified:
                    self.git_service.stage_paths(local_path, list(set(untracked + modified)))
                self.git_service.commit(local_path, message)
            self.git_service.push(local_path)
            if row.entry.id:
                self.last_check_store.clear(row.entry.id)

        self._run_with_wait_cursor(action)

    def _run_with_wait_cursor(self, action) -> None:
        self._set_busy(True)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            action()
        except GitOperationError as exc:
            QMessageBox.warning(self, "External Plugin Updater", str(exc))
        finally:
            QApplication.restoreOverrideCursor()
            self._set_busy(False)
        self.refresh_list()
