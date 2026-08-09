# plugins/core/project_editor/

Node-graph editor for the Project/Repo registry — an ordinary
`SectionRegistry` section, a Sidebar row and `view_stack` page like every
other section. Before this refactor it was `persistent=True`: never a
sidebar row, docked permanently beside `view_stack` in a `QSplitter`
instead, always visible no matter which ordinary section was currently
showing — folded into the single `view_stack` along with everything else
as part of tightening the app down to one navigation model (its node
highlight/HUD now only refreshes when this tab is actually visible,
matching how every other page already behaved, instead of continuously).
Renamed from `pipeline_architect` on 2026-07-15, when
this stopped being a buried Settings > Developer tab (`ProjectDataEditorPage`,
a CRUD tree); briefly a full-width switchable section the same day, then
changed again the same day to the always-visible docked panel it is now.
Three things bundled into one plugin (originally two, before the
2026-07-19 CustomPath addition):

1. **Project/Repo CRUD** — Add/Rename/Delete Project (Setting > Project,
   moved there 2026-08-03 from the graph view's own top bar — see
   `project_settings_page.py` below), Add/Rename/Delete/Thumbnail Repo
   (node context menu) — same `core/store.py` `MetadataStore` calls the old
   tree page made, just triggered from Settings/graph UI instead of tree
   rows/buttons.
2. **Pipeline connections** — which other repos a given repo has
   connected to, via Repository Setting's "Custom Paths" tab, "Connect
   Input Path" section (moved there 2026-07-19 from a node's right-click
   menu — see `custom_paths_settings_page.py` below). Stored in
   `core/models.py`'s `Repo.plugin_data["project_editor"]` (moved there
   from this plugin's own standalone `PluginConfigStore` file — see the
   `manifest.json` bullet below) — other plugins read it via
   `api.metadata.get_repo_plugin_data(project_id, repo_id, "project_editor")`
   without `core/` needing to know the concept exists.
   As of the 2026-07-15 redesign these are no longer just an editable
   list — they're rendered as directed edges between nodes in the graph,
   which is what actually gives "Pipeline Architect" a visual meaning. As
   of 2026-07-19, each connection points at one specific **CustomPath** a
   repo declares for itself (see below), not the whole repo — a shared
   "...Publish" repo is rarely one undifferentiated destination, so a
   connecting repo needs to say *which* declared location it means. There
   used to be a separate, independently-curated "pipeline outputs"
   concept (a node context menu action "Set as Pipeline Output...")
   alongside this "pipeline inputs" one — **removed 2026-07-19**: every
   connection a repo makes is curated the same single way now, regardless
   of whether the real data flow is "I publish into this" or "I read from
   this" — see `custom_paths_settings_page.py` below and `pipeline_store.py`'s
   `RepoRef` docstring for why. Each connection also carries a `direction`
   (`"input"` or `"output"`, also added 2026-07-19, picked in
   `ConnectInputPathDialog`) — purely cosmetic, it only decides which end
   of the drawn edge the Graph View puts the arrowhead on (into the
   connecting repo for `"input"`, out toward the target repo for
   `"output"`), never the graph's row layout/topology.
3. **CustomPath catalog** — a repo's own list of named locations
   (`{id, label, path}`, `path` relative to that repo's root) other repos'
   pipeline connections pick from — see "Custom Paths" tab
   (`custom_paths_settings_page.py`) below.

## ⚠️ Deliberate architecture tradeoff (unchanged from pipeline_architect)

Creating/renaming/deleting a Project or Repo depends on this plugin loading
successfully — the one place in the app where a plugin load failure has a
real, visible consequence (no way to add/edit/delete repos at all until
it's fixed). See `core/extensibility/loader.py`'s `PluginLoadFailure`
handling for why every other plugin failure is isolated and this one isn't.

`MainWindow._apply_plugin_visibility` never gates this section at all —
there used to be a `manifest.json` `"core": true` flag here, load-bearing
back when this plugin registered a normal switchable section, but it had
already gone fully redundant once the section became `persistent=True`
(now removed, see the top of this file). Removed 2026-08-04 once every
`plugins/core/` plugin (not just this one) became unconditionally visible
for every repo — see `plugins/README.md`. This plugin's row still shows up, label-only and
unchecked, in the "Core Plugin" list on the "Requirements & Plugins" tab
(`interface/repo_settings/requirements_and_plugins_page.py`), same as
every other `plugins/core/` plugin — nothing plugin-specific needed here
anymore.

## Files

- `manifest.json` — plugin id `project_editor` (renamed from
  `pipeline_architect`; the shared data file at
  `data/plugins/core/project_editor.json` was `git mv`'d in the same
  commit as the folder, so no migration step was needed then). That file
  itself was later superseded by `Repo.plugin_data["project_editor"]`
  (`core/models.py`, `data/projects/<project_id>.json`) — `pipeline_store.py`'s
  `migrate_legacy_data(api)` does a one-time, self-healing cutover of any
  data still in the old blob on `register(api)`.
- `plugin.py` — `register(api)`: constructs `PipelineStore` and one
  `ProjectEditorPage` instance, registers it via `api.register_section(...)`
  with `wire=_wire` — `_wire` calls `page.bind_set_active_repo(host.set_active_repo)`,
  `page.bind_switch_project(host.switch_project)`, and
  `page.bind_open_settings_tab(host.open_settings_tab)` — all three
  `UICommandService` fields (see `interface/section_registry.py`) so a node
  click can trigger a real active-repo switch, Settings > Project's
  "Switch Project..." button can trigger a full app restart, and a node's
  "Repository Setting..." right-click can open the unified Settings dialog
  on its Repo Setting (Dev) category — all without the page holding a
  `MainWindow` reference.
- `dialogs.py` — `ProjectDialog`/`RepoDialog`. `RepoDialog` embeds
  `interface/shared/requirements_tree_widget.py`'s `RequirementsTreeWidget`
  (the checkable Program requirements tree, for repo creation) — that
  widget briefly lived in this file (moved in 2026-07-20, moved back out
  2026-08-04 once `interface/repo_settings/requirements_and_plugins_page.py`
  became a second real consumer; see `interface/shared/README.md`).
  `ProjectDialog`/`RepoDialog` themselves are imported as a normal sibling
  module (`from plugins.core.project_editor.dialogs import ...`, the same
  real-package convention `plugins/README.md`'s "Multi-file plugins"
  section documents), not a relative import. Used by
  `project_graph_view.py` (`RepoDialog`, node context menu Add/Edit Repo,
  plus `add_repo` — see below) and `project_settings_page.py`
  (`ProjectDialog`, "Add New Project..."/Rename Project — moved here from
  `project_editor_page.py` 2026-08-03, see that file's own bullet).
- `project_editor_page.py` — `ProjectEditorPage`: the section's top-level
  widget. No top bar at all as of 2026-08-03 (second pass — the project
  `QComboBox`/Rename/Delete Project buttons moved out earlier the same day,
  then Add Repo followed once the user asked for it too) — just
  `ProjectGraphView`, full width/height, with zero chrome of its own.
  Every action that used to be a top-bar button now lives in Setting >
  **Project** (`project_settings_page.py` below) instead. As of the
  single-project-per-session change, the Viewgraph is fixed at
  construction to whichever project `local_config_store.active_project_id`
  already names (guaranteed real by then — see `launcher.py`'s mandatory
  Project Selector gate) rather than defaulting to the first project in
  the registry.
  `current_project_id()`/`add_repo()` are this page's own single source of
  truth/entry points — `plugin.py` binds these to `ProjectSettingsPage`'s
  `get_current_project_id`/`add_repo` callbacks (`add_repo()` itself just
  delegates to `ProjectGraphView.add_repo`), so a freshly-constructed
  settings page always reads/acts through to this persistent page
  (matching every `CATEGORY_REPO` tab's own self-resolving-active-state
  convention) rather than holding that state itself — clicking Add Repo in
  Settings takes effect immediately, even while that dialog is still open,
  since it's a plain synchronous call, not deferred until the dialog
  closes (Add Repo's own `RepoDialog` opens as a nested modal on top of
  the already-open Settings dialog, which Qt handles fine).
  `set_current_project()` still exists as the one place that actually
  loads a project into the graph (also used defensively by `set_repo()`,
  see below), but nothing calls it with a project id other than the one
  fixed at construction anymore — `bind_switch_project()`/`switch_project()`
  is the only way to view a different project at all, and it does that via
  a full app restart (`UICommandService.switch_project`, wrapping
  `MainWindow._request_switch_project`), not an in-place load. Implements
  the standard `set_repo()` page protocol purely to keep the graph's
  active-node highlight in sync when the active repo changes elsewhere —
  this page only *reacts* to active-repo changes, it never receives a
  command to make one (that only happens via a node click, through
  `bind_set_active_repo`).
- `project_settings_page.py` — `ProjectSettingsPage`: a `CATEGORY_PROJECT`
  Settings tab ("Project", added 2026-08-03), rendered by
  `interface/settings/settings_view.py` under its own "PROJECT" header row
  (alongside General/Developer) rather than in the Repository Setting
  popup. Originally had a project `QComboBox` here to view a different
  project's graph in place — **removed** as of the single-project-per-
  session change: Project is fixed for the whole run by `launcher.py`'s
  mandatory Project Selector gate, so this tab now just shows the active
  project's name (read-only), Rename/Delete acting on it, Add Repo, "New
  Project..." (adds to the shared catalog without switching into it — only
  selectable the next time the Selector gate actually runs), and "Switch
  Project..." (the only way to view a different project at all — triggers
  a real app restart back through that gate, `on_switch_project`, bound to
  `ProjectEditorPage.switch_project`). Deleting the currently-active
  project also falls through to the same restart, since there's nothing
  left for this session to show otherwise. Holds no state of its own;
  every read/action goes through the `get_current_project_id`/`add_repo`/
  `on_switch_project` callbacks `plugin.py` binds to
  `ProjectEditorPage.current_project_id`/`add_repo`/`switch_project`.
- `project_graph_view.py` — `ProjectGraphView` (`QGraphicsView`),
  `RepoNodeItem` (`QGraphicsItem`, one per repo), and `PipelineEdgeItem`
  (`QGraphicsPathItem` with a hand-drawn arrowhead, one per directed
  pipeline dependency). Native `QGraphicsView`, not a Mermaid.js/
  QWebEngineView markup renderer — the interaction requirements here
  (click, hover, per-node thumbnail, context menus) don't fit a
  static-diagram renderer without a `QWebChannel` bridge, and this avoids
  the extra Chromium/QtWebEngine dependency for a feature that doesn't need
  a browser. Edges are plain straight lines, each end at whichever point
  on that node's own border a straight line toward the other node's
  center would exit through (`_border_point`) — simplified 2026-07-19 from
  an earlier version that picked a fixed top/bottom/left/right anchor per
  node and routed a rounded elbow between them (`_build_elbow_path`, since
  removed), which produced messy overlapping bends once a node had several
  connections at different angles. Edges paint **above**
  nodes (`_EDGE_Z_VALUE`), not below — a node used to hide any edge segment
  passing near/behind it — with a selected node's connected edges
  highlighted yellow one z-level higher again (`_EDGE_HIGHLIGHT_Z_VALUE`,
  `ProjectGraphView._update_edge_highlights`). The view's own background is
  painted in an overridden `drawBackground` (changed 2026-08-03 from a flat
  `setBackgroundBrush` color) — a radial gradient from `_GRAPH_BACKGROUND_CENTER_HEX`
  (`#3a3b3e`, gray) to `_GRAPH_BACKGROUND_EDGE_HEX` (`#0a0a0b`, near-black),
  centered on the *viewport* (via `mapToScene(viewport().rect().center())`,
  not scene coordinates) so panning never drags the glow off-center, plus a
  faint white grid (`_GRID_SPACING`/`_GRID_LINE_ALPHA`) drawn in scene
  coordinates on top so the grid itself does scroll/pan with the node
  content, like graph paper. Darker than the app-wide theme background it
  would otherwise inherit, so the graph reads as its own recessed canvas.
  - **Node visuals**: paints the repo's thumbnail fill-cropped plus
    a name label; border/overlay react to two independent flags — `is_active`
    (thick border, `_EDGE_HIGHLIGHT_COLOR_HEX` — the same yellow as a
    highlighted pipeline edge, changed 2026-08-03 from the theme's plain
    accent color so an active node visually matches the highlighted arrows
    pointing at/from it) and `_is_hovered` (medium accent-hover border +
    a subtle white wash over the thumbnail, set from `hoverEnterEvent`/
    `hoverLeaveEvent` — `setAcceptHoverEvents(True)` plus the existing
    `PointingHandCursor` together carry the "this is clickable" affordance).
    A clone-status badge (`_clone_status_icon`, added 2026-07-20) paints
    top-right on every node — `assets/icons/icons8-connected-30.png` if
    `RepoNodeItem.is_cloned` (computed once at construction via
    `ProjectGraphView._is_repo_cloned`), else
    `icons8-disconnected-30.png`; both cached as pre-scaled `QPixmap`s at
    module level rather than reloaded per paint. Only recomputed on the
    next `load_project()`/node rebuild — cloning a repo doesn't retroactively
    flip an already-painted node's badge without a reload.
  - **Switching repos**: a single left-click (`mousePressEvent`, guarded to
    `Qt.LeftButton` so right-click's own `contextMenuEvent` isn't also
    treated as a switch request) calls `ProjectGraphView.request_active_repo`,
    deferred one event-loop tick via `QTimer.singleShot(0, ...)` — the
    switch can end up reloading this very scene (`load_project`'s
    `scene.clear()`), which would destroy this `RepoNodeItem`'s C++ object
    while its own event handler is still on the call stack, crashing with
    "Internal C++ object already deleted" the moment that handler resumes;
    deferring lets it finish first (same reasoning applies to every
    scene-mutating context-menu action below). `request_active_repo` checks
    `_is_repo_cloned` (a `.git` folder under `workspace_root / repo.local_path`
    — fixed 2026-07-20 to read the stored `local_path` instead of
    recomputing the folder from the repo's current name via
    `core.paths.resolve_repo_path`, which resolved to the wrong folder for
    any repo renamed after creation; same fix as
    `plugins/repo_internal/PublishApi/maya-scripts/PublishApi/repo_paths.py`'s
    `get_active_repo`/`resolve_ref`) first and shows a one-time "hasn't
    been cloned yet, clone and switch now?" confirmation before the very
    first clone — an already-cloned repo switches immediately with no
    prompt.
    `request_active_repo` also resolves this repo's own **direct**
    `pipeline_store.get_required_repos` — repos it connects an Input Path
    to — and folds any not-yet-cloned ones into that same confirmation
    dialog ("... will also be cloned: RepoB, RepoC"). Deliberately
    direct-only: it never looks at what those required repos themselves
    require, so a single node click can't cascade into cloning the whole
    graph. On confirm, the required repos clone first, sequentially, on a
    background `RequiredRepoCloneWorker` (`required_repo_clone_worker.py`
    — a local duplicate of `submit/git_stream_worker.py`'s
    QThread-wraps-a-callable shape, not an import of it, per this plugin's
    own boundary rules further down) behind a `QProgressDialog`, then
    `load_project()` runs again immediately so their corner badges flip
    right away instead of waiting for some later reload (same precedent as
    `open_repo_settings`, below) — only then does the primary repo's own
    switch/clone proceed through the unchanged Submit pathway. A repo with
    no pipeline connections (or whose connections are all already cloned)
    still sees the exact same one-line prompt as before this existed.
  - **Right-click context menu**: "Repository Setting..." (opens
    `open_repo_settings`, which opens the unified Settings dialog via
    `bind_open_settings_tab` — this one doesn't touch the scene, so it's
    called directly, no `QTimer` deferral needed), then
    rename/thumbnail/delete — every mutation delegated back to
    `ProjectGraphView`'s own methods rather than duplicated per node.
  - **Bottom-right overlay HUD** (`ProjectGraphView._overlay_container`, a
    plain child `QWidget` positioned by hand in `resizeEvent`/
    `_position_overlay` rather than a layout of its own, so it floats over
    the viewport without scrolling/zooming with the graph content — added
    2026-07-20): a `QVBoxLayout` stacking two labels, changed 2026-08-03 to
    split out the project name from the rest, and again 2026-08-03 to drop
    `_overlay`'s own boxed `rgba(0,0,0,150)` background entirely (per the
    user's own request — the whole HUD now reads as plain text floating
    directly over the graph, not a panel) —
    `_project_name_label` (oversized, bold, transparent background, just
    the project's name with no "Project:" prefix) above `_overlay` (now
    also `background: transparent`, no padding/border-radius since there's
    no box left to pad): active repo name, `Repo.last_synced`
    (reformatted via `_format_last_synced` — parses the stored UTC
    isoformat string and renders it in the machine's own local time as
    `"%d %b %Y, %H:%M"`, rather than showing the raw ISO string),
    `Repo.status`, and this repo's own pipeline connections
    (`pipeline_store.get_inputs`) split into "Input Custom Path"/"Output
    Custom Path" lines by each `RepoRef.direction` — the same wording
    `custom_paths_settings_page.py`'s "Connect Input Path" list already
    uses. Refreshed on every `set_active_repo(project, repo)` call (now
    takes the full `Project`/`Repo` objects instead of bare ids, since the
    overlay needs their fields) — hidden when there's no active repo.
    There's no "Connect Pipeline Input Path..." item here anymore (moved
    2026-07-19 into Repository Setting's "Custom Paths" tab, "Connect
    Input Path" section — see `custom_paths_settings_page.py` below) and
    no separate "Set as Pipeline Output..." item either (removed
    2026-07-19, see the "Pipeline connections" bullet up top) — one action
    handles every connection a repo makes. `open_repo_settings` reloads
    the graph (`load_project`) right after the settings dialog closes, so
    a connection added/removed inside it is reflected in the edges
    immediately.
  - **Layout** (`_layout_nodes`): a simplified Sugiyama-style layered
    bottom-up pass instead of a plain grid. Baseline level = longest path
    from a "root" (no predecessors — the connecting repos nothing else
    points at) through pipeline edges (cycle-safe: a cycle in
    independently-curated pipeline data just gets treated as a root rather
    than recursing forever). On top of that baseline, added 2026-07-19 per
    the user's own request to declutter the busy rows: a repo with
    `_LOW_DEGREE_THRESHOLD` (currently 1) or fewer total connections gets
    pushed UP to the highest row its own successors still allow
    (`final_level_of`, a second recursive pass over `successors` computed
    the same way `predecessors` is) — a well-connected repo (e.g. a busy
    "...Publish" hub) keeps its original baseline row unchanged. This is
    provably safe: `final_level_of(repo) < final_level_of(successor)`
    always holds, by induction over the recursion (see that function's own
    docstring for the short proof) — so a boosted repo can never end up
    level-with-or-above one of its own successors. The resulting levels
    are then compacted to consecutive integers (boosting can leave gaps)
    before level 0 (the lowest row after boosting) is placed at the
    **bottom** and higher levels rise toward the top (inverted 2026-07-19,
    was top-down — `y = (max_level - level) * row_height`); within a
    level, nodes are ordered by the average x-position of their baseline
    predecessors one row down (barycenter heuristic — only approximate for
    a boosted repo, whose true predecessor may no longer be exactly one
    row below it) to reduce edge crossings, then each row is horizontally
    centered against the widest level. An isolated repo with no pipeline
    edges at all has zero connections, so it's always boosted all the way
    to the top row.
    Combined with `PipelineEdgeItem`'s arrowhead-at-`target` convention
    (also inverted 2026-07-19 — `load_project` passes the connected-to
    repo as `source` and the connecting repo as `target`), every edge
    points strictly **downward** by default (`"input"` direction — see
    `RepoRef.direction`) — drawn as a plain straight line between each
    node's own border, each end aimed directly at the other node's center
    (`_border_point`, simplified 2026-07-19 from an elbow-routed
    fixed-anchor version — see the `project_graph_view.py` bullet below).
  - `_collect_edges` reads `pipeline_store.get_inputs` for every repo in
    the loaded project — each entry's own declared connections — and
    returns them as `(connecting_repo_id, target_repo_id)` pairs, matching
    Custom Paths' "Connect Input Path" section's own naming (as of
    2026-07-19 there's no separate "outputs" list to also read and
    de-duplicate against — see the "Pipeline connections" bullet up top).
    `load_project` draws each edge **the other way round** from that pair
    — arrowhead pointing from the connected-to repo down into the
    connecting repo (inverted 2026-07-19, was connecting-repo-to-target)
    — see the "Layout" bullet above. Only edges where both endpoints are
    in the currently loaded project are drawn; a pipeline ref pointing at
    a different project's repo (allowed by `RepoRef`'s shape) is simply
    not drawn, matching the old tree panel's own one-project-at-a-time
    scope.
- `required_repo_clone_worker.py` — `RequiredRepoCloneWorker` (`QThread`):
  clones/pulls a fixed list of `(project_id, Repo)` targets sequentially,
  stopping at the first failure (repos already cloned earlier in the same
  batch are left on disk, never rolled back). Used only by
  `ProjectGraphView.request_active_repo` (see above) to clone a repo's
  direct pipeline requirements before switching to it. A deliberate local
  duplicate of `plugins/core/submit/git_stream_worker.py`'s
  QThread-wraps-a-callable/`finished_ok`/`failed` shape rather than an
  import of it — this plugin doesn't reach into a sibling plugin's source
  (see "Working here" at the bottom of this file).
- `repo_settings_panel.py` (**removed** as part of this refactor —
  `RepoSettingsPanel`/`RepoSettingsDialog` used to render every
  `CATEGORY_REPO` `SettingsTabSpec` in its own popup, opened via a node's
  right-click "Repository Setting...", so these tabs weren't editable from
  both there and the app-level Setting dialog at once. Those tabs now
  render inside `interface/settings/settings_view.py`'s Repo Setting (Dev)
  top tab instead — see that file's `README.md` "Rendering history" note —
  and `ProjectGraphView.open_repo_settings()` opens that same dialog via
  `UICommandService.open_settings_tab` rather than building a second one).
- `pipeline_store.py` — `PipelineStore`/`RepoRef`/`CustomPath`. Lives in each
  repo's own `Repo.plugin_data["project_editor"]` (`core/models.py`,
  `data/projects/<project_id>.json` — moved off the old standalone
  `data/plugins/core/project_editor.json` blob; `migrate_legacy_data(api)`
  in this same file does the one-time cutover). Per-repo shape:
  ```json
  {
    "pipeline_inputs": [{"project_id": "...", "repo_id": "...", "custom_path_id": "...", "direction": "input"}],
    "custom_paths": [{"id": "...", "label": "Character", "path": "Character"}]
  }
  ```
  There used to also be a `"pipeline_outputs"` key here (a separate,
  independently-curated list, written by a now-removed "Set as Pipeline
  Output..." context-menu action) — **removed 2026-07-19**; every
  connection a repo makes is a `"pipeline_inputs"` entry now (see the
  "Pipeline connections" bullet at the top of this file for why).
  `RepoRef.custom_path_id` is looked up against the **target** repo's own
  `custom_paths` entry (`PipelineStore.get_custom_path(target_project_id,
  target_repo_id, custom_path_id)`) — it's meaningless without also
  knowing which repo it belongs to, since ids are only unique within one
  repo's own list, not globally. `custom_path_id=None` is only possible on
  data saved before this field existed; every ref created through
  `CustomPathsSettingsPage`'s "Connect Input Path" section now requires
  picking one. `CustomPath.id` is a stable `uuid4` (not derived from
  `label`) so renaming one doesn't invalidate every `RepoRef` already
  pointing at it. `RepoRef.direction` (added 2026-07-19) defaults to
  `"input"` for any ref saved before the field existed, matching this
  app's arrow behavior prior to that date — see `RepoRef`'s own docstring
  and `project_graph_view.py`'s `ProjectGraphView.load_project`.
  `get_required_repos(project_id, repo_id)` resolves a repo's own direct
  `pipeline_inputs` refs into the actual target `Repo` objects
  (deduped, direct-only — no recursion into each target's own inputs), used
  by `ProjectGraphView.request_active_repo` to auto-clone a repo's pipeline
  dependencies (see that bullet above).
- `custom_paths_settings_page.py` — `CustomPathsSettingsPage`: a
  `CATEGORY_REPO` Settings tab ("Custom Paths"), split into two
  `QGroupBox` sections. "Create Input Path" — add/rename/edit-path/remove
  the active repo's own `CustomPath` catalog (mostly unchanged logic from
  before 2026-07-19, just relabeled, plus a "Browse..." button added
  2026-07-19 next to the add-row's path field — opens
  `QFileDialog.getExistingDirectory` rooted at the active repo's own
  folder and fills in the chosen folder's path relative to it, rejecting
  anything picked from outside the repo since `CustomPath.path` is always
  relative to it). "Connect Input Path" — the active repo's own outgoing
  pipeline connections, moved here 2026-07-19 from the graph node's
  right-click menu: a list of its current `RepoRef`s, each described with
  an arrow glyph and "(Input)"/"(Output)" matching its `direction` (see
  below) plus Edit and Remove buttons — there was previously no way to
  change or remove a connection at all, since graph edges are
  non-interactive — plus a "Connect..." button opening
  `ConnectInputPathDialog` (defined in this same file) — one compact
  window with a repo `QComboBox`, a custom-path `QComboBox`, and an
  Input/Output direction radio-button pair (added 2026-07-19 — see
  `RepoRef.direction`), together replacing the old two-dialog
  `RepoPickerDialog` + `CustomPathPickerDialog` flow. Edit reopens this
  same dialog pre-filled via its `initial_ref` param (also 2026-07-19),
  shared with "Connect..." through `CustomPathsSettingsPage._run_connect_dialog`.
  A target
  repo with zero declared custom paths shows an inline hint instead of a
  separate `QMessageBox` interruption. Same self-resolving-active-repo
  `refresh()` pattern as
  `interface/settings/browser_links_settings_page.py`'s
  `BrowserLinksSettingsPage`. Shows up in `repo_settings_panel.py`'s
  Repository Setting popup automatically (it renders every `CATEGORY_REPO`
  tab generically) — no wiring needed there. A repo with zero entries in
  "Create Input Path" can't be connected to via "Connect Input Path" at
  all — this tab is where a studio admin has to go first before another
  repo can reference it.

## Reading pipeline data from another plugin

As of the `Repo.plugin_data` consolidation, this data lives in each repo's
own `plugin_data["project_editor"]` entry (`core/models.py`'s `Repo`),
inside that repo's project blob (`data/projects/<project_id>.json`) — not
in a separate `PluginConfigStore` file anymore. Read it via
`api.metadata.get_repo_plugin_data(project_id, repo_id, "project_editor")`
(same "agree on the `plugin_id` string, don't import this folder"
convention as before, just backed by `MetadataStore` now instead of a
standalone blob). `plugins/repo_internal/PublishApi/`'s `repo_paths.py`
(Maya-side, reads `repo.plugin_data` straight off the `Repo` object it
already constructs — no `PluginAPI` instance inside Maya's Python),
consumed in turn by `MayaPublisher`'s tickets, is the current real
consumer — read it for a live example. Since a `RepoRef.custom_path_id` is
only meaningful against the **target** repo's own `custom_paths` entry,
resolving a pipeline connection all the way to an actual filesystem path
takes two lookups, not one:

```python
def resolve_pipeline_connection(api, project_id: str, repo_id: str, connection_index: int = 0):
    entry = api.metadata.get_repo_plugin_data(project_id, repo_id, "project_editor")
    connections = entry.get("pipeline_inputs", [])
    if connection_index >= len(connections):
        return None
    ref = connections[connection_index]

    target_entry = api.metadata.get_repo_plugin_data(ref["project_id"], ref["repo_id"], "project_editor")
    custom_path = next(
        (cp for cp in target_entry.get("custom_paths", []) if cp["id"] == ref.get("custom_path_id")), None
    )
    if custom_path is None:
        return None

    target_repo = api.metadata.get_repo(ref["project_id"], ref["repo_id"])
    target_repo_path = Path(api.local_config.workspace_root) / target_repo.local_path
    return target_repo_path / custom_path["path"]
```

**Working here:** stay inside this folder unless the change needs a new
`core/` primitive, or touches `interface/section_registry.py`'s
`UICommandService` (the `open_settings_tab`/`set_active_repo`/`switch_project`
fields this plugin's `_wire` binds). `interface/settings_tab_registry.py`'s
`CATEGORY_PROJECT` and `interface/settings/settings_view.py`'s category
grouping are the one other cross-boundary exception (added 2026-08-03
specifically to give `project_settings_page.py` a real "Project" header
row in the app-level Setting popup) — a genuinely new settings category is
framework-level, not something this plugin's own folder can add by itself.
