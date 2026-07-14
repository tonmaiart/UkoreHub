from __future__ import annotations

from PySide6.QtCore import QSortFilterProxyModel


class FileTableFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._search_text = ""
        self.setDynamicSortFilter(True)

    def set_search_text(self, text: str) -> None:
        self._search_text = text.lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent) -> bool:
        fs_model = self.sourceModel()
        index = fs_model.index(source_row, 0, source_parent)
        file_name = fs_model.fileName(index)

        if self._search_text and self._search_text not in file_name.lower():
            return False

        return True
