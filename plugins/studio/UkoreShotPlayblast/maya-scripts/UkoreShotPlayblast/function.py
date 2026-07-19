"""Configurable playblast — replaces UkoreMaya's old hardcoded "Quick
Playblast" (plugins/studio/MayaToolkit/maya-scripts/UkoreMaya/core/
function.py's now-removed publish_playblast, still called from
menu_utils.py's playblast(), just routed here now). Destination folder
comes from UkoreHub's Repository Setting > UkoreShot; options come from
this tool's own "Playblast Options..." dialog inside Maya (options_dialog.py
— confirmed with the user 2026-07-19 this belongs in Maya, not a UkoreHub
Settings tab) via options_store.py. Both resolved the same "construct the
store straight off disk" way every Maya-side module in this codebase uses
(Maya's Python has no PluginAPI instance), via PublishApi for
active-repo/CustomPath resolution."""

from __future__ import annotations

import datetime
import os

import maya.cmds as cmds
from PublishApi import repo_paths
from UkoreShotPlayblast import options_store


def _repo_key(project_id: str, repo_id: str) -> str:
    return "{}:{}".format(project_id, repo_id)


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

    return repo_path / custom_path["path"]


def publish_playblast() -> None:
    try:
        project, repo, repo_path = repo_paths.get_active_repo()
        if project is None:
            raise RuntimeError("No active repo selected in UkoreHub. Open UkoreHub, pick a project/repo, then try again.")

        video_root = _resolve_video_root(project.id, repo.id, repo_path)
        os.makedirs(str(video_root), exist_ok=True)

        options = options_store.get_options(project.id, repo.id)

        current_file = cmds.file(q=True, sn=True)
        scene_basename = os.path.splitext(os.path.basename(current_file))[0] if current_file else "untitled"
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        export_file_path = os.path.join(str(video_root), "{}_{}".format(scene_basename, timestamp))

        if options["resolution_mode"] == "custom":
            width = options["width"]
            height = options["height"]
        else:
            width = cmds.getAttr("defaultResolution.width")
            height = cmds.getAttr("defaultResolution.height")

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

        if options["camera"]:
            panel = cmds.getPanel(withFocus=True)
            if panel and cmds.getPanel(typeOf=panel) == "modelPanel":
                cmds.modelPanel(panel, edit=True, camera=options["camera"])

        cmds.playblast(**playblast_kwargs)

        cmds.inViewMessage(amg="<hl>Playblast saved:</hl> {}".format(export_file_path), pos="midCenter", fade=True)
    except Exception as e:
        cmds.confirmDialog(title="UkoreShot Playblast", message=str(e))
