from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QModelIndex, QSortFilterProxyModel, Qt

from plugins.core.explorer.file_row_authors_worker import FileAuthorInfo

TIME_AGO_COLUMN = 4
LOCAL_MODIFIED_BY_COLUMN = 5
LAST_COMMIT_BY_COLUMN = 6

_SYNTHETIC_HEADERS = {
    TIME_AGO_COLUMN: "Time Ago",
    LOCAL_MODIFIED_BY_COLUMN: "Local Modified By",
    LAST_COMMIT_BY_COLUMN: "Last Commit By",
}


def format_time_ago(dt: datetime) -> str:
    seconds = (datetime.now() - dt).total_seconds()
    if seconds < 60:
        return "just now"
    minutes = int(seconds // 60)
    if minutes < 60:
        return f"{minutes} min ago"
    hours = int(seconds // 3600)
    if hours < 24:
        return f"{hours} hour ago" if hours == 1 else f"{hours} hours ago"
    days = int(seconds // 86400)
    if days < 30:
        return f"{days} day ago" if days == 1 else f"{days} days ago"
    months = int(seconds // 2592000)
    if months < 12:
        return f"{months} month ago" if months == 1 else f"{months} months ago"
    years = int(seconds // 31536000)
    return f"{years} year ago" if years == 1 else f"{years} years ago"


class FileTableFilterProxy(QSortFilterProxyModel):
    """Wraps a QFileSystemModel and appends synthetic columns on top of its
    4 real ones (Name/Size/Type/Date Modified): Time Ago, Local Modified By,
    Last Commit By (see _SYNTHETIC_HEADERS for the column indices).
    QSortFilterProxyModel's default index()/mapToSource() bound column
    requests against the source model's own columnCount(), so a column that
    doesn't exist on the source needs index()/mapToSource() overridden to
    redirect it onto column 0's source index instead — every column of a Qt
    tree/table item shares the same internal id/parent, so reusing column
    0's identifies the same row correctly. Reuse internalId() (a plain
    quintptr/int), not internalPointer() — PySide6 can't reliably
    round-trip the opaque pointer wrapper internalPointer() returns back
    through createIndex(), which crashed the app the moment the file table
    actually painted this column.

    Local Modified By / Last Commit By have no way to compute their value
    from the source model itself (they come from RepoBrowserWidget's
    FileRowAuthorsWorker, an async git/GitHub lookup keyed by absolute
    path) — set_author_info()/clear_author_cache() let the widget push
    results in as they arrive, keyed by the same absolute path
    QFileSystemModel.filePath() returns, and dataChanged is emitted for
    just that row's two columns so the view repaints incrementally instead
    of waiting for the whole folder to resolve."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._search_text = ""
        self._author_cache: dict[str, FileAuthorInfo] = {}
        self.setDynamicSortFilter(True)

    def set_search_text(self, text: str) -> None:
        self._search_text = text.lower()
        self.invalidateFilter()

    def set_author_info(self, abs_path: str, info: FileAuthorInfo) -> None:
        self._author_cache[abs_path] = info
        self._notify_row_changed(abs_path)

    def clear_author_cache(self) -> None:
        self._author_cache.clear()

    def _notify_row_changed(self, abs_path: str) -> None:
        fs_model = self.sourceModel()
        if fs_model is None:
            return
        source_index = fs_model.index(abs_path)
        if not source_index.isValid():
            return
        proxy_index = self.mapFromSource(source_index)
        if not proxy_index.isValid():
            return
        row = proxy_index.row()
        parent = proxy_index.parent()
        top_left = self.index(row, LOCAL_MODIFIED_BY_COLUMN, parent)
        bottom_right = self.index(row, LAST_COMMIT_BY_COLUMN, parent)
        self.dataChanged.emit(top_left, bottom_right)

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        fs_model = self.sourceModel()
        # Rapid folder-to-folder navigation can fire this while QFileSystemModel
        # is mid-rescan of source_parent's directory (rows being removed/added
        # out from under us) — hasIndex()/isValid() must be checked before
        # touching fileName() on a row that may no longer exist, since that's
        # a native QFileSystemModel call, not a Python-level lookup.
        if fs_model is None or not fs_model.hasIndex(source_row, 0, source_parent):
            return False
        if not self._search_text:
            return True

        index = fs_model.index(source_row, 0, source_parent)
        if not index.isValid():
            return False
        return self._search_text in fs_model.fileName(index).lower()

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if self.sourceModel() is None:
            return 0
        return super().columnCount(parent) + len(_SYNTHETIC_HEADERS)

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        if column in _SYNTHETIC_HEADERS:
            if row < 0 or row >= self.rowCount(parent):
                return QModelIndex()
            anchor = super().index(row, 0, parent)
            if not anchor.isValid():
                return QModelIndex()
            return self.createIndex(row, column, anchor.internalId())
        return super().index(row, column, parent)

    def mapToSource(self, proxy_index: QModelIndex) -> QModelIndex:
        if proxy_index.isValid() and proxy_index.column() in _SYNTHETIC_HEADERS:
            anchor = self.createIndex(proxy_index.row(), 0, proxy_index.internalId())
            return super().mapToSource(anchor)
        return super().mapToSource(proxy_index)

    def headerData(self, section: int, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and section in _SYNTHETIC_HEADERS and role == Qt.DisplayRole:
            return _SYNTHETIC_HEADERS[section]
        return super().headerData(section, orientation, role)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid() or index.column() not in _SYNTHETIC_HEADERS:
            return super().data(index, role)

        column = index.column()
        fs_model = self.sourceModel()
        source_index = self.mapToSource(index)
        if fs_model is None or not source_index.isValid():
            return None

        if column == TIME_AGO_COLUMN:
            mod_time = fs_model.lastModified(source_index)
            if not mod_time.isValid():
                return None
            if role == Qt.DisplayRole:
                return format_time_ago(mod_time.toPython())
            if role == Qt.ToolTipRole:
                return mod_time.toString("yyyy-MM-dd HH:mm:ss")
            return None

        abs_path = fs_model.filePath(source_index)
        info = self._author_cache.get(abs_path)
        if info is None:
            return None
        if column == LOCAL_MODIFIED_BY_COLUMN:
            if role == Qt.DisplayRole:
                return info.local_modified_by
            if role == Qt.DecorationRole:
                return info.local_modified_icon
            return None
        # LAST_COMMIT_BY_COLUMN
        if role == Qt.DisplayRole:
            return info.last_commit_by
        if role == Qt.DecorationRole:
            return info.last_commit_icon
        return None

    def sort(self, column: int, order=Qt.AscendingOrder) -> None:
        # Synthetic columns — no underlying source column to sort by, so
        # clicking their header just leaves the current sort order in place.
        if column in _SYNTHETIC_HEADERS:
            return
        super().sort(column, order)
