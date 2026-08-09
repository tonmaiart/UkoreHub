# interface/

PySide6 GUI layer for UkoreHub. Builds on `core/` for all data and git
operations — widgets here handle layout, user interaction, and background
`QThread` workers so the UI doesn't block on git/network calls.

Organized by domain rather than by suffix convention: each of `sidebar/`,
`browser_links/`, `repo_settings/`, `settings/` owns one feature
area end-to-end (page + its dialogs + its workers), the same discipline
`plugins/` already enforces for its own folders. GitHub login used to be
its own domain here too (`login/`) but moved out entirely — see the
"GitHub login" note below. Explorer and Submit used
to live here too (`explorer/`, `submit/`) but are now real always-on
plugins under `plugins/core/explorer/` and `plugins/core/submit/` —
registered into `SectionRegistry` via `register(api)` exactly like any
other plugin, not special-cased by `interface/` — see their own
`README.md`s and `core/extensibility/README.md` for how plugin discovery
works.
`about/` was dissolved 2026-07-20 the same way, once its one remaining
file turned out to belong to the Browser Links domain, not an "about"
concept — see `browser_links/README.md`. `shared/` holds the handful of
files genuinely used by 2+ consumers, `interface/` domains and plugins
alike (checked repo-wide before this split, and re-checked whenever a
domain folder is split out — a file with only one real consumer moves into
that consumer's own folder instead, see `shared/README.md`). Everything
left flat at this level is app-wiring/registries with no single domain
home — `main_window.py` is the one file that threads all of it together.

**Working here:** read that domain's own `README.md` first — it's a
faster map than opening every file. Stay inside the one folder the task
names; only cross into `shared/` or a root-level registry when the task
genuinely needs it (e.g. a new page that needs a new `shared/` helper, or
a new top-level section that needs `section_registry.py`).

## Root-level app shell (no single window)

- `main_window.py` — top-level `QMainWindow`: constructs every window's
  page from `SectionRegistry`, wires `sidebar/`'s `Sidebar` (the left-hand
  navigation column — display-only repo thumbnail/name label,
  `SectionTabList`, a `SidebarFooterActionRegistry`-driven footer), drives
  active-repo restore + auto-sync on launch, and owns
  the one shared `QWebEngineProfile`
  (`browser_links/web_engine_profile.py`) every
  `browser_links/browser_link_page.py` tab uses. GitHub login happens
  entirely before this process is even spawned now (see the "GitHub login"
  note below), so `MainWindow` builds the real UI immediately on
  construction — no gate to show/teardown. Every ordinary section is its
  own standalone page in `view_stack`,
  switched to via `Sidebar.navigation_changed` — except a section flagged
  `SectionSpec.persistent=True` (Project Editor), which is never added to
  `view_stack`/`SectionTabList` at all and instead sits permanently docked
  beside `view_stack` in a `QSplitter`, always visible regardless of which
  ordinary section is currently showing.
- `registry_base.py` — `KeyedOrderedRegistry[T]`: shared base for
  `section_registry.py`/`settings_tab_registry.py`/
  `sidebar_footer_action_registry.py` below, each otherwise an identical
  keyed-with-duplicate-rejection, sorted-by-`(order, key)` collection.
  `core/extensibility/file_opener.py`'s `FileOpenerRegistry` (unordered,
  duplicate keys allowed by design) is deliberately not built on this —
  see `registry_base.py`'s own docstring for why forcing it into the same
  shape would fight its design.
- `section_registry.py` / `settings_tab_registry.py` /
  `sidebar_footer_action_registry.py` — open, ordered registries (built on
  `registry_base.py`) that top-level sections, Settings tabs, and Sidebar
  footer widgets register into (built-in and plugin-provided alike). All
  three stay at this root level rather than moving into a domain folder
  because they're cross-cutting infrastructure with no single domain
  owner — and `settings_tab_registry.py` specifically is imported directly
  by `plugins/core/software_linker/plugin.py`, so keeping it at a stable
  path avoids touching that plugin's source.
- `builtin_settings_tabs.py` — constructs the built-in Settings tabs
  (pulling from `settings/`, `browser_links/`, `repo_settings/` —
  Explorer and Submit register themselves from `plugins/core/`, not from
  here) and registers them into `settings_tab_registry.py`, exactly as a
  plugin would register its own.
- `plugin_api.py` — `PluginAPI`, the object passed to every plugin's
  `register(api)` entry point; composes `core/` services with the
  section/settings-tab/sidebar-footer-action registries.
- `theme.py` — color theme definitions (`ThemeColors`, `THEMES`,
  `DEFAULT_THEME_NAME`) and Qt stylesheet generation (`build_stylesheet`).
  Moved here from `core/` since it's a pure UI/presentation concern with no
  data or git logic of its own — `core/storage/config_store.py`'s
  `LocalConfigStore` still needs a default theme name to persist, so it
  keeps its own duplicated `DEFAULT_THEME_NAME` literal rather than
  importing this module (`core/` never depends on `interface/`).
- `theme_apply.py` — applies a `theme.py` stylesheet to the
  `QApplication`; used only by `launcher.py`.
- `project_selector_dialog.py` — `ProjectSelectorDialog`: the mandatory
  pre-`MainWindow` gate for which Project this run is scoped to, shown by
  `launcher.py` (only when `LocalConfigStore.active_project_id` doesn't
  already resolve and there's more than one project to choose from — see
  that module's own comment). Once chosen, Project is fixed for the whole
  run — no page anywhere else can change it again; only a real restart back
  through this same gate can (`plugins/core/project_editor`'s Settings >
  Project "Switch Project...", `MainWindow._request_switch_project`).

## Domain folders

- `sidebar/` — the left navigation column: `ActiveRepoWidget` (display-only
  repo thumbnail + name label — no click-to-open picker; double-clicking a
  node in Project Editor's always-visible graph panel is the only way to
  change the active repo now), `SectionTabList` (a vertical list of section
  tabs + dynamic Browser Link tabs + a trailing Setting row — Project
  Editor is not one of these rows, see below), and a footer built from
  `sidebar_footer_action_registry.py`. See `sidebar/README.md`.
- `browser_links/` — the Browser Link feature end-to-end: its Settings tab
  and its runtime `QWebEngineView` tab, previously split across
  `settings/`/`about/` by UI-kind rather than domain (`about/` itself was
  dissolved once nothing else was left in it). See `browser_links/README.md`.
- `repo_settings/` — the repo-configuration domain (Local Repository,
  Requirements & Plugins) — split out of `settings/` since these two are
  per-repo `CATEGORY_REPO` tabs, a different concern from `settings/`'s
  remaining app/machine-level tabs. See `repo_settings/README.md`.
- `settings/` — the Setting view's remaining app/machine-level tabs: common
  settings, program database, GitHub OAuth client ID, plugin catalog. See
  `settings/README.md`.
- `shared/` — `commit_history.py` (`plugins/core/explorer/` +
  `plugins/core/submit/`) and `image_asset.py`/`widget_helpers.py`
  (used by several domains/plugins) — files with a confirmed multi-consumer
  use, re-checked whenever a domain folder is split out. See
  `shared/README.md`.

## GitHub login

There is no login domain in `interface/` anymore — the old mandatory
in-app gate (`login/`: `LoginOverlay`, `GitHubLoginDialog`,
`GitHubAuthWidget`, `LoginGate`) was deleted entirely. GitHub login (OAuth
device flow) and the token cache now live in `updater.py (UkoreHubLauncher repo)`,
run by the launcher exe (`UkoreHub.exe`) *before* this process is even
spawned — by the time `launcher.py` constructs `GitService`, it just loads
whatever token the launcher already cached (`core/github/token_store.py`)
and calls `git_service.set_github_token(...)`.

`MainWindow` still shows the signed-in username (`Sidebar.account_label`,
pushed from `local_config_store.github_username` in `_start_app`) and still
owns logout (`Settings > Common`'s Logout button, wired to
`_on_logout_requested`) — but logout here doesn't tear down any in-app UI
(there isn't any): it clears the cached token/username via `TokenStore`
and relaunches `UkoreHub.exe`, whose own login step shows the GitHub login
screen again. `MainWindow` holds a `TokenStore` reference for exactly this
one purpose — it never reads a token to authenticate anything itself.

## Testing conventions

Qt widgets are **never constructed inside pytest tests**: registries are
tested with `page_factory=lambda: None`, verifying registry bookkeeping
only (registration, duplicate-key rejection, lookup/ordering), never
`QWidget` behavior. For anything that genuinely needs a live `QApplication`
+ `MainWindow` (e.g. verifying a new registry threads all the way through
without crashing), use a throwaway headless smoke-test script instead of a
pytest test — **and always point it at a scratch copy of `data/`, never
the real one** (see root `CLAUDE.md`'s "Headless/smoke testing" section):
construct `QApplication`, all registries, and `MainWindow` without calling
`app.exec()`. `MainWindow` has no login gate of its own anymore (see the
"GitHub login" note above) — it always builds the real UI immediately, so
there's nothing to pre-seed/skip there; it does still take a `token_store`
constructor argument (any `TokenStore` pointed at the scratch `data/` copy
works, even with no token ever saved to it — it's read only if the user
clicks Logout). End the script with
`sys.stdout.flush(); os._exit(0)` — `os._exit` is required because Qt/
Windows can hang on normal process teardown after `QApplication` is
destroyed without an explicit `app.quit()`; without the `os._exit(0)` the
script can look hung even though it actually finished. Note that
constructing a real `QWebEngineProfile`/`QWebEngineView` can itself be slow
to spin up cold (Chromium subsystem init) — a plain
`importlib.import_module` sweep over every file is a faster, sufficient
check for import-path correctness alone (no GUI needed).
