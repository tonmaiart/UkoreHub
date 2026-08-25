from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QFile, QFileInfo, QSize, Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFileIconProvider,
    QHeaderView,
    QInputDialog,
    QLineEdit,
    QListWidget,
    QMenu,
    QMessageBox,
    QPushButton,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from plugin_api import GitService, LocalConfigStore, MetadataStore, open_in_file_explorer, open_with_default_app
from plugins.core.explorer.bookmarks_store import BookmarksStore
from plugins.core.explorer.file_local_change_panel import FileLocalChangePanel
from plugins.core.explorer.file_row_authors_worker import FileRowAuthorsWorker
from plugins.core.explorer.file_table_proxy import format_time_ago
from plugins.core.explorer.last_opened_store import LastOpenedStore
from plugins.core.explorer.path_commit_history_panel import PathCommitHistoryPanel

COLUMN_COUNT = 5
OPENING_POPUP_DURATION_MS = 3000
_MAX_LAST_OPENED = 20
_UI_FILE = Path(__file__).parent / "explorer_section.ui"
_ICONS_DIR = Path(__file__).parent / "icons"
_NAV_ICON_SIZE = QSize(20, 20)

# tableWidget_current_directory's columns, authored directly in
# explorer_section.ui (Designer <column> entries, so headers come from the
# .ui rather than being set here).
COL_NAME = 0
COL_SIZE = 1
COL_DATE_MODIFIED = 2
COL_TIME_AGO = 3
COL_LOCAL_MODIFIED = 4
COL_LAST_COMMIT = 5
# (button attr name, icon filename, tooltip) — nav buttons are icon-only
# (label text cleared) rather than the old text/emoji labels.
_NAV_BUTTON_ICONS = (
    ("history_back_button", "icons8-back-arrow-48.png", "Back"),
    ("up_button", "icons8-up-48.png", "Up"),
    ("reload_button", "icons8-refresh-60.png", "Refresh"),
    ("add_folder_button", "icons8-add-folder-48.png", "Create New Folder"),
    ("open_directory_button", "icons8-opened-folder-48.png", "Open Current Directory"),
)

logger = logging.getLogger("Explorer")

_ICON_PROVIDER = QFileIconProvider()


def _file_icon(path: Path) -> QIcon:
    """File/folder icon for the Last Opened File and Bookmarks tables — the
    OS-appropriate icon (folder glyph, or the file-type icon Windows
    associates with the extension) via Qt's own QFileIconProvider rather
    than a bundled bitmap, since a bookmark can point at either a file or a
    folder."""
    return _ICON_PROVIDER.icon(QFileInfo(str(path)))


def _mtime_ago(path: Path) -> str:
    try:
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
    except OSError:
        return ""
    return format_time_ago(mtime)


def _format_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{int(size)} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


class _SortableItem(QTableWidgetItem):
    """A QTableWidgetItem that sorts by an explicit key instead of its
    displayed text — needed for Size (numeric) and Date Modified/Time Ago
    (chronological), where the shown string ("12.3 KB", "5 min ago")
    doesn't sort correctly as plain text."""

    def __init__(self, text: str, sort_key):
        super().__init__(text)
        self._sort_key = sort_key

    def __lt__(self, other) -> bool:
        if isinstance(other, _SortableItem):
            return self._sort_key < other._sort_key
        return super().__lt__(other)


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
        local_config_store: LocalConfigStore | None = None,
    ):
        super().__init__(parent)
        self._git_service = git_service
        self._local_config_store = local_config_store
        self._cache_dir = cache_dir
        self._metadata_store = metadata_store
        self._open_file = open_file or open_with_default_app
        self._root: Path | None = None
        self._current_path: Path | None = None
        self._opening_popup: QMessageBox | None = None
        self._back_stack: list[Path] = []
        self._last_opened_store: LastOpenedStore | None = None
        self._bookmarks_store: BookmarksStore | None = None
        self._path_mode: str = "relative"

        # "Last Commit By" per relative_path — fetched once (git log/GitHub,
        # the expensive part) and reused on every later revisit; reset only
        # on repo switch (set_root). "Local Modified By" is cheap (one git
        # status call per navigation) and always recomputed fresh instead —
        # see FileRowAuthorsWorker.
        self._last_commit_cache: dict[str, tuple[str | None, QIcon | None]] = {}
        self._authors_worker: FileRowAuthorsWorker | None = None
        self._retiring_authors_workers: set[FileRowAuthorsWorker] = set()

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
        self.absolute_relative_switch: QPushButton = self.ui.findChild(QPushButton, "pushButton_absolute_relative_switch")
        self.breadcrumb: QLineEdit = self.ui.findChild(QLineEdit, "lineEdit_path")
        self.search_edit: QLineEdit = self.ui.findChild(QLineEdit, "lineEdit_search")
        self.table: QTableWidget = self.ui.findChild(QTableWidget, "tableWidget_current_directory")
        self.last_opened_table: QTableWidget = self.ui.findChild(QTableWidget, "tableWidget_last_opened_file")
        self.bookmarks_table: QTableWidget = self.ui.findChild(QTableWidget, "tableWidget_bookmarks")
        self.commit_table: QTableWidget = self.ui.findChild(QTableWidget, "tableWidget_file_commit_history")
        self.local_change_table: QTableWidget = self.ui.findChild(QTableWidget, "tableWidget_file_local_change")

        self._apply_nav_icons()

        self.history_back_button.setEnabled(False)
        self.history_back_button.clicked.connect(self._on_history_back)

        self.up_button.clicked.connect(self._on_up)

        self.add_folder_button.clicked.connect(self._on_add_folder_clicked)

        self.reload_button.clicked.connect(self.reload)

        self.open_directory_button.clicked.connect(self._on_open_directory_clicked)

        self.breadcrumb.returnPressed.connect(self._on_breadcrumb_entered)
        self.absolute_relative_switch.clicked.connect(self._on_absolute_relative_switch_clicked)
        self.absolute_relative_switch.setText(self._path_mode.capitalize())

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(200)
        self.search_timer.timeout.connect(self._apply_search)
        self.search_edit.textChanged.connect(lambda _t: self.search_timer.start())

        # Miller-column population (iterdir()+sorted() per column, on the UI
        # thread) and the commit-history fetch are both too heavy to redo on
        # every single navigation when the user double-clicks through several
        # folders in quick succession — each _navigate_to call just restarts
        # this timer, so only the folder the user actually settles on pays
        # for the rescan/fetch instead of every folder along the way.
        self._nav_settle_timer = QTimer(self)
        self._nav_settle_timer.setSingleShot(True)
        self._nav_settle_timer.setInterval(120)
        self._nav_settle_timer.timeout.connect(self._apply_settled_navigation)

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

        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(22)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        # Stretch (auto-fills leftover space) would fight a fixed width, so
        # Name is plain Interactive with a large starting width instead —
        # still user-resizable, just wide by default for now.
        header.setSectionResizeMode(COL_NAME, QHeaderView.Interactive)
        self.table.setColumnWidth(COL_NAME, 500)
        # Date Modified used to be Stretch too — with two Stretch columns,
        # Qt splits leftover space between them evenly regardless of actual
        # content width, so a short date string ended up as wide as Name.
        # ResizeToContents sizes it to what it actually needs instead.
        header.setSectionResizeMode(COL_DATE_MODIFIED, QHeaderView.ResizeToContents)
        self.table.setColumnWidth(COL_SIZE, 80)
        self.table.setColumnWidth(COL_TIME_AGO, 100)
        self.table.setColumnWidth(COL_LOCAL_MODIFIED, 150)
        self.table.setColumnWidth(COL_LAST_COMMIT, 150)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_table_context_menu)
        self.table.doubleClicked.connect(self._on_table_double_clicked)
        self.table.selectionModel().currentRowChanged.connect(self._on_table_selection_changed)

        self.commit_panel = PathCommitHistoryPanel(git_service, self.commit_table)
        self.local_change_panel = FileLocalChangePanel(git_service, self.local_change_table, local_config_store)

        self._setup_last_opened_table()
        self._setup_bookmarks_table()

    def _apply_nav_icons(self) -> None:
        for attr_name, filename, tooltip in _NAV_BUTTON_ICONS:
            button: QPushButton = getattr(self, attr_name)
            icon_path = _ICONS_DIR / filename
            if not icon_path.is_file():
                logger.warning(f"Nav icon missing: {icon_path}")
                continue
            button.setIcon(QIcon(str(icon_path)))
            button.setIconSize(_NAV_ICON_SIZE)
            button.setText("")
            button.setToolTip(tooltip)

    def _setup_last_opened_table(self) -> None:
        table = self.last_opened_table
        table.setColumnCount(3)
        table.horizontalHeader().setVisible(False)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setShowGrid(False)
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        table.setColumnWidth(0, 24)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.itemClicked.connect(self._on_last_opened_clicked)

    def _setup_bookmarks_table(self) -> None:
        table = self.bookmarks_table
        table.setColumnCount(2)
        table.horizontalHeader().setVisible(False)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setShowGrid(False)
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        table.setColumnWidth(0, 24)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        table.itemClicked.connect(self._on_bookmark_clicked)
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(self._on_bookmarks_context_menu)

    def browse_to_file(self, path: Path) -> None:
        path = Path(path)
        if not path.exists():
            QMessageBox.warning(self, "File Not Found", f"'{path.name}' no longer exists at:\n{path}")
            return
        self._navigate_to(path.parent)
        self._select_file_in_table(path)

    def set_root(self, path: Path, *, repo_id: str, project_id: str | None = None) -> None:
        path = Path(path).resolve()
        self._root = path

        # Relative paths are meaningless across repos — a cached "last
        # commit by" for path "assets/model.ma" in one repo has nothing to
        # do with a file of the same relative path in a different one.
        self._last_commit_cache = {}

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

        self._navigate_to(path)

    def reload(self) -> None:
        """Forces the file table + Folder Navigator to re-read the current
        folder from disk, without changing which folder is open or touching
        navigation history. The file table is populated directly from
        iterdir() on every navigation (no cached filesystem-model listing to
        invalidate), so this is just a re-navigate to the same path. Wired
        to the Reload nav button, and to RepoBrowserPage.refresh_content()
        (interface's RefreshablePage protocol) for Submit's "Sync Others
        Commit" to call into automatically."""
        if self._root is None:
            return
        current = self._current_path or self._root
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
        self.bookmarks_table.setRowCount(0)
        if self._bookmarks_store is None:
            return
        bookmarks = self._bookmarks_store.get_bookmarks()
        self.bookmarks_table.setRowCount(len(bookmarks))
        for row, b_path in enumerate(bookmarks):
            icon_item = QTableWidgetItem()
            icon_item.setIcon(_file_icon(b_path))
            icon_item.setData(Qt.UserRole, str(b_path))
            icon_item.setToolTip(str(b_path))

            name_item = QTableWidgetItem(b_path.name)
            name_item.setToolTip(str(b_path))

            for item in (icon_item, name_item):
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)

            self.bookmarks_table.setItem(row, 0, icon_item)
            self.bookmarks_table.setItem(row, 1, name_item)

    def _on_bookmark_clicked(self, item: QTableWidgetItem) -> None:
        path_item = self.bookmarks_table.item(item.row(), 0)
        if path_item is None:
            return
        path = Path(path_item.data(Qt.UserRole))
        if path.is_dir():
            self._navigate_to(path)
        else:
            self._navigate_to(path.parent)
            self._select_file_in_table(path)

    def _on_bookmarks_context_menu(self, pos) -> None:
        item = self.bookmarks_table.itemAt(pos)
        if item is None or self._bookmarks_store is None:
            return
        path_item = self.bookmarks_table.item(item.row(), 0)
        path = Path(path_item.data(Qt.UserRole))
        menu = QMenu(self)
        act_remove = menu.addAction("Remove Bookmark")
        action = menu.exec(self.bookmarks_table.viewport().mapToGlobal(pos))
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
            logger.warning(f"Path {path} is outside root {self._root}. Falling back to root.")
            path = self._root

        if _record_history and self._current_path is not None and path != self._current_path:
            self._back_stack.append(self._current_path)
            self.history_back_button.setEnabled(True)

        self._current_path = path
        self._update_breadcrumb_text(path)
        self._populate_table(path)
        # Rebuilding the table already drops any selection made in the
        # previous folder — without this, File Commit History / File Local
        # Change could otherwise keep showing a file that isn't even in the
        # folder being shown anymore.
        self._clear_file_panels()

        self._nav_settle_timer.start()

    def _populate_table(self, folder: Path) -> None:
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        try:
            entries = list(folder.iterdir())
        except OSError:
            entries = []
        entries.sort(key=lambda p: p.name.lower())

        self.table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            self._set_row(row, entry)

        self.table.setSortingEnabled(True)
        self._apply_search()

    def _set_row(self, row: int, path: Path) -> None:
        is_dir = path.is_dir()
        try:
            stat = path.stat()
        except OSError:
            stat = None

        name_item = _SortableItem(path.name, path.name.lower())
        name_item.setIcon(_file_icon(path))
        name_item.setData(Qt.UserRole, str(path))
        name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(row, COL_NAME, name_item)

        if is_dir or stat is None:
            size_item = _SortableItem("", -1)
        else:
            size_item = _SortableItem(_format_size(stat.st_size), stat.st_size)
        size_item.setFlags(size_item.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(row, COL_SIZE, size_item)

        if stat is not None:
            mod_dt = datetime.fromtimestamp(stat.st_mtime)
            date_item = _SortableItem(mod_dt.strftime("%Y-%m-%d %H:%M:%S"), stat.st_mtime)
            time_ago_item = _SortableItem(format_time_ago(mod_dt), stat.st_mtime)
        else:
            date_item = _SortableItem("", 0)
            time_ago_item = _SortableItem("", 0)
        for item in (date_item, time_ago_item):
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(row, COL_DATE_MODIFIED, date_item)
        self.table.setItem(row, COL_TIME_AGO, time_ago_item)

        for column in (COL_LOCAL_MODIFIED, COL_LAST_COMMIT):
            item = QTableWidgetItem("")
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, column, item)

    def _path_for_row(self, row: int) -> Path | None:
        item = self.table.item(row, COL_NAME)
        if item is None:
            return None
        data = item.data(Qt.UserRole)
        return Path(data) if data else None

    def _row_for_path(self, path: Path) -> int | None:
        for row in range(self.table.rowCount()):
            candidate = self._path_for_row(row)
            if candidate is not None and candidate == path:
                return row
        return None

    def _apply_settled_navigation(self) -> None:
        if self._root is None or self._current_path is None:
            return
        self._sync_columns_from_path(self._current_path)
        self._start_folder_authors_fetch(self._current_path)

    def _start_folder_authors_fetch(self, folder: Path) -> None:
        if self._authors_worker is not None:
            self._retire_authors_worker(self._authors_worker)
            self._authors_worker = None

        try:
            children = list(folder.iterdir())
        except OSError:
            children = []

        entries: list[tuple[str, str, bool]] = []
        for child in children:
            relative = self._relative_path_str(child)
            if not relative:
                continue
            try:
                is_dir = child.is_dir()
            except OSError:
                continue
            # _on_folder_author_ready looks the row up via Path equality
            # (_row_for_path), so the exact separator style doesn't matter —
            # any string Path() can parse works as the abs_path key.
            entries.append((child.as_posix(), relative, is_dir))

        if not entries:
            return

        username = getattr(self._local_config_store, "github_username", None) if self._local_config_store else None
        token = self._git_service.get_github_token()

        worker = FileRowAuthorsWorker(
            self._git_service, self._root, entries, username, token, self._last_commit_cache
        )
        worker.entry_ready.connect(self._on_folder_author_ready)
        self._authors_worker = worker
        worker.start()

    def _on_folder_author_ready(self, abs_path: str, info) -> None:
        row = self._row_for_path(Path(abs_path))
        if row is None:
            return
        local_item = self.table.item(row, COL_LOCAL_MODIFIED)
        if local_item is not None:
            local_item.setText(info.local_modified_by or "")
            local_item.setIcon(info.local_modified_icon or QIcon())
        commit_item = self.table.item(row, COL_LAST_COMMIT)
        if commit_item is not None:
            commit_item.setText(info.last_commit_by or "")
            commit_item.setIcon(info.last_commit_icon or QIcon())

    def _retire_authors_worker(self, worker: FileRowAuthorsWorker) -> None:
        # Same QThread-lifetime hazard as PathCommitHistoryPanel._retire_worker
        # — never let Python's refcounting drop the last reference to a
        # QThread before it has actually finished. requestInterruption() also
        # lets the loop in run() stop between entries promptly instead of
        # grinding through every remaining file in the old folder first.
        worker.requestInterruption()
        if worker.isFinished():
            return
        self._retiring_authors_workers.add(worker)
        worker.finished.connect(lambda: self._retiring_authors_workers.discard(worker))

    def _relative_path_str(self, path: Path) -> str:
        # as_posix() (not str()) is required here: this value is fed to
        # `git log -- <path>` and the GitHub commits API, both of which
        # match pathspecs with forward slashes — a Windows-style
        # backslash-separated relative path silently fails to match either.
        if self._root is None:
            return ""
        try:
            rel = path.relative_to(self._root)
        except ValueError:
            return ""
        rel_str = rel.as_posix()
        return "" if rel_str == "." else rel_str

    def _relative_display_str(self, path: Path) -> str:
        """Repo-relative path for display/copy — always starts with the
        repo's own folder name (unlike _relative_path_str, which is
        relative to _root and omits it), per the "relative path always
        starts at the repo name" convention."""
        if self._root is None:
            return str(path)
        try:
            rel = path.relative_to(self._root)
        except ValueError:
            return str(path)
        root_name = self._root.name
        return root_name if str(rel) == "." else str(Path(root_name) / rel)

    def _update_breadcrumb_text(self, path: Path) -> None:
        self.breadcrumb.setText(self._relative_display_str(path) if self._path_mode == "relative" else str(path))

    def _set_path_mode(self, mode: str) -> None:
        if mode not in ("absolute", "relative"):
            return
        self._path_mode = mode
        self.absolute_relative_switch.setText(mode.capitalize())
        if self._current_path is not None:
            self._update_breadcrumb_text(self._current_path)

    def _on_absolute_relative_switch_clicked(self) -> None:
        self._set_path_mode("relative" if self._path_mode == "absolute" else "absolute")

    def _resolve_typed_path(self, text: str) -> Path | None:
        """Resolves a user-typed breadcrumb path, whether relative
        (starting with the repo's own folder name, e.g. "MyRepo/assets")
        or absolute (possibly from a different machine, e.g.
        "D:/OtherUser/storage/MyRepo/assets") — both are rebased onto this
        machine's own root by finding the repo folder name in the typed
        path's parts and reattaching the remainder to _root, so an
        absolute path copied from a teammate's machine still resolves
        locally instead of failing outright."""
        if self._root is None or not text:
            return None
        candidate = Path(text)
        root_name = self._root.name.lower()
        for idx, part in enumerate(candidate.parts):
            if part.lower() == root_name:
                return self._root.joinpath(*candidate.parts[idx + 1 :])
        if candidate.is_absolute():
            return candidate
        return None

    def _on_table_selection_changed(self, current, _previous) -> None:
        if not current.isValid():
            self._clear_file_panels()
            return
        path = self._path_for_row(current.row())
        if path is None or path.is_dir():
            self._clear_file_panels()
            return
        relative_path = self._relative_path_str(path)
        self.commit_panel.show_commits_for(self._root, relative_path)
        self.local_change_panel.show_local_change_for(self._root, relative_path)

    def _clear_file_panels(self) -> None:
        # File Commit History / File Local Change only ever reflect an
        # actual selected file, never the folder being browsed — clear both
        # rather than leaving a previous file's info on screen.
        self.commit_panel.clear()
        self.local_change_panel.clear()

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
        typed_text = self.breadcrumb.text().strip()
        resolved_path = self._resolve_typed_path(typed_text)
        if resolved_path is not None and resolved_path.exists():
            if resolved_path.is_dir():
                self._navigate_to(resolved_path)
            else:
                # File path pasted in — same behavior as clicking a Last
                # Opened File entry: land on its parent folder with the
                # file itself selected, rather than trying to "open" it.
                self._navigate_to(resolved_path.parent)
                self._select_file_in_table(resolved_path)
            self._set_path_mode("absolute" if Path(typed_text).is_absolute() else "relative")
        elif self._current_path is not None:
            self._update_breadcrumb_text(self._current_path)

    def _apply_search(self) -> None:
        text = self.search_edit.text().strip().lower()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, COL_NAME)
            name = item.text().lower() if item is not None else ""
            self.table.setRowHidden(row, bool(text) and text not in name)

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

    def _on_table_double_clicked(self, index) -> None:
        path = self._path_for_row(index.row())
        if path is None:
            return
        if path.is_dir():
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
        self.last_opened_table.setRowCount(0)
        if self._last_opened_store is None:
            return
        entries = self._last_opened_store.get_last_opened()
        self.last_opened_table.setRowCount(len(entries))
        for row, opened_path in enumerate(entries):
            icon_item = QTableWidgetItem()
            icon_item.setIcon(_file_icon(opened_path))
            icon_item.setData(Qt.UserRole, str(opened_path))
            icon_item.setToolTip(str(opened_path))

            name_item = QTableWidgetItem(opened_path.name)
            name_item.setToolTip(str(opened_path))

            time_item = QTableWidgetItem(_mtime_ago(opened_path))

            for item in (icon_item, name_item, time_item):
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)

            self.last_opened_table.setItem(row, 0, icon_item)
            self.last_opened_table.setItem(row, 1, name_item)
            self.last_opened_table.setItem(row, 2, time_item)

    def _on_last_opened_clicked(self, item: QTableWidgetItem) -> None:
        path_item = self.last_opened_table.item(item.row(), 0)
        if path_item is None:
            return
        path = Path(path_item.data(Qt.UserRole))
        self._navigate_to(path.parent)
        self._select_file_in_table(path)

    def _select_file_in_table(self, path: Path) -> None:
        row = self._row_for_path(path)
        if row is None:
            return
        index = self.table.model().index(row, COL_NAME)
        self.table.setCurrentIndex(index)
        self.table.selectRow(row)
        self.table.scrollTo(index)

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
        index = self.table.indexAt(pos)
        path = self._path_for_row(index.row()) if index.isValid() else None
        if path is None:
            self._on_empty_area_context_menu(pos)
            return

        menu = QMenu(self)
        act_bookmark = menu.addAction("Add this to bookmarks")
        act_bookmark.setEnabled(self._bookmarks_store is not None)
        menu.addSeparator()
        act_copy_name = menu.addAction("Copy Name")
        act_copy_relative_path = menu.addAction("Copy File Relative Path")
        act_copy_absolute_path = menu.addAction("Copy File Absolute Path")
        menu.addSeparator()
        act_rename = menu.addAction("Rename")
        act_delete = menu.addAction("Delete")

        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        if action == act_bookmark:
            self._add_to_bookmarks(path)
        elif action == act_copy_name:
            QApplication.clipboard().setText(path.name)
        elif action == act_copy_relative_path:
            QApplication.clipboard().setText(self._relative_display_str(path))
        elif action == act_copy_absolute_path:
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
