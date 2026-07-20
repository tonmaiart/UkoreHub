"""Configurable playblast — replaces UkoreMaya's old hardcoded "Quick
Playblast" (plugins/studio/MayaToolkit/maya-scripts/UkoreMaya/core/
function.py's now-removed publish_playblast, still called from
menu_utils.py's playblast(), just routed here now). Destination folder
comes from UkoreHub's Repository Setting > UkoreShot; the filename itself
encodes shot/variation/index/version (see "Flat naming convention" in this
plugin's README, and _resolve_filename_stem below) instead of the folder
structure carrying that information. Options come from this tool's own
"Playblast Options..." dialog inside Maya (options_dialog.py — confirmed
with the user 2026-07-19 this belongs in Maya, not a UkoreHub Settings
tab) via options_store.py. Both resolved the same "construct the store
straight off disk" way every Maya-side module in this codebase uses
(Maya's Python has no PluginAPI instance), via PublishApi for
active-repo/CustomPath resolution."""

from __future__ import annotations

import os
import re

import maya.cmds as cmds
from PublishApi import repo_paths
from UkorePlayblast import options_store

_SHOT_CODE_PATTERN = re.compile(r"^([A-Za-z]+)(\d+)")
# SEQ_ShotCode_Variation_index_version — see the README's "Flat naming
# convention" section. Every one of the first three tokens is sanitized to
# letters/digits only before a filename is ever built (_sanitize_token),
# so splitting a stem on "_" and expecting exactly 5 parts is safe; this
# is also what lets plugins/studio/UkoreShot/video_naming.py (the
# desktop-side reader of these same filenames) parse them back reliably.
_FILENAME_PATTERN = re.compile(r"^([^_]+)_([^_]+)_([^_]+)_(\d+)_v(\d+)$")


def _repo_key(project_id: str, repo_id: str) -> str:
    return "{}:{}".format(project_id, repo_id)


def _sanitize_token(value: str) -> str:
    """Strips anything that isn't a letter/digit — the flat filename
    convention splits its stem on "_" into exactly 5 parts, so a sequence/
    shot/variation containing an underscore (or a space, which is worse to
    have literally in a shared-drive filename anyway) would silently
    corrupt that split. Falls back to "x" for a value that sanitizes down
    to nothing (e.g. an all-symbols scene name)."""
    return re.sub(r"[^A-Za-z0-9]", "", value) or "x"


def _resolve_video_root(project_id: str, repo_id: str, repo_path):
    """Mirrors plugins/studio/UkoreShot/video_path_store.py's
    resolve_video_root exactly (same resolution order: explicit choice,
    else the repo's only declared Custom Path, else nothing) — duplicated
    for the same "Maya's Python can't import the desktop-side plugins/
    package" reason options_store.py's own docstring gives. Raises
    RuntimeError with a human-readable reason in every failure case, same
    convention PublishApi.repo_paths.get_publish_root uses."""
    custom_paths = repo_paths.get_custom_paths(project_id, repo_id)
    if not custom_paths:
        raise RuntimeError(
            "This repo has no Custom Paths declared yet. Add one under Repository Setting > "
            "Custom Paths > Create Input Path, then pick it under Repository Setting > UkoreShot."
        )

    root = repo_paths.find_ukorehub_root()
    from core.extensibility.config_store import PluginConfigStore

    ukore_shot_store = PluginConfigStore(root / "data" / "plugins" / "studio" / "ukore_shot.json")
    custom_path_id = ukore_shot_store.get("repo_video_custom_path", {}).get(_repo_key(project_id, repo_id))

    if custom_path_id is None:
        if len(custom_paths) != 1:
            raise RuntimeError(
                "This repo has multiple Custom Paths declared and none is chosen for UkoreShot yet. "
                "Pick one under Repository Setting > UkoreShot."
            )
        custom_path = custom_paths[0]
    else:
        custom_path = repo_paths.get_custom_path(project_id, repo_id, custom_path_id)
        if custom_path is None:
            raise RuntimeError(
                "UkoreShot's chosen Custom Path for this repo no longer exists — re-pick one under "
                "Repository Setting > UkoreShot."
            )

    # A stored Custom Path is always meant to be relative to the repo root
    # (see GLOSSARY.md's "Custom Path" entry) but is saved as raw user
    # input with no sanitization (project_editor's pipeline_store.py).
    # A leading "/" or "\" makes pathlib's `/` operator treat it as
    # anchored to the current drive, silently discarding repo_path.
    return repo_path / custom_path["path"].lstrip("/\\")


def _current_scene_basename() -> str:
    current_file = cmds.file(q=True, sn=True)
    return os.path.splitext(os.path.basename(current_file))[0] if current_file else "untitled"


def _resolve_seq_shot(scene_basename: str):
    """(sequence, shot_code) parsed off the scene name's leading
    letters+digits run, e.g. "KBA140_Anim_Layout_v001" -> ("KBA",
    "KBA140"), both already letters/digits-only so no _sanitize_token
    round-trip is needed for the common case. Falls back to sequence
    "misc" + the whole (sanitized) scene basename as the shot code when
    the scene name doesn't start with that pattern (untitled scene, or a
    name this shot-code rule doesn't apply to) — a deliberate fallback,
    not an error, so an oddly-named scene still produces a playblast
    instead of failing outright."""
    match = _SHOT_CODE_PATTERN.match(scene_basename)
    if match:
        prefix, digits = match.group(1), match.group(2)
        return prefix, prefix + digits
    return "misc", _sanitize_token(scene_basename)


def _matching_versions(video_root, sequence: str, shot_code: str, variation: str):
    """{version: [index, index, ...]} for every existing flat file in
    video_root whose stem matches this exact sequence/shot/variation via
    _FILENAME_PATTERN. video_root's top level only (not recursive) — this
    convention has no subfolders of its own; a legacy shot/version-
    subfoldered playblast from before 2026-07-20 sits inside a subfolder
    and is invisible to this scan, left alone per the user's own decision
    (see the README) rather than migrated. Also ignores any other file in
    video_root that doesn't happen to match this exact pattern — not an
    error, just not one of this tool's own files."""
    result = {}
    if not video_root.is_dir():
        return result
    for path in video_root.iterdir():
        if not path.is_file():
            continue
        match = _FILENAME_PATTERN.match(path.stem)
        if not match:
            continue
        seq, shot, var, index_str, version_str = match.groups()
        if seq == sequence and shot == shot_code and var == variation:
            result.setdefault(int(version_str), []).append(int(index_str))
    return result


def _next_version(video_root, sequence: str, shot_code: str, variation: str) -> int:
    versions = _matching_versions(video_root, sequence, shot_code, variation)
    return (max(versions) + 1) if versions else 1


def _latest_version(video_root, sequence: str, shot_code: str, variation: str):
    versions = _matching_versions(video_root, sequence, shot_code, variation)
    return max(versions) if versions else None


def _next_index(video_root, sequence: str, shot_code: str, variation: str, version: int) -> int:
    indices = _matching_versions(video_root, sequence, shot_code, variation).get(version, [])
    return (max(indices) + 1) if indices else 1


def _resolve_filename_stem(video_root, sequence: str, shot_code: str, variation: str, *, is_image: bool) -> str:
    """SEQ_ShotCode_Variation_index_version, no extension. A video
    playblast always starts a brand-new version (index always "001" — one
    clip is the whole version). A current-frame image playblast instead
    reuses whichever version for this exact sequence/shot/variation
    already exists (creating v001 if this is the first playblast for it
    at all) and takes the next index within *that* version — confirmed
    with the user 2026-07-20: an image playblast "adds an index into the
    same version" rather than starting a new one, so a set of stills for
    one take ends up as v001 index 001, 002, 003... instead of each being
    its own version."""
    if is_image:
        version = _latest_version(video_root, sequence, shot_code, variation)
        if version is None:
            version = 1
        index = _next_index(video_root, sequence, shot_code, variation, version)
    else:
        version = _next_version(video_root, sequence, shot_code, variation)
        index = 1
    return "{}_{}_{}_{:03d}_v{:03d}".format(sequence, shot_code, variation, index, version)


def _finalize_single_frame_image(export_file_path: str, image_format: str) -> str:
    """cmds.playblast's format="image" always appends its own frame-number
    suffix to `filename` (e.g. "<export_file_path>.0001.<ext>"), even for
    a single-frame capture — there is no Maya flag to suppress it. Renamed
    to the exact target name afterward so this tool's own naming
    convention (SEQ_Shot_variation_index_version.ext) still holds for
    image output too. The produced file is located by globbing the
    directory for anything starting with the same base name rather than
    assuming an exact zero-padding width, since that padding isn't
    documented as stable across Maya versions."""
    directory = os.path.dirname(export_file_path)
    base_name = os.path.basename(export_file_path)
    target_path = "{}.{}".format(export_file_path, image_format)
    target_name = os.path.basename(target_path)
    candidates = sorted(
        name
        for name in os.listdir(directory)
        if name.startswith(base_name + ".") and name.endswith("." + image_format) and name != target_name
    )
    if candidates:
        os.replace(os.path.join(directory, candidates[0]), target_path)
    return target_path


def resolve_destination_path():
    """Full file path (including extension) the next publish_playblast()
    call would write, without creating anything or running Maya's
    playblast — used by options_dialog.py's destination_label to preview
    exactly what a playblast right now would produce. Meaningful as a full
    *file* preview (not just a folder, like before 2026-07-20) now that
    the video root is flat and the filename itself is where all the
    shot/variation/index/version information lives. Raises RuntimeError
    with the same human-readable reasons publish_playblast() itself would
    hit."""
    project, repo, repo_path = repo_paths.get_active_repo()
    if project is None:
        raise RuntimeError("No active repo selected in UkoreHub. Open UkoreHub, pick a project/repo, then try again.")
    video_root = _resolve_video_root(project.id, repo.id, repo_path)
    options = options_store.get_options(project.id, repo.id)
    sequence, shot_code = _resolve_seq_shot(_current_scene_basename())
    variation = _sanitize_token(options.get("variation") or "layout")
    is_image = options.get("output_mode") == "current_frame_image"
    stem = _resolve_filename_stem(video_root, sequence, shot_code, variation, is_image=is_image)
    extension = (options.get("image_format") or "png") if is_image else options["format"]
    return video_root / "{}.{}".format(stem, extension)


def publish_playblast() -> None:
    print("[UkorePlayblast] Playblast started...")
    try:
        project, repo, repo_path = repo_paths.get_active_repo()
        if project is None:
            raise RuntimeError("No active repo selected in UkoreHub. Open UkoreHub, pick a project/repo, then try again.")

        video_root = _resolve_video_root(project.id, repo.id, repo_path)
        os.makedirs(str(video_root), exist_ok=True)

        options = options_store.get_options(project.id, repo.id)
        print("[UkorePlayblast] Options: {}".format(options))

        sequence, shot_code = _resolve_seq_shot(_current_scene_basename())
        variation = _sanitize_token(options.get("variation") or "layout")
        is_image = options.get("output_mode") == "current_frame_image"
        stem = _resolve_filename_stem(video_root, sequence, shot_code, variation, is_image=is_image)
        export_file_path = os.path.join(str(video_root), stem)
        print("[UkorePlayblast] Destination folder: {}".format(video_root))
        print("[UkorePlayblast] Filename: {}".format(stem))

        if options["resolution_mode"] == "custom":
            width = options["width"]
            height = options["height"]
        else:
            width = cmds.getAttr("defaultResolution.width")
            height = cmds.getAttr("defaultResolution.height")

        if options["camera"]:
            panel = cmds.getPanel(withFocus=True)
            if panel and cmds.getPanel(typeOf=panel) == "modelPanel":
                cmds.modelPanel(panel, edit=True, camera=options["camera"])

        if is_image:
            # Current-frame-only capture — deliberately not the whole
            # timeline turned into an image sequence (confirmed with the
            # user 2026-07-20): startTime/endTime/frame all pinned to
            # cmds.currentTime so exactly one still comes out, no matter
            # what the saved frame_range_mode/start_frame/end_frame options
            # say (those only apply to the video output mode).
            current_time = cmds.currentTime(query=True)
            image_format = options.get("image_format") or "png"
            playblast_kwargs = {
                "filename": export_file_path,
                "format": "image",
                "compression": image_format,
                "qlt": options["quality"],
                "width": width,
                "height": height,
                "percent": options["percent"],
                "showOrnaments": options["show_ornaments"],
                "offScreen": True,
                "startTime": current_time,
                "endTime": current_time,
                "frame": [current_time],
            }
            cmds.playblast(**playblast_kwargs)
            saved_path = _finalize_single_frame_image(export_file_path, image_format)
        else:
            playblast_kwargs = {
                "filename": export_file_path,
                "format": options["format"],
                "compression": options["compression"],
                "qlt": options["quality"],
                "width": width,
                "height": height,
                "percent": options["percent"],
                "showOrnaments": options["show_ornaments"],
                "offScreen": True,
            }

            if options["frame_range_mode"] == "custom":
                playblast_kwargs["startTime"] = options["start_frame"]
                playblast_kwargs["endTime"] = options["end_frame"]

            sound_node_name = ""
            if options["sound"]:
                sound_nodes = cmds.ls(type="audio")
                sound_node_name = sound_nodes[0] if sound_nodes else ""
                if sound_node_name:
                    current_source_start = cmds.getAttr("{}.sourceStart".format(sound_node_name))
                    current_offset = cmds.getAttr("{}.offset".format(sound_node_name))
                    if current_source_start != 0:
                        cmds.setAttr("{}.sourceStart".format(sound_node_name), 0)
                        cmds.setAttr("{}.offset".format(sound_node_name), current_offset - current_source_start)
                    playblast_kwargs["sound"] = sound_node_name

            cmds.playblast(**playblast_kwargs)
            saved_path = "{}.{}".format(export_file_path, options["format"])

        print("[UkorePlayblast] Playblast saved: {}".format(saved_path))
        cmds.inViewMessage(amg="<hl>Playblast saved:</hl> {}".format(saved_path), pos="midCenter", fade=True)
    except Exception as e:
        print("[UkorePlayblast] Playblast failed: {}".format(e))
        cmds.confirmDialog(title="UkorePlayblast", message=str(e))
