"""
Natchapon Srisuk for Ukore Studio , 4 December 2025

All of this script design for get publsh , validate publish path across Blender and Maya
So I will keep only import python default module, no bpy or maya.cmds
"""

import os
import re
import shutil

import maya.cmds as cmds

import tmlib
from tmlib.core import Scene

import UkoreMaya
from UkoreMaya.core import Logic

def list_meshes_with_suffix_geo():
    all_meshes = cmds.ls(type="mesh")
    geo_transforms = []
    for shape in all_meshes:
        transform = cmds.listRelatives(
            shape, parent=True, fullPath=True, type="transform"
        )
        if transform:
            transform_name = transform[0]
            if transform_name.endswith("_Geo"):
                geo_transforms.append(transform_name)

    return geo_transforms


def _validate_path(path):
    return Logic.convert_to_publish_path(path)



def get_new_version(current_share_path, subfolder):
    return Logic.get_new_version(current_share_path, subfolder)


def get_publish_path(current_share_path, subfolder, extension, version, name=""):
    return Logic.create_publish_path(
        current_share_path, subfolder, extension, version, name
    )


def get_latest_version_in_folder_based(ref_path):
    return Logic.get_latest_version_in_folder_based(ref_path)



def setup_marking_menus():
    """
    Use for set up marking menus menu
    """
    def get_press_command(menu_file):
        # --- MEL Commands ---
        press_command = f"""
        if (`popupMenu -exists tempMM`) {{W
            deleteUI tempMM;
        }}
        popupMenu -button 1 -ctl false -alt false -sh true -allowOptionBoxes true 
                    -parent `findPanelPopupParent` -mm 1 tempMM;
        source "{menu_file}";
        """

        return press_command
            
    print("##=== Setup Marking Menus for Ukore Studio ===##")

    # =====================
    # Checking Hotkey Set
    # =====================

    # Get current hotkey set
    current_set = cmds.hotkeySet(query=True, current=True)

    # Duplicate it to a new set if user using default set.
    if current_set == "Maya_Default":
        new_set_name = "UkoreHotkeySet"

        if new_set_name not in cmds.hotkeySet(query=True, hotkeySetArray=True):
            cmds.hotkeySet(new_set_name, source=current_set)

        cmds.hotkeySet(new_set_name, edit=True, current=True)
        
        print("Hotkey Set :", cmds.hotkeySet(query=True, current=True))

    # ====================
    # --- Setup paths ---
    current_path = os.path.dirname(UkoreMaya.__file__)

    # get marking menu directory
    marking_menu_dir = os.path.join(current_path, "markingMenus")
    marking_menu_dir = marking_menu_dir.replace("\\", "/")

    # Normalize path for Maya (always forward slashes)
    common_menu_file = os.path.join(marking_menu_dir, "menu_TonmaiMenus.mel")
    common_menu_file = common_menu_file.replace("\\", "/")

    # Rigger Menu
    rigger_menu_file = os.path.join(marking_menu_dir, "menu_RiggerKit.mel")
    rigger_menu_file = rigger_menu_file.replace("\\","/")

    # Add to MAYA_SCRIPT_PATH if not already present
    if marking_menu_dir not in os.environ.get("MAYA_SCRIPT_PATH", ""):
        os.environ["MAYA_SCRIPT_PATH"] = (
            marking_menu_dir + ";" + os.environ.get("MAYA_SCRIPT_PATH", "")
        )

    #  mel_file = mel_file.
    print(f"#### Setup Marking Menus : {common_menu_file} ####")

    release_command = """
   if (`popupMenu -exists tempMM`) {
      deleteUI tempMM;
   }
   """


    # Common Menu Command Set up
    for name, ann, cmd in [
        ("TonmaiMenus_Press",   "TonmaiMenus (Press)",   get_press_command(common_menu_file)),
        ("TonmaiMenus_Release", "TonmaiMenus (Release)", release_command),
    ]:
        if cmds.runTimeCommand(name, exists=True):
            cmds.runTimeCommand(name, edit=True, delete=True)
        cmds.runTimeCommand(name, annotation=ann, category="User", command=cmd, commandLanguage="mel")

    cmds.nameCommand("TonmaiMenus_PressNameCommand",   ann="TonmaiMenus_PressNameCommand",   c="TonmaiMenus_Press")
    cmds.nameCommand("TonmaiMenus_ReleaseNameCommand", ann="TonmaiMenus_ReleaseNameCommand", c="TonmaiMenus_Release")
    cmds.hotkey(k="a", sht=True, name="TonmaiMenus_PressNameCommand", releaseName="TonmaiMenus_ReleaseNameCommand")

    # Rigging Menu Command Set up
    for name, ann, cmd in [
        ("RiggerMenu_Press",   "RiggerMenu (Press)",   get_press_command(rigger_menu_file)),
        ("RiggerMenu_Release", "RiggerMenu (Release)", release_command),
    ]:
        if cmds.runTimeCommand(name, exists=True):
            cmds.runTimeCommand(name, edit=True, delete=True)
        cmds.runTimeCommand(name, annotation=ann, category="User", command=cmd, commandLanguage="mel")

    cmds.nameCommand("RiggerMenu_PressNameCommand",   ann="RiggerMenu_PressNameCommand",   c="RiggerMenu_Press")
    cmds.nameCommand("RiggerMenu_ReleaseNameCommand", ann="RiggerMenu_ReleaseNameCommand", c="RiggerMenu_Release")
    cmds.hotkey(k="q", sht=True, name="RiggerMenu_PressNameCommand", releaseName="RiggerMenu_ReleaseNameCommand")


    print("Setting Hotkey Complete !")
    print("Shift+A : Common Menu like reset transform , reset selected attribute.")
    print("Shift+Q : mGear Menu for rigger.")

    cmds.inViewMessage(
        amg="<hl>Marking Menus is Update , Check Script Editor for How to use.</hl>",
        pos="botCenter",
        fade=True,
    )