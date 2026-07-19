"""
Used to export / validate pipeline file, this is Add-On Script for Ukore Pipeline

Folder highlights
Maya Publisher Python scripts define publishing workflows for Model, Rig, and Anim tasks, including FBX, ABC, and Playblast exports.


"""

import shutil
import json
import os
import glob

import tmlib
from tmlib.core import Scene, Utility, Validate
from tmlib.ui import uitools

import maya.cmds as cmds
import maya.mel as mel
import os, shutil
import maya.mel as mel


@uitools.undoable
def playblast_screenshot_to_project_folder():
    def get_next_image_name(folder, base_name, ext=".jpg"):
        indices = []
        for f in os.listdir(folder):
            if f.startswith(base_name + "_") and f.endswith(ext):
                try:
                    indices.append(int(f.split("_")[-1].split(".")[0]))
                except:
                    pass
        next_index = max(indices) + 1 if indices else 1
        return f"{base_name}_{next_index:04d}"

    def playblast_single_frame_jpg_500():
        cmds.refresh(f=True)  # IMPORTANT

        workspace_path = cmds.workspace(q=True, rootDirectory=True)
        screenshot_folder = os.path.join(workspace_path, "screenshot")
        os.makedirs(screenshot_folder, exist_ok=True)

        frame = int(cmds.currentTime(q=True))

        scene = cmds.file(q=True, sn=True)
        base_name = (
            os.path.splitext(os.path.basename(scene))[0] if scene else "playblast"
        )

        img_name = get_next_image_name(screenshot_folder, base_name)
        out_path = os.path.join(screenshot_folder, img_name)

        # get active model panel
        panel = cmds.getPanel(withFocus=True)
        if not panel or not cmds.getPanel(typeOf=panel) == "modelPanel":
            panels = cmds.getPanel(type="modelPanel")
            panel = panels[0]

        a = cmds.playblast(
            format="image",
            filename=out_path,
            startTime=frame,
            endTime=frame,
            viewer=False,
            showOrnaments=False,
            compression="jpg",
            widthHeight=(400, 400),
            percent=100,
            clearCache=True,
            offScreen=False,  # 👈 THIS FIXES IT
            forceOverwrite=True,
        )
        files = glob.glob(a.replace("####", "*"))
        # print("a : ", a)
        img_path = files[0]

        if os.path.exists(img_path):
            cmds.launch(imageViewer="fcheck", file=img_path)

        return img_path

    img_path = playblast_single_frame_jpg_500()

    return img_path


def list_meshes_with_suffix_geo():
    """Get only mesh that have suffix Geo and live in side geo_grp"""

    all_meshes = cmds.ls(type="mesh", l=1)

    geo_transforms = []
    for shape in all_meshes:
        if "Geo_Grp|" in shape or "geo|" in shape:
            transform_name = cmds.listRelatives(
                shape, parent=True, fullPath=True, type="transform"
            )[0]
            if transform_name.endswith("_Geo"):
                geo_transforms.append(transform_name)

    return geo_transforms


def export_fbx_common(export_path):
    cmds.file(
        export_path,
        force=True,
        options="v=0;",
        type="FBX export",
        exportAll=True,
    )


def export_abc_common(export_path):
    start = cmds.playbackOptions(q=True, min=True)
    end = cmds.playbackOptions(q=True, max=True)
    job = f'-frameRange {start} {end} -worldSpace -uvWrite -writeVisibility -file "{export_path}"'
    cmds.AbcExport(j=job)


def export_maya_common(export_file_path):
    shutil.copy(cmds.file(q=True, sn=True), export_file_path)




def get_character_meshes(pick_character_enable=False, pick_character=["Kafka"]):
    """
    Get character list from scene based on suffix
    """

    dict_character = {}

    for mesh_name in list_meshes_with_suffix_geo():
        transform_key = Utility.cut(mesh_name, hierarchy=True, namespace=True).split(
            "_"
        )[0]

        if pick_character_enable and transform_key not in pick_character:
            continue

        # create new key if not exist
        if transform_key not in dict_character:
            dict_character[transform_key] = []

        if mesh_name not in dict_character[transform_key]:
            dict_character[transform_key].append(mesh_name)

    return dict_character


def export_playblast(export_path):
    """
    Quick playblast to given export folder
    """

    # Playblast
    width = cmds.getAttr("defaultResolution.width")
    height = cmds.getAttr("defaultResolution.height")

    sound_nodes = cmds.ls(type="audio")
    sound_node_name = sound_nodes[0] if sound_nodes else ""

    cmds.playblast(
        filename=export_path,
        format="avi",
        compression="none",
        width=width,
        height=height,
        percent=100,
        showOrnaments=False,
        offScreen=True,
        sound=sound_node_name,
    )

def update_maya_env():
    src = r"G:\My Drive\Mellowstar\dev\Others\env_template\Maya.env"
    maya_app_dir = mel.eval('getenv "MAYA_APP_DIR"')

    for version in os.listdir(maya_app_dir):
        if os.path.isdir(os.path.join(maya_app_dir, version)) and version.isdigit():
            shutil.copy2(src, os.path.join(maya_app_dir, version, "Maya.env"))
            print(f"Update Maya.env file : {os.path.join(maya_app_dir, version, 'Maya.env')}")