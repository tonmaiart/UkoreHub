---
name: ukorehub-plugin
description: Token-scoping discipline for UkoreHub's plugins/ folder (C:\Tonmai\UkoreHub) — when a task names a specific plugin (Explorer, Submit, SoftwareLinker, MayaLauncher, or a new one) or the target path is under plugins/studio/<Name>/ or plugins/local/<Name>/, read and edit ONLY that plugin's own folder — never open a sibling plugin's source as a side effect. Use this for any plugin-specific task even if the user doesn't say "scope" or "context" explicitly; for how plugins are discovered/authored in general see plugins/README.md, and for the plugin/add-on discovery mechanics see the ukorehub-core skill. For the analogous discipline on add-on/<Name>/ (repo-scoped, opt-in extensions — a different concept from plugins/), see the ukorehub-addon skill instead.
---

# Working on a single plugin — stay inside its folder

`plugins/studio/` and `plugins/local/` hold UkoreHub's own always-on
sub-systems, sitting side by side (see `plugins/README.md` for the full
authoring guide). Same reasoning as `add-on/`'s folders (`ukorehub-addon`
skill): reading one plugin has **zero information value** for working on a
different one, even though some plugins are larger, multi-file trees
rather than the single-`plugin.py` shape `software_linker` uses —
`explorer`/`submit` are ordinary multi-file plugins, and
`plugins/studio/maya_launcher/` goes further still, nesting 7 nominally
separate Maya tools (each its own subfolder) inside one plugin — treat that
whole folder as one unit too, not 7 things to read independently, unless
the task explicitly names one of the nested tools. Treat every
`plugins/studio/<Name>/` or `plugins/local/<Name>/` as its own repo for
context-budget purposes.

## Rule

1. Identify the one plugin folder the task is actually about
   (`plugins/studio/<Name>/` or `plugins/local/<Name>/`).
2. Read that plugin's own `README.md` first if it has one — same
   folder-README convention as `core/README.md`/`interface/README.md` (root
   `CLAUDE.md`). Every plugin should have one; if it doesn't, that's worth
   adding while you're in there, not a reason to skip the step.
3. Read and edit only files inside that plugin's own folder. Do not open a
   sibling plugin's `plugin.py`/other files "just in case" — `explorer/`
   and `submit/` are each 6-8 files; don't read one while working on the
   other just because they sit next to each other in `plugins/studio/`.
4. When creating a **new** plugin, don't read an existing one wholesale as
   a copy-paste template. `plugins/README.md` already documents the
   minimum shape (manifest.json + `register(api)`) and the multi-file
   package setup if you need more than one file — read only
   `plugins/studio/software_linker/plugin.py` (single-file reference) or
   `plugins/studio/explorer/plugin.py` (multi-file reference) depending on
   which shape you're copying, not both.

## Cross-plugin data: convention, not source-reading

If a task genuinely needs another plugin's data or behavior, it's almost
always one of two documented conventions — you need the *convention*, not
the other plugin's source:

- **Shared config data**: the `plugin_config_store` convention — two
  plugins independently constructing a `PluginConfigStore` with the same
  `plugin_id` string, so they share a JSON file with no coupling and no
  import (e.g. `plugins/studio/maya_launcher/plugin.py` reading
  `software_linker`'s per-machine `maya.exe` path via
  `api.plugin_config_store("software_linker", shared=False)`). See
  `plugins/README.md`'s "Sharing data with another plugin" section.
- **Cross-plugin UI navigation**: a plain string `SectionRegistry` key
  (e.g. Submit jumping to Explorer's `"repo_browser"` key) plus an
  optional protocol method on the target page (`browse_to_path(path)`,
  same shape as the existing `set_repo()` convention every page
  implements), invoked generically through `SectionHost` — never by
  importing the other plugin's page type. See
  `plugins/studio/submit/plugin.py`'s `_wire` for the working example and
  `plugins/README.md`'s "SectionSpec.wire/SectionHost" section.

Reading the *skill or README section* that documents a convention is fine
and expected — reading another plugin's source to reverse-engineer the same
information is the thing to avoid.

## The one real exception: explicit cross-plugin debugging

If the task is genuinely about an interaction between two plugins (e.g.
"why doesn't Submit's Inspect-in-Explorer jump actually scroll to the
file"), that's a cross-plugin task — read both deliberately, because the
task named both. The rule above is about not defaulting to broad
exploration when the task only named one.

## Not the same as `interface/`'s window folders

Unlike `interface/`'s window folders (`sidebar/`, `login/`, `about/`,
`settings/`) — where sibling files sometimes share patterns worth seeing,
and a task can legitimately need `interface/main_window.py`'s wiring — a
plugin folder is meant to be fully self-contained apart from the
documented `PluginAPI` surface and the two cross-plugin conventions above.
If a plugin task seems to require reading `interface/main_window.py` or
another plugin's internals beyond those conventions, that's a signal the
task has grown beyond "one plugin" — say so rather than reaching across
silently.
