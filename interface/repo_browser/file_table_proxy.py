from __future__ import annotations

import os
import re

from PySide6.QtCore import QSortFilterProxyModel

RE_VERSION = re.compile(r"([_-]?v)(\d{3})", re.IGNORECASE)


class FileTableFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._search_text = ""
        self._latest_version_only = False
        self.setDynamicSortFilter(True)

    def set_search_text(self, text: str) -> None:
        self._search_text = text.lower()
        self.invalidateFilter()

    def set_latest_version_only(self, enabled: bool) -> None:
        self._latest_version_only = enabled
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent) -> bool:
        fs_model = self.sourceModel()
        index = fs_model.index(source_row, 0, source_parent)
        file_name = fs_model.fileName(index)

        if self._search_text and self._search_text not in file_name.lower():
            return False

        if self._latest_version_only and not fs_model.isDir(index):
            stem, ext = os.path.splitext(file_name)
            base, version = self._parse_version(stem)
            if version is not None:
                max_version = self._max_version_for_base(fs_model, source_parent, base, ext)
                if version < max_version:
                    return False

        return True

    @staticmethod
    def _parse_version(stem: str) -> tuple[str, int | None]:
        match = RE_VERSION.search(stem)
        if not match:
            return stem, None
        base = stem[: match.start()] + stem[match.end() :]
        return base, int(match.group(2))

    def _max_version_for_base(self, fs_model, parent_index, base: str, ext: str) -> int:
        max_version = -1
        for row in range(fs_model.rowCount(parent_index)):
            sibling_index = fs_model.index(row, 0, parent_index)
            if fs_model.isDir(sibling_index):
                continue
            sibling_stem, sibling_ext = os.path.splitext(fs_model.fileName(sibling_index))
            if sibling_ext != ext:
                continue
            sibling_base, sibling_version = self._parse_version(sibling_stem)
            if sibling_base == base and sibling_version is not None:
                max_version = max(max_version, sibling_version)
        return max_version
