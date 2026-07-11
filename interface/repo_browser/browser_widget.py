from __future__ import annotations

import shutil
from pathlib import Path

from PySide6.QtCore import QDir, Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileSystemModel,
    QHBoxLayout,
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

from core.os_utils import open_in_file_explorer, open_with_default_app
from interface.repo_browser.file_table_proxy import FileTableFilterProxy

COLUMN_COUNT = 5


class RepoBrowserWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._root: Path | None = None
        self._current_path: Path | None = None
        self._history: list[Path] = []

        self.fs_model = QFileSystemModel()
        self.fs_model.setFilter(QDir.NoDotAndDotDot | QDir.AllEntries)
        self.proxy = FileTableFilterProxy()
        self.proxy.setSourceModel(self.fs_model)

        self.back_button = QPushButton("< Back")
        self.back_button.clicked.connect(self._on_back)
        self.breadcrumb = QLineEdit()
        self.breadcrumb.returnPressed.connect(self._on_breadcrumb_entered)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search files...")
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(200)
        self.search_timer.timeout.connect(self._apply_search)
        self.search_edit.textChanged.connect(lambda _t: self.search_timer.start())
        self.latest_version_checkbox = QCheckBox("Latest version only")
        self.latest_version_checkbox.toggled.connect(self.proxy.set_latest_version_only)

        top_row = QHBoxLayout()
        top_row.addWidget(self.back_button)
        top_row.addWidget(self.breadcrumb, stretch=1)
        top_row.addWidget(self.search_edit)
        top_row.addWidget(self.latest_version_checkbox)

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
            list_widget.itemClicked.connect(lambda item, idx=i: self._on_column_item_clicked(idx, item))
            column_layout.addWidget(filter_edit)
            column_layout.addWidget(list_widget)
            columns_row.addWidget(column_widget)
            self.columns.append(list_widget)
            self.column_filters.append(filter_edit)

        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_table_context_menu)
        self.table.doubleClicked.connect(self._on_table_double_clicked)

        layout = QVBoxLayout(self)
        layout.addLayout(top_row)
        layout.addLayout(columns_row)
        layout.addWidget(self.table)

    def set_root(self, path: Path) -> None:
        path = Path(path)
        self._root = path
        self._history.clear()
        self.fs_model.setRootPath(str(path))
        self._navigate_to(path, push_history=False)

    def _navigate_to(self, path: Path, *, push_history: bool = True) -> None:
        path = Path(path)
        if self._root is None:
            return
        try:
            path.relative_to(self._root)
        except ValueError:
            return
        if push_history and self._current_path is not None and self._current_path != path:
            self._history.append(self._current_path)
        self._current_path = path
        self.breadcrumb.setText(str(path))
        index = self.fs_model.index(str(path))
        self.table.setRootIndex(self.proxy.mapFromSource(index))
        self._sync_columns_from_path(path)

    def _on_back(self) -> None:
        if not self._history:
            return
        previous = self._history.pop()
        self._navigate_to(previous, push_history=False)

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
            open_with_default_app(path)

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
        menu.addSeparator()
        act_open_explorer = menu.addAction("Open in File Explorer")

        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        if action == act_copy_name:
            QApplication.clipboard().setText(path.name)
        elif action == act_copy_path:
            QApplication.clipboard().setText(str(path))
        elif action == act_rename:
            self._rename(path)
        elif action == act_delete:
            self._delete(path)
        elif action == act_open_explorer:
            open_in_file_explorer(path)

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
