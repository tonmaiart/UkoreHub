from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from interface.shared.widget_helpers import wrap_scrollable

_WIDTH = 170
_SECTION_LIST_HEIGHT = 90

# (category key, display label) — category keys match the dict keys
# video_library_page.py's _collect_filter_values/_video_matches_filters
# use, and video_naming.parse_video_filename's own field names for the
# first five ("sequence" maps to parse_video_filename's "sequence" key,
# etc.) — the last, "commenter", isn't a video_naming field at all, see
# comment_store.list_commenters.
_CATEGORIES = [
    ("sequence", "Sequence"),
    ("shot_code", "Shot Name"),
    ("variation", "Variation"),
    ("index", "Index"),
    ("version", "Version"),
    ("commenter", "Commented By"),
]


class FilterSidebar(QWidget):
    """Left-hand library filter panel — one multi-select list per category
    (sequence/shot name/variation/index/version/commenter) plus a
    free-text search box, added 2026-07-20 per the user's own request.
    Selecting multiple values within one category is OR ("this sequence
    OR that one"); selecting across different categories is AND ("this
    sequence AND this variation") — video_library_page.py's
    `_video_matches_filters` implements that combination, this widget
    just exposes the raw selection state (`selected_values`/
    `search_text`) plus a single `filtersChanged` signal so the page
    doesn't need to wire up six separate list widgets' selection-changed
    signals itself. A video that doesn't parse under UkorePlayblast's
    naming convention (a pre-2026-07-20 shot/version-subfoldered
    playblast, left alone per the user's own decision — see that
    plugin's README) shows up as "Unknown" in every video_naming-derived
    category rather than being excluded from filtering entirely."""

    filtersChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(_WIDTH)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search...")
        self.search_edit.textChanged.connect(self.filtersChanged)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)

        self._lists: dict[str, QListWidget] = {}
        for key, label in _CATEGORIES:
            section_label = QLabel(label)
            section_label.setProperty("secondary", True)
            list_widget = QListWidget()
            list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
            list_widget.setFixedHeight(_SECTION_LIST_HEIGHT)
            list_widget.itemSelectionChanged.connect(self.filtersChanged)
            content_layout.addWidget(section_label)
            content_layout.addWidget(list_widget)
            self._lists[key] = list_widget

        scroll = wrap_scrollable(content)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.search_edit)
        layout.addWidget(scroll, stretch=1)

    def set_available_values(self, values_by_category: dict) -> None:
        """Rebuilds every category's list items from scratch (called from
        video_library_page.py's `_reload_videos` after every rescan) —
        preserves selection for values that still exist, so re-scanning
        after Refresh doesn't silently clear an active filter, but drops
        selection for a value that's disappeared (e.g. the last video
        with that variation was deleted)."""
        for key, list_widget in self._lists.items():
            values = values_by_category.get(key, [])
            previously_selected = {item.text() for item in list_widget.selectedItems()}
            list_widget.blockSignals(True)
            list_widget.clear()
            for value in values:
                item = QListWidgetItem(value)
                list_widget.addItem(item)
                if value in previously_selected:
                    item.setSelected(True)
            list_widget.blockSignals(False)

    def search_text(self) -> str:
        return self.search_edit.text().strip().lower()

    def selected_values(self, category: str) -> set:
        list_widget = self._lists.get(category)
        if list_widget is None:
            return set()
        return {item.text() for item in list_widget.selectedItems()}
