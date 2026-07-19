"""Rig publish logic — split out of the original UkorePublisher's
function.py (the "Rig" branch of publish_dialog/publish_common) on
2026-07-19. Path resolution/versioning goes through PublishApi
(repo_paths.get_publish_root(TOOL_ID) + versioning.get_version_directory())
instead of the old share/publish scene-path convention — see
plugins/studio/PublishApi/README.md. The publish root's own "which
CustomPath" decision moved out of this Maya UI entirely on 2026-07-19,
into RigPublisher's Repo Studio Setting tab (settings_page.py, UkoreHub
side) — get_publish_root(TOOL_ID) already resolves it."""

import os

import maya.cmds as mc
from PublishApi import repo_paths, versioning
from UkoreMaya.core import Pipeline

TOOL_ID = "rig_publisher"
TICKETS = ["Main", "Proxy", "Hi"]


def publish(ticket: str):
    """Exports the current scene as a raw Maya Ascii copy into PublishApi's
    resolved publish root, versioned automatically (mirrors the original
    UkorePublisher's Rig branch: "Rig, Proxy, Hi > Maya Ascii"). Returns
    (version_dir, version_number)."""
    scene_path = mc.file(q=True, sn=True)
    if not scene_path:
        raise RuntimeError("กรุณาบันทึกไฟล์ก่อนดำเนินการ Publish!")

    publish_root = repo_paths.get_publish_root(TOOL_ID)
    version_dir, version = versioning.get_version_directory(publish_root, ticket)

    ma_path = os.path.join(version_dir, "{}_v{:03d}.ma".format(ticket, version))
    Pipeline.export_maya_common(export_file_path=ma_path)

    return version_dir, version
