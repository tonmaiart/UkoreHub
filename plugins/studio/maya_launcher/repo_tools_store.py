from __future__ import annotations

from core.extensibility.config_store import PluginConfigStore

_KEY = "repo_disabled_tools"
# The old (pre-2026-07-19) storage key/shape: {"<project_id>:<repo_id>":
# [enabled_tool_id, ...]} — an opt-IN list. Read-only now, for one-time
# migration of any entry that predates the switch to opt-out storage below.
_LEGACY_ENABLED_KEY = "repo_enabled_tools"
# The exact TOOL_IDS the pre-2026-07-19 Settings > Maya Launcher checkbox
# list ever offered (plugins/studio/maya_launcher/tools.py, since deleted)
# — the only tool ids a legacy repo_enabled_tools entry could possibly have
# recorded a real "explicitly disabled" decision about. Used only by
# _migrate_legacy_entry() below; never add a new tool id to this constant —
# see that method's docstring for why.
_LEGACY_TOOL_IDS = frozenset(
    {
        "advanced_skeleton",
        "maya_ngskin",
        "maya_toolkit",
        "mgear",
        "ukore_browser",
        "dreamwall_picker",
        "studio_library",
    }
)


class RepoToolsStore:
    """Per-repo enable/disable state for whichever Maya tool plugins are
    currently contributing to the shared maya_launcher_env_bridge (see
    plugins/studio/maya_launcher/README.md) — owned entirely by this plugin
    instead of the generic Repo.enabled_addon_ids mechanism. Backed by a
    single shared PluginConfigStore (api.plugin_config_store("maya_launcher",
    shared=True)), keyed "<project_id>:<repo_id>" -> [tool_id, ...].

    Stores the DISABLED set (opt-out), not the enabled set — changed
    2026-07-19 after a real ModuleNotFoundError for a brand-new tool
    (RigPublisher, then PublishApi before it) on a repo whose entry
    predated that tool's existence. The old opt-in shape had no way to
    distinguish "explicitly unchecked" from "didn't exist yet when this
    repo's list was last saved," so any repo with an existing customized
    list silently excluded every tool added after that point forever,
    requiring someone to notice and manually re-check it in Settings. With
    opt-out storage, a brand-new tool id is simply never in any repo's
    disabled set until someone actually unchecks it, so it defaults to
    enabled everywhere — matching the "no entry = everything enabled"
    behavior this store has always documented, but now true for tool ids
    added after a repo was first customized too, not just for repos with
    no customization at all.

    Unlike the pre-2026-07-19 version, this store no longer knows the set
    of tool ids itself (that used to be a hardcoded TOOL_IDS list) — every
    caller passes `all_tool_ids`, read live off the bridge by plugin.py,
    since the known tool set is now whatever independently-loaded plugin
    happened to contribute this app run."""

    def __init__(self, config_store: PluginConfigStore):
        self._config_store = config_store

    @staticmethod
    def _repo_key(project_id: str, repo_id: str) -> str:
        return f"{project_id}:{repo_id}"

    def _disabled_ids_for(self, key: str) -> list[str] | None:
        """The stored disabled-id list for this repo key, migrating a
        legacy repo_enabled_tools entry in place (write-through, so this
        only runs once per repo) if there's no repo_disabled_tools entry
        yet. Returns None if this repo has never been customized at all
        under either shape."""
        repo_map = self._config_store.get(_KEY, {})
        if key in repo_map:
            return list(repo_map[key])

        legacy_map = self._config_store.get(_LEGACY_ENABLED_KEY, {})
        if key not in legacy_map:
            return None

        return self._migrate_legacy_entry(key, legacy_map[key])

    def _migrate_legacy_entry(self, key: str, legacy_enabled_ids: list[str]) -> list[str]:
        """Converts one legacy opt-in entry to the new opt-out shape:
        disabled = every tool id the old Settings UI could have possibly
        offered (_LEGACY_TOOL_IDS) that ISN'T in the old enabled list —
        i.e. exactly the tools someone actually unchecked back when that
        was the only kind of tool that existed. Any tool id added after
        2026-07-19 was never part of that old universe, so it can never
        end up in the migrated disabled set — it defaults to enabled,
        which is the whole point of this migration. Persists the result
        under the new key so this repo is fully migrated from here on."""
        disabled_ids = sorted(_LEGACY_TOOL_IDS - set(legacy_enabled_ids))
        repo_map = self._config_store.get(_KEY, {})
        repo_map[key] = disabled_ids
        self._config_store.set(_KEY, repo_map)
        return disabled_ids

    def enabled_tool_ids_for(
        self, project_id: str | None, repo_id: str | None, all_tool_ids: list[str]
    ) -> list[str]:
        """Every known tool id, minus this repo's disabled set (empty/no
        entry means "everything enabled" — the default every repo has had
        since this store existed, now also true for any tool id added
        after a repo was first customized, see class docstring)."""
        if not project_id or not repo_id:
            return list(all_tool_ids)
        disabled_ids = self._disabled_ids_for(self._repo_key(project_id, repo_id))
        if disabled_ids is None:
            return list(all_tool_ids)
        disabled_set = set(disabled_ids)
        return [tid for tid in all_tool_ids if tid not in disabled_set]

    def set_enabled_tool_ids(self, project_id: str, repo_id: str, all_tool_ids: list[str], tool_ids: list[str]) -> None:
        """Persists `tool_ids` (the newly-checked set) as this repo's
        enabled tools — internally stored as the complement,
        `all_tool_ids` minus `tool_ids`. `all_tool_ids` must be the full
        set of tool ids the caller offered as checkboxes (see
        MayaLauncherSettingsPage._on_tool_toggled), so a tool NOT present
        in `all_tool_ids` at all (e.g. one hidden from the checkbox list,
        like PublishApi) is never accidentally recorded as disabled."""
        disabled_ids = sorted(set(all_tool_ids) - set(tool_ids))
        repo_map = self._config_store.get(_KEY, {})
        repo_map[self._repo_key(project_id, repo_id)] = disabled_ids
        self._config_store.set(_KEY, repo_map)
