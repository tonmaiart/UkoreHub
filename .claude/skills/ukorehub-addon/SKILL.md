---
name: ukorehub-addon
description: Token-scoping discipline for UkoreHub's add-on/ folder (C:\Tonmai\UkoreHub) — when a task names a specific add-on (MayaLauncher, MayaToolkit, UkoreBrowser, AdvancedSkeleton, MayaNgskin, mGear, BlenderLauncher, UnrealLauncher, DreamwallPicker, or a new one) or the target path is under add-on/<Name>/, read and edit ONLY that add-on's own folder — never open a sibling add-on's source as a side effect. Use this for any add-on-specific task even if the user doesn't say "scope" or "context" explicitly; for how add-ons are discovered/authored in general see add-on/README.md, and for the plugin/add-on discovery mechanics see the ukorehub-core skill.
---

# Working on a single add-on — stay inside its folder

`add-on/` is a flat directory of independent, often-vendored tool trees
sitting side by side (see `add-on/README.md` for the full authoring guide).
Unlike `interface/`'s window folders (`explorer/`, `submit/`, etc.) — where
sibling files often share patterns worth seeing — reading one add-on has
**zero information value** for working on a different one. Treat every
`add-on/<Name>/` as its own repo for context-budget purposes.

## Rule

1. Identify the one add-on folder the task is actually about
   (`add-on/<Name>/`).
2. Read that add-on's own `README.md` first if it has one — same
   folder-README convention as `core/README.md`/`interface/README.md` (root
   `CLAUDE.md`).
3. Read and edit only files inside `add-on/<Name>/`. Do not open another
   add-on's `plugin.py`/scripts "just in case" — some of these trees are
   large (e.g. `DreamwallPicker/maya-scripts/dwpicker/` alone is dozens of
   files; `MayaToolkit/maya-scripts/` bundles a dozen unrelated tools plus
   the vendored `tmlib`/`UkoreMaya` packages).
4. When creating a **new** add-on, don't read an existing one wholesale as
   a copy-paste template. `add-on/README.md` already documents the minimum
   shape; `add-on/MayaLauncher/plugin.py` and `add-on/MayaToolkit/plugin.py`
   are the two reference examples the docs point to explicitly — read only
   the one relevant to the pattern you're copying (a file-opener add-on vs.
   a plain PYTHONPATH-contributor add-on).

## Cross-add-on data: convention, not source-reading

If a task genuinely needs another add-on's data, it's almost always the
shared-`plugin_config_store` convention — two add-ons independently
constructing a `PluginConfigStore` with the same `plugin_id` string, so
they share a JSON file with no coupling and no import. You need the
*convention* (the plugin_id string and JSON shape, both already
documented), not the other add-on's source:

- **Consumer reads another plugin's config**: e.g. MayaLauncher reading
  `software_linker`'s per-machine `maya.exe` path via
  `api.plugin_config_store("software_linker", shared=False)`.
- **Multiple add-ons feed one shared bridge**: e.g. `AdvancedSkeleton`,
  `MayaNgskin`, `MayaToolkit`, `mGear`, and `UkoreBrowser` each write their
  own key into `api.plugin_config_store("maya_launcher_env_bridge",
  shared=True)`'s `contributions` dict at `register()` time — see the
  `ukorehub-maya-launcher-addon` skill's "bridge contract" section for the
  exact shape, and `add-on/README.md`'s "Sharing data with another add-on"
  section for the general pattern.

Reading the *skill or README section* that documents a convention is fine
and expected — reading another add-on's `plugin.py` to reverse-engineer the
same information is the thing to avoid.

## The one real exception: explicit cross-add-on debugging

If the task is genuinely about an interaction between two add-ons (e.g.
"why doesn't MayaLauncher pick up UkoreBrowser's PYTHONPATH contribution"),
that's a cross-add-on task — read both deliberately, because the task
named both. The rule above is about not defaulting to broad exploration
when the task only named one.
