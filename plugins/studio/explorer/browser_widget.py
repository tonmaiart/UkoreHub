from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QDir, QSize, Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFileSystemModel,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLineEdit,
    QListWidget,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from core.git_service import GitService
from core.os_utils import open_with_default_app
from plugins.studio.explorer.file_table_proxy import FileTableFilterProxy
from plugins.studio.explorer.path_commit_history_panel import PathCommitHistoryPanel

COLUMN_COUNT = 5
OPENING_POPUP_DURATION_MS = 3000

_ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
# Both nav icons live at the repo root rather than data/icons/ — falls back
# to text (same convention as interface/sidebar/sidebar.py's Setting
# button) if a file isn't there.
BACK_ICON_PATH = _ROOT_DIR / "icons8-back-50.png"
UP_ICON_PATH = _ROOT_DIR / "icons8-up-50.png"
NAV_ICON_SIZE = QSize(18, 18)


def _apply_nav_icon(button: QPushButton, icon_path: Path, fallback_text: str) -> None:
    if icon_path.exists():
        button.setIcon(QIcon(str(icon_path)))
        button.setIconSize(NAV_ICON_SIZE)
        button.setToolTip(fallback_text)
    else:
        button.setText(fallback_text)


class RepoBrowserWidget(QWidget):
    def __init__(self, parent=None, *, git_service: GitService, open_file: Callable[[Path], None] | None = None):
        super().__init__(parent)
        self._open_file = open_file or open_with_default_app
        self._root: Path | None = None
        self._current_path: Path | None = None
        self._opening_popup: QMessageBox | None = None
        # History for the "Back" button (browser-style: return to whatever
        # path was current before the most recent navigation) — separate
        # from the "Up" button, which always goes to the parent folder
        # regardless of navigation history.
        self._back_stack: list[Path] = []

        self.fs_model = QFileSystemModel()
        self.fs_model.setFilter(QDir.NoDotAndDotDot | QDir.AllEntries)
        self.proxy = FileTableFilterProxy()
        self.proxy.setSourceModel(self.fs_model)

        # "Back" returns to the previously visited path (browser history-style,
        # see _back_stack) — "Up" always jumps to the current path's parent
        # folder, regardless of what was visited before.
        self.history_back_button = QPushButton()
        _apply_nav_icon(self.history_back_button, BACK_ICON_PATH, "Back")
        self.history_back_button.setEnabled(False)
        self.history_back_button.clicked.connect(self._on_history_back)
        self.up_button = QPushButton()
        _apply_nav_icon(self.up_button, UP_ICON_PATH, "Up")
        self.up_button.clicked.connect(self._on_up)
        self.breadcrumb = QLineEdit()
        self.breadcrumb.returnPressed.connect(self._on_breadcrumb_entered)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search files...")
        self.search_edit.setMaximumWidth(160)
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(200)
        self.search_timer.timeout.connect(self._apply_search)
        self.search_edit.textChanged.connect(lambda _t: self.search_timer.start())

        nav_row = QHBoxLayout()
        nav_row.addWidget(self.history_back_button)
        nav_row.addWidget(self.up_button)
        nav_row.addWidget(self.breadcrumb, stretch=1)
        nav_row.addWidget(self.search_edit)

        # "Folder Navigator": the COLUMN_COUNT (5) side-by-side drill-down
        # lists above the file table — one column per folder depth, each
        # narrowing the next (a Miller-column browser, like macOS Finder's
        # column view). Kept spacing tight so more entries fit per column.
        self.columns: list[QListWidget] = []
        self.column_filters: list[QLineEdit] = []
        columns_row = QHBoxLayout()
        for i in range(COLUMN_COUNT):
            column_widget = QWidget()
            column_layout = QVBoxLayout(column_widget)
            column_layout.setContentsMargins(0, 0, 0, 0)
            filter_edit = QLineEdit()
            filter_edit.setPlaceholderText("Filter...")
            filter_edit.textChanged.connect(lambda _t, idx=i: self._filter_column(idx))
            list_widget = QListWidget()
            list_widget.setSpacing(0)
            list_widget.setStyleSheet("QListWidget::item { padding: 0px 4px; margin: 0px; }")
            list_widget.itemClicked.connect(lambda item, idx=i: self._on_column_item_clicked(idx, item))
            column_layout.addWidget(filter_edit)
            column_layout.addWidget(list_widget)
            columns_row.addWidget(column_widget)
            self.columns.append(list_widget)
            self.column_filters.append(filter_edit)

        folder_navigator_group = QGroupBox("Folder Navigator")
        folder_navigator_layout = QVBoxLayout(folder_navigator_group)
        folder_navigator_layout.addLayout(columns_row)

        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(22)
        # Name and Date Modified are the columns users actually scan, so they
        # get Stretch (claim any resize slack first) — Size stays Interactive
        # so it can't eat into their share, and Type is hidden entirely
        # (QFileSystemModel column 2 — redundant with the file's icon/name).
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setColumnHidden(2, True)
        self.table.setColumnWidth(1, 80)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_table_context_menu)
        self.table.doubleClicked.connect(self._on_table_double_clicked)
        self.table.selectionModel().currentRowChanged.connect(self._on_table_selection_changed)

        self.commit_panel = PathCommitHistoryPanel(git_service)

        table_row = QHBoxLayout()
        table_row.addWidget(self.table, stretch=1)
        table_row.addWidget(self.commit_panel)

        main_column = QVBoxLayout()
        main_column.addWidget(folder_navigator_group, stretch=0)
        main_column.addLayout(nav_row, stretch=0)
        main_column.addLayout(table_row, stretch=1)

        layout = QVBoxLayout(self)
        layout.addLayout(main_column)

    def browse_to_file(self, path: Path) -> None:
        """Navigates to the folder containing `path` — called from other
        tabs (e.g. Submit's commit-card Browse button / Inspect in Explorer)
        to jump here and show a specific file."""
        self._navigate_to(Path(path).parent)

    def set_root(self, path: Path) -> None:
        path = Path(path)
        self._root = path
        self.fs_model.setRootPath(str(path))
        self._navigate_to(path)

    def _navigate_to(self, path: Path, *, _record_history: bool = True) -> None:
        path = Path(path)
        if self._root is None:
            return
        try:
            path.relative_to(self._root)
        except ValueError:
            return
        if _record_history and self._current_path is not None and path != self._current_path:
            self._back_stack.append(self._current_path)
            self.history_back_button.setEnabled(True)
        self._current_path = path
        self.breadcrumb.setText(str(path))
        index = self.fs_model.index(str(path))
        self.table.setRootIndex(self.proxy.mapFromSource(index))
        self._sync_columns_from_path(path)
        self.commit_panel.show_commits_for(self._root, self._relative_path_str(path))

    def _relative_path_str(self, path: Path) -> str:
        if self._root is None:
            return ""
        try:
            rel = path.relative_to(self._root)
        except ValueError:
            return ""
        rel_str = str(rel)
        return "" if rel_str == "." else rel_str

    def _on_table_selection_changed(self, current, _previous) -> None:
        if not current.isValid():
            return
        source_index = self.proxy.mapToSource(current)
        path = Path(self.fs_model.filePath(source_index))
        if self.fs_model.isDir(source_index):
            return  # folder-level history is already shown by _navigate_to
        self.commit_panel.show_commits_for(self._root, self._relative_path_str(path))

    def _on_up(self) -> None:
        if self._current_path is None or self._root is None or self._current_path == self._root:
            return
        self._navigate_to(self._current_path.parent)

    def _on_history_back(self) -> None:
        if not self._back_stack:
            return
        previous_path = self._back_stack.pop()
        self._navigate_to(previous_path, _record_history=False)
        self.history_back_button.setEnabled(bool(self._back_stack))

    def _on_breadcrumb_entered(self) -> None:
        typed_path = Path(self.breadcrumb.text().strip())
        if typed_path.exists():
            self._navigate_to(typed_path)
        else:
            self.breadcrumb.setText(str(self._current_path))

    def _apply_search(self) -> None:
        self.proxy.set_search_text(self.search_edit.text())

    def _populate_column(self, index: int, folder: Path) -> None:
        list_widget = self.columns[index]
        list_widget.clear()
        if not folder.is_dir():
            return
        try:
            entries = sorted(p for p in folder.iterdir() if p.is_dir())
        except OSError:
            entries = []
        for entry in entries:
            list_widget.addItem(entry.name)
            item = list_widget.item(list_widget.count() - 1)
            item.setData(Qt.UserRole, str(entry))
        self.column_filters[index].clear()

    def _filter_column(self, index: int) -> None:
        text = self.column_filters[index].text().lower()
        list_widget = self.columns[index]
        for row in range(list_widget.count()):
            item = list_widget.item(row)
            item.setHidden(bool(text) and text not in item.text().lower())

    def _on_column_item_clicked(self, index: int, item) -> None:
        folder_path = Path(item.data(Qt.UserRole))
        for later in self.columns[index + 1 :]:
            later.clear()
        if index + 1 < COLUMN_COUNT:
            self._populate_column(index + 1, folder_path)
        self._navigate_to(folder_path)

    def _sync_columns_from_path(self, path: Path) -> None:
        if self._root is None:
            return
        self._populate_column(0, self._root)
        try:
            rel_parts = path.relative_to(self._root).parts
        except ValueError:
            rel_parts = ()
        current = self._root
        for depth, part in enumerate(rel_parts[:COLUMN_COUNT]):
            self._select_in_column(depth, part)
            current = current / part
            if depth + 1 < COLUMN_COUNT:
                self._populate_column(depth + 1, current)
        for depth in range(len(rel_parts) + 1, COLUMN_COUNT):
            self.columns[depth].clear()

    def _select_in_column(self, index: int, name: str) -> None:
        list_widget = self.columns[index]
        for row in range(list_widget.count()):
            item = list_widget.item(row)
            if item.text() == name:
                list_widget.setCurrentItem(item)
                return

    def _on_table_double_clicked(self, proxy_index) -> None:
        source_index = self.proxy.mapToSource(proxy_index)
        path = Path(self.fs_model.filePath(source_index))
        if self.fs_model.isDir(source_index):
            self._navigate_to(path)
        else:
            self._show_opening_popup(path)
            self._open_file(path)

    def _show_opening_popup(self, path: Path) -> None:
        # Non-modal and self-closing — just a quick acknowledgement that the
        # double-click registered and the app is launching, not something
        # the user has to dismiss. Kept as an instance attribute (rather
        # than a bare local) and explicitly deleteLater()'d so a rapid
        # double-click on another file can't leave a stale popup lingering.
        if self._opening_popup is not None:
            self._opening_popup.close()
            self._opening_popup.deleteLater()
            self._opening_popup = None

        popup = QMessageBox(self)
        popup.setWindowTitle("Opening")
        popup.setText(f"Opening '{path.name}'...")
        popup.setStandardButtons(QMessageBox.NoButton)
        popup.setModal(False)
        popup.show()
        self._opening_popup = popup
        QTimer.singleShot(OPENING_POPUP_DURATION_MS, lambda: self._close_opening_popup(popup))

    def _close_opening_popup(self, popup: QMessageBox) -> None:
        popup.close()
        popup.deleteLater()
        if self._opening_popup is popup:
            self._opening_popup = None

    def _on_table_context_menu(self, pos) -> None:
        proxy_index = self.table.indexAt(pos)
        if not proxy_index.isValid():
            return
        source_index = self.proxy.mapToSource(proxy_index)
        path = Path(self.fs_model.filePath(source_index))

        menu = QMenu(self)
        act_copy_name = menu.addAction("Copy Name")
        act_copy_path = menu.addAction("Copy File Path")
        menu.addSeparator()
        act_rename = menu.addAction("Rename")
        act_delete = menu.addAction("Delete")

        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        if action == act_copy_name:
            QApplication.clipboard().setText(path.name)
        elif action == act_copy_path:
            QApplication.clipboard().setText(str(path))
        elif action == act_rename:
            self._rename(path)
        elif action == act_delete:
            self._delete(path)

    def _rename(self, path: Path) -> None:
        new_name, ok = QInputDialog.getText(self, "Rename", "New name:", text=path.name)
        if not ok or not new_name.strip():
            return
        try:
            path.rename(path.parent / new_name.strip())
        except OSError as exc:
            QMessageBox.warning(self, "Rename Failed", str(exc))

    def _delete(self, path: Path) -> None:
        confirm = QMessageBox.question(self, "Delete", f"Delete '{path.name}'?")
        if confirm != QMessageBox.Yes:
            return
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
        except OSError as exc:
            QMessageBox.warning(self, "Delete Failed", str(exc))
