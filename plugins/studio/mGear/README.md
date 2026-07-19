# plugins/studio/mGear/

mGear — vendored [mGear](https://www.mgear-framework.com/) rigging
framework for Maya (`maya-modules/mGear.mod` + its version-aware payload,
`mgear-custom-component/` for Shifter component discovery). Unchanged
internal layout from the original `add-on/mGear/` (moved to
`plugins/studio/maya_launcher/mGear/` during the 2026-07-14 consolidation,
then split back out to its own top-level plugin here on 2026-07-19 — see
`plugins/studio/maya_launcher/README.md` for why).

Like every other Maya tool plugin here, this does **not** launch Maya
itself and has no UI of its own inside UkoreHub — `plugin.py`'s
`register(api)` writes `MAYA_MODULE_PATH` (`maya-modules/`) and
`MGEAR_SHIFTER_COMPONENT_PATH` (`mgear-custom-component/`) contributions
into `plugins/studio/maya_launcher/`'s shared `maya_launcher_env_bridge`
`PluginConfigStore`, read and merged by that plugin's `open_maya_file`
when it actually launches Maya. No direct import relationship with
`maya_launcher` — just the shared `PluginConfigStore` id convention (see
that plugin's README for the full bridge shape). `RepoToolsStore` (owned
by `maya_launcher`) is what lets a studio admin disable this tool per-repo;
this plugin always contributes unconditionally.
