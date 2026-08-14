from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QModelIndex, QSortFilterProxyModel, Qt

TIME_AGO_COLUMN = 4
TIME_AGO_HEADER = "Time Ago"


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
    """Wraps a QFileSystemModel and appends a synthetic "Time Ago" column
    (index TIME_AGO_COLUMN) on top of its 4 real columns (Name/Size/Type/
    Date Modified). QSortFilterProxyModel's default index()/mapToSource()
    bound column requests against the source model's own columnCount(), so
    a column that doesn't exist on the source needs index()/mapToSource()
    overridden to redirect it onto column 0's source index instead — every
    column of a Qt tree/table item shares the same internal id/parent, so
    reusing column 0's identifies the same row correctly. Reuse
    internalId() (a plain quintptr/int), not internalPointer() — PySide6
    can't reliably round-trip the opaque pointer wrapper internalPointer()
    returns back through createIndex(), which crashed the app the moment
    the file table actually painted this column."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._search_text = ""
        self.setDynamicSortFilter(True)

    def set_search_text(self, text: str) -> None:
        self._search_text = text.lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        fs_model = self.sourceModel()
        if fs_model is None:
            return True

        index = fs_model.index(source_row, 0, source_parent)

        if not self._search_text:
            return True

        file_name = fs_model.fileName(index)
        return self._search_text in file_name.lower()

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return super().columnCount(parent) + 1

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        if column == TIME_AGO_COLUMN:
            anchor = super().index(row, 0, parent)
            if not anchor.isValid():
                return QModelIndex()
            return self.createIndex(row, column, anchor.internalId())
        return super().index(row, column, parent)

    def mapToSource(self, proxy_index: QModelIndex) -> QModelIndex:
        if proxy_index.isValid() and proxy_index.column() == TIME_AGO_COLUMN:
            anchor = self.createIndex(proxy_index.row(), 0, proxy_index.internalId())
            return super().mapToSource(anchor)
        return super().mapToSource(proxy_index)

    def headerData(self, section: int, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and section == TIME_AGO_COLUMN and role == Qt.DisplayRole:
            return TIME_AGO_HEADER
        return super().headerData(section, orientation, role)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if index.isValid() and index.column() == TIME_AGO_COLUMN:
            fs_model = self.sourceModel()
            source_index = self.mapToSource(index)
            if fs_model is None or not source_index.isValid():
                return None
            if role == Qt.DisplayRole:
                return format_time_ago(fs_model.lastModified(source_index).toPython())
            if role == Qt.ToolTipRole:
                return fs_model.lastModified(source_index).toString("yyyy-MM-dd HH:mm:ss")
            return None
        return super().data(index, role)

    def sort(self, column: int, order=Qt.AscendingOrder) -> None:
        # Synthetic column — no underlying source column to sort by, so
        # clicking its header just leaves the current sort order in place.
        if column == TIME_AGO_COLUMN:
            return
        super().sort(column, order)
