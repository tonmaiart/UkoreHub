from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRect, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from core.store import MetadataStore
from core.theme import DEFAULT_THEME_NAME, get_theme
from interface.shared.widget_helpers import wrap_scrollable

CARD_MIN_HEIGHT = 90
# Must match core/theme.py's QFrame#repoCard border-radius so the painted
# thumbnail's clip path lines up with the QSS-drawn border.
CARD_CORNER_RADIUS = 6.0
_ACCENT_COLOR = QColor(get_theme(DEFAULT_THEME_NAME).accent)


class _RepoCard(QFrame):
    """One clickable card per repo — click selects it (exclusive among all
    cards in the dialog, see RepoPickerDialog._select_card); the dialog is
    only ever accepted via its own OK button, not by clicking a card, so a
    stray double-click can't jump into the wrong repo. Shows only
    "Project / Repo" and status — this picker's whole point is a fast way
    to jump to a repo, not a status/admin view (see
    interface/shared/project_repo_tree.py's QTreeWidget for that, used by
    Settings' Project Status / Project Data Editor tabs).

    When the repo has a thumbnail, it's painted fill-cropped as the card's
    own background with a dark dimming overlay (paintEvent) so the name/
    status text stay legible over an arbitrary studio image — core/theme.py
    gives QFrame#repoCard[hasThumbnail="true"] a transparent background so
    this custom painting isn't erased by the card's normal solid-color
    background rule."""

    clicked = Signal()

    def __init__(
        self,
        *,
        project_id: str,
        repo_id: str,
        project_name: str,
        repo_name: str,
        status: str,
        thumbnail_path: Path | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("repoCard")
        self.setFrameShape(QFrame.StyledPanel)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(CARD_MIN_HEIGHT)
        self.project_id = project_id
        self.repo_id = repo_id

        self._pixmap = QPixmap(str(thumbnail_path)) if thumbnail_path and thumbnail_path.exists() else None
        if self._pixmap is not None and self._pixmap.isNull():
            self._pixmap = None
        self.setProperty("hasThumbnail", self._pixmap is not None)

        name_label = QLabel(f"<b>{project_name} / {repo_name}</b>")
        name_label.setWordWrap(True)
        status_label = QLabel(status)
        status_label.setProperty("secondary", True)
        status_label.setProperty("status", status)
        status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Name and status share one row, status pinned to the right — more
        # compact than stacking them on separate lines.
        top_row = QHBoxLayout()
        top_row.addWidget(name_label, stretch=1)
        top_row.addWidget(status_label)

        layout = QVBoxLayout(self)
        layout.addLayout(top_row)
        layout.addStretch()

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)

    def paintEvent(self, event) -> None:
        if self._pixmap is not None:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            clip_path = QPainterPath()
            clip_path.addRoundedRect(QRectF(self.rect()), CARD_CORNER_RADIUS, CARD_CORNER_RADIUS)
            painter.setClipPath(clip_path)
            scaled = self._pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            x = max(0, (scaled.width() - self.width()) // 2)
            y = max(0, (scaled.height() - self.height()) // 2)
            painter.drawPixmap(self.rect(), scaled, QRect(x, y, self.width(), self.height()))
            # Dim the image down so the name/status text on top stays readable.
            painter.fillPath(clip_path, QColor(0, 0, 0, 140))
            painter.end()
        super().paintEvent(event)
        if self._pixmap is not None and self.property("selected"):
            # Drawn by hand rather than relying on QSS's border on a
            # transparent-background QFrame — that combination doesn't
            # reliably paint the border here, so the selection ring would
            # silently vanish on thumbnail cards otherwise.
            border_painter = QPainter(self)
            border_painter.setRenderHint(QPainter.Antialiasing)
            border_painter.setPen(QPen(_ACCENT_COLOR, 2))
            border_painter.setBrush(Qt.NoBrush)
            border_painter.drawRoundedRect(
                QRectF(self.rect()).adjusted(1, 1, -1, -1), CARD_CORNER_RADIUS, CARD_CORNER_RADIUS
            )
            border_painter.end()

    def mousePressEvent(self, event) -> None:
        self.clicked.emit()
        super().mousePressEvent(event)


class RepoPickerDialog(QDialog):
    def __init__(
        self,
        parent=None,
        *,
        store: MetadataStore,
        selected_project_id: str | None = None,
        selected_repo_id: str | None = None,
        cancel_button_text: str = "Cancel",
        allowed_pairs: set[tuple[str, str]] | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Select Repo")
        self.resize(420, 480)

        self._selected_card: _RepoCard | None = None

        # Must exist before any card can be selected — _select_card() reads
        # self.buttons to enable/disable OK, and a card can be pre-selected
        # (below) while the cards list is still being built.
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Cancel).setText(cancel_button_text)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        cards_container = QWidget()
        cards_layout = QVBoxLayout(cards_container)
        for project in store.list_projects():
            for repo in project.repos:
                # allowed_pairs=None means "no restriction" (every repo
                # shown) — used by callers that only want the picker
                # narrowed to a specific set of (project_id, repo_id) pairs,
                # e.g. plugins/studio/explorer's "Add Pinned Repo..." only
                # offering pipeline_architect's declared inputs/outputs.
                if allowed_pairs is not None and (project.id, repo.id) not in allowed_pairs:
                    continue
                card = _RepoCard(
                    project_id=project.id,
                    repo_id=repo.id,
                    project_name=project.name,
                    repo_name=repo.name,
                    status=repo.status,
                    thumbnail_path=store.resolve_thumbnail_path(repo),
                )
                card.clicked.connect(lambda c=card: self._select_card(c))
                cards_layout.addWidget(card)
                if project.id == selected_project_id and repo.id == selected_repo_id:
                    self._select_card(card)
        cards_layout.addStretch()

        layout = QVBoxLayout(self)
        layout.addWidget(wrap_scrollable(cards_container))
        layout.addWidget(self.buttons)

        self._update_ok_enabled()

    def _select_card(self, card: _RepoCard) -> None:
        if self._selected_card is not None:
            self._selected_card.set_selected(False)
        card.set_selected(True)
        self._selected_card = card
        self._update_ok_enabled()

    def _update_ok_enabled(self) -> None:
        self.buttons.button(QDialogButtonBox.Ok).setEnabled(self._selected_card is not None)

    def selected_project_id(self) -> str | None:
        return self._selected_card.project_id if self._selected_card else None

    def selected_repo_id(self) -> str | None:
        return self._selected_card.repo_id if self._selected_card else None
