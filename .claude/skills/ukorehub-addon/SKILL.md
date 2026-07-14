---
name: ukorehub-addon
description: Token-scoping discipline for UkoreHub's add-on/ folder (C:\Tonmai\UkoreHub) — when a task names a specific add-on or the target path is under add-on/<Name>/, read and edit ONLY that add-on's own folder — never open a sibling add-on's source as a side effect. Use this for any add-on-specific task even if the user doesn't say "scope" or "context" explicitly; for how add-ons are discovered/authored in general see add-on/README.md, and for the plugin/add-on discovery mechanics see the ukorehub-core skill. Note: as of 2026-07-14, add-on/ has no folders (its previous entries — MayaLauncher and 7 Maya env-contributor add-ons — were consolidated into plugins/studio/maya_launcher/; see that plugin's README and the ukorehub-plugin skill) — this skill's rule still applies the next time a new add-on is created.
---

# Working on a single add-on — stay inside its folder

`add-on/` is a flat directory of independent, often-vendored tool trees
sitting side by side (see `add-on/README.md` for the full authoring guide).
Unlike `interface/`'s window folders — where sibling files often share
patterns worth seeing — reading one add-on has **zero information value**
for working on a different one. Treat every `add-on/<Name>/` as its own
repo for context-budget purposes.

## Rule

1. Identify the one add-on folder the task is actually about
   (`add-on/<Name>/`).
2. Read that add-on's own `README.md` first if it has one — same
   folder-README convention as `core/README.md`/`interface/README.md` (root
   `CLAUDE.md`).
3. Read and edit only files inside `add-on/<Name>/`. Do not open another
   add-on's `plugin.py`/scripts "just in case" — some of these trees can be
   large, vendored tool trees (a whole third-party tool's own script
   folder, easily dozens to hundreds of files).
4. When creating a **new** add-on, don't read an existing one wholesale as
   a copy-paste template. `add-on/README.md` already documents the minimum
   shape (`manifest.json` + `plugin.py`'s `register(api) -> None`) — if
   another add-on currently exists that matches the pattern you're copying
   (a file-opener add-on vs. a plain env/PYTHONPATH-contributor add-on),
   read only that one, not several.

## Cross-add-on data: convention, not source-reading

If a task genuinely needs another add-on's (or plugin's) data, it's almost
always the shared-`plugin_config_store` convention — two independently
constructing a `PluginConfigStore` with the same `plugin_id` string, so
they share a JSON file with no coupling and no import. You need the
*convention* (the plugin_id string and JSON shape, both already
documented), not the other add-on's source. See `add-on/README.md`'s
"Sharing data with another add-on" section and `plugins/README.md`'s
"Sharing data with another plugin" section (identical convention on both
sides) — `plugins/studio/maya_launcher/plugin.py` reading
`plugins/studio/software_linker`'s per-machine executable path is the
current live worked example of the "consumer reads another's config" half
of this pattern.

## The one real exception: explicit cross-add-on debugging

If the task is genuinely about an interaction between two add-ons, that's
a cross-add-on task — read both deliberately, because the task named both.
The rule above is about not defaulting to broad exploration when the task
only named one.
