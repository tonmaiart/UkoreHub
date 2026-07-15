# plugins/studio/pipeline_architect/

Two things bundled into one plugin:

1. **Project Data Editor** — full CRUD for the Project/Repo registry
   (`core/store.py`'s `MetadataStore`): Add/Edit/Delete Project, Add/Edit/
   Delete Repo. Moved here **verbatim** from the former built-in
   `interface/settings/project_data_editor_page.py` (2026-07-15) — same
   class body, same tree, same buttons.
2. **Pipeline inputs/outputs** — a new, separate metadata concept: which
   repos feed *into* a given repo, and which repos it feeds *out to*. Not
   part of `core/models.py`'s `Repo` — stored in this plugin's own
   `PluginConfigStore` file instead (`data/plugins/studio/pipeline_architect.json`,
   `shared=True`), specifically so other plugins can read it later without
   `core/` needing to know this concept exists at all.

## ⚠️ Deliberate architecture tradeoff

Project Data Editor used to be a built-in `interface/settings/` page —
moving it into a plugin means **creating/renaming/deleting a Project or
Repo now depends on this plugin loading successfully.** Every other
plugin/add-on failure is isolated (`core/extensibility/loader.py` never
raises — a broken one is recorded as a `PluginLoadFailure` and skipped, so
one broken plugin can't take the app down); this is the one exception,
accepted deliberately by the studio rather than overlooked. The long-term
plan is a "core plugin" concept (a plugin flagged as load-bearing, distinct
from an optional one) to formalize this — not implemented yet, this is
just the split itself. If you're touching plugin load-order/failure
handling later, remember this plugin is the one place where a load failure
has a real, visible consequence (no way to add/edit/delete repos at all
until it's fixed).

## Files

- `manifest.json` — plugin id `pipeline_architect`.
- `plugin.py` — `register(api)`: constructs `PipelineStore` from
  `api.plugin_config_store(PLUGIN_ID, shared=True)` and `ProjectDataEditorPage`,
  registers the page as a `CATEGORY_DEVELOPER` Settings tab (same slot the
  old built-in tab used — order 10, label "Project Data Editor"). Reads
  `api.addon_store`/`api.addon_catalog` — both added to `interface/plugin_api.py`'s
  `PluginAPI` specifically for this move (the CRUD page's "Add Repo" flow
  needs the add-on catalog for its Requirements/Add-ons picker,
  `interface/shared/dialogs.py`'s `RepoDialog`).
- `editor_page.py` — `ProjectDataEditorPage`: the CRUD tree + buttons
  (unchanged logic) plus a "Pipeline" panel shown whenever a **repo** row
  (not a project row) is selected in the tree — Inputs/Outputs lists with
  Add (reuses `interface/login/repo_picker.py`'s `RepoPickerDialog`, the
  same dialog `MainWindow._on_select_repo` and the Explorer pin feature
  already reuse) / Remove Selected. Self-persists immediately, no Save
  button. The two lists are independently curated — listing repo B as an
  input of A does **not** automatically add A as an output of B.
- `pipeline_store.py` — `PipelineStore`/`RepoRef`: wraps the single
  `"projects"` key inside this plugin's `PluginConfigStore` JSON file. Full
  shape:
  ```json
  {
    "projects": {
      "<project_id>": {
        "repos": {
          "<repo_id>": {
            "pipeline_inputs": [{"project_id": "...", "repo_id": "..."}],
            "pipeline_outputs": [{"project_id": "...", "repo_id": "..."}]
          }
        }
      }
    }
  }
  ```
  Each entry is a `{project_id, repo_id}` pair (not a bare repo id) —
  matches how every other cross-repo reference in this codebase is stored
  (`ExplorerPin`, `local_config_store.active_project_id`/`active_repo_id`),
  rather than relying on `Repo.id` UUIDs being implicitly globally unique.

## Reading pipeline data from another plugin

Don't import anything from this folder — construct your own
`PluginConfigStore` with the same id string (the "convention, not import"
pattern `plugins/README.md`'s "Sharing data with another plugin" section
documents, same as `maya_launcher` reading `software_linker`'s config):

```python
def get_repo_pipeline_paths(api, project_id: str, repo_id: str):
    store = api.plugin_config_store("pipeline_architect", shared=True)
    entry = store.get("projects", {}).get(project_id, {}).get("repos", {}).get(repo_id, {})
    input_paths = []
    for ref in entry.get("pipeline_inputs", []):
        repo = api.metadata.get_repo(ref["project_id"], ref["repo_id"])
        input_paths.append(Path(api.local_config.workspace_root) / repo.local_path)
    return input_paths, entry.get("pipeline_outputs", [])
```

**Working here:** stay inside this folder unless the change needs a new
`core/` primitive or touches `interface/plugin_api.py`'s `addon_store`/
`addon_catalog` wiring.
