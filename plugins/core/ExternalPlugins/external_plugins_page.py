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
from core.git_service import GitService
from core.os_utils import open_in_file_explorer
from interface.shared.widget_helpers import confirm_action
from plugins.core.ExternalPlugins.catalog_entry_dialog import CatalogEntryDialog
from plugins.core.ExternalPlugins.catalog_store import CatalogEntry, ExternalPluginCatalog

_NOT_CLONED = "Not cloned"
_NOT_CHECKED = "Not checked yet"
_BROKEN_GIT = "Broken .git directory (not a valid clone) — delete the folder and Clone again"


@dataclass
class _Row:
    entry: CatalogEntry
    catalogued: bool  # False for an on-disk folder auto-detected but not yet added to the catalog
    status: str


class ExternalPluginsPage(QWidget):
    """Settings > Developer tab: every known cache/plugins/ repo plugin
    (catalogued or just found on disk), whether it's behind its remote,
    and Clone/Pull actions. See this plugin's own README for why this
    runs everything synchronously (with a wait cursor) instead of a
    background QThread."""

    def __init__(
        self,
        parent=None,
        *,
        git_service: GitService,
        plugins_root: Path,
        catalog: ExternalPluginCatalog,
    ):
        super().__init__(parent)
        self.git_service = git_service
        self.plugins_root = Path(plugins_root)
        self.catalog = catalog
        self._rows: list[_Row] = []

        description = QLabel(
            "Every external (repo) plugin known to the studio — cloned into cache/plugins/ or not yet. "
            "Add one that hasn't been cloned here yet, then Clone it; use Check for Updates to see which "
            "cloned ones are behind their remote."
        )
        description.setWordWrap(True)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)

        add_btn = QPushButton("Add")
        edit_btn = QPushButton("Edit")
        delete_btn = QPushButton("Delete")
        clone_btn = QPushButton("Clone")
        pull_btn = QPushButton("Pull")
        check_btn = QPushButton("Check for Updates")
        open_dir_btn = QPushButton("Open Git Directory")
        stage_push_btn = QPushButton("Stage Untracked && Push")
        add_btn.clicked.connect(self._on_add)
        edit_btn.clicked.connect(self._on_edit)
        delete_btn.clicked.connect(self._on_delete)
        clone_btn.clicked.connect(self._on_clone)
        pull_btn.clicked.connect(self._on_pull)
        check_btn.clicked.connect(self._on_check_for_updates)
        open_dir_btn.clicked.connect(self._on_open_git_directory)
        stage_push_btn.clicked.connect(self._on_stage_untracked_and_push)

        button_row = QHBoxLayout()
        for button in (add_btn, edit_btn, delete_btn, clone_btn, pull_btn, check_btn, open_dir_btn, stage_push_btn):
            button_row.addWidget(button)
        button_row.addStretch()

        layout = QVBoxLayout(self)
        layout.addWidget(description)
        layout.addLayout(button_row)
        layout.addWidget(self.list_widget)

        self.refresh_list()

    # -- listing --------------------------------------------------------------

    def refresh_list(self) -> None:
        """Fast, local-only pass: catalog entries + any un-catalogued
        cache/plugins/ folder. No network calls — Check for Updates does
        those on demand."""
        catalogued = self.catalog.list_entries()
        known_folder_names = {entry.folder_name for entry in catalogued}

        rows: list[_Row] = []
        for entry in catalogued:
            rows.append(_Row(entry=entry, catalogued=True, status=self._local_status(entry.folder_name)))

        if self.plugins_root.exists():
            for child in sorted(self.plugins_root.iterdir()):
                if not child.is_dir() or child.name in known_folder_names:
                    continue
                if not self.git_service.is_cloned(child):
                    continue
                git_url = self.git_service.get_remote_url(child) if self.git_service.is_repo_root(child) else ""
                status = _NOT_CHECKED if self.git_service.is_repo_root(child) else _BROKEN_GIT
                ad_hoc_entry = CatalogEntry(id="", name=f"{child.name} (not catalogued)", git_url=git_url, folder_name=child.name)
                rows.append(_Row(entry=ad_hoc_entry, catalogued=False, status=status))

        self._rows = rows
        self._render()

    def _local_status(self, folder_name: str) -> str:
        local_path = self.plugins_root / folder_name
        if not self.git_service.is_cloned(local_path):
            return _NOT_CLONED
        if not self.git_service.is_repo_root(local_path):
            return _BROKEN_GIT
        return _NOT_CHECKED

    def _render(self) -> None:
        selected_folder = self._selected_row().entry.folder_name if self._selected_row() else None
        self.list_widget.clear()
        for row in self._rows:
            label = f"{row.entry.name} — {row.status}"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, row.entry.folder_name)
            self.list_widget.addItem(item)
            if row.entry.folder_name == selected_folder:
                item.setSelected(True)
                self.list_widget.setCurrentItem(item)

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
        dialog = CatalogEntryDialog(
            self,
            name=entry.name if row.catalogued else entry.name.removesuffix(" (not catalogued)"),
            git_url=entry.git_url,
            folder_name=entry.folder_name,
        )
        if not dialog.exec():
            return
        try:
            if row.catalogued:
                self.catalog.edit_entry(
                    entry.id, name=dialog.name(), git_url=dialog.git_url(), folder_name=dialog.folder_name()
                )
            else:
                # Adopts an auto-detected, un-catalogued folder into the catalog.
                self.catalog.add_entry(dialog.name(), dialog.git_url(), dialog.folder_name())
        except UkoreHubError as exc:
            QMessageBox.warning(self, "Edit External Plugin", str(exc))
            return
        self.refresh_list()

    def _on_delete(self) -> None:
        row = self._selected_row()
        if row is None:
            QMessageBox.information(self, "Delete", "Select an entry first.")
            return
        if not row.catalogued:
            QMessageBox.information(self, "Delete", "This folder isn't in the catalog — nothing to remove.")
            return
        confirmed = confirm_action(
            self,
            "Delete External Plugin",
            f"Remove '{row.entry.name}' from the External Plugins catalog for EVERYONE at the studio?\n\n"
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
        self._run_with_wait_cursor(lambda: self.git_service.pull(local_path), "Pull")

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
            QMessageBox.information(self, "Stage Untracked & Push", "Select an entry first.")
            return
        local_path = self.plugins_root / row.entry.folder_name
        if not self._require_valid_clone(local_path, "Stage Untracked & Push"):
            return
        try:
            untracked, _modified, _staged = self.git_service.get_working_tree_status(local_path)
        except GitOperationError as exc:
            QMessageBox.warning(self, "Stage Untracked & Push", str(exc))
            return
        if not untracked:
            QMessageBox.information(self, "Stage Untracked & Push", "No untracked files to stage.")
            return
        confirmed = confirm_action(
            self,
            "Stage Untracked & Push",
            f"Stage {len(untracked)} untracked file(s), commit, and push in '{row.entry.name}'?",
        )
        if not confirmed:
            return
        # A push needs a commit, not just staged changes — a plain message
        # prompt is enough here since this is a bulk "get untracked files
        # in" action, not a real per-file commit-review workflow (Submit's
        # own page already covers that for repos, not repo plugins).
        message, ok = QInputDialog.getMultiLineText(
            self, "Commit Message", "Commit message:", f"Add untracked files ({len(untracked)})"
        )
        if not ok or not message.strip():
            return

        def action() -> None:
            self.git_service.stage_paths(local_path, untracked)
            self.git_service.commit(local_path, message)
            self.git_service.push(local_path)

        self._run_with_wait_cursor(action, "Stage Untracked & Push")

    def _run_with_wait_cursor(self, action, title: str) -> None:
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            action()
        except GitOperationError as exc:
            QMessageBox.warning(self, title, str(exc))
        finally:
            QApplication.restoreOverrideCursor()
        self.refresh_list()

    # -- check for updates --------------------------------------------------------

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
                row.status = "Checking..."
                self._render()
                QApplication.processEvents()
                try:
                    self.git_service.fetch(local_path)
                    ahead_behind = self.git_service.get_ahead_behind(local_path)
                    untracked, _modified, _staged = self.git_service.get_working_tree_status(local_path)
                except GitOperationError as exc:
                    row.status = f"Check failed: {exc}"
                    continue
                row.status = self._format_status(ahead_behind, len(untracked))
        finally:
            QApplication.restoreOverrideCursor()
        self._render()

    @staticmethod
    def _format_status(ahead_behind: tuple[int, int] | None, untracked_count: int) -> str:
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
        if untracked_count > 0:
            # Untracked files mean this clone isn't a clean match for
            # "latest" even when it's otherwise even with its upstream —
            # surfaced as its own not-up-to-date signal since a Pull alone
            # won't resolve it.
            if base == "Up to date":
                base = "Not up to date"
            return f"{base} — {untracked_count} untracked file(s)"
        return base
