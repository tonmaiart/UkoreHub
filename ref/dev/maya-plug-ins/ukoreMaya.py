import os

import maya.cmds as cmds
import maya.mel as mel
import maya.api.OpenMaya as om

from importlib import reload

import UkoreMaya
from UkoreMaya.core import menu_utils, Plugin, function, utils

# reload first launch
Plugin.reload_scripts()

# --------------------------------------------------------------------
# Menu Settings
# --------------------------------------------------------------------
MENU_MAIN = "UkoreStudioToolMenu"
MENU_LABEL = "Ukore Studio Tool"
MENU_PARENT = "MayaWindow"

list_menu_name = []


def maya_useNewAPI():
    pass


# --------------------------------------------------------------------
# Menu Creation
# --------------------------------------------------------------------
def loadMenu():
    global list_menu_name
    mel.eval("evalDeferred buildFileMenu")

    if not cmds.menu(f"{MENU_PARENT}|{MENU_MAIN}", exists=True):
        cmds.menu(
            MENU_MAIN,
            label=MENU_LABEL,
            parent=MENU_PARENT,
            tearOff=True,
            allowOptionBoxes=True,
        )

    cmds.menuItem(
        label="Ukore File Browser...",
        # image="contentBrowserGeneric.png",
        parent=MENU_MAIN,
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.browser()",
    )

    # cmds.menuItem(
    #     label="Publish...",
    #     # image="contentBrowserGeneric.png",
    #     parent=MENU_MAIN,
    #     command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.publisher()",
    # )



    cmds.menuItem(
        label="Quick Script...",
        # image="contentBrowserGeneric.png",
        parent=MENU_MAIN,
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.quick_script()",
    )
    # ---------------- Main ----------------
    cmds.menuItem(divider=True, dividerLabel="จัดการไฟล์", parent=MENU_MAIN)

    # cmds.menuItem(
    #     label="Publish Browser...",
    #     # image="confirm.png",
    #     parent=MENU_MAIN,
    #     command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.publish_browser()",
    # )

    # ---------------- Scene ----------------
    # cmds.menuItem(divider=True, parent=MENU_MAIN)

    cmds.menuItem(
        label="Save Increment",
        parent=MENU_MAIN,
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.save_increment()",
    )
    cmds.menuItem(
        label="Update All Reference and Picker",
        parent=MENU_MAIN,
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.update_references()",
    )

    cmds.menuItem(divider=True, dividerLabel="เครื่องมือของแผนก", parent=MENU_MAIN)

    # ---------------- Selection ----------------

    MENU_SELCTION = cmds.menuItem(
        subMenu=True,
        label="Selection",
        parent=MENU_MAIN,
        tearOff=True,
        image="selectObject.png",
    )
    cmds.menuItem(divider=True, dividerLabel="Scripts", parent=MENU_SELCTION)

    # cmds.menuItem(
    #     label="Select Ctrl L",
    #     parent=MENU_SELCTION,
    #     image="flipU.png",
    #     command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.flip_selection()",
    # )

    # cmds.menuItem(
    #     label="Select Ctrl R",
    #     parent=MENU_SELCTION,
    #     image="flipU.png",
    #     command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.flip_selection()",
    # )

    cmds.menuItem(divider=True, dividerLabel="Copy to Clipboard", parent=MENU_SELCTION)

    cmds.menuItem(
        label="Flip Selection",
        parent=MENU_SELCTION,
        image="flipU.png",
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.flip_selection()",
    )

    cmds.menuItem(
        label="Flip Selection Value...",
        parent=MENU_SELCTION,
        # image="flipU.png",
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.flip_animation_value()",
    )

    cmds.menuItem(divider=True, dividerLabel="Copy to Clipboard", parent=MENU_SELCTION)

    cmds.menuItem(
        label="Selected (LIST)",
        parent=MENU_SELCTION,
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.print_selected()",
        image="savePreset.png",
    )

    cmds.menuItem(
        label="Pair Selected (DICT)",
        parent=MENU_SELCTION,
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.selected_to_dict()",
        image="savePreset.png",
    )

    cmds.menuItem(divider=True, dividerLabel="Sort by Type", parent=MENU_SELCTION)

    cmds.menuItem(
        label="Anim Control",
        parent=MENU_SELCTION,
        command='import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.sort_type("anim_curve")',
    )
    cmds.menuItem(
        label="transform",
        parent=MENU_SELCTION,
        command='import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.sort_type("transform")',
    )
    cmds.menuItem(
        label="joint",
        parent=MENU_SELCTION,
        command='import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.sort_type("joint")',
    )
    cmds.menuItem(
        label="nurbsCurve",
        parent=MENU_SELCTION,
        command='import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.sort_type("nurbsCurve")',
    )

    cmds.menuItem(
        label="Custom...",
        parent=MENU_SELCTION,
        command='import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.sort_type("custom")',
    )

    # ---------------- Common ----------------

    MENU_COMMON = cmds.menuItem(
        subMenu=True,
        label="Common",
        parent=MENU_MAIN,
        tearOff=True,
        image="layerEditor.png",
    )

    cmds.menuItem(divider=True, dividerLabel="Tools", parent=MENU_COMMON)

    cmds.menuItem(
        label="Renamer",
        parent=MENU_COMMON,
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.renamer()",
    )
    cmds.menuItem(
        label="Attribute",
        parent=MENU_COMMON,
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.attribute()",
    )

    cmds.menuItem(divider=True, dividerLabel="Scripts", parent=MENU_COMMON)

    cmds.menuItem(
        label="Reset Transform",
        parent=MENU_COMMON,
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.reset_transform()",
    )

    cmds.menuItem(
        label="Smart Parent",
        parent=MENU_COMMON,
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.smart_parent()",
    )

    cmds.menuItem(divider=True, parent=MENU_COMMON)

    cmds.menuItem(
        label="Lock Attribute",
        parent=MENU_COMMON,
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.lock_attr()",
    )
    cmds.menuItem(
        label="Unlock Attribute",
        parent=MENU_COMMON,
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.unlock_attr()",
    )

    cmds.menuItem(divider=True, parent=MENU_COMMON)

    # -------------- Model ----------------

    MENU_MODEL = cmds.menuItem(
        subMenu=True,
        label="Model / Texture",
        parent=MENU_MAIN,
        tearOff=True,
        image="cube.png",
    )

    cmds.menuItem(divider=True, dividerLabel="Scripts", parent=MENU_MODEL)

    cmds.menuItem(
        label="Auto Position to Grid from Selected",
        parent=MENU_MODEL,
        ann="Transform Each Mesh for grid",
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.auto_position_to_grid()",
    )
    cmds.menuItem(divider=True, parent=MENU_MODEL)

    cmds.menuItem(
        label="Validate Selected Materials Naming",
        parent=MENU_MODEL,
        ann="Export Selection for Substance Painter",
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.validate_material()",
    )

    cmds.menuItem(
        label="Validate Selected Facesets",
        parent=MENU_MODEL,
        ann="Export Selection for Substance Painter",
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.validate_facesets()",
    )

    cmds.menuItem(
        label="Validate Unwanted UV Sets",
        parent=MENU_MODEL,
        ann="Export Selection for Substance Painter",
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.validate_uv_map()",
    )
    cmds.menuItem(divider=True, parent=MENU_MODEL)

    cmds.menuItem(
        label="Remove UV Sets to single sets",
        parent=MENU_MODEL,
        ann="Export Selection for Substance Painter",
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.cleanup_uvmap()",
    )

    cmds.menuItem(divider=True, parent=MENU_MODEL)

    cmds.menuItem(
        label="Export Selected to Fbx Single...",
        parent=MENU_MODEL,
        ann="Export Selection for Substance Painter",
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.export_selected_to_substance()",
    )

    cmds.menuItem(
        label="Export Selected to Fbx Multiple...",
        parent=MENU_MODEL,
        ann="Export Selection for Substance Painter",
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.export_selected_to_multiple()",
    )

    # ---------------- Rig ----------------
    MENU_RIG = cmds.menuItem(
        subMenu=True, label="Rig", image="kinJoint.png", parent=MENU_MAIN, tearOff=True
    )

    cmds.menuItem(divider=True, dividerLabel="Tools", parent=MENU_RIG)

    cmds.menuItem(
        label="Local Script...",
        # image="contentBrowserGeneric.png",
        parent=MENU_RIG,
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.python_reader()",
    )
    cmds.menuItem(
        label="Quick Data",
        parent=MENU_RIG,
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.quickdata()",
    )

    cmds.menuItem(
        label="Easy Controller",
        parent=MENU_RIG,
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.easy_controller()",
    )

    cmds.menuItem(
        label="Snapper",
        parent=MENU_RIG,
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.snapper()",
    )

    cmds.menuItem(
        label="Weight Puller",
        parent=MENU_RIG,
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.weight_puller()",
    )

    cmds.menuItem(divider=True, dividerLabel="External Tools", parent=MENU_RIG)

    cmds.menuItem(
        label="Advanced Skeleton",
        parent=MENU_RIG,
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.run_advanced()",
    )

    cmds.menuItem(
        label="Advanced Skeleton Face",
        parent=MENU_RIG,
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.run_advanced_face()",
    )

    cmds.menuItem(
        label="ngSkinTools",
        parent=MENU_RIG,
        command="import ngSkinTools2; ngSkinTools2.open_ui()",
    )

    cmds.menuItem(divider=True, dividerLabel="Scripts", parent=MENU_RIG)

    # Auto Constraint
    constraint_menu = cmds.menuItem(
        subMenu=True, label="Auto Constraint", parent=MENU_RIG, tearOff=True
    )
    for text, mode in [
        ("Parent + Scale", "all"),
        ("Parent", "parent"),
        ("Point", "point"),
        ("Orient", "orient"),
        ("Scale", "scale"),
    ]:
        cmds.menuItem(
            label=text,
            parent=constraint_menu,
            command=f'import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.auto_constraint("{mode}")',
        )

    # Auto Connection
    conn_menu = cmds.menuItem(
        subMenu=True, label="Auto Connection", parent=MENU_RIG, tearOff=True
    )
    for text, mode in [
        ("All", "all"),
        ("Translate", "translate"),
        ("Rotate", "rotate"),
        ("Scale", "scale"),
    ]:
        cmds.menuItem(
            label=text,
            parent=conn_menu,
            command=f'import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.auto_connection("{mode}")',
        )

    cmds.menuItem(divider=True, parent=MENU_RIG)

    cmds.menuItem(
        label="Add Follicle Pin",
        parent=MENU_RIG,
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.follicle_pin()",
    )

    cmds.menuItem(
        label="Freeze Group",
        parent=MENU_RIG,
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.freeze_group()",
    )

    cmds.menuItem(divider=True, parent=MENU_RIG)

    cmds.menuItem(
        label="Create Joint Set",
        parent=MENU_RIG,
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.create_joint_set()",
    )

    cmds.menuItem(
        label="Copy Mesh Shape",
        parent=MENU_RIG,
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.copy_shape()",
    )

    cmds.menuItem(divider=True, parent=MENU_RIG)

    cmds.menuItem(
        label="Copy Skin Weight",
        parent=MENU_RIG,
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.copy_skin_weight()",
    )

    cmds.menuItem(
        label="Add Multi Skin Cluster",
        parent=MENU_RIG,
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.add_multi_skin()",
    )

    # ---------------- Animation ----------------
    MENU_ANIM = cmds.menuItem(
        subMenu=True,
        label="Animation",
        image="character.svg",
        parent=MENU_MAIN,
        tearOff=True,
    )

    cmds.menuItem(divider=True, dividerLabel="ปลั้กอิน", parent=MENU_ANIM)

    cmds.menuItem(
        label="Dreamwall Picker",
        parent=MENU_ANIM,
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.dreamwall_picker()",
    )

    cmds.menuItem(
        label="Studio Library",
        parent=MENU_ANIM,
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.studio_library()",
    )

    cmds.menuItem(
        label="Shot Splitter",
        parent=MENU_ANIM,
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.shot_splitter()",
    )
    cmds.menuItem(divider=True, parent=MENU_ANIM)

    cmds.menuItem(
        label="Quick Playblast",
        parent=MENU_ANIM,
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.playblast()",
    )

    # ---------------- Simulation ----------------
    # MENU_SIM = cmds.menuItem(
    #     subMenu=True,
    #     label="Simulate",
    #     parent=MENU_MAIN,
    #     tearOff=True,
    #     image="nClothDisplayCurrent.png",
    # )

    # cmds.menuItem(
    #     label="CFX Tools...",
    #     parent=MENU_SIM,
    #     command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.cfx_tools()",
    # )

    # # ---------------- Developer ----------------
    # cmds.menuItem(divider=True, dividerLabel="สำหรับทีมพัฒนา", parent=MENU_MAIN)

    # MENU_DEV = cmds.menuItem(
    #     subMenu=True,
    #     label="คำสั่งทดสอบ",
    #     parent=MENU_MAIN,
    #     tearOff=True,
    #     # image="123d.png",
    # )

    # cmds.menuItem(
    #     label="Set Faster Plugin",
    #     parent=MENU_DEV,
    #     command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.faster_plugin()",
    # )

    # cmds.menuItem(
    #     label="ติดตั้งและเปิดใช้เมนูเสริม",
    #     parent=MENU_MAIN,
    #     command="from UkoreMaya.core import utils; utils.setup_marking_menus()",
    # )

    # ---------------- Help ----------------

    # cmds.menuItem(
    #     label="อ่านคู่มือการใช้งาน...",
    #     parent=MENU_MAIN,
    #     image="info.png",
    #     command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.documentation()",
    # )
    # cmds.menuItem(divider=True, dividerLabel="About", parent=MENU_MAIN)

    # ---------------- Marking Menu ----------------

    cmds.menuItem(divider=True, parent=MENU_MAIN)

    # ---------------- Reload Plugins ----------------

    cmds.menuItem(
        label="รีโหลด Plug-ins",
        parent=MENU_MAIN,
        image="rebuild.png",
        command="import UkoreMaya; from UkoreMaya.core import menu_utils; menu_utils.reload_plugins()",
    )

    list_menu_name = [
        MENU_SELCTION,
        MENU_ANIM,
        MENU_COMMON,
        MENU_MODEL,
        MENU_RIG,
        # MENU_SIM,
        # MENU_DEV,
    ]
    utils.setup_marking_menus()


# --------------------------------------------------------------------
def unloadMenuItem():
    """Clear Toolkit menu on plugin unload"""

    def clear(menu):
        if cmds.menu(menu, exists=True):
            items = cmds.menu(menu, q=True, itemArray=True) or []
            for i in items:
                cmds.deleteUI(i)

    if cmds.menu(f"{MENU_PARENT}|{MENU_MAIN}", exists=True):
        clear(MENU_MAIN)
        cmds.deleteUI(f"{MENU_PARENT}|{MENU_MAIN}", menu=True)


# --------------------------------------------------------------------
def initializePlugin(plugin):
    pluginFn = om.MFnPlugin(plugin)

    function.auto_launch_ukore_file_browser()

    loadMenu()


def uninitializePlugin(plugin):
    pluginFn = om.MFnPlugin(plugin)
    unloadMenuItem()
