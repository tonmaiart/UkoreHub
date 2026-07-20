from __future__ import annotations

import math
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QLineF, QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import (
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
    QVBoxLayout,
)

from core.addon_store import AddonMetadataStore
from core.exceptions import NotFoundError, UkoreHubError
from core.extensibility.loader import DiscoveredPlugin
from core.models import Project, Repo
from core.program_store import ProgramStore
from core.store import LocalConfigStore, MetadataStore
from interface.settings_tab_registry import SettingsTabRegistry
from plugins.studio.project_editor.dialogs import RepoDialog
from interface.shared.image_asset import pick_image_file, save_image_asset
from interface.shared.widget_helpers import confirm_action
from plugins.studio.project_editor.pipeline_store import PipelineStore
from plugins.studio.project_editor.repo_settings_panel import RepoSettingsDialog

NODE_WIDTH = 160.0
NODE_HEIGHT = 110.0
NODE_CORNER_RADIUS = 6.0
NODE_H_SPACING = 40.0
LEVEL_V_SPACING = 60.0
# A repo with this many total pipeline connections (in + out) or fewer gets
# pushed up toward the top rows by _layout_nodes' final_level_of, instead of
# staying at its baseline (longest-path-from-root) row — added 2026-07-19
# per the user's own request to declutter the busy, well-connected rows.
_LOW_DEGREE_THRESHOLD = 1
_ARROW_SIZE = 8.0
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
# Darker than the app-wide theme background (core/theme.py's "grey_dark"
# background="#1e1f22", inherited by default since this view sets no
# stylesheet of its own) so the graph reads as its own recessed canvas
# rather than blending into the surrounding chrome.
_GRAPH_BACKGROUND_COLOR_HEX = "#141517"

# Clone-status corner icon, drawn top-right on every node — file lives at
# plugins/studio/project_editor/project_graph_view.py, three parents up is
# the UkoreHub repo root.
_ICONS_DIR = Path(__file__).resolve().parents[3] / "data" / "icons"
_CONNECTED_ICON_PATH = _ICONS_DIR / "icons8-connected-30.png"
_DISCONNECTED_ICON_PATH = _ICONS_DIR / "icons8-disconnected-30.png"
_CLONE_STATUS_ICON_SIZE = 16
_CLONE_STATUS_ICON_MARGIN = 6
_clone_status_icon_cache: dict[bool, QPixmap | None] = {}

# Bottom-right HUD (active project/repo, sync state, pipeline connections).
_OVERLAY_MARGIN = 12


def _theme_colors():
    from core.theme import DEFAULT_THEME_NAME, get_theme

    return get_theme(DEFAULT_THEME_NAME)


def _clone_status_icon(is_cloned: bool) -> QPixmap | None:
    """Cached, pre-scaled QPixmap for the clone/not-cloned corner badge —
    loaded once per status value, not once per node per paint() call."""
    if is_cloned not in _clone_status_icon_cache:
        path = _CONNECTED_ICON_PATH if is_cloned else _DISCONNECTED_ICON_PATH
        pixmap = QPixmap(str(path)) if path.exists() else None
        if pixmap is not None and not pixmap.isNull():
            pixmap = pixmap.scaled(
                _CLONE_STATUS_ICON_SIZE, _CLONE_STATUS_ICON_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        else:
            pixmap = None
        _clone_status_icon_cache[is_cloned] = pixmap
    return _clone_status_icon_cache[is_cloned]


class RepoNodeItem(QGraphicsItem):
    """One node = one repo. Paints the repo's thumbnail fill-cropped (same
    crop math as interface/login/repo_picker.py's _RepoCard.paintEvent) plus
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
        if clone_icon is not None:
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
            border_color, border_width = QColor(colors.accent), 3
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
    assuming one mirrors the other) and how it also drives node layering
    (the connected-to repo above, the connecting repo below, regardless of
    `direction` — see _layout_nodes, inverted 2026-07-19).

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


class ProjectGraphView(QGraphicsView):
    """1 node = 1 repo, for whichever project is currently loaded, laid out
    bottom-up by pipeline dependency (roots — the connecting repos — at
    the bottom, rows rising toward the top, inverted 2026-07-19 — see
    _layout_nodes). Each edge's arrowhead points into the connecting repo
    by default ("input" direction) or out toward the target repo instead
    ("output" — a per-connection choice, RepoRef.direction, added
    2026-07-19, see load_project) — direction only ever changes the
    arrowhead end, never which row a node lands in. A single left-click
    on a node requests an active-repo switch (see request_active_repo — the
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
        program_store: ProgramStore,
        addon_store: AddonMetadataStore,
        addon_catalog: list[DiscoveredPlugin],
        pipeline_store: PipelineStore,
        settings_tab_registry: SettingsTabRegistry,
    ):
        super().__init__(parent)
        self.store = store
        self.local_config_store = local_config_store
        self.program_store = program_store
        self.addon_store = addon_store
        self.addon_catalog = addon_catalog
        self.pipeline_store = pipeline_store
        self.settings_tab_registry = settings_tab_registry

        self._set_active_repo_callback: Callable[[str, str], None] | None = None
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
        self.setBackgroundBrush(QColor(_GRAPH_BACKGROUND_COLOR_HEX))

        # Bottom-right HUD, a plain child QLabel positioned by hand in
        # resizeEvent/_position_overlay rather than a layout — it floats
        # over the QGraphicsView viewport, not inside the scene, so it
        # never scrolls/zooms with the graph content.
        self._overlay = QLabel(self)
        self._overlay.setObjectName("projectGraphOverlay")
        self._overlay.setTextFormat(Qt.RichText)
        self._overlay.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self._overlay.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._overlay.setStyleSheet(
            "QLabel#projectGraphOverlay {"
            " background-color: rgba(0, 0, 0, 150);"
            " color: #dcddde;"
            " padding: 8px 10px;"
            " border-radius: 6px;"
            " font-size: 11px;"
            "}"
        )
        self._overlay.hide()

    # -- wiring ---------------------------------------------------------

    def bind_set_active_repo(self, callback: Callable[[str, str], None]) -> None:
        self._set_active_repo_callback = callback

    def request_active_repo(self, project_id: str, repo_id: str) -> None:
        if self._set_active_repo_callback is None:
            return
        if not self._is_repo_cloned(project_id, repo_id):
            try:
                repo = self.store.get_repo(project_id, repo_id)
            except NotFoundError:
                return
            if not confirm_action(
                self,
                "Clone Repo",
                f"'{repo.name}' hasn't been cloned yet. Clone it and switch to it now?",
            ):
                return
        self._set_active_repo_callback(project_id, repo_id)

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

        self._layout_nodes(repos, edges)

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
        end load_project draws the arrowhead at, never the topology here or
        in _layout_nodes' level assignment — both always treat
        connecting_repo_id as the "source" of the dependency and
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

    def _layout_nodes(self, repos: list[Repo], edges: set[tuple[str, str, str]]) -> None:
        """Layered bottom-up layout (a simplified Sugiyama-style pass):
        baseline level = longest path from a "root" (no predecessors)
        through pipeline edges, so the repo whose Custom Path was connected
        to always sits in a row above the repo that connected to it — this
        ordering always holds regardless of each edge's `direction` (added
        2026-07-19), which only affects load_project's arrowhead
        placement, never row assignment.

        On top of that baseline, a repo with `_LOW_DEGREE_THRESHOLD` or
        fewer total connections (in + out) is pushed UP as far as its own
        successors' rows allow (added 2026-07-19, per the user's own
        request to declutter the busy, well-connected rows) — see
        final_level_of below for how that stays provably consistent with
        the "target above source" ordering even after boosting. A
        well-connected repo (more than _LOW_DEGREE_THRESHOLD connections,
        e.g. a busy "...Publish" hub) keeps its original baseline row,
        unchanged from before 2026-07-19. Isolated repos with no pipeline
        edges at all have zero connections, so they're always boosted all
        the way to the top row.

        Level 0 (the lowest row after boosting) is placed at the BOTTOM
        and higher levels rise toward the top (inverted 2026-07-19, was
        top-down). Within each row, nodes are ordered by the average
        x-position of their predecessors one row down (barycenter
        heuristic, using the *baseline* predecessor relationship — a
        boosted repo's true predecessor may no longer sit in the row
        immediately below it once boosted, so this heuristic is only
        approximate for boosted repos, falling back to declaration order
        same as any other repo with no predecessor in the row below) to
        reduce edge crossings, then the whole row is horizontally centered
        against the widest level."""
        repo_order = {repo.id: index for index, repo in enumerate(repos)}
        predecessors: dict[str, list[str]] = {repo.id: [] for repo in repos}
        successors: dict[str, list[str]] = {repo.id: [] for repo in repos}
        degree: dict[str, int] = {repo.id: 0 for repo in repos}
        for source_id, target_id, _direction in edges:
            if source_id == target_id:
                continue
            if target_id in predecessors:
                predecessors[target_id].append(source_id)
            if source_id in successors and target_id in successors:
                successors[source_id].append(target_id)
            if source_id in degree:
                degree[source_id] += 1
            if target_id in degree:
                degree[target_id] += 1

        levels: dict[str, int] = {}
        visiting: set[str] = set()

        def level_of(repo_id: str) -> int:
            if repo_id in levels:
                return levels[repo_id]
            if repo_id in visiting:
                # Cycle in declared pipeline data (curated independently per
                # repo, never validated as acyclic) — treat as a root here
                # rather than recursing forever.
                return 0
            visiting.add(repo_id)
            preds = predecessors.get(repo_id, [])
            result = 0 if not preds else 1 + max(level_of(p) for p in preds)
            visiting.discard(repo_id)
            levels[repo_id] = result
            return result

        for repo in repos:
            level_of(repo.id)

        overall_max_level = max(levels.values(), default=0)
        final_levels: dict[str, int] = {}
        final_visiting: set[str] = set()

        def final_level_of(repo_id: str) -> int:
            """The baseline level_of(repo_id) unless this repo is
            low-degree, in which case it's pushed up to the highest row
            still strictly below every one of its own successors' *final*
            rows. Recurses into successors first (so that bound reflects
            each successor's actual chosen row, whether boosted or not),
            which by induction guarantees final_level_of(repo) is always
            strictly less than final_level_of(successor) for every edge:
              - An unboosted repo keeps base = level_of(repo_id), and
                level_of already guarantees level_of(successor) >=
                level_of(repo_id) + 1 for every edge — and every final
                level is >= its own baseline level (boosting only ever
                raises a level), so final_level_of(successor) >= base + 1.
              - A boosted repo's result is at most
                min(final_level_of(s) for s in successors) - 1, i.e.
                strictly below every successor's own final row by
                construction.
            Cycle-guarded the same way level_of is — a repo_id already on
            the current recursion stack falls back to its own baseline
            level rather than recursing forever."""
            if repo_id in final_levels:
                return final_levels[repo_id]
            if repo_id in final_visiting:
                return levels.get(repo_id, 0)
            final_visiting.add(repo_id)
            succs = successors.get(repo_id, [])
            upper_bound = min((final_level_of(s) - 1 for s in succs), default=overall_max_level)
            base = levels.get(repo_id, 0)
            result = max(base, upper_bound) if degree.get(repo_id, 0) <= _LOW_DEGREE_THRESHOLD else base
            final_visiting.discard(repo_id)
            final_levels[repo_id] = result
            return result

        for repo in repos:
            final_level_of(repo.id)

        # Compact whatever final levels were actually used down to
        # consecutive integers starting at 0 — boosting can leave gaps
        # (e.g. nothing left at level 2 because everything that would've
        # landed there got pushed higher), and the barycenter pass below
        # indexes "the row immediately below" by literal level number,
        # which needs no gaps. A strictly increasing renumbering can't
        # change the relative order between any two repos, so it can't
        # reintroduce a "successor at or below its source" ordering
        # violation either.
        distinct_levels = sorted(set(final_levels.values()))
        level_rank = {level: rank for rank, level in enumerate(distinct_levels)}
        levels_for_layout = {repo_id: level_rank[level] for repo_id, level in final_levels.items()}

        repos_by_level: dict[int, list[str]] = {}
        for repo in repos:
            repos_by_level.setdefault(levels_for_layout[repo.id], []).append(repo.id)

        for level in sorted(repos_by_level):
            if level == 0:
                repos_by_level[level].sort(key=lambda rid: repo_order[rid])
                continue
            prev_position = {rid: index for index, rid in enumerate(repos_by_level[level - 1])}

            def sort_key(rid: str, prev_position=prev_position) -> tuple[int, float]:
                preds_above = [p for p in predecessors.get(rid, []) if p in prev_position]
                if preds_above:
                    return (0, sum(prev_position[p] for p in preds_above) / len(preds_above))
                return (1, repo_order[rid])

            repos_by_level[level].sort(key=sort_key)

        row_widths = {
            level: len(row) * NODE_WIDTH + max(len(row) - 1, 0) * NODE_H_SPACING
            for level, row in repos_by_level.items()
        }
        max_width = max(row_widths.values(), default=0.0)
        max_level = max(repos_by_level, default=0)

        for level, row in repos_by_level.items():
            x_offset = (max_width - row_widths[level]) / 2
            # Inverted 2026-07-19: level 0 (roots) at the bottom row, rising
            # toward the top as level increases — see this method's
            # docstring for why (arrows now point up instead of down).
            y = (max_level - level) * (NODE_HEIGHT + LEVEL_V_SPACING)
            for index, repo_id in enumerate(row):
                x = x_offset + index * (NODE_WIDTH + NODE_H_SPACING)
                self._nodes[repo_id].setPos(x, y)

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
            self._overlay.hide()
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
            f"<b>Project:</b> {project.name}",
            f"<b>Repo:</b> {repo.name}",
            f"<b>Last Sync:</b> {repo.last_synced or 'Never'}",
            f"<b>Status:</b> {repo.status}",
            f"<b>Input Custom Path:</b> {', '.join(input_labels) if input_labels else '—'}",
            f"<b>Output Custom Path:</b> {', '.join(output_labels) if output_labels else '—'}",
        ]
        self._overlay.setText("<br>".join(lines))
        self._overlay.adjustSize()
        self._overlay.show()
        self._position_overlay()

    def _position_overlay(self) -> None:
        if not self._overlay.isVisible():
            return
        viewport_rect = self.viewport().rect()
        x = viewport_rect.right() - self._overlay.width() - _OVERLAY_MARGIN
        y = viewport_rect.bottom() - self._overlay.height() - _OVERLAY_MARGIN
        self._overlay.move(max(0, x), max(0, y))

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
        dialog = RepoDialog(
            self, program_store=self.program_store, addon_catalog=self.addon_catalog, addon_store=self.addon_store
        )
        if not dialog.exec():
            return
        try:
            repo = self.store.add_repo(self._project_id, dialog.name(), dialog.git_url(), workspace_root)
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
        self.store.set_repo_enabled_addons(self._project_id, repo.id, dialog.selected_addon_ids())
        self.load_project(self._project_id)

    # -- node context-menu actions ---------------------------------------

    def open_repo_settings(self) -> None:
        """Opens RepoSettingsDialog for whichever repo is currently ACTIVE
        (not necessarily the node that was right-clicked — see
        RepoSettingsDialog's own docstring for why)."""
        title = "Repository Setting"
        project_id = self.local_config_store.active_project_id
        repo_id = self.local_config_store.active_repo_id
        if project_id and repo_id:
            try:
                repo = self.store.get_repo(project_id, repo_id)
                title = f"Repository Setting — {repo.name}"
            except NotFoundError:
                pass
        dialog = RepoSettingsDialog(self, settings_tab_registry=self.settings_tab_registry, title=title)
        dialog.exec()
        # Custom Paths' "Connect Input Path" section (see
        # custom_paths_settings_page.py) can add/remove pipeline_inputs
        # entries while this dialog is open — reload so the graph's edges
        # (_collect_edges reads that same data) reflect any change made
        # without requiring a separate repo switch/reload.
        if self._project_id is not None:
            self.load_project(self._project_id)

    def rename_repo(self, project_id: str, repo_id: str) -> None:
        repo = self.store.get_repo(project_id, repo_id)
        dialog = RepoDialog(self, name=repo.name, git_url=repo.git_url, show_thumbnail=False)
        if not dialog.exec():
            return
        try:
            self.store.edit_repo(project_id, repo_id, name=dialog.name(), git_url=dialog.git_url())
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
        self.store.delete_repo(project_id, repo_id)
        self.load_project(self._project_id)
