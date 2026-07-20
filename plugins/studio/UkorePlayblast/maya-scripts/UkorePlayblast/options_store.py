"""Per-repo playblast option storage — read/written entirely from inside
Maya (function.py's publish_playblast, options_dialog.py's "Playblast
Options..." dialog) since this tool has no UkoreHub desktop UI of its own
(confirmed with the user 2026-07-19 — see plugin.py). Constructs the
PluginConfigStore straight off disk, same pattern every Maya-side module
in this codebase uses (Maya's Python has no PluginAPI instance) —
PublishApi.repo_paths and UkoreBrowser's core/repo_context.py are the
established examples."""

from __future__ import annotations

import re

from PublishApi import repo_paths

_OPTIONS_KEY = "repo_options"
_VARIATIONS_KEY = "repo_variations"

# Built-in variation choices always offered regardless of repo — a repo
# can add more on top via add_variation, confirmed with the user
# 2026-07-20 that custom variations are scoped per-repo (get_variations
# below), same as every other per-repo choice this store already holds.
BUILTIN_VARIATIONS = ["layout", "blocking", "spline"]

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
    # Applies to "video" output_mode only — "image" format used to be a
    # third choice here too, but that produced a full-timeline image
    # sequence via Maya's own per-frame numbering, not the deliberate
    # single-current-frame capture the user asked for 2026-07-20; that's
    # now output_mode/image_format below instead, a separate axis.
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
    # "video" | "current_frame_image" — added 2026-07-20 alongside the
    # flat SEQ_Shot_variation_index_version naming convention (see the
    # README's "Flat naming convention" section and function.py's
    # _resolve_filename_stem): "current_frame_image" captures exactly the
    # frame Maya's playhead is on right now, not a range, and adds a new
    # index onto whichever version for this shot/variation already
    # exists instead of starting a fresh one — the "video" mode is
    # unchanged from before.
    "output_mode": "video",
    "image_format": "png",
    # Which BUILTIN_VARIATIONS/repo-custom entry the naming convention's
    # "variation" token comes from for this repo's next playblast.
    "variation": "layout",
}


def _repo_key(project_id, repo_id):
    return "{}:{}".format(project_id, repo_id)


def _sanitize_token(value: str) -> str:
    """Mirrors function.py's own _sanitize_token exactly (small enough,
    and used by different concerns — storage vs. filename-building — that
    a shared module would be more ceremony than the two-line function
    warrants; same reasoning _repo_key above is already duplicated
    independently in both files for). Strips anything that isn't a
    letter/digit so a custom variation can never contain the "_" the flat
    naming convention's stem is split on."""
    return re.sub(r"[^A-Za-z0-9]", "", value) or "x"


def _store():
    root = repo_paths.find_ukorehub_root()
    from core.extensibility.config_store import PluginConfigStore

    return PluginConfigStore(root / "data" / "plugins" / "studio" / "ukore_playblast.json")


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


def get_variations(project_id, repo_id):
    """BUILTIN_VARIATIONS plus this repo's own custom additions (order
    preserved, no duplicates) — safe to call with project_id/repo_id both
    None (no active repo), returning just the builtins, since the lookup
    key simply won't match anything saved."""
    saved = _store().get(_VARIATIONS_KEY, {}).get(_repo_key(project_id, repo_id), [])
    result = list(BUILTIN_VARIATIONS)
    for variation in saved:
        if variation not in result:
            result.append(variation)
    return result


def add_variation(project_id, repo_id, variation) -> str:
    """Sanitizes and persists a new custom variation for this repo,
    returning the sanitized value actually saved so the caller (the
    options dialog) can select exactly that. A no-op (beyond sanitizing)
    if it's already a builtin or already saved for this repo."""
    sanitized = _sanitize_token(variation)
    store = _store()
    all_variations = store.get(_VARIATIONS_KEY, {})
    key = _repo_key(project_id, repo_id)
    repo_variations = list(all_variations.get(key, []))
    if sanitized not in BUILTIN_VARIATIONS and sanitized not in repo_variations:
        repo_variations.append(sanitized)
        all_variations[key] = repo_variations
        store.set(_VARIATIONS_KEY, all_variations)
    return sanitized
