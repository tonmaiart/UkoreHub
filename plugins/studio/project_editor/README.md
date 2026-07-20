# plugins/studio/project_editor/

Node-graph editor for the Project/Repo registry — a `SectionRegistry`
section (`persistent=True`), meaning it's never a sidebar row and never a
switchable `view_stack` page: it's docked permanently beside `view_stack`
in a `QSplitter` (see `interface/main_window.py`'s `_build_main_ui`), always
visible no matter which ordinary section (Explorer/Submit/About/Settings)
is currently showing. Renamed from `pipeline_architect` on 2026-07-15, when
this stopped being a buried Settings > Developer tab (`ProjectDataEditorPage`,
a CRUD tree); briefly a full-width switchable section the same day, then
changed again the same day to the always-visible docked panel it is now.
Three things bundled into one plugin (originally two, before the
2026-07-19 CustomPath addition):

1. **Project/Repo CRUD** — Add/Rename/Delete Project (top bar), Add/Rename/
   Delete/Thumbnail Repo (node context menu) — same `core/store.py`
   `MetadataStore` calls the old tree page made, just triggered from graph
   UI instead of tree rows/buttons.
2. **Pipeline connections** — which other repos a given repo has
   connected to, via Repository Setting's "Custom Paths" tab, "Connect
   Input Path" section (moved there 2026-07-19 from a node's right-click
   menu — see `custom_paths_settings_page.py` below). Still not part of
   `core/models.py`'s `Repo` — stored
   in this plugin's own `PluginConfigStore` file
   (`data/plugins/studio/project_editor.json`, `shared=True`) so other
   plugins can read it without `core/` needing to know the concept exists.
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

**`manifest.json` sets `"core": true`** (`PluginManifest.core`, added
2026-07-15). This was originally load-bearing back when this plugin
registered a normal switchable section — `MainWindow._apply_plugin_visibility`
force-shows a core plugin's section regardless of a repo's restricted
`active_plugin_ids` allowlist, since hiding the only way to switch the
active repo would be a lockout, not a preference. Now that this section is
`persistent=True` instead (never added to `_section_view_index`/
`SectionTabList` at all — see the top of this file), `_apply_plugin_visibility`
never gates it either way, so the `core` flag is currently redundant for
*this* plugin specifically — kept because (a) it costs nothing, (b) it's
still what `interface/settings/enable_plugin_page.py` reads to render this
plugin's row checked-and-disabled (an honest signal to a manager that
toggling it does nothing), and (c) it'd matter again immediately if this
plugin were ever changed back to a normal section.

## Files

- `manifest.json` — plugin id `project_editor` (renamed from
  `pipeline_architect`; the shared data file at
  `data/plugins/studio/project_editor.json` was `git mv`'d in the same
  commit as the folder, so no migration step is needed).
- `plugin.py` — `register(api)`: constructs `PipelineStore` and one
  `ProjectEditorPage` instance, registers it via `api.register_section(...)`
  with `wire=_wire` — `_wire` calls `page.bind_set_active_repo(host.set_active_repo)`,
  the `SectionHost` field added specifically for this plugin (see
  `interface/section_registry.py`) so a node click can trigger a real
  active-repo switch without the page holding a `MainWindow` reference.
  Also reads `api.settings_tab_registry` (a new read-access property on
  `PluginAPI`, mirroring the existing `api.file_opener_registry` pattern)
  so the Repository Setting popup can enumerate `CATEGORY_REPO` tabs
  generically.
- `dialogs.py` — `ProjectDialog`/`RepoDialog`/`RequirementsTreeWidget`
  (the checkable Program/Add-on tree `RepoDialog` embeds for repo
  creation) — moved in from `interface/shared/dialogs.py` 2026-07-20 once
  a repo-wide grep confirmed this plugin was the only real consumer left;
  imported as a normal sibling module (`from
  plugins.studio.project_editor.dialogs import ...`, the same
  real-package convention `plugins/README.md`'s "Multi-file plugins"
  section documents), not a relative import. Used by
  `project_graph_view.py` (`RepoDialog`, node context menu Add/Edit Repo)
  and `project_editor_page.py` (`ProjectDialog`, top-bar Add/Rename
  Project).
- `project_editor_page.py` — `ProjectEditorPage`: the section's top-level
  widget. Top bar = project `QComboBox` (+ "Add New Project..." as the
  trailing item), Rename/Delete Project buttons, Add Repo button. Below
  that, `ProjectGraphView` full width — no right panel here anymore (moved
  to a popup dialog 2026-07-15, see `repo_settings_panel.py` below).
  Implements the standard `set_repo()` page protocol purely to keep the
  graph's active-node highlight in sync when the active repo changes
  elsewhere — this page only *reacts* to active-repo changes, it never
  receives a command to make one (that only happens via a node click,
  through `bind_set_active_repo`).
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
  `setBackgroundBrush`-ed to `_GRAPH_BACKGROUND_COLOR_HEX` (`#141517`,
  added 2026-07-20), darker than the app-wide theme background it would
  otherwise inherit, so the graph reads as its own recessed canvas.
  - **Node visuals**: paints the repo's thumbnail fill-cropped (same crop
    math as `interface/login/repo_picker.py`'s `_RepoCard.paintEvent`) plus
    a name label; border/overlay react to two independent flags — `is_active`
    (thick accent border) and `_is_hovered` (medium accent-hover border +
    a subtle white wash over the thumbnail, set from `hoverEnterEvent`/
    `hoverLeaveEvent` — `setAcceptHoverEvents(True)` plus the existing
    `PointingHandCursor` together carry the "this is clickable" affordance).
    A clone-status badge (`_clone_status_icon`, added 2026-07-20) paints
    top-right on every node — `data/icons/icons8-connected-30.png` if
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
    `plugins/studio/PublishApi/maya-scripts/PublishApi/repo_paths.py`'s
    `get_active_repo`/`resolve_ref`) first and shows a one-time "hasn't
    been cloned yet, clone and switch now?" confirmation before the very
    first clone — an already-cloned repo switches immediately with no
    prompt.
  - **Right-click context menu**: "Repository Setting..." (opens
    `open_repo_settings`, see `repo_settings_panel.py` below — this one
    doesn't touch the scene, so it's called directly, no `QTimer` deferral
    needed), then rename/thumbnail/delete — every mutation delegated back
    to `ProjectGraphView`'s own methods rather than duplicated per node.
  - **Bottom-right overlay HUD** (`ProjectGraphView._overlay`, a plain
    child `QLabel` positioned by hand in `resizeEvent`/`_position_overlay`
    rather than a layout, so it floats over the viewport without
    scrolling/zooming with the graph content — added 2026-07-20):
    active project name, active repo name, `Repo.last_synced`,
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
- `repo_settings_panel.py` — `RepoSettingsPanel`: every `CATEGORY_REPO`
  `SettingsTabSpec`, read off `SettingsTabRegistry.ordered()` and rendered
  with the **exact same tab-list + `QStackedWidget` template**
  `interface/settings/settings_view.py`'s `SettingsView` uses (a
  `QListWidget` of tab labels on the left switching a `QStackedWidget` on
  the right, every page constructed eagerly) — fully generic, so any
  plugin's own `CATEGORY_REPO` settings tab shows up here automatically
  with zero edits to this file. Changed 2026-07-19 away from a column of
  collapsible accordion sections (`_CollapsibleSection`, now removed) so
  this popup reads as one consistent settings UI with the program's own
  Setting view. Changed again 2026-07-20 to group tabs under two
  non-selectable category header rows, same `settings_view.py`
  General/Developer grouping mechanic: "Repository" (a hardcoded key set —
  Local Repository, Custom Paths, Enable Plugin, Browser) and "Plugins"
  (everything else registered under `CATEGORY_REPO`, i.e. every
  plugin-contributed tab) — this is also when the "Project Status" tab was
  removed entirely (no longer needed). This is also why
  `interface/settings/settings_view.py`
  stopped rendering `CATEGORY_REPO` at all (see that file) — a single
  source of UI for repo settings. `RepoSettingsDialog` wraps a fresh
  `RepoSettingsPanel` in a `QDialog`, constructed on every open (no state
  carried between opens, same convention `interface/builtin_settings_tabs.py`
  documents for Settings tabs) — this used to be a permanent panel beside
  the graph, moved into this popup 2026-07-15, opened via a node's
  right-click "Repository Setting..." (`ProjectGraphView.open_repo_settings`).
  Always reflects the currently **active** repo, not necessarily whichever
  node was right-clicked — every tab inside self-resolves the active repo
  from `local_config_store`, the same convention each one already used
  inside Settings; left-click a node first (switches the active repo) if
  you want the two to match.
- `pipeline_store.py` — `PipelineStore`/`RepoRef`/`CustomPath`. Full JSON
  shape (as of 2026-07-19):
  ```json
  {
    "projects": {
      "<project_id>": {
        "repos": {
          "<repo_id>": {
            "pipeline_inputs": [{"project_id": "...", "repo_id": "...", "custom_path_id": "...", "direction": "input"}],
            "custom_paths": [{"id": "...", "label": "Character", "path": "Character"}]
          }
        }
      }
    }
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

Don't import anything from this folder — construct your own
`PluginConfigStore` with the same id string (the "convention, not import"
pattern `plugins/README.md`'s "Sharing data with another plugin" section
documents, same as `maya_launcher` reading `software_linker`'s config).
`ModelPublisher`/`RigPublisher`/`AnimationPublisher`'s own Repo Studio
Setting tabs and `plugins/studio/PublishApi/`'s `repo_paths.py` (Maya-side,
constructs the store straight off disk instead — no `PluginAPI` instance
inside Maya's Python) are the current real consumers — read either for a
live example. Since a `RepoRef.custom_path_id` is only meaningful against
the **target** repo's own `custom_paths` entry, resolving a pipeline
connection all the way to an actual filesystem path takes two lookups,
not one:

```python
def resolve_pipeline_connection(api, project_id: str, repo_id: str, connection_index: int = 0):
    store = api.plugin_config_store("project_editor", shared=True)
    entry = store.get("projects", {}).get(project_id, {}).get("repos", {}).get(repo_id, {})
    connections = entry.get("pipeline_inputs", [])
    if connection_index >= len(connections):
        return None
    ref = connections[connection_index]

    target_entry = store.get("projects", {}).get(ref["project_id"], {}).get("repos", {}).get(ref["repo_id"], {})
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
`SectionHost`/`SectionSpec.persistent`, `interface/plugin_api.py`'s
`settings_tab_registry` wiring, or `interface/main_window.py`'s persistent-
panel docking in `_build_main_ui` (all added specifically for this plugin).
