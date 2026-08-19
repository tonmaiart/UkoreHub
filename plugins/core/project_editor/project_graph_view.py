from __future__ import annotations

import math
from datetime import datetime
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QEventLoop, QLineF, QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygonF,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsScene,
    QGraphicsSceneContextMenuEvent,
    QGraphicsSceneHoverEvent,
    QGraphicsSceneMouseEvent,
    QGraphicsView,
    QLabel,
    QMenu,
    QMessageBox,
    QProgressDialog,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from plugin_api import (
    LOCAL_REPOSITORY,
    ConflictError,
    GitService,
    LocalConfigStore,
    MetadataStore,
    NotFoundError,
    Project,
    Repo,
    UkoreHubError,
    confirm_action,
    pick_image_file,
    save_image_asset,
)
from plugins.core.project_editor.dialogs import AssignCategoryDialog, RepoDialog
from plugins.core.project_editor.pipeline_store import PipelineStore
from plugins.core.project_editor.required_repo_clone_worker import RequiredRepoCloneWorker

NODE_WIDTH = 160.0
NODE_HEIGHT = 110.0
NODE_CORNER_RADIUS = 6.0
NODE_H_SPACING = 40.0
_ARROW_SIZE = 8.0
# Category-box vertical stack (_layout_nodes/CategoryBoxItem, replaced the
# old pipeline-derived Sugiyama-style layered layout 2026-08-19, then
# switched from an auto-wrapping grid of boxes to a single top-to-bottom
# column per the user's own request, same day). A repo's box is picked by
# a deliberate "Assign to Category..." choice (assign_repo_category), not
# inferred from pipeline edges, which are still drawn but no longer affect
# node position. Box order (top to bottom) is PipelineStore.get_categories'
# own stored list order, user-editable via a box's own right-click "Move
# Category Up"/"Move Category Down" (ProjectGraphView.move_category).
_CATEGORY_BOX_PADDING = 20.0
_CATEGORY_BOX_HEADER_HEIGHT = 32.0
_CATEGORY_BOX_V_SPACING = 60.0
_NODE_V_SPACING_IN_BOX = 30.0
_CATEGORY_BOX_Z_VALUE = -1
_CATEGORY_BOX_CORNER_RADIUS = 10.0
_CATEGORY_BOX_FILL_ALPHA = 70
_CATEGORY_BOX_BORDER_ALPHA = 120
_UNCATEGORIZED_TITLE = "Uncategorized"
_EDGE_WIDTH = 2
_EDGE_HIGHLIGHT_WIDTH = 3
_EDGE_HIGHLIGHT_COLOR_HEX = "#ffcc00"
# Nodes paint at the scene's default zValue (0). Edges used to sit BELOW
# that (-1) so they'd tuck cleanly under a node's own connection point —
# but with several nodes per level and the (now-removed) 4-side elbow
# routing, a rerouted edge legitimately had to pass near/behind unrelated
# nodes, and at -1 those nodes hid it completely. Still true with plain
# straight lines (2026-07-19) whenever one passes near an unrelated node
# on its way between two others, so edges stay painted ABOVE nodes instead
# (never hidden), with a highlighted edge one level above that again so it
# reads as "on top of everything" while a node is selected.
_EDGE_Z_VALUE = 1
_EDGE_HIGHLIGHT_Z_VALUE = 2
# Radial gradient background (gray center fading to black edges), painted
# in drawBackground below instead of a flat setBackgroundBrush color —
# darker than the app-wide theme background (interface/theme.py's "grey_dark"
# background="#1e1f22", inherited by default since this view sets no
# stylesheet of its own) so the graph reads as its own recessed canvas
# rather than blending into the surrounding chrome. Centered on the
# viewport (not the scene) so panning doesn't drag the glow off-center.
_GRAPH_BACKGROUND_CENTER_HEX = "#414141"
_GRAPH_BACKGROUND_EDGE_HEX = "#080808"
# Faint white grid drawn on top of the radial background, in scene
# coordinates so it scrolls/pans with the node content like graph paper.
_GRID_SPACING = 40
_GRID_LINE_ALPHA = 8

# Clone-status corner icon, drawn top-right on every node.
_CLONE_STATUS_ICON_SIZE = 16
_CLONE_STATUS_ICON_MARGIN = 6
_clone_status_icon_cache: dict[bool, QPixmap] = {}

# Bottom-right HUD (active project/repo, sync state, pipeline connections).
_OVERLAY_MARGIN = 12


def _theme_colors():
    from plugin_api import DEFAULT_THEME_NAME, get_theme

    return get_theme(DEFAULT_THEME_NAME)


def _format_last_synced(last_synced: str | None) -> str:
    """Repo.last_synced is stored as a UTC isoformat string
    (core/store.py's _utc_now_iso) — reformatted here to the machine's own
    local time in a plain day-month-year + time form for the HUD, instead
    of showing the raw ISO string. Falls back to the raw string if it
    somehow doesn't parse, rather than hiding a real (if oddly formatted)
    value."""
    if not last_synced:
        return "Never"
    try:
        parsed = datetime.fromisoformat(last_synced)
    except ValueError:
        return last_synced
    return parsed.astimezone().strftime("%d %b %Y, %H:%M")


def _clone_status_icon(is_cloned: bool) -> QPixmap:
    """Cached, pre-scaled QPixmap for the clone/not-cloned corner badge —
    built once per status value from QApplication's own standardIcon
    (QGraphicsItem.paint() has no widget/style() of its own to draw from),
    not once per node per paint() call."""
    if is_cloned not in _clone_status_icon_cache:
        standard_icon = QStyle.SP_DialogYesButton if is_cloned else QStyle.SP_DialogNoButton
        icon = QApplication.style().standardIcon(standard_icon)
        _clone_status_icon_cache[is_cloned] = icon.pixmap(_CLONE_STATUS_ICON_SIZE, _CLONE_STATUS_ICON_SIZE)
    return _clone_status_icon_cache[is_cloned]


class RepoNodeItem(QGraphicsItem):
    """One node = one repo. Paints the repo's thumbnail fill-cropped plus
    a name label, a hover highlight, and an accent border while this is the
    active repo. A single left-click requests an active-repo switch (see
    mousePressEvent); right-click opens a context menu for the repo/
    pipeline/settings actions the old CRUD tree used to offer. All actual
    store mutations are delegated back to the owning ProjectGraphView
    rather than duplicated per node."""

    def __init__(self, *, view: "ProjectGraphView", project_id: str, repo: Repo, thumbnail_path: Path | None):
        super().__init__()
        self._view = view
        self.project_id = project_id
        self.repo_id = repo.id
        self.repo_name = repo.name
        self.is_active = False
        self.is_cloned = view._is_repo_cloned(project_id, repo.id)
        self._is_hovered = False
        self._pixmap: QPixmap | None = None
        self.set_thumbnail(thumbnail_path)
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.PointingHandCursor)

    def set_thumbnail(self, thumbnail_path: Path | None) -> None:
        pixmap = QPixmap(str(thumbnail_path)) if thumbnail_path and thumbnail_path.exists() else None
        if pixmap is not None and pixmap.isNull():
            pixmap = None
        self._pixmap = pixmap
        self.update()

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, NODE_WIDTH, NODE_HEIGHT)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        colors = _theme_colors()
        rect = self.boundingRect()
        clip_path = QPainterPath()
        clip_path.addRoundedRect(rect, NODE_CORNER_RADIUS, NODE_CORNER_RADIUS)

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.save()
        painter.setClipPath(clip_path)
        if self._pixmap is not None:
            scaled = self._pixmap.scaled(rect.size().toSize(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            x = max(0, (scaled.width() - rect.width()) / 2)
            y = max(0, (scaled.height() - rect.height()) / 2)
            painter.drawPixmap(rect, scaled, QRectF(x, y, rect.width(), rect.height()))
            painter.fillPath(clip_path, QColor(0, 0, 0, 140))
        else:
            painter.fillPath(clip_path, QBrush(QColor(colors.surface_alt)))
        if self._is_hovered:
            # Subtle lightening wash on top of the thumbnail/background —
            # the border below carries most of the hover affordance, this
            # just keeps the whole card reading as "interactive" under the
            # cursor, on top of the PointingHandCursor already set.
            painter.fillPath(clip_path, QColor(255, 255, 255, 25))
        painter.restore()

        clone_icon = _clone_status_icon(self.is_cloned)
        icon_rect = QRectF(
            rect.right() - clone_icon.width() - _CLONE_STATUS_ICON_MARGIN,
            rect.top() + _CLONE_STATUS_ICON_MARGIN,
            clone_icon.width(),
            clone_icon.height(),
        )
        painter.drawPixmap(icon_rect.topLeft(), clone_icon)

        painter.save()
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor("#ffffff") if self._pixmap is not None else QColor(colors.text_primary))
        text_rect = QRectF(rect.left() + 8, rect.bottom() - 30, rect.width() - 16, 24)
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter | Qt.TextWordWrap, self.repo_name)
        painter.restore()

        if self.is_active:
            # Same yellow as PipelineEdgeItem's highlighted-edge color
            # (_EDGE_HIGHLIGHT_COLOR_HEX) rather than the theme's plain
            # accent color, so the active node visually matches the
            # highlighted arrows pointing at/from it.
            border_color, border_width = QColor(_EDGE_HIGHLIGHT_COLOR_HEX), 3
        elif self._is_hovered:
            border_color, border_width = QColor(colors.accent_hover), 2
        else:
            border_color, border_width = QColor(colors.border), 1
        painter.setPen(QPen(border_color, border_width))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), NODE_CORNER_RADIUS, NODE_CORNER_RADIUS)

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self._is_hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self._is_hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(event)
        if event.button() != Qt.LeftButton:
            return
        # Deferred via QTimer.singleShot rather than called directly: the
        # active-repo-switch callback can end up reloading this very scene
        # (ProjectGraphView.load_project's scene.clear(), e.g. via
        # ProjectEditorPage.set_repo() reacting to the switch), which
        # destroys this RepoNodeItem's C++ object — doing that synchronously
        # while still inside this item's own mousePressEvent crashes
        # ("Internal C++ object already deleted") the moment this handler
        # resumes. Deferring to the next event-loop tick lets this call
        # finish first. Capture plain values, not `self`, since `self` may
        # not survive until the timer fires.
        view = self._view
        project_id = self.project_id
        repo_id = self.repo_id
        QTimer.singleShot(0, lambda: view.request_active_repo(project_id, repo_id))

    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent) -> None:
        menu = QMenu()
        settings_action = menu.addAction("Repository Setting...")
        category_action = menu.addAction("Assign to Category...")
        menu.addSeparator()
        rename_action = menu.addAction("Rename Repo...")
        thumbnail_action = menu.addAction("Change Thumbnail...")
        menu.addSeparator()
        delete_action = menu.addAction("Delete Repo")

        chosen = menu.exec(event.screenPos())
        # Same deferral as mousePressEvent above for every action that can
        # end up reloading (and thereby destroying) this very item via
        # ProjectGraphView.load_project() — none of those may run
        # synchronously from within this item's own event handler.
        # Repository Setting only opens a dialog (never touches the scene),
        # so it's safe to call directly.
        view = self._view
        project_id = self.project_id
        repo_id = self.repo_id
        if chosen is settings_action:
            view.open_repo_settings()
        elif chosen is category_action:
            QTimer.singleShot(0, lambda: view.assign_repo_category(project_id, repo_id))
        elif chosen is rename_action:
            QTimer.singleShot(0, lambda: view.rename_repo(project_id, repo_id))
        elif chosen is thumbnail_action:
            QTimer.singleShot(0, lambda: view.change_repo_thumbnail(project_id, repo_id))
        elif chosen is delete_action:
            QTimer.singleShot(0, lambda: view.delete_repo(project_id, repo_id))


def _border_point(center: QPointF, toward: QPointF) -> QPointF:
    """Where a straight line from `center` toward `toward` exits this
    node's own rectangle border (NODE_WIDTH x NODE_HEIGHT, centered on
    `center`) — used by PipelineEdgeItem.update_position to start/end a
    plain straight line exactly at each node's edge, always pointed
    directly at the other node's center, rather than a fixed top/bottom/
    left/right anchor point picked by which side "faces" the other node.
    Simplified 2026-07-19: the old elbow-routed, side-picking version
    (removed) looked tidy for a simple top-down layout but produced messy
    overlapping bends once several connections fan out at different
    angles — see the user's own screenshot of the tangle it produced."""
    dx = toward.x() - center.x()
    dy = toward.y() - center.y()
    if dx == 0 and dy == 0:
        return QPointF(center)
    half_width = NODE_WIDTH / 2
    half_height = NODE_HEIGHT / 2
    scales = []
    if dx != 0:
        scales.append(half_width / abs(dx))
    if dy != 0:
        scales.append(half_height / abs(dy))
    t = min(scales)
    return QPointF(center.x() + dx * t, center.y() + dy * t)


class PipelineEdgeItem(QGraphicsPathItem):
    """One directed pipeline dependency between two repo nodes in the same
    project, with a hand-drawn arrowhead pointing at whichever repo the
    connection's `direction` says it should (`__init__`'s `source`/`target`
    args are the *drawing* roles — arrowhead always at `target` — not the
    pipeline data's own connecting-repo/target-repo roles).
    ProjectGraphView.load_project picks which way round to pass them per
    edge based on RepoRef.direction (added 2026-07-19): `"input"` (the
    default) passes the connected-to repo as `source` and the connecting
    repo as `target`, so the arrow points at the connecting repo;
    `"output"` passes them the other way round, pointing the arrow at the
    connected-to repo instead. See ProjectGraphView.load_project for how
    the edge set is derived from PipelineStore (inputs and outputs are
    independently curated, so both are read and de-duplicated rather than
    assuming one mirrors the other). Node position no longer depends on
    this edge set at all as of 2026-08-19 — see _layout_nodes.

    A plain straight line from source's border to target's border, each
    end pointed directly at the *other* node's center (see _border_point)
    — simplified 2026-07-19 from an earlier version that picked a fixed
    top/bottom/left/right anchor per node and routed a rounded elbow
    between them, which produced messy overlapping bends once a node had
    several connections at different angles. No routing/bending at all
    now, just the two border-intersection points."""

    def __init__(self, source: RepoNodeItem, target: RepoNodeItem):
        super().__init__()
        self._source = source
        self._target = target
        colors = _theme_colors()
        self._default_color = QColor(colors.accent)
        self._highlighted = False
        self.setPen(QPen(self._default_color, _EDGE_WIDTH))
        self.setZValue(_EDGE_Z_VALUE)
        self._arrow_from = QPointF()
        self._arrow_to = QPointF()
        self.update_position()

    @property
    def source_repo_id(self) -> str:
        return self._source.repo_id

    @property
    def target_repo_id(self) -> str:
        return self._target.repo_id

    def set_highlighted(self, highlighted: bool) -> None:
        if highlighted == self._highlighted:
            return
        self._highlighted = highlighted
        color = QColor(_EDGE_HIGHLIGHT_COLOR_HEX) if highlighted else self._default_color
        width = _EDGE_HIGHLIGHT_WIDTH if highlighted else _EDGE_WIDTH
        self.setPen(QPen(color, width))
        self.setZValue(_EDGE_HIGHLIGHT_Z_VALUE if highlighted else _EDGE_Z_VALUE)
        self.update()

    def update_position(self) -> None:
        source_pos = self._source.pos()
        target_pos = self._target.pos()
        source_center = source_pos + QPointF(NODE_WIDTH / 2, NODE_HEIGHT / 2)
        target_center = target_pos + QPointF(NODE_WIDTH / 2, NODE_HEIGHT / 2)

        start = _border_point(source_center, target_center)
        end = _border_point(target_center, source_center)

        path = QPainterPath(start)
        path.lineTo(end)

        self._arrow_from = start
        self._arrow_to = end
        self.setPath(path)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        super().paint(painter, option, widget)
        line = QLineF(self._arrow_from, self._arrow_to)
        if line.length() == 0:
            return
        angle = math.atan2(-(line.dy()), line.dx())
        arrow_p1 = line.p2() - QPointF(
            math.cos(angle - math.pi / 6) * _ARROW_SIZE, -math.sin(angle - math.pi / 6) * _ARROW_SIZE
        )
        arrow_p2 = line.p2() - QPointF(
            math.cos(angle + math.pi / 6) * _ARROW_SIZE, -math.sin(angle + math.pi / 6) * _ARROW_SIZE
        )
        painter.setBrush(QBrush(self.pen().color()))
        painter.drawPolygon(QPolygonF([line.p2(), arrow_p1, arrow_p2]))


class CategoryBoxItem(QGraphicsItem):
    """One rectangle per Category (plus a synthetic "Uncategorized" bucket
    for repos with no category_id) — added 2026-08-19 alongside
    ProjectGraphView._layout_nodes' category-box stack. Purely a
    background/title label: a RepoNodeItem placed "inside" one of these
    stays an independent scene item positioned in absolute scene
    coordinates that happens to fall within this rect, not an actual
    child of it — the same flat-scene-siblings relationship
    PipelineEdgeItem already has with the nodes it connects, so dragging
    or rebuilding the graph never needs to reparent anything. Painted at
    `_CATEGORY_BOX_Z_VALUE` (below RepoNodeItem's default zValue of 0) so
    every node visually floats on top of its own box.

    `category_id` is None for the synthetic Uncategorized bucket, which
    isn't a real PipelineStore Category and so can't be reordered — its
    right-click menu is empty (no move actions) for every other box."""

    def __init__(self, width: float, height: float, title: str, *, view: "ProjectGraphView", category_id: str | None):
        super().__init__()
        self._width = width
        self._height = height
        self._title = title
        self._view = view
        self.category_id = category_id
        self.setZValue(_CATEGORY_BOX_Z_VALUE)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._width, self._height)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        colors = _theme_colors()
        rect = self.boundingRect()
        painter.setRenderHint(QPainter.Antialiasing)

        # Plain black rather than colors.surface_alt (a light theme gray) —
        # over the graph's own dark radial-gradient background
        # (_GRAPH_BACKGROUND_CENTER_HEX/_EDGE_HEX), a black fill reads as a
        # darker recessed panel instead of a lighter highlighted one.
        fill = QColor(0, 0, 0)
        fill.setAlpha(_CATEGORY_BOX_FILL_ALPHA)
        border = QColor(colors.border)
        border.setAlpha(_CATEGORY_BOX_BORDER_ALPHA)
        painter.setBrush(QBrush(fill))
        painter.setPen(QPen(border, 1))
        painter.drawRoundedRect(rect, _CATEGORY_BOX_CORNER_RADIUS, _CATEGORY_BOX_CORNER_RADIUS)

        painter.save()
        font = painter.font()
        font.setBold(True)
        font.setPixelSize(13)
        painter.setFont(font)
        painter.setPen(QColor(colors.text_primary))
        header_rect = QRectF(rect.left() + 12, rect.top(), rect.width() - 24, _CATEGORY_BOX_HEADER_HEIGHT)
        painter.drawText(header_rect, Qt.AlignLeft | Qt.AlignVCenter, self._title)
        painter.restore()

    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent) -> None:
        if self.category_id is None:
            return  # synthetic Uncategorized bucket — nothing to reorder
        menu = QMenu()
        move_up_action = menu.addAction("Move Category Up")
        move_down_action = menu.addAction("Move Category Down")
        chosen = menu.exec(event.screenPos())
        # Same QTimer deferral as RepoNodeItem's own context menu actions —
        # move_category ends up reloading the scene (load_project's
        # scene.clear()), which would destroy this very item while its own
        # event handler is still on the call stack.
        view = self._view
        category_id = self.category_id
        if chosen is move_up_action:
            QTimer.singleShot(0, lambda: view.move_category(category_id, -1))
        elif chosen is move_down_action:
            QTimer.singleShot(0, lambda: view.move_category(category_id, 1))


class ProjectGraphView(QGraphicsView):
    """1 node = 1 repo, for whichever project is currently loaded, grouped
    into one box per Category plus a synthetic "Uncategorized" bucket,
    stacked top to bottom in one column (see _layout_nodes/CategoryBoxItem)
    — a repo's box is a deliberate per-node "Assign to Category..." choice
    (assign_repo_category/AssignCategoryDialog, added 2026-08-19),
    replacing the old pipeline-derived automatic layered layout entirely;
    the stack's own top-to-bottom order is user-editable too, via a box's
    own right-click "Move Category Up"/"Move Category Down"
    (move_category). Each edge's
    arrowhead points into the connecting repo by default ("input"
    direction) or out toward the target repo instead ("output" — a
    per-connection choice, RepoRef.direction, added 2026-07-19, see
    load_project) — direction only ever changes the arrowhead end, never
    which box a node lands in (pipeline edges no longer affect node
    position at all). A single left-click on a node requests an
    active-repo switch (see request_active_repo — the
    actual switch happens via the callback bound from plugin.py's _wire,
    not here; a repo that's never been cloned gets a one-time confirmation
    first). Pipeline inputs/outputs render as directed edges between nodes.
    "Add Repo" is a public method the top bar's button calls, not a button
    drawn inside the scene itself."""

    def __init__(
        self,
        parent=None,
        *,
        store: MetadataStore,
        local_config_store: LocalConfigStore,
        pipeline_store: PipelineStore,
        git_service: GitService,
    ):
        super().__init__(parent)
        self.store = store
        self.local_config_store = local_config_store
        self.pipeline_store = pipeline_store
        self.git_service = git_service

        self._set_active_repo_callback: Callable[[str, str], None] | None = None
        self._open_settings_tab_callback: Callable[[str], None] | None = None
        self._project_id: str | None = None
        self._nodes: dict[str, RepoNodeItem] = {}
        self._edges: list[PipelineEdgeItem] = []
        self._active_repo_id: str | None = None
        self._active_project: Project | None = None
        self._active_repo: Repo | None = None

        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        # No flat setBackgroundBrush color anymore — drawBackground below
        # paints the radial gradient + grid instead.

        # Bottom-right HUD — a plain child container positioned by hand in
        # resizeEvent/_position_overlay rather than a layout of its own, so
        # it floats over the QGraphicsView viewport, not inside the scene,
        # and never scrolls/zooms with the graph content. Two stacked
        # labels, both fully transparent (no boxed background at all as of
        # 2026-08-03, per the user's own request — this used to be a plain
        # rgba(0,0,0,150) panel) so the whole HUD reads as text floating
        # directly over the graph: the project name on its own, oversized,
        # and the info panel below it for the rest (Repo/Last Sync/Status/
        # Custom Paths).
        self._overlay_container = QWidget(self)
        self._overlay_container.setAttribute(Qt.WA_TransparentForMouseEvents)
        overlay_layout = QVBoxLayout(self._overlay_container)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.setSpacing(6)

        self._project_name_label = QLabel(self._overlay_container)
        self._project_name_label.setObjectName("projectGraphProjectName")
        self._project_name_label.setAlignment(Qt.AlignRight)
        self._project_name_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        name_font = QFont()
        name_font.setPixelSize(22)
        name_font.setWeight(QFont.Bold)
        self._project_name_label.setFont(name_font)
        name_palette = self._project_name_label.palette()
        name_palette.setColor(self._project_name_label.foregroundRole(), QColor("#ffffff"))
        self._project_name_label.setPalette(name_palette)
        overlay_layout.addWidget(self._project_name_label, alignment=Qt.AlignRight)

        self._overlay = QLabel(self._overlay_container)
        self._overlay.setObjectName("projectGraphOverlay")
        self._overlay.setTextFormat(Qt.RichText)
        self._overlay.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self._overlay.setAttribute(Qt.WA_TransparentForMouseEvents)
        overlay_font = QFont()
        overlay_font.setPixelSize(11)
        self._overlay.setFont(overlay_font)
        overlay_palette = self._overlay.palette()
        overlay_palette.setColor(self._overlay.foregroundRole(), QColor("#dcddde"))
        self._overlay.setPalette(overlay_palette)
        overlay_layout.addWidget(self._overlay, alignment=Qt.AlignRight)

        self._overlay_container.hide()

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        # Radial gradient centered on the viewport (not the scene) so
        # panning the graph never drags the glow off to one side — mapped
        # to scene coordinates just so fillRect(rect, ...) (rect is already
        # in scene coordinates, the area QGraphicsView is asking to redraw)
        # lines up correctly.
        viewport_center = self.mapToScene(self.viewport().rect().center())
        radius = math.hypot(self.viewport().width(), self.viewport().height()) / 2 or 1.0
        gradient = QRadialGradient(viewport_center, radius)
        gradient.setColorAt(0.0, QColor(_GRAPH_BACKGROUND_CENTER_HEX))
        gradient.setColorAt(1.0, QColor(_GRAPH_BACKGROUND_EDGE_HEX))
        painter.fillRect(rect, QBrush(gradient))

        # Grid lines in scene coordinates — scrolls with the node content
        # like graph paper, rather than staying fixed to the viewport the
        # way the gradient above does.
        painter.setPen(QPen(QColor(255, 255, 255, _GRID_LINE_ALPHA), 1))
        left = int(math.floor(rect.left() / _GRID_SPACING)) * _GRID_SPACING
        top = int(math.floor(rect.top() / _GRID_SPACING)) * _GRID_SPACING
        x = left
        while x < rect.right():
            painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
            x += _GRID_SPACING
        y = top
        while y < rect.bottom():
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            y += _GRID_SPACING

    # -- wiring ---------------------------------------------------------

    def bind_set_active_repo(self, callback: Callable[[str, str], None]) -> None:
        self._set_active_repo_callback = callback

    def bind_open_settings_tab(self, callback: Callable[[str], None]) -> None:
        self._open_settings_tab_callback = callback

    def request_active_repo(self, project_id: str, repo_id: str) -> None:
        if self._set_active_repo_callback is None:
            return
        if not self._is_repo_cloned(project_id, repo_id):
            try:
                repo = self.store.get_repo(project_id, repo_id)
            except NotFoundError:
                return
            required = self.pipeline_store.get_required_repos(project_id, repo_id)
            to_clone = [(pid, r) for pid, r in required if not self._is_repo_cloned(pid, r.id)]
            if not confirm_action(self, "Clone Repo", self._build_clone_confirm_message(repo, to_clone)):
                return
            if to_clone:
                if not self._clone_required_repos(to_clone):
                    return
                self.load_project(self._project_id)
        self._set_active_repo_callback(project_id, repo_id)

    def _build_clone_confirm_message(self, repo: Repo, to_clone: list[tuple[str, Repo]]) -> str:
        if not to_clone:
            return f"'{repo.name}' hasn't been cloned yet. Clone it and switch to it now?"
        noun = "repo" if len(to_clone) == 1 else "repos"
        bullets = "\n".join(f"  • {target_repo.name}" for _pid, target_repo in to_clone)
        return (
            f"'{repo.name}' hasn't been cloned yet.\n\n"
            f"It connects an Input Path to the following required {noun}, which will also be cloned:\n\n"
            f"{bullets}\n\n"
            f"Clone everything and switch to '{repo.name}' now?"
        )

    def _clone_required_repos(self, to_clone: list[tuple[str, Repo]]) -> bool:
        workspace_root = self.local_config_store.workspace_root
        progress = QProgressDialog("Preparing...", None, 0, len(to_clone), self)
        progress.setWindowTitle("Cloning Required Repos")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        worker = RequiredRepoCloneWorker(git_service=self.git_service, workspace_root=workspace_root, targets=to_clone)
        loop = QEventLoop()
        outcome: dict[str, object] = {"ok": False, "repo_name": None, "error": None}
        step = {"n": 0}

        def on_progress(repo_name: str) -> None:
            progress.setLabelText(f"Cloning '{repo_name}'...")
            progress.setValue(step["n"])
            step["n"] += 1

        def on_finished_ok() -> None:
            outcome["ok"] = True
            loop.quit()

        def on_failed(repo_name: str, error: str) -> None:
            outcome["repo_name"] = repo_name
            outcome["error"] = error
            loop.quit()

        worker.repo_progress.connect(on_progress)
        worker.finished_ok.connect(on_finished_ok)
        worker.failed.connect(on_failed)
        worker.start()
        loop.exec()
        progress.close()
        worker.wait()

        if not outcome["ok"]:
            QMessageBox.warning(
                self,
                "Clone Failed",
                f"Cloning required repo '{outcome['repo_name']}' failed:\n\n{outcome['error']}\n\n"
                "Some required repos may not have been cloned. Nothing was switched — you can try again.",
            )
            return False
        return True

    def _is_repo_cloned(self, project_id: str, repo_id: str) -> bool:
        workspace_root = self.local_config_store.workspace_root
        if not workspace_root:
            return False
        try:
            repo = self.store.get_repo(project_id, repo_id)
        except NotFoundError:
            return False
        # repo.local_path, not a recompute from repo.name — a repo renamed
        # after creation keeps its original on-disk folder (core/store.py's
        # add_repo only computes the name-based path once, at creation), so
        # recomputing here would check the wrong folder and report a
        # cloned repo as not-cloned. Same fix as PublishApi.repo_paths'
        # get_active_repo/resolve_ref (2026-07-20).
        dest_path = Path(workspace_root) / repo.local_path
        return (dest_path / ".git").exists()

    # -- loading / layout / active-repo highlight -------------------------

    def load_project(self, project_id: str | None) -> None:
        self._project_id = project_id
        self._scene.clear()
        self._nodes = {}
        self._edges = []
        if project_id is None:
            return
        try:
            project = self.store.get_project(project_id)
        except NotFoundError:
            return

        repos = project.repos
        edges = self._collect_edges(project_id, repos)

        for repo in repos:
            node = RepoNodeItem(
                view=self, project_id=project_id, repo=repo, thumbnail_path=self.store.resolve_thumbnail_path(repo)
            )
            node.is_active = repo.id == self._active_repo_id
            self._scene.addItem(node)
            self._nodes[repo.id] = node

        self._layout_nodes(repos)

        for source_id, target_id, direction in edges:
            if source_id == target_id:
                continue
            # PipelineEdgeItem always draws the arrowhead at its `target`
            # argument. `direction` (RepoRef.direction, per-connection,
            # cosmetic only — see pipeline_store.py's RepoRef docstring)
            # picks which way round: "input" (default) points the arrow
            # INTO the connecting repo, so pass the connected-to repo as
            # `source` and the connecting repo as `target`; "output"
            # points it OUT of the connecting repo instead, so pass them
            # the other way round.
            if direction == "output":
                edge = PipelineEdgeItem(self._nodes[source_id], self._nodes[target_id])
            else:
                edge = PipelineEdgeItem(self._nodes[target_id], self._nodes[source_id])
            self._scene.addItem(edge)
            self._edges.append(edge)
        self._update_edge_highlights()

    def _collect_edges(self, project_id: str, repos: list[Repo]) -> set[tuple[str, str, str]]:
        """Every directed (connecting_repo_id, target_repo_id, direction)
        pipeline dependency within this project — reads each repo's own
        declared "Connect Pipeline Input Path" list (pipeline_store.py's
        get_inputs), matching Custom Paths' "Connect Input Path" section in
        Repository Setting (custom_paths_settings_page.py — moved there
        2026-07-19 from this node's right-click menu). `direction` (added
        2026-07-19, per RepoRef — "input" or "output") only affects which
        end load_project draws the arrowhead at, never the topology here
        (_layout_nodes doesn't read this edge set at all as of 2026-08-19
        — see that method) — this always treats connecting_repo_id as the
        "source" of the dependency and
        target_repo_id (the repo whose CustomPath it connected to) as the
        "target", regardless of direction. As of 2026-07-19 there's also no
        separate "Set as Pipeline Output" action anymore — every
        connection, regardless of whether the real data flow is "I publish
        into this" or "I read from this", is curated the same way, from
        the connecting repo's own settings; `direction` is purely a
        cosmetic per-connection override of which node the arrowhead
        visually points at. A pipeline ref pointing at a different
        project's repo (allowed by RepoRef's shape) is simply not drawn —
        the graph only shows one project at a time."""
        repo_ids = {repo.id for repo in repos}
        edges: set[tuple[str, str, str]] = set()
        for repo in repos:
            for ref in self.pipeline_store.get_inputs(project_id, repo.id):
                if ref.project_id == project_id and ref.repo_id in repo_ids:
                    edges.add((repo.id, ref.repo_id, ref.direction))
        return edges

    def _layout_nodes(self, repos: list[Repo]) -> None:
        """Groups nodes into one CategoryBoxItem per PipelineStore.get_categories
        entry, plus a synthetic "Uncategorized" box for any repo with no
        category_id (or one pointing at a category that's since been
        deleted) — replaced the old pipeline-dependency Sugiyama-style
        layered layout entirely on 2026-08-19, per the user's own request:
        node position is now a deliberate per-repo "Assign to Category..."
        choice (assign_repo_category/AssignCategoryDialog), not something
        an algorithm infers from pipeline edges. Pipeline edges themselves
        are unaffected by this — load_project still draws one between
        whichever two node positions this method ends up picking.

        Each category's own repos fill a near-square grid inside its own
        box (_category_grid_columns/_category_box_size), in declaration
        order (project.repos' own order, same as every other repo listing
        in this plugin). Boxes themselves stack top to bottom, one column,
        in PipelineStore.get_categories' own stored order (Uncategorized
        always last, since it isn't a real stored Category) — that stored
        order is what a box's own right-click "Move Category Up"/"Move
        Category Down" (move_category) edits, so dragging a category's
        position in the stack is really just reordering this list and
        reloading."""
        categories = self.pipeline_store.get_categories()
        category_by_id = {category.id: category for category in categories}

        repos_by_category_id: dict[str | None, list[Repo]] = {}
        for repo in repos:
            category_id = self.pipeline_store.get_repo_category_id(self._project_id, repo.id)
            if category_id not in category_by_id:
                category_id = None
            repos_by_category_id.setdefault(category_id, []).append(repo)

        ordered_group_ids: list[str | None] = [
            category.id for category in categories if category.id in repos_by_category_id
        ]
        if None in repos_by_category_id:
            ordered_group_ids.append(None)

        y_cursor = 0.0
        for group_id in ordered_group_ids:
            group_repos = repos_by_category_id[group_id]
            title = category_by_id[group_id].name if group_id is not None else _UNCATEGORIZED_TITLE
            box_width, box_height = self._category_box_size(len(group_repos))

            box = CategoryBoxItem(box_width, box_height, title, view=self, category_id=group_id)
            box.setPos(0.0, y_cursor)
            self._scene.addItem(box)

            columns = self._category_grid_columns(len(group_repos))
            for index, repo in enumerate(group_repos):
                column, row = index % columns, index // columns
                node_x = _CATEGORY_BOX_PADDING + column * (NODE_WIDTH + NODE_H_SPACING)
                node_y = (
                    y_cursor
                    + _CATEGORY_BOX_HEADER_HEIGHT
                    + _CATEGORY_BOX_PADDING
                    + row * (NODE_HEIGHT + _NODE_V_SPACING_IN_BOX)
                )
                self._nodes[repo.id].setPos(node_x, node_y)

            y_cursor += box_height + _CATEGORY_BOX_V_SPACING

    @staticmethod
    def _category_grid_columns(count: int) -> int:
        """Near-square column count for `count` nodes inside one category
        box — e.g. 4 -> 2 columns, 5 -> 3 columns (one short in the last
        row rather than a lopsided single row)."""
        return max(1, math.ceil(math.sqrt(count))) if count else 1

    def _category_box_size(self, count: int) -> tuple[float, float]:
        columns = self._category_grid_columns(count)
        rows = math.ceil(count / columns) if count else 1
        width = _CATEGORY_BOX_PADDING * 2 + columns * NODE_WIDTH + max(columns - 1, 0) * NODE_H_SPACING
        height = (
            _CATEGORY_BOX_HEADER_HEIGHT
            + _CATEGORY_BOX_PADDING * 2
            + rows * NODE_HEIGHT
            + max(rows - 1, 0) * _NODE_V_SPACING_IN_BOX
        )
        return width, height

    def set_active_repo(self, project: Project | None, repo: Repo | None) -> None:
        self._active_project = project
        self._active_repo = repo
        project_id = project.id if project is not None else None
        repo_id = repo.id if repo is not None else None
        self._active_repo_id = repo_id
        for node in self._nodes.values():
            node.is_active = project_id == self._project_id and node.repo_id == repo_id
            node.update()
        self._update_edge_highlights()
        self._refresh_overlay()

    def _refresh_overlay(self) -> None:
        project = self._active_project
        repo = self._active_repo
        if project is None or repo is None:
            self._overlay_container.hide()
            return

        # Split this repo's own pipeline connections (Repository Setting >
        # Custom Paths > "Connect Input Path") by RepoRef.direction — the
        # same Input/Output wording custom_paths_settings_page.py's
        # connection list already uses (defaults to "input" for refs saved
        # before `direction` existed).
        input_labels: list[str] = []
        output_labels: list[str] = []
        for ref in self.pipeline_store.get_inputs(project.id, repo.id):
            try:
                target_repo = self.store.get_repo(ref.project_id, ref.repo_id)
            except NotFoundError:
                continue
            custom_path = self.pipeline_store.get_custom_path(ref.project_id, ref.repo_id, ref.custom_path_id)
            entry = f"{target_repo.name} – {custom_path.label if custom_path is not None else '?'}"
            (output_labels if ref.direction == "output" else input_labels).append(entry)

        lines = [
            f"<b>Repo:</b> {repo.name}",
            f"<b>Last Sync:</b> {_format_last_synced(repo.last_synced)}",
            f"<b>Status:</b> {repo.status}",
            f"<b>Input Custom Path:</b> {', '.join(input_labels) if input_labels else '—'}",
            f"<b>Output Custom Path:</b> {', '.join(output_labels) if output_labels else '—'}",
        ]
        self._project_name_label.setText(project.name)
        self._project_name_label.adjustSize()
        self._overlay.setText("<br>".join(lines))
        self._overlay.adjustSize()
        self._overlay_container.adjustSize()
        self._overlay_container.show()
        self._position_overlay()

    def _position_overlay(self) -> None:
        if not self._overlay_container.isVisible():
            return
        viewport_rect = self.viewport().rect()
        x = viewport_rect.right() - self._overlay_container.width() - _OVERLAY_MARGIN
        y = viewport_rect.bottom() - self._overlay_container.height() - _OVERLAY_MARGIN
        self._overlay_container.move(max(0, x), max(0, y))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._position_overlay()

    def _update_edge_highlights(self) -> None:
        active_repo_id = self._active_repo_id
        for edge in self._edges:
            connected = active_repo_id is not None and (
                edge.source_repo_id == active_repo_id or edge.target_repo_id == active_repo_id
            )
            edge.set_highlighted(connected)

    # -- Add Repo (called by the top bar button) -------------------------

    def add_repo(self) -> None:
        if self._project_id is None:
            QMessageBox.information(self, "Add Repo", "Select or create a project first.")
            return
        workspace_root = self.local_config_store.workspace_root
        if not workspace_root:
            QMessageBox.information(self, "Add Repo", "Set and save a workspace folder in Setting > Common first.")
            return
        dialog = RepoDialog(self, store=self.store, project_id=self._project_id)
        if not dialog.exec():
            return
        try:
            repo = self.store.add_repo(self._project_id, dialog.name(), dialog.git_url(), workspace_root)
        except ConflictError as exc:
            self.store.load()
            QMessageBox.warning(self, "Add Repo", str(exc))
            self.load_project(self._project_id)
            return
        except UkoreHubError as exc:
            QMessageBox.warning(self, "Add Repo", str(exc))
            return
        if dialog.chosen_thumbnail_path():
            filename = save_image_asset(
                self, source_path=dialog.chosen_thumbnail_path(), dest_dir=self.store.thumbnails_dir, asset_id=repo.id
            )
            if filename is not None:
                self.store.set_repo_thumbnail(self._project_id, repo.id, filename)
        self.store.set_repo_requirements(self._project_id, repo.id, dialog.selected_program_ids())
        self.store.set_repo_program_version_pins(self._project_id, repo.id, dialog.selected_program_version_pins())
        self.load_project(self._project_id)

    # -- node context-menu actions ---------------------------------------

    def open_repo_settings(self) -> None:
        """Opens the unified Settings dialog on its Repo Setting (Dev) >
        Local Repository tab, for whichever repo is currently ACTIVE (not
        necessarily the node that was right-clicked — every Repo Setting
        (Dev) page self-resolves the active repo from local_config_store,
        same as every other CATEGORY_REPO tab). Repo-scoped settings used
        to render in this plugin's own "Repository Setting" popup
        (RepoSettingsDialog, retired) — they moved back into the main
        Settings dialog, so this just opens that dialog via
        UICommandService.open_settings_tab instead of building a second one."""
        if self._open_settings_tab_callback is None:
            return
        self._open_settings_tab_callback(LOCAL_REPOSITORY)
        # Custom Paths' "Connect Input Path" section (see
        # custom_paths_settings_page.py) can add/remove pipeline_inputs
        # entries while this dialog is open — reload so the graph's edges
        # (_collect_edges reads that same data) reflect any change made
        # without requiring a separate repo switch/reload.
        if self._project_id is not None:
            self.load_project(self._project_id)

    def assign_repo_category(self, project_id: str, repo_id: str) -> None:
        """"Assign to Category..." — AssignCategoryDialog picks one of
        PipelineStore.get_categories, "(Uncategorized)" to clear the
        repo's own category_id, or "New Category..." to create one on the
        spot (add_category, since a freshly organized repo usually needs a
        brand-new category rather than an existing one). Reloads the graph
        afterward so _layout_nodes' grid reflects the new grouping right
        away, same as every other mutating node action in this file."""
        categories = self.pipeline_store.get_categories()
        current_category_id = self.pipeline_store.get_repo_category_id(project_id, repo_id)
        dialog = AssignCategoryDialog(self, categories=categories, current_category_id=current_category_id)
        if not dialog.exec():
            return

        category_id = dialog.selected_category_id()
        if dialog.is_new_category():
            try:
                category_id = self.pipeline_store.add_category(dialog.new_category_name()).id
            except ConflictError as exc:
                self.pipeline_store.reload_categories()
                QMessageBox.warning(self, "Assign to Category", str(exc))
                self.load_project(self._project_id)
                return

        try:
            self.pipeline_store.set_repo_category_id(project_id, repo_id, category_id)
        except ConflictError as exc:
            self.store.load()
            QMessageBox.warning(self, "Assign to Category", str(exc))
        self.load_project(self._project_id)

    def move_category(self, category_id: str, direction: int) -> None:
        """A category box's own right-click "Move Category Up" (direction
        -1) / "Move Category Down" (direction +1) — swaps this category
        with its neighbor in PipelineStore.get_categories' own stored
        order (what _layout_nodes stacks boxes top-to-bottom in) and
        persists it. A no-op, without touching the store or reloading, if
        category_id is already at that end of the list — the synthetic
        Uncategorized bucket is never in this list at all, so it's never
        a valid neighbor to swap into either."""
        categories = self.pipeline_store.get_categories()
        index = next((i for i, category in enumerate(categories) if category.id == category_id), None)
        if index is None:
            return
        new_index = index + direction
        if not (0 <= new_index < len(categories)):
            return
        categories[index], categories[new_index] = categories[new_index], categories[index]
        try:
            self.pipeline_store.set_categories(categories)
        except ConflictError as exc:
            self.pipeline_store.reload_categories()
            QMessageBox.warning(self, "Reorder Category", str(exc))
        self.load_project(self._project_id)

    def rename_repo(self, project_id: str, repo_id: str) -> None:
        repo = self.store.get_repo(project_id, repo_id)
        dialog = RepoDialog(self, name=repo.name, git_url=repo.git_url, show_thumbnail=False)
        if not dialog.exec():
            return
        try:
            self.store.edit_repo(project_id, repo_id, name=dialog.name(), git_url=dialog.git_url())
        except ConflictError as exc:
            self.store.load()
            QMessageBox.warning(self, "Rename Repo", str(exc))
            self.load_project(self._project_id)
            return
        except UkoreHubError as exc:
            QMessageBox.warning(self, "Rename Repo", str(exc))
            return
        self.load_project(self._project_id)

    def change_repo_thumbnail(self, project_id: str, repo_id: str) -> None:
        source_path = pick_image_file(self, "Choose Thumbnail Image")
        if source_path is None:
            return
        filename = save_image_asset(self, source_path=source_path, dest_dir=self.store.thumbnails_dir, asset_id=repo_id)
        if filename is not None:
            self.store.set_repo_thumbnail(project_id, repo_id, filename)
            node = self._nodes.get(repo_id)
            if node is not None:
                node.set_thumbnail(self.store.resolve_thumbnail_path(self.store.get_repo(project_id, repo_id)))

    def delete_repo(self, project_id: str, repo_id: str) -> None:
        repo = self.store.get_repo(project_id, repo_id)
        if not confirm_action(
            self,
            "Delete Repo",
            f"Delete repo '{repo.name}' from the registry for EVERYONE at the studio?\n\n"
            "This removes it from the shared registry immediately and cannot be undone.",
        ):
            return
        try:
            self.store.delete_repo(project_id, repo_id)
        except ConflictError as exc:
            self.store.load()
            QMessageBox.warning(self, "Delete Repo", str(exc))
        self.load_project(self._project_id)
