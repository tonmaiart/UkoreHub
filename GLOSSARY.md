# GLOSSARY.md

Casual/colloquial terms used when talking about UkoreHub, mapped to the
actual feature or file each one refers to. Added 2026-07-20 after "ปุ่ม
setting ของ program" (meaning the app's own Setting button) got misread as
the Program Database feature — consult this before assuming a casual term
matches the nearest-sounding code symbol or feature name; several terms
below are easy to misread that way.

## "The program" / "program's setting"

When used casually (e.g. "ปุ่ม setting ของ program"), "program" usually
means **UkoreHub itself**, not the Program Database feature below. "The
program's Setting button" = the app-level **Setting** popup, opened via
the icon-only Setting button in Sidebar's footer
(`interface/sidebar/sidebar.py`'s `setting_button`, positioned right after
the GitHub username/avatar). Wired through
`MainWindow._on_settings_requested` -> `interface/settings/settings_view.py`'s
`SettingsDialog`.

**Not to be confused with:**

- **Program Database** — Settings > Developer > "Program Database", a CRUD
  list of pipeline software (Maya, Nuke, ...) a repo can declare as a
  requirement (`core/program_store.py`,
  `interface/settings/program_database_page.py`). "Program" here means one
  catalog entry, not the app.
- **Repository Setting** — a *per-repo* settings popup, opened from
  Project Editor's node right-click menu ("Repository Setting..."), not
  the sidebar's app-level Setting button. See
  `plugins/studio/project_editor/repo_settings_panel.py`. As of
  2026-07-20 its tabs are grouped under two headers — "Repository" (Local
  Repository, Custom Paths, Enable Plugin, Browser) and "Plugins" (every
  plugin-contributed `CATEGORY_REPO` tab) — matching the app-level
  Setting popup's own General/Developer grouping.

## "Viewgraph"

Not a name used anywhere in the codebase itself — refers to Project
Editor's node-graph view: the `QGraphicsView` showing every repo in a
project as a node, with pipeline connections drawn as edges between them.
Code name: `ProjectGraphView`
(`plugins/studio/project_editor/project_graph_view.py`), hosted inside
`ProjectEditorPage`. Always visible, docked beside whichever section is
currently showing (`SectionSpec.persistent=True`) — not a page you
navigate to via the sidebar.

## Custom Path — "Input" vs "Output"

Two related-but-distinct things both get called "Custom Path", and the
in-app button labels don't map cleanly onto "Input"/"Output" the way
you'd expect:

- **A repo's own declared Custom Path(s)** — named locations *within*
  that repo that other repos can point at (`pipeline_store.py`'s
  `CustomPath`). Managed under Repository Setting > Custom Paths >
  **"Create Input Path"** — despite the button's name, these are the
  locations this repo *exposes* for others to connect to, not something
  it consumes.
- **A pipeline connection** — this repo pointing at *another* repo's
  declared Custom Path (`pipeline_store.py`'s `RepoRef`, list returned by
  `PipelineStore.get_inputs`). Managed under Repository Setting > Custom
  Paths > **"Connect Input Path"**. Each connection carries its own
  `direction` field ("input" or "output", purely cosmetic — only affects
  which end of the drawn graph edge gets the arrowhead), and this is the
  actual "Input"/"Output" split shown in the Viewgraph's bottom-right
  overlay HUD (`ProjectGraphView._refresh_overlay`).

## Plugin vs Add-on vs Program

Already documented in root `CLAUDE.md`'s "Project layout" section — see
that instead of re-deriving from context: **Plugins** (`plugins/`) are
UkoreHub's own always-on sub-systems; **Add-ons** (`add-on/`) are per-repo
opt-in extensions; a **Program** (`core/program_store.py`) is neither —
it's a catalog entry for external pipeline software (Maya, Nuke, ...) a
repo can require.

## Repo About (removed)

Referenced in old conversations as "About tab" or (mistakenly) "Plug-ins
about" — a per-repo info page (`interface/about/repo_about_page.py`,
"About" + "Requirement" sub-tabs) removed entirely 2026-07-20, no longer
needed. If asked about it: it no longer exists, and there is currently no
UI for editing a repo's required Programs, nor a host for add-on
per-repo panels (`RepoAddonPanelRegistry` — see `add-on/README.md`).
