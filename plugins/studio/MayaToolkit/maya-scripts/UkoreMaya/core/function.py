# ============================================================
#   MAYA Utility for Ukore Tools, no pymel, keep using cmds
#   Natchapon Srisuk , 4 December 2025
#   Maya 2026 Compatible
# ============================================================

import maya.cmds as cmds
import os
import shutil
import subprocess
import re
import json
import maya.mel as mel
from importlib import reload
from tmlib.core import File
from tmlib.module.PySide import QtWidgets

from UkoreMaya.core import utils, Plugin


# --------------------------------------------------------------------
def print_selected():
    a = cmds.ls(sl=True)

    print(a)

    clipboard = QtWidgets.QApplication.clipboard()
    clipboard.setText(str(a))
    cmds.inViewMessage(message="<hl> Copy Clipboard Selection to list text </hl>")


def selected_to_blank_dict():
    sel = cmds.ls(sl=True)
    result = {}

    for obj in sel:
        result[obj] = ""  # key = object name, value = empty string

    print(result)
    return result


def auto_launch_ukore_file_browser():
    reload(Plugin)
    Plugin.reload_scripts()
    if not cmds.file(query=True, sceneName=True):
        File.launch("UkoreBrowser")


# ------------------------------------------------------------
# FILE PICKER (REFERENCE TOOL)
# ------------------------------------------------------------
def browse_file_dialog():
    """
    Open File Dialog with default path (show all files)
    """
    DEFAULT_DIR = r"G:\My Drive\Projects\KafkaProj\publish"

    if not os.path.exists(DEFAULT_DIR):
        cmds.warning(f"Default directory not found: {DEFAULT_DIR}")

    file_path = cmds.fileDialog2(
        fileMode=1,
        startingDirectory=DEFAULT_DIR,
        caption="Select File to Reference",
        okCaption="Reference",
        fileFilter="All Files (*.*)",  # <- ALWAYS show all
    )

    if not file_path:
        return None

    return file_path[0].replace("\\", "/")


# ------------------------------------------------------------
# REFERENCE FILE (ALL FORMATS)
# ------------------------------------------------------------
def reference_file():
    """
    แบบง่ายสุด:
    1) reference ไฟล์
    2) หา top-level transforms
    3) ถ้า namespace ตรงกับ reference → parent เข้า group
    """

    path = browse_file_dialog()
    if not path:
        return

    filename = os.path.basename(path)
    namespace = os.path.splitext(filename)[0]
    group_name = os.path.basename(os.path.dirname(path))

    try:
        # Reference file
        cmds.file(
            path,
            reference=True,
            namespace=namespace,
            ignoreVersion=True,
            mergeNamespacesOnClash=False,
        )

        # สร้าง group
        if not cmds.objExists(group_name):
            top_grp = cmds.group(em=True, name=group_name)
        else:
            top_grp = group_name

        # หา top-level objects ทั้งหมด
        top_nodes = cmds.ls(assemblies=True, long=True)

        # เอาเฉพาะ nodes ที่มี namespace ตรงกับ reference
        to_parent = []
        for node in top_nodes:
            short_name = node.split("|")[-1]  # last segment
            if short_name.startswith(namespace + ":"):
                to_parent.append(node)

        # Parent เข้า group
        if to_parent:
            cmds.parent(to_parent, top_grp)

        cmds.inViewMessage(
            amg=f"<hl>Referenced & Grouped:</hl> {group_name}",
            pos="midCenter",
            fade=True,
        )

    except Exception as e:
        cmds.confirmDialog(title="Error", message=str(e))


# Playblast moved out to its own plugin 2026-07-19 — see
# plugins/studio/UkoreShotPlayblast/maya-scripts/UkoreShotPlayblast/
# function.py's publish_playblast (called from menu_utils.py's playblast()).

# ================================


def import_all_picker():
    import UkoreMaya
    from UkoreMaya.core import menu_utils
    menu_utils.dreamwall_picker()

    current_project = cmds.workspace(q=True, rd=True)
    default_dir = os.path.join(current_project, "publish", "Character")
    print("Searching Picker from : ", default_dir)

    import dwpicker
    from dwpicker.namespace import detect_picker_namespace

    # from dwpicker.namespace import search_and_replace_namespace

    dwpicker._dwpicker.clear()

    for char_folder in os.listdir(default_dir):
        ls_ref = cmds.ls("*:{}".format(char_folder))
        ls_scene = cmds.ls(char_folder)

        if not (ls_ref or ls_scene):
            continue

        picker_path = os.path.join(default_dir, char_folder, "Picker", "Picker.json")
        if os.path.exists(picker_path):
            dwpicker.open_picker_file(picker_path)

        # Update Namespaces

        picker = dwpicker.current()
        if not picker:
            return

        if ls_scene:
            new_ns = ""
        elif ls_ref:
            new_ns = ls_ref[0].split(":")[0]

        for shape in picker.document.shapes:
            targets = shape.options.get("action.targets", [])
            if not targets:
                continue

            new_targets = []
            for t in targets:
                base_name = t.split(":")[-1]
                if new_ns == ":":
                    new_targets.append(base_name)
                else:
                    new_targets.append("{}:{}".format(new_ns, base_name))

            shape.options["action.targets"] = new_targets

        picker.update()


# ------------------------------------------------------------
# REFERENCE RIG
# ------------------------------------------------------------
def reference_rig(job_task="Proxy"):
    scene_path = cmds.file(q=True, sn=True)
    if not scene_path:
        cmds.warning("Please save your scene first.")
        return

    job_name = os.path.basename(scene_path).split("_")[0]

    search_dir = rf"G:\My Drive\Projects\KafkaProj\publish\Rig\{job_task}"

    if not os.path.exists(search_dir):
        cmds.error(f"No Rig publish directory: {search_dir}")

    files = sorted(os.listdir(search_dir))
    if not files:
        cmds.error("No published rigs found.")

    latest = files[-1]
    full_path = os.path.join(search_dir, latest)

    namespace = os.path.splitext(latest)[0]

    cmds.file(
        full_path,
        reference=True,
        namespace=namespace,
        mergeNamespacesOnClash=False,
        ignoreVersion=True,
    )

    cmds.inViewMessage(
        amg=f"<hl>Referenced Rig:</hl> {latest}", pos="midCenter", fade=True
    )


def update_references():
    """
    สแกน References ทั้งหมด → ตรวจจับว่ามีเวอร์ชันใหม่หรือไม่ → สอบถามผู้ใช้ → อัปเดต
    """
    refs = cmds.file(q=True, r=True)

    if not refs:
        cmds.inViewMessage(
            amg="Have no any reference in this scene.", pos="midCenter", fade=True
        )
        return False

    # search for update info
    updates_info = []

    for ref_path in refs:
        ref_path = ref_path.split("{")[0]
        ref_path = os.path.normpath(ref_path)

        # ใช้ฟังก์ชันใหม่ในการค้นหาเวอร์ชัน
        latest = utils.get_latest_version_in_folder_based(ref_path)

        print("- {} > {}".format(ref_path, latest))
        if latest and latest != ref_path:
            updates_info.append((ref_path, latest))

    if not updates_info:
        cmds.inViewMessage(
            amg="<hl>All file already up to date.</hl>", pos="midCenter", fade=True
        )
        return True

    # Show Up New Version Detail
    msg_lines = ["ตรวจพบไฟล์เวอร์ชันใหม่ แนะนำให้กดอัพเดท!:\n"]
    for old, new in updates_info:
        name = os.path.normpath(old).split(os.sep)

        msg_lines.append(
            f"- {name[-5]} {name[-4]} {name[-3]} | {os.path.basename(old)} → {os.path.basename(new)}"
        )

    result = cmds.confirmDialog(
        title="Update References",
        message="\n".join(msg_lines),
        button=["Update", "Cancel"],
        defaultButton="Update",
        cancelButton="Cancel",
        dismissString="Cancel",
    )

    # Update Reference Confirm
    if result != "Update":
        return False
    else:
        # Update references one by one
        for old, new in updates_info:
            try:
                ref_node = cmds.file(old, q=True, rfn=True)
                if not ref_node:
                    continue

                cmds.file(
                    new,
                    loadReference=ref_node,
                    options="v=0;",
                    ignoreVersion=True,
                )

            except Exception as e:
                cmds.warning(f"Failed to update: {old} → {new}\n{e}")

        cmds.inViewMessage(
            amg="<hl>Reference and Picker Update Complete</hl>",
            pos="midCenter",
            fade=True,
        )

        return True


def dreamwall_picker():
    import dwpicker

    dwpicker.show()


def run_advance():
    mel.eval(
        'source "G:/My Drive/Mellowstar/dev/maya-scripts/AdvancedSkeleton/AdvancedSkeleton.mel";'
    )
    mel.eval("AdvancedSkeleton;")


def run_advance_face():
    mel.eval(
        'source "G:/My Drive/Mellowstar/dev/maya-scripts/AdvancedSkeleton/AdvancedSkeletonFiles/Selector/face.mel";'
    )

def studio_library():
    import studiolibrary

    studiolibrary.main()
