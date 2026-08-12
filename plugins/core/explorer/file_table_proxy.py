from __future__ import annotations

from PySide6.QtCore import QSortFilterProxyModel, QModelIndex


class FileTableFilterProxy(QSortFilterProxyModel):
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
        
        # ถ้าไม่มีการพิมพ์ค้นหา ให้ผ่านได้ทุกกรณี (รวมถึงโฟลเดอร์ทั้งหมด)
        if not self._search_text:
            return True

        # ถ้ามีการค้นหา ให้เช็คชื่อไฟล์/โฟลเดอร์
        file_name = fs_model.fileName(index)
        return self._search_text in file_name.lower()