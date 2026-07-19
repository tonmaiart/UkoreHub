"""Animation publish logic — split out of the original UkorePublisher's
function.py (the "Anim" branch of publish_dialog/publish_common) on
2026-07-19. Path resolution/versioning goes through PublishApi
(repo_paths.get_publish_root(TOOL_ID) + versioning.get_version_directory())
instead of the old share/publish scene-path convention — see
plugins/studio/PublishApi/README.md. The publish root's own "which
CustomPath" decision moved out of this Maya UI entirely on 2026-07-19,
into AnimationPublisher's Repo Studio Setting tab (settings_page.py,
UkoreHub side) — get_publish_root(TOOL_ID) already resolves it.

Only the Main/Playblast tickets are implemented — the original tool's
Layout/Blocking/Polish branch called
UkoreMaya.core.Pipeline.export_shot_to_ue(...), a function that doesn't
exist anywhere in Pipeline.py. That gap predates this split (it was
already broken in the original UkorePublisher) and isn't something this
refactor invents an implementation for — see publish() below, which
raises a clear error for those tickets instead of silently guessing at
what that export should do."""

import os

import maya.cmds as mc
from PublishApi import repo_paths, versioning
from UkoreMaya.core import Pipeline

TOOL_ID = "animation_publisher"
TICKETS = ["Main", "Layout", "Blocking", "Polish", "Playblast"]
_PLAYBLAST_TICKETS = {"Main", "Playblast"}


def publish(ticket: str):
    """Exports a playblast (.avi) into PublishApi's resolved publish root,
    versioned automatically, for the Main/Playblast tickets. Raises
    RuntimeError for Layout/Blocking/Polish — see module docstring.
    Returns (version_dir, version_number)."""
    scene_path = mc.file(q=True, sn=True)
    if not scene_path:
        raise RuntimeError("กรุณาบันทึกไฟล์ก่อนดำเนินการ Publish!")

    if ticket not in _PLAYBLAST_TICKETS:
        raise RuntimeError(
            "'{}' export isn't implemented yet — Pipeline.export_shot_to_ue "
            "doesn't exist in plugins/studio/MayaToolkit's UkoreMaya.core.Pipeline "
            "(a pre-existing gap from the original UkorePublisher tool, not "
            "something this split fixed). Only Main/Playblast currently work.".format(ticket)
        )

    publish_root = repo_paths.get_publish_root(TOOL_ID)
    version_dir, version = versioning.get_version_directory(publish_root, ticket)

    avi_path = os.path.join(version_dir, "{}_v{:03d}.avi".format(ticket, version))
    Pipeline.export_playblast(export_path=avi_path)

    return version_dir, version
