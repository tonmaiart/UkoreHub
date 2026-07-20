from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRect, QRectF, Qt, Signal
from PySide6.QtGui import QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from interface.shared.widget_helpers import show_exclusive, wrap_scrollable
from plugins.studio.UkoreShot.core import comment_store, video_naming, video_path_store
from plugins.studio.UkoreShot.interface.edit_video_dialog import EditVideoDialog
from plugins.studio.UkoreShot.interface.filter_sidebar import FilterSidebar
from plugins.studio.UkoreShot.interface.flow_layout import FlowLayout
from plugins.studio.UkoreShot.interface.player_widget import PlayerWidget
from plugins.studio.UkoreShot.interface.thumbnail_loader import ThumbnailLoader

_VIDEO_EXTENSIONS = {".mov", ".mp4", ".avi"}
_UNKNOWN = "Unknown"
# Must match core/theme.py's QFrame#videoCard border-radius (same reasoning
# as interface/login/repo_picker.py's CARD_CORNER_RADIUS) so the painted
# thumbnail's clip path lines up with the QSS-drawn card border.
_CARD_CORNER_RADIUS = 6.0

# Two view-mode presets (view_small_button/view_large_button, added
# 2026-07-20) — _VideoCard used to hard-code these as module constants;
# now takes them as constructor args so switching the toggle can rebuild
# the grid at a different size.
_CARD_SIZES = {
    "small": {"card_width": 110, "thumbnail_height": 52},
    "large": {"card_width": 170, "thumbnail_height": 84},
}
_DEFAULT_CARD_SIZE = "large"

_SORT_NAME_ASC = "name_asc"
_SORT_NAME_DESC = "name_desc"
_SORT_OLDEST = "oldest"
_SORT_NEWEST = "newest"
_DEFAULT_SORT = _SORT_NEWEST

# video_naming.parse_video_filename's dict keys, in filter_sidebar.py's
# category order — used to build FilterSidebar.set_available_values'
# input and to test a parsed video against the sidebar's selections in
# _video_matches_filters. "commenter" isn't one of parse_video_filename's
# keys (see comment_store.list_commenters instead), so it's handled
# separately in both places.
_NAMING_FILTER_FIELDS = ["sequence", "shot_code", "variation", "index", "version"]


def _format_filter_value(field: str, parsed) -> str:
    """The filter sidebar shows index/version the same zero-padded way
    they actually appear in the filename (e.g. "003", "v001") rather than
    plain ints — this formatting must stay identical between
    _collect_filter_values (building the list of choices) and
    _video_matches_filters (matching a selection against it), since a
    selection is compared by exact string."""
    if parsed is None:
        return _UNKNOWN
    value = parsed[field]
    if field == "index":
        return "{:03d}".format(value)
    if field == "version":
        return "v{:03d}".format(value)
    return str(value)


class _VideoCard(QFrame):
    """One clickable card per video, painted the same fill-cropped-
    thumbnail way interface/login/repo_picker.py's _RepoCard does (reusing
    core/theme.py's card idiom as QFrame#videoCard) — replaces a plain
    QListWidget IconMode list, which rendered badly (overlapping
    thumbnails, cut-off text) for anything beyond a small square icon.
    Unlike _RepoCard the thumbnail only fills a fixed-height strip at the
    top, with the video's relative path underneath as normal child labels,
    so paintEvent draws the QSS background/border first and only overlays
    the thumbnail on top of that top strip — no transparent-background
    trick needed."""

    clicked = Signal()

    def __init__(self, video_path: Path, *, video_root: Path, card_width: int, thumbnail_height: int, parent=None):
        super().__init__(parent)
        self.video_path = video_path
        self.setObjectName("videoCard")
        self.setFrameShape(QFrame.StyledPanel)
        self.setCursor(Qt.PointingHandCursor)
        self._pixmap: QPixmap | None = None
        self._thumbnail_height = thumbnail_height

        self.setFixedWidth(card_width)

        relative = video_path.relative_to(video_root)
        name_label = QLabel(relative.name)
        name_label.setWordWrap(True)
        name_label.setProperty("cardTitle", True)

        folder = str(relative.parent)
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(8, 6, 8, 6)
        text_layout.setSpacing(2)
        text_layout.addWidget(name_label)
        if folder != ".":
            folder_label = QLabel(folder)
            folder_label.setProperty("secondary", True)
            folder_label.setWordWrap(True)
            text_layout.addWidget(folder_label)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addSpacing(self._thumbnail_height)
        layout.addLayout(text_layout)

    def set_thumbnail(self, pixmap: QPixmap) -> None:
        self._pixmap = pixmap
        self.update()

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if self._pixmap is None:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        # Clip against the whole card's rounded rect (not just the
        # thumbnail strip) so the top two corners come out rounded to match
        # the card, while the strip's bottom edge — well below the corner
        # radius — stays a plain straight line against the text area.
        clip_path = QPainterPath()
        clip_path.addRoundedRect(QRectF(self.rect()), _CARD_CORNER_RADIUS, _CARD_CORNER_RADIUS)
        painter.setClipPath(clip_path)
        thumb_rect = QRect(0, 0, self.width(), self._thumbnail_height)
        scaled = self._pixmap.scaled(thumb_rect.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        x = max(0, (scaled.width() - thumb_rect.width()) // 2)
        y = max(0, (scaled.height() - thumb_rect.height()) // 2)
        painter.drawPixmap(thumb_rect, scaled, QRect(x, y, thumb_rect.width(), thumb_rect.height()))
        painter.end()

    def mousePressEvent(self, event) -> None:
        self.clicked.emit()
        super().mousePressEvent(event)


class UkoreShotPage(QWidget):
    """The UkoreShot sidebar tab's page — a plain PlayerWidget (top half,
    playback only — drawing/comments live in EditVideoDialog, opened via
    "Edit Comment") plus a video library (bottom half) for picking which
    video to play. `content_layout` gives player_panel/library_panel
    equal `stretch=1` so the two always split available height 50/50,
    confirmed with the user 2026-07-20. The library itself is
    `filter_sidebar` (left, `FilterSidebar` — see that file) next to
    `library_content` (right: a sort/view controls row, then
    `cards_layout`, a `FlowLayout` wrapping grid of `_VideoCard`s that
    scrolls vertically). Implements the standard set_repo() page protocol
    (interface/main_window.py's _apply_to_current_page/_set_active_repo)
    so it re-resolves its video root whenever the active repo changes or
    this tab regains focus."""

    def __init__(self, parent=None, *, api):
        super().__init__(parent)
        self._api = api
        self._project_id: str | None = None
        self._repo_id: str | None = None
        self._video_root: Path | None = None
        self._all_videos: list[Path] = []
        self._parsed_by_video: dict[Path, dict | None] = {}
        self._commenters_by_video: dict[Path, set] = {}
        self._cards: dict[str, _VideoCard] = {}
        self._selected_card: _VideoCard | None = None
        self._sort_mode = _DEFAULT_SORT
        self._card_size_mode = _DEFAULT_CARD_SIZE
        self._thumbnail_loader = ThumbnailLoader(self)
        self._thumbnail_loader.thumbnailReady.connect(self._on_thumbnail_ready)

        self.empty_label = QLabel("Select a repo to see this information.")
        self.empty_label.setWordWrap(True)

        self.filter_sidebar = FilterSidebar()
        self.filter_sidebar.filtersChanged.connect(self._apply_filter)

        # Wrapping grid — FlowLayout packs cards left-to-right and wraps to
        # a new row once it runs out of width, so the strip grows downward
        # (vertical scroll) instead of sideways.
        self.cards_container = QWidget()
        self.cards_layout = FlowLayout(self.cards_container, spacing=8)
        self.cards_scroll = wrap_scrollable(self.cards_container)
        self.cards_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self._reload_videos)
        self.list_empty_label = QLabel("No videos found yet.")
        self.list_empty_label.setWordWrap(True)
        self.list_empty_label.setProperty("secondary", True)

        # Sort buttons (added 2026-07-20 per the user's own request) —
        # four plain checkable buttons in one exclusive QButtonGroup
        # rather than a QComboBox, matching "ปุ่ม sort by a-z, z-a,
        # oldest, newest" (explicitly "buttons") literally.
        self.sort_az_button = QPushButton("A-Z")
        self.sort_za_button = QPushButton("Z-A")
        self.sort_oldest_button = QPushButton("Oldest")
        self.sort_newest_button = QPushButton("Newest")
        self._sort_buttons = {
            _SORT_NAME_ASC: self.sort_az_button,
            _SORT_NAME_DESC: self.sort_za_button,
            _SORT_OLDEST: self.sort_oldest_button,
            _SORT_NEWEST: self.sort_newest_button,
        }
        self._sort_button_group = QButtonGroup(self)
        self._sort_button_group.setExclusive(True)
        for mode, button in self._sort_buttons.items():
            button.setCheckable(True)
            self._sort_button_group.addButton(button)
            button.clicked.connect(lambda checked, m=mode: self._set_sort_mode(m))
        self._sort_buttons[_DEFAULT_SORT].setChecked(True)

        # View-mode (thumbnail size) buttons — same exclusive-button-group
        # shape as the sort buttons above, per the user's own "ปุ่ม view
        # แบบต่างๆ เช่น thumbnail เล็ก, thumbnail ใหญ่" request.
        self.view_small_button = QPushButton("Small")
        self.view_large_button = QPushButton("Large")
        self._view_buttons = {"small": self.view_small_button, "large": self.view_large_button}
        self._view_button_group = QButtonGroup(self)
        self._view_button_group.setExclusive(True)
        for mode, button in self._view_buttons.items():
            button.setCheckable(True)
            self._view_button_group.addButton(button)
            button.clicked.connect(lambda checked, m=mode: self._set_card_size_mode(m))
        self._view_buttons[_DEFAULT_CARD_SIZE].setChecked(True)

        controls_row = QHBoxLayout()
        controls_row.addWidget(self.refresh_button)
        controls_row.addWidget(self.sort_az_button)
        controls_row.addWidget(self.sort_za_button)
        controls_row.addWidget(self.sort_oldest_button)
        controls_row.addWidget(self.sort_newest_button)
        controls_row.addStretch()
        controls_row.addWidget(self.view_small_button)
        controls_row.addWidget(self.view_large_button)

        library_content = QWidget()
        library_content_layout = QVBoxLayout(library_content)
        library_content_layout.setContentsMargins(0, 0, 0, 0)
        library_content_layout.addLayout(controls_row)
        library_content_layout.addWidget(self.cards_scroll, stretch=1)
        library_content_layout.addWidget(self.list_empty_label)

        library_panel = QWidget()
        library_layout = QHBoxLayout(library_panel)
        library_layout.setContentsMargins(0, 0, 0, 0)
        library_layout.addWidget(self.filter_sidebar)
        library_layout.addWidget(library_content, stretch=1)

        # Edit Comment now lives inside PlayerWidget itself (view mode) as
        # a square icon button next to Show/Hide Comments — moved out of
        # this page 2026-07-20 per the user's own request. PlayerWidget
        # tracks its own enabled state (load_video/clear_video) since it
        # already knows whether a video is loaded; this page just needs to
        # know *which* video to open when the signal fires, via
        # _selected_card (set in _select_card, always alongside
        # load_video).
        self.player_widget = PlayerWidget(show_edit_tools=False)
        self.player_widget.editCommentRequested.connect(self._on_edit_comment_clicked)

        player_panel = QWidget()
        player_layout = QVBoxLayout(player_panel)
        player_layout.setContentsMargins(0, 0, 0, 0)
        player_layout.addWidget(self.player_widget, stretch=1)

        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(player_panel, stretch=1)
        content_layout.addWidget(library_panel, stretch=1)

        layout = QVBoxLayout(self)
        layout.addWidget(self.empty_label)
        layout.addWidget(self.content_widget)

        self._update_empty_state()

    # -- standard page protocol -------------------------------------------

    def set_repo(self, project, repo, workspace_root: str) -> None:
        self._project_id = project.id if project is not None else None
        self._repo_id = repo.id if repo is not None else None
        self._reload_videos()

    # -- video list ---------------------------------------------------------

    def _reload_videos(self) -> None:
        self._clear_cards()
        self.player_widget.clear_video()
        self._video_root = None
        self._all_videos = []
        self._parsed_by_video = {}
        self._commenters_by_video = {}
        if self._project_id and self._repo_id:
            self._video_root = video_path_store.resolve_video_root(self._api, self._project_id, self._repo_id)
        self._update_empty_state()
        if self._video_root is None or not self._video_root.is_dir():
            self.filter_sidebar.set_available_values({})
            return

        # Recursive: a video flat-named under UkorePlayblast's 2026-07-20
        # naming convention lives directly in video_root, but an older
        # playblast from before that date may still sit nested under its
        # own <sequence>/<shot_code>/vNNN/ subfolder (left alone there per
        # the user's own decision — see UkorePlayblast/README.md) — both
        # need to show up here.
        self._all_videos = [
            p for p in self._video_root.rglob("*") if p.is_file() and p.suffix.lower() in _VIDEO_EXTENSIONS
        ]
        for video_path in self._all_videos:
            self._parsed_by_video[video_path] = video_naming.parse_video_filename(video_path)
            self._commenters_by_video[video_path] = comment_store.list_commenters(video_path)

        self.filter_sidebar.set_available_values(self._collect_filter_values())
        self._apply_filter()

    def _collect_filter_values(self) -> dict:
        """{"sequence": [...], "shot_code": [...], ..., "commenter": [...]}
        — every distinct value currently present across `_all_videos`, for
        `filter_sidebar.set_available_values`. A video that doesn't parse
        under the naming convention contributes "Unknown" to every
        video_naming-derived category instead of being left out."""
        values = {field: set() for field in _NAMING_FILTER_FIELDS}
        values["commenter"] = set()
        for video_path in self._all_videos:
            parsed = self._parsed_by_video.get(video_path)
            for field in _NAMING_FILTER_FIELDS:
                values[field].add(_format_filter_value(field, parsed))
            values["commenter"].update(self._commenters_by_video.get(video_path, set()))
        return {key: _sort_with_unknown_last(v) for key, v in values.items()}

    def _clear_cards(self) -> None:
        for card in self._cards.values():
            card.setParent(None)
            card.deleteLater()
        self._cards = {}
        self._selected_card = None

    def _video_matches_filters(self, video_path: Path) -> bool:
        search = self.filter_sidebar.search_text()
        if search and search not in str(video_path.relative_to(self._video_root)).lower():
            return False
        parsed = self._parsed_by_video.get(video_path)
        for field in _NAMING_FILTER_FIELDS:
            selected = self.filter_sidebar.selected_values(field)
            if not selected:
                continue
            if _format_filter_value(field, parsed) not in selected:
                return False
        selected_commenters = self.filter_sidebar.selected_values("commenter")
        if selected_commenters and not (self._commenters_by_video.get(video_path, set()) & selected_commenters):
            return False
        return True

    def _sort_videos(self, videos: list[Path]) -> list[Path]:
        if self._sort_mode == _SORT_NAME_ASC:
            return sorted(videos, key=lambda p: str(p.relative_to(self._video_root)).lower())
        if self._sort_mode == _SORT_NAME_DESC:
            return sorted(videos, key=lambda p: str(p.relative_to(self._video_root)).lower(), reverse=True)
        if self._sort_mode == _SORT_OLDEST:
            return sorted(videos, key=lambda p: p.stat().st_mtime)
        return sorted(videos, key=lambda p: p.stat().st_mtime, reverse=True)  # _SORT_NEWEST, the default

    def _set_sort_mode(self, mode: str) -> None:
        self._sort_mode = mode
        self._apply_filter()

    def _set_card_size_mode(self, mode: str) -> None:
        self._card_size_mode = mode
        self._apply_filter()

    def _apply_filter(self) -> None:
        self._clear_cards()
        if self._video_root is None:
            return
        videos = self._sort_videos([p for p in self._all_videos if self._video_matches_filters(p)])
        size = _CARD_SIZES[self._card_size_mode]
        for video_path in videos:
            card = _VideoCard(video_path, video_root=self._video_root, parent=self.cards_container, **size)
            card.clicked.connect(lambda c=card: self._select_card(c))
            self.cards_layout.addWidget(card)
            self._cards[str(video_path)] = card
            self._thumbnail_loader.request(video_path)
        self.list_empty_label.setVisible(not videos)
        self.cards_scroll.setVisible(bool(videos))

    def _on_thumbnail_ready(self, video_path_str: str, pixmap: QPixmap) -> None:
        card = self._cards.get(video_path_str)
        if card is not None:
            card.set_thumbnail(pixmap)

    def _update_empty_state(self) -> None:
        if not self._project_id or not self._repo_id:
            self.empty_label.setText("Select a repo to see this information.")
            show_exclusive(self.empty_label, self.content_widget)
            return
        if self._video_root is None:
            self.empty_label.setText(
                "No video library configured for this repo yet — set one in Repository Setting > UkoreShot."
            )
            show_exclusive(self.empty_label, self.content_widget)
            return
        show_exclusive(self.content_widget, self.empty_label)

    def _select_card(self, card: _VideoCard) -> None:
        if self._selected_card is not None:
            self._selected_card.set_selected(False)
        card.set_selected(True)
        self._selected_card = card
        self.player_widget.load_video(card.video_path)

    def _on_edit_comment_clicked(self) -> None:
        if self._selected_card is None:
            return
        EditVideoDialog(self._selected_card.video_path, self).exec()


def _sort_with_unknown_last(values: set) -> list[str]:
    return sorted(values - {_UNKNOWN}) + ([_UNKNOWN] if _UNKNOWN in values else [])
