"""Per-repo playblast option storage — read/written entirely from inside
Maya (function.py's publish_playblast, options_dialog.py's "Playblast
Options..." dialog) since this tool has no UkoreHub desktop UI of its own
(confirmed with the user 2026-07-19 — see plugin.py). Constructs the
PluginConfigStore straight off disk, same pattern every Maya-side module
in this codebase uses (Maya's Python has no PluginAPI instance) —
PublishApi.repo_paths and UkoreBrowser's core/repo_context.py are the
established examples."""

from __future__ import annotations

from PublishApi import repo_paths

_OPTIONS_KEY = "repo_options"

DEFAULT_OPTIONS = {
    "resolution_mode": "render_settings",  # "render_settings" | "custom"
    "width": 1920,
    "height": 1080,
    # "avi", not the old hardcoded "qt" — fixed 2026-07-19 after a real
    # "Unable to create a movie file. It may be open by another
    # application." playblast failure: modern Maya on Windows has no
    # QuickTime backend at all ("qt" format), so that default (carried
    # over unchanged from the pre-2026-07-19 hardcoded Quick Playblast)
    # likely never actually worked on Windows. "avi" needs no external
    # codec framework. Compression left blank (uncompressed) for the same
    # reason — a named codec like "H.264" isn't guaranteed to be
    # installed/available for Maya's AVI writer on every machine, and an
    # invalid/unavailable one fails with this exact same generic error.
    "format": "avi",
    "compression": "",
    "quality": 80,
    "percent": 80,
    "frame_range_mode": "current_timeline",  # "current_timeline" | "custom"
    "start_frame": 1,
    "end_frame": 100,
    "camera": "",  # empty = active viewport camera
    "sound": True,
    "show_ornaments": False,
}


def _repo_key(project_id, repo_id):
    return "{}:{}".format(project_id, repo_id)


def _store():
    root = repo_paths.find_ukorehub_root()
    from core.extensibility.config_store import PluginConfigStore

    return PluginConfigStore(root / "data" / "plugins" / "studio" / "ukore_shot_playblast.json")


def get_options(project_id, repo_id):
    """DEFAULT_OPTIONS merged with whatever's saved for this repo — every
    field always present, so callers never need a .get() fallback."""
    saved = _store().get(_OPTIONS_KEY, {}).get(_repo_key(project_id, repo_id), {})
    options = dict(DEFAULT_OPTIONS)
    options.update(saved)
    return options


def set_options(project_id, repo_id, options):
    store = _store()
    all_options = store.get(_OPTIONS_KEY, {})
    all_options[_repo_key(project_id, repo_id)] = options
    store.set(_OPTIONS_KEY, all_options)
