from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QDir, QFile, QSize, Qt, QTimer
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QApplication,
    QFileSystemModel,
    QGroupBox,
    QHeaderView,
    QInputDialog,
    QLineEdit,
    QListView,
    QListWidget,
    QMenu,
    QMessageBox,
    QPushButton,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from plugin_api import GitService, MetadataStore, open_in_file_explorer, open_with_default_app
from plugins.core.explorer.bookmarks_store import BookmarksStore
from plugins.core.explorer.file_table_proxy import FileTableFilterProxy, TIME_AGO_COLUMN
from plugins.core.explorer.last_opened_store import LastOpenedStore
from plugins.core.explorer.path_commit_history_panel import PathCommitHistoryPanel

COLUMN_COUNT = 5
OPENING_POPUP_DURATION_MS = 3000
_MAX_LAST_OPENED = 20
NAV_ICON_SIZE = QSize(18, 18)
_UI_FILE = Path(__file__).parent / "explorer_section.ui"


def _apply_nav_icon(button: QPushButton, standard_icon: QStyle.StandardPixmap, fallback_text: str) -> None:
    button.setIcon(button.style().standardIcon(standard_icon))
    button.setIconSize(NAV_ICON_SIZE)
    button.setToolTip(fallback_text)


class _PaddedItemDelegate(QStyledItemDelegate):
    """4px left/right item padding for the column list widgets below —
    replaces the old `QListWidget::item { padding: 0px 4px; }` QSS rule
    with a delegate that insets the paint/sizeHint rect directly."""

    _PADDING = 4

    def paint(self, painter, option, index) -> None:
        option = QStyleOptionViewItem(option)
        option.rect = option.rect.adjusted(self._PADDING, 0, -self._PADDING, 0)
        super().paint(painter, option, index)

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        size.setWidth(size.width() + self._PADDING * 2)
        return size


class RepoBrowserWidget(QWidget):
    def __init__(
        self,
        parent=None,
        *,
        git_service: GitService,
        open_file: Callable[[Path], None] | None = None,
        cache_dir: Path | None = None,
        metadata_store: MetadataStore | None = None,
        debug_bus=None,
    ):
        super().__init__(parent)
        self._debug_bus = debug_bus
        self._cache_dir = cache_dir
        self._metadata_store = metadata_store
        self._open_file = open_file or open_with_default_app
        self._root: Path | None = None
        self._current_path: Path | None = None
        self._opening_popup: QMessageBox | None = None
        self._back_stack: list[Path] = []
        self._last_opened_store: LastOpenedStore | None = None
        self._bookmarks_store: BookmarksStore | None = None

        # UI is authored in Qt Designer (explorer_section.ui) and loaded at
        # runtime instead of being built widget-by-widget in code, so the
        # layout can be edited without touching this file.
        loader = QUiLoader()
        ui_file = QFile(str(_UI_FILE))
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, self)
        ui_file.close()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ui)

        self.history_back_button: QPushButton = self.ui.findChild(QPushButton, "pushButton_back")
        self.up_button: QPushButton = self.ui.findChild(QPushButton, "pushButton_up")
        self.reload_button: QPushButton = self.ui.findChild(QPushButton, "pushButton_refresh")
        self.add_folder_button: QPushButton = self.ui.findChild(QPushButton, "pushButton_create_folder")
        self.open_directory_button: QPushButton = self.ui.findChild(QPushButton, "pushButton_open_current_directory")
        self.breadcrumb: QLineEdit = self.ui.findChild(QLineEdit, "lineEdit_path")
        self.search_edit: QLineEdit = self.ui.findChild(QLineEdit, "lineEdit_search")
        self.table: QTableView = self.ui.findChild(QTableView, "tableView_current_directory")
        self.last_opened_list: QListWidget = self.ui.findChild(QListWidget, "listWidget_last_opened_file")
        self.bookmarks_view: QListView = self.ui.findChild(QListView, "listView_bookmarks")
        commit_panel_container: QGroupBox = self.ui.findChild(QGroupBox, "groupBox_5")

        self.fs_model = QFileSystemModel()
        self.fs_model.setFilter(QDir.NoDotAndDotDot | QDir.AllEntries)
        self.fs_model.directoryLoaded.connect(self._on_directory_loaded)
        self.proxy = FileTableFilterProxy()
        self.proxy.setSourceModel(self.fs_model)

        _apply_nav_icon(self.history_back_button, QStyle.SP_ArrowBack, "Back")
        self.history_back_button.setEnabled(False)
        self.history_back_button.clicked.connect(self._on_history_back)

        _apply_nav_icon(self.up_button, QStyle.SP_FileDialogToParent, "Up")
        self.up_button.clicked.connect(self._on_up)

        _apply_nav_icon(self.add_folder_button, QStyle.SP_FileDialogNewFolder, "New Folder")
        self.add_folder_button.clicked.connect(self._on_add_folder_clicked)

        _apply_nav_icon(self.reload_button, QStyle.SP_BrowserReload, "Reload")
        self.reload_button.clicked.connect(self.reload)

        _apply_nav_icon(self.open_directory_button, QStyle.SP_DirOpenIcon, "Open Directory")
        self.open_directory_button.clicked.connect(self._on_open_directory_clicked)

        self.breadcrumb.returnPressed.connect(self._on_breadcrumb_entered)

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(200)
        self.search_timer.timeout.connect(self._apply_search)
        self.search_edit.textChanged.connect(lambda _t: self.search_timer.start())

        self.columns: list[QListWidget] = []
        self.column_filters: list[QLineEdit] = []
        for i in range(COLUMN_COUNT):
            list_widget: QListWidget = self.ui.findChild(QListWidget, f"listWidget_column_{i + 1}")
            filter_edit: QLineEdit = self.ui.findChild(QLineEdit, f"lineEdit_column_{i + 1}_search")
            list_widget.setSpacing(0)
            list_widget.setItemDelegate(_PaddedItemDelegate(list_widget))
            list_widget.itemClicked.connect(lambda item, idx=i: self._on_column_item_clicked(idx, item))
            filter_edit.textChanged.connect(lambda _t, idx=i: self._filter_column(idx))
            self.columns.append(list_widget)
            self.column_filters.append(filter_edit)

        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(22)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setColumnHidden(2, True)
        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(TIME_AGO_COLUMN, 100)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_table_context_menu)
        self.table.doubleClicked.connect(self._on_table_double_clicked)
        self.table.selectionModel().currentRowChanged.connect(self._on_table_selection_changed)

        self.commit_panel = PathCommitHistoryPanel(git_service)
        commit_layout = commit_panel_container.layout()
        if commit_layout is None:
            commit_layout = QVBoxLayout(commit_panel_container)
        commit_layout.setContentsMargins(0, 0, 0, 0)
        commit_layout.addWidget(self.commit_panel)

        self.last_opened_list.setSpacing(0)
        self.last_opened_list.itemClicked.connect(self._on_last_opened_clicked)

        self.bookmarks_model = QStandardItemModel(self)
        self.bookmarks_view.setModel(self.bookmarks_model)
        self.bookmarks_view.setEditTriggers(QListView.NoEditTriggers)
        self.bookmarks_view.clicked.connect(self._on_bookmark_clicked)
        self.bookmarks_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.bookmarks_view.customContextMenuRequested.connect(self._on_bookmarks_context_menu)

    def browse_to_file(self, path: Path) -> None:
        self._navigate_to(Path(path).parent)

    def set_root(self, path: Path, *, repo_id: str, project_id: str | None = None) -> None:
        path = Path(path).resolve()
        self._root = path

        if self._cache_dir:
            self._last_opened_store = LastOpenedStore(
                repo_root=path, cache_dir=self._cache_dir, repo_id=repo_id, max_entries=_MAX_LAST_OPENED
            )
            self._refresh_last_opened_list()

        if self._metadata_store is not None and project_id:
            self._bookmarks_store = BookmarksStore(
                metadata_store=self._metadata_store, project_id=project_id, repo_id=repo_id, repo_root=path
            )
        else:
            self._bookmarks_store = None
        self._refresh_bookmarks_list()

        self.fs_model.setRootPath(path.as_posix())
        self._navigate_to(path)

    def reload(self) -> None:
        """Forces the file table + Folder Navigator to re-read the current
        folder from disk, without changing which folder is open or touching
        navigation history. QFileSystemModel has no public "rescan" call and
        normally relies on its own filesystem watcher — which can miss or
        lag behind a bulk change like a git clone/pull (many files
        created/modified/deleted at once). Toggling setRootPath to "" and
        back forces Qt to drop its cached listing and re-fetch instead of
        waiting on the watcher. Wired to the Reload nav button, and to
        RepoBrowserPage.refresh_content() (interface's RefreshablePage
        protocol) for Submit's "Sync Others Commit" to call into
        automatically."""
        if self._root is None:
            return
        current = self._current_path or self._root
        self.fs_model.setRootPath("")
        self.fs_model.setRootPath(self._root.as_posix())
        self._navigate_to(current, _record_history=False)

    # -------------------------------------------------------------
    # Bookmarks
    # -------------------------------------------------------------
    def _add_to_bookmarks(self, path: Path) -> None:
        if self._bookmarks_store is None:
            return
        self._bookmarks_store.add(path)
        self._refresh_bookmarks_list()

    def _refresh_bookmarks_list(self) -> None:
        self.bookmarks_model.clear()
        if self._bookmarks_store is None:
            return
        for b_path in self._bookmarks_store.get_bookmarks():
            item = QStandardItem(b_path.name)
            item.setEditable(False)
            item.setData(str(b_path), Qt.UserRole)
            item.setToolTip(str(b_path))
            self.bookmarks_model.appendRow(item)

    def _on_bookmark_clicked(self, index) -> None:
        path = Path(index.data(Qt.UserRole))
        if path.is_dir():
            self._navigate_to(path)
        else:
            self._navigate_to(path.parent)
            self._select_file_in_table(path)

    def _on_bookmarks_context_menu(self, pos) -> None:
        index = self.bookmarks_view.indexAt(pos)
        if not index.isValid() or self._bookmarks_store is None:
            return
        path = Path(index.data(Qt.UserRole))
        menu = QMenu(self)
        act_remove = menu.addAction("Remove Bookmark")
        action = menu.exec(self.bookmarks_view.viewport().mapToGlobal(pos))
        if action == act_remove:
            self._bookmarks_store.remove(path)
            self._refresh_bookmarks_list()

    def _navigate_to(self, path: Path, *, _record_history: bool = True) -> None:
        path = Path(path).resolve()
        if self._root is None:
            return

        try:
            path.relative_to(self._root)
        except ValueError:
            if self._debug_bus:
                self._debug_bus.log("Explorer", f"[WARN] Path {path} is outside root {self._root}. Falling back to root.")
            path = self._root

        if _record_history and self._current_path is not None and path != self._current_path:
            self._back_stack.append(self._current_path)
            self.history_back_button.setEnabled(True)

        self._current_path = path
        self.breadcrumb.setText(str(path))

        posix_path = path.as_posix()
        source_index = self.fs_model.index(posix_path)
        proxy_index = self.proxy.mapFromSource(source_index)

        if self._debug_bus:
            self._debug_bus.log(
                "Explorer",
                f"_navigate_to: {posix_path} | source_valid={source_index.isValid()} | proxy_valid={proxy_index.isValid()}",
            )

        if proxy_index.isValid():
            self.table.setRootIndex(proxy_index)
        elif source_index.isValid():
            self.table.setRootIndex(self.proxy.mapFromSource(source_index))

        self._sync_columns_from_path(path)
        self.commit_panel.show_commits_for(self._root, self._relative_path_str(path))

    def _on_directory_loaded(self, path_str: str) -> None:
        if self._current_path and Path(path_str).resolve() == self._current_path.resolve():
            source_index = self.fs_model.index(path_str)
            proxy_index = self.proxy.mapFromSource(source_index)

            if proxy_index.isValid():
                self.table.setRootIndex(proxy_index)
                if self._debug_bus:
                    self._debug_bus.log("Explorer", f"directoryLoaded success: {path_str}")
            elif source_index.isValid():
                self.table.setRootIndex(self.proxy.mapFromSource(source_index))

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
            return
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

    def _on_add_folder_clicked(self) -> None:
        if self._current_path is None:
            return
        self._create_new_folder(self._current_path)

    def _on_open_directory_clicked(self) -> None:
        if self._current_path is None:
            return
        open_in_file_explorer(self._current_path)

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
            self._record_last_opened(path)

    def _record_last_opened(self, path: Path) -> None:
        if self._last_opened_store is None:
            return
        self._last_opened_store.add(path)
        self._refresh_last_opened_list()

    def _refresh_last_opened_list(self) -> None:
        self.last_opened_list.clear()
        if self._last_opened_store is None:
            return
        for opened_path in self._last_opened_store.get_last_opened():
            self.last_opened_list.addItem(opened_path.name)
            item = self.last_opened_list.item(self.last_opened_list.count() - 1)
            item.setData(Qt.UserRole, str(opened_path))
            item.setToolTip(str(opened_path))

    def _on_last_opened_clicked(self, item) -> None:
        path = Path(item.data(Qt.UserRole))
        self._navigate_to(path.parent)
        self._select_file_in_table(path)

    def _select_file_in_table(self, path: Path) -> None:
        source_index = self.fs_model.index(str(path))
        if not source_index.isValid():
            return
        proxy_index = self.proxy.mapFromSource(source_index)
        if not proxy_index.isValid():
            return
        self.table.setCurrentIndex(proxy_index)
        self.table.selectRow(proxy_index.row())
        self.table.scrollTo(proxy_index)

    def _show_opening_popup(self, path: Path) -> None:
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
            self._on_empty_area_context_menu(pos)
            return
        source_index = self.proxy.mapToSource(proxy_index)
        path = Path(self.fs_model.filePath(source_index))

        menu = QMenu(self)
        act_bookmark = menu.addAction("Add this to bookmarks")
        act_bookmark.setEnabled(self._bookmarks_store is not None)
        menu.addSeparator()
        act_copy_name = menu.addAction("Copy Name")
        act_copy_path = menu.addAction("Copy File Path")
        menu.addSeparator()
        act_rename = menu.addAction("Rename")
        act_delete = menu.addAction("Delete")

        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        if action == act_bookmark:
            self._add_to_bookmarks(path)
        elif action == act_copy_name:
            QApplication.clipboard().setText(path.name)
        elif action == act_copy_path:
            QApplication.clipboard().setText(str(path))
        elif action == act_rename:
            self._rename(path)
        elif action == act_delete:
            self._delete(path)

    def _on_empty_area_context_menu(self, pos) -> None:
        if self._current_path is None:
            return
        is_root = self._root is not None and self._current_path == self._root

        menu = QMenu(self)
        act_new_folder = menu.addAction("Create New Folder")
        menu.addSeparator()
        act_rename_folder = menu.addAction("Rename Folder")
        act_delete_folder = menu.addAction("Delete Folder")
        act_rename_folder.setEnabled(not is_root)
        act_delete_folder.setEnabled(not is_root)

        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        if action == act_new_folder:
            self._create_new_folder(self._current_path)
        elif action == act_rename_folder:
            self._rename_current_folder()
        elif action == act_delete_folder:
            self._delete_current_folder()

    def _create_new_folder(self, parent_dir: Path) -> None:
        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if not ok or not name.strip():
            return
        try:
            (parent_dir / name.strip()).mkdir()
        except OSError as exc:
            QMessageBox.warning(self, "Create Folder Failed", str(exc))

    def _rename_current_folder(self) -> None:
        if self._current_path is None or self._root is None or self._current_path == self._root:
            return
        old_path = self._current_path
        new_name, ok = QInputDialog.getText(self, "Rename Folder", "New name:", text=old_path.name)
        if not ok or not new_name.strip():
            return
        new_path = old_path.parent / new_name.strip()
        try:
            old_path.rename(new_path)
        except OSError as exc:
            QMessageBox.warning(self, "Rename Failed", str(exc))
            return
        self._navigate_to(new_path, _record_history=False)

    def _delete_current_folder(self) -> None:
        if self._current_path is None or self._root is None or self._current_path == self._root:
            return
        folder = self._current_path
        confirm = QMessageBox.question(self, "Delete Folder", f"Delete '{folder.name}' and all its contents?")
        if confirm != QMessageBox.Yes:
            return
        try:
            shutil.rmtree(folder)
        except OSError as exc:
            QMessageBox.warning(self, "Delete Failed", str(exc))
            return
        self._navigate_to(folder.parent, _record_history=False)

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
