# plugins/studio/PublishApi/

Shared Maya-side library — the single source of truth for "where does a
publish go" and "how do I create the next version folder" — consumed by
`ModelPublisher`, `RigPublisher`, `AnimationPublisher`, and `UkoreBrowser`
(its `core/repo_context.py`). Has no UI of its own and does not launch
Maya; like every other Maya tool plugin here, it exists purely to
contribute a `PYTHONPATH` entry to `plugins/studio/maya_launcher/`'s
shared `maya_launcher_env_bridge` `PluginConfigStore`.

Added 2026-07-19, alongside splitting the original `UkorePublisher` plugin
into `ModelPublisher`/`RigPublisher`/`AnimationPublisher` — see
`plugins/studio/maya_launcher/README.md` for the bridge convention this
follows, and each Publisher plugin's own README for how it's actually used.

**Never gated by `plugins/studio/maya_launcher/`'s per-repo `RepoToolsStore`
toggle** — unlike every other tool plugin listed above, this one has no
legitimate reason to ever be disabled per-repo (it's pure infrastructure,
not an artist-facing feature), and `maya_launcher/plugin.py`'s
`open_maya_file` force-includes its bridge contribution regardless of what
a repo's stored tool list says. See that plugin's README's "Per-repo tool
toggle" section for why — this was added after a repo whose stored list
predated this plugin's existence hit `ModuleNotFoundError: No module named
'PublishApi'` inside `UkoreBrowser/core/repo_context.py`.

## Files

- `manifest.json` — plugin id `publish_api`, entry point `plugin.py`.
- `plugin.py` — `register(api)`: contributes `maya-scripts/` **and**
  `api.app_root` to the shared bridge (same reason
  `plugins/studio/UkoreBrowser/plugin.py` contributes `api.app_root` too —
  so `import core.store`/`core.paths`/`core.extensibility.config_store`
  resolve inside Maya's Python).
- `maya-scripts/PublishApi/repo_paths.py`:
  - `find_ukorehub_root()` — locates the UkoreHub install root from this
    file's own position on disk (`parents[5]` — see the UkoreBrowser
    plugin's own `repo_context.py` for the sibling version of this trick,
    one level deeper because of its extra `core/` subfolder).
  - `get_active_repo()` — `(project, repo, repo_path)` for whichever repo
    UkoreHub currently has active, constructing `LocalConfigStore`/
    `MetadataStore` straight off disk (Maya's Python has no `PluginAPI`
    instance to go through).
  - `get_pipeline_refs()` — every `{"project_id", "repo_id",
    "custom_path_id"}` dict the active repo has connected to via "Connect
    Pipeline Input Path..." in Project Editor, read directly from
    `data/plugins/studio/project_editor.json`. (There used to be a
    `direction="inputs"|"outputs"` parameter here, reading two separate
    lists — removed 2026-07-19 alongside Project Editor's own "Set as
    Pipeline Output..." action; there's only one list now, see
    `plugins/studio/project_editor/README.md`.)
  - `resolve_ref(ref)` — a pipeline ref (or any `{"project_id","repo_id"}`
    dict) resolved to `(project, repo, repo_path)`.
  - `get_custom_paths(project_id, repo_id)` / `get_custom_path(project_id,
    repo_id, custom_path_id)` — a repo's own declared `CustomPath` catalog
    (`{"id","label","path"}`, `path` relative to that repo's root — see
    `plugins/studio/project_editor`'s `custom_paths_settings_page.py`) and
    a single lookup by id.
  - `get_chosen_output_ref(tool_id)` — the pipeline connection a studio
    admin picked as `tool_id`'s (e.g. `"model_publisher"`) publish
    destination on the active repo, via that tool's own Repo Studio
    Setting tab (see each Publisher plugin's README) — read from that
    tool's own `data/plugins/studio/<tool_id>.json`, key
    `"repo_publish_target"`. `None` if nothing's been chosen yet for this
    repo.
  - `get_publish_root(tool_id)` — **the** publish destination: the active
    repo's pipeline connection chosen for `tool_id` (falling back to the
    repo's only declared connection if there's exactly one — no ambiguity
    to resolve, so the common case needs no per-tool configuration at
    all), resolved to `<target repo's cloned path>/<its chosen
    CustomPath's own relative path>`. Raises `RuntimeError` (no active
    repo / no pipeline connection declared / ambiguous choice with
    multiple connections and none picked / target repo not cloned yet /
    chosen CustomPath no longer exists) rather than ever falling back to
    a filesystem-path convention — callers show the message to the
    artist.
- `maya-scripts/PublishApi/versioning.py`:
  - `make_sure_folder_exist(path)` — trivial `os.makedirs` wrapper.
  - `get_new_version(base_dir)` — next available `vNNN` integer under a
    directory, by scanning its immediate subfolders.
  - `get_version_directory(publish_root, subfolder, version=None)` —
    creates and returns `(version_dir, version_number)` for
    `<publish_root>/<subfolder>/vNNN/`. `publish_root` is always
    `repo_paths.get_publish_root(tool_id)`'s result, never something else
    — as of 2026-07-19 that result already has the studio-chosen
    CustomPath's own relative path baked in, so there's no separate
    "custom path" segment to join here anymore (there used to be, back
    when the artist typed it into a Publisher plugin's own free-text
    field — removed the same day, see each Publisher plugin's README).
    `subfolder` is the ticket/department subfolder (e.g. "Proxy", "Hi").

## Why this replaces the old `share`/`publish` path-swap convention

Before this plugin existed, `UkorePublisher`'s publish root was derived by
string-swapping `.../share/...` for `.../publish/...` in the current Maya
scene's own file path (`UkoreMaya/core/Logic.py`'s `convert_to_publish_path`,
still present in `plugins/studio/MayaToolkit/` — unrelated tools may still
use it, this plugin just doesn't). That convention had no connection to
UkoreHub's own Project/Repo/pipeline model at all — it only worked because
every studio scene file happened to sit under a folder literally named
`share`. `get_publish_root(tool_id)` above resolves the destination from
Project Editor's actual declared pipeline **connection** for the active
repo instead (e.g. `RigTeam`'s Maya scene resolves to wherever
`RigPublish` — the repo it connected to — is cloned, further scoped down
to whichever `CustomPath` that connection points at, e.g.
`RigPublish/Character`), which is correct regardless of where the
artist's local clone happens to live on disk, and keeps publishing in
sync with whatever the studio has declared in Project Editor's graph.

## Working on this plugin

Read/edit only files under this folder unless the change is specifically
about how `ModelPublisher`/`RigPublisher`/`AnimationPublisher`/`UkoreBrowser`
*consume* this API (a genuine cross-plugin task, not a reason to read them
by default) — see the `ukorehub-plugin` skill.
