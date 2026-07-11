import inspect, re, importlib, math, configparser
from TonmaiToolkit.core import Misc, BlendShape, Utility, Create, Connection
from TonmaiToolkit.module.PySide import QtWidgets, QtCore, QtGui, QUiLoader, QtWidgets
import maya.cmds as mc
import pymel.core as pm
import os
from TonmaiToolkit import config
import json


def launch_toolkit(toolkit_name):
    """Launch Given Name of toolkit"""

    interface = importlib.import_module(
        "TonmaiToolkit.toolkits.{}.interface".format(toolkit_name)
    )
    importlib.reload(interface)

    window = interface.MainWindow()
    window.show(dockable=True)


def load_ui(ui_path):
    """Use to load .ui file by given path"""
    loader = QUiLoader()
    ui = QtCore.QFile(ui_path)
    ui.open(QtCore.QFile.ReadOnly)
    ui_return = loader.load(ui)
    ui.close()

    return ui_return


def load_ui_toolkit(toolkit_name):
    """Use to load .ui file by toolkit name (toolkit folder must be in default toolkit path)"""
    ui_path = os.path.join(config.TOOLKIT_PATH, toolkit_name, "ui.ui")

    loader = QUiLoader()
    ui = QtCore.QFile(ui_path)
    ui.open(QtCore.QFile.ReadOnly)
    ui_return = loader.load(ui)
    ui.close()

    return ui_return


def load_json_file_to_dict(file_path):
    """
    Open a file dialog to select a JSON file and return its contents as a Python dictionary.

    Returns:
        dict or None: Parsed JSON data if successful, or None if the user cancels or an error occurs.
    """

    if not os.path.isfile(file_path):
        mc.warning(f"File does not exist: {file_path}")
        return None

    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        return data

    except Exception as e:
        mc.warning(f"Failed to read JSON file: {e}")
        return None


def create_quick_data_folder():
    current_file_path = pm.sceneName()

    if not current_file_path:
        pm.confirmDialog(
            m="Please save this file, then try to create quick data folder again."
        )
        return

    pm.displayInfo("Create Quick Data Path at : ", current_file_path)


def open_file(file_path):
    try:
        with open(file_path, "r") as file_object:
            # The file is now open and accessible via 'file_object'
            content = file_object.read()
    except FileNotFoundError:
        print(f"Error: The file at '{file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


@Misc.undoable
def add_local_rig_from_file(
    file_path=os.path.normpath(
        "/home/users/natchapo/Documents/MayaCombineTest/FacialLocalRig/FacialRig.ma"
    ),
    parent_config={
        "main_mesh_group": "Geo_Grp",
        "rig_parent": ["rig", "neck_C0_head_ctl"],
        "mesh_parent": ["FclGeo_Grp", "LocalGeo_Grp"],
        "joint_parent": ["jnt_org", "jnt_org"],
        "geo_key_name": ["Body", "EyeBrows", "Cornea_L_Geo", "Cornea_R_Geo"],
    },
    root_source_controller="global_C0_ctl",
):

    print("######## Add Local Rig Descriptions ########")

    # extract variables
    current_mesh_grp = parent_config["main_mesh_group"]
    source_rig_grp, current_rig_grp = parent_config["rig_parent"]
    source_mesh_extra_grp, current_mesh_extra_grp = parent_config["mesh_parent"]
    source_joint_grp, current_joint_grp = parent_config["mesh_parent"]

    # check is current folder exist
    if not pm.objExists(current_rig_grp):
        pm.error(
            "- ✘ Rig group not exist in current scene : {}".format(current_rig_grp)
        )
    if not pm.objExists(current_mesh_grp):
        pm.error(
            "- ✘ Mesh group not exist in current scene : {}".format(current_mesh_grp)
        )
    if not pm.objExists(current_mesh_extra_grp):
        pm.error(
            "- ✘ Extra mesh group not exist in current scene : {}".format(
                current_mesh_extra_grp
            )
        )
    if not pm.objExists(current_joint_grp):
        pm.error(
            "- ✘ Joint group not exist in current scene : {}".format(current_joint_grp)
        )

    print("- ✔ Current File is Clean")

    # reference file
    # imported = mc.file(file_path, i=True, namespace=":localRig")
    reference = mc.file(file_path, reference=True, namespace=":localRig")
    print("- ✔ Referenced File : {}".format(reference))

    # check is reference folder exist
    if not pm.objExists("localRig:{}".format(source_rig_grp)):
        pm.error(
            "- ✘ Rig group not exist in reference scene : {}".format(source_rig_grp)
        )
    if not pm.objExists("localRig:{}".format(source_mesh_extra_grp)):
        pm.error(
            "- ✘ Extra mesh group not exist in reference scene : {}".format(
                source_mesh_extra_grp
            )
        )
    if not pm.objExists("localRig:{}".format(source_joint_grp)):
        pm.error(
            "- ✘ Joint group not exist in reference scene : {}".format(source_joint_grp)
        )

    print("- ✔ Referenced File is Clean")

    # parent rig group to rig parent
    grp_rig = Create.create_freeze_group(
        ["localRig:{}".format(parent_config["rig_parent"][0])]
    )[0]

    pm.parent(
        grp_rig,
        parent_config["rig_parent"][1],
    )
    print("- ✔ Parent Rig Group")

    # hide rig controller of local
    shapes = pm.listRelatives(
        "localRig:{}".format(root_source_controller), c=1, s=1, typ="nurbsCurve"
    )
    for shape in shapes:
        pm.setAttr("{}.visibility".format(shape), False)

    # parent joint group
    pm.parent("localRig:{}".format(source_joint_grp), current_joint_grp)
    print("- ✔ Parent Joint Group")

    # parent mesh group extra
    pm.parent("localRig:{}".format(source_mesh_extra_grp), current_mesh_extra_grp)
    pm.setAttr("localRig:{}.visibility".format(source_mesh_extra_grp), False)

    print("- ✔ Parent Mesh Group Extra")

    # Import Reference
    mc.file(reference, importReference=True)
    print("- ✔ Import Reference")

    # remove another
    if pm.objExists("localRig:Delete_Grp"):
        pm.delete("localRig:Delete_Grp")

    # remove namespace
    pm.namespace(moveNamespace=["localRig:", ":"], force=True)
    pm.namespace(rm="localRig:")

    # get local geo name
    local_geos_data = BlendShape.scan_local_geo_by_name(
        list_geo_group=parent_config["mesh_parent"][0],
        geo_key_name=parent_config["geo_key_name"],
    )

    # get main geo name
    main_geos_data = BlendShape.scan_local_geo_by_name(
        list_geo_group=parent_config["main_mesh_group"],
        geo_key_name=parent_config["geo_key_name"],
    )

    # create new dict blend shape local
    dict_blend_shape_local = {}

    for key in parent_config["geo_key_name"]:
        dict_blend_shape_local[key] = [local_geos_data[key][0], main_geos_data[key][0]]

    # create wrap mesh if vertex count not match
    for key in dict_blend_shape_local:
        local_geo = dict_blend_shape_local[key][0]
        main_geo = dict_blend_shape_local[key][1]

        local_geo_count = mc.polyEvaluate(str(local_geo), vertex=True)
        main_geo_count = mc.polyEvaluate(str(main_geo), vertex=True)

        if local_geo_count != main_geo_count:
            wrap_mesh = pm.duplicate(main_geo, n="{}_fullMesh_Geo".format(key))[0]
            pm.parent(wrap_mesh, parent_config["mesh_parent"][0])

            wrap_deformer = Create.create_wrap_deformer(
                source_wrap=wrap_mesh, target_wrap=local_geo
            )[0]

            pm.setAttr("{}.autoWeightThreshold".format(wrap_deformer), False)

            # update local geo
            dict_blend_shape_local[key][0] = str(wrap_mesh)

    # Add Blend Shape
    for key in dict_blend_shape_local:
        local_geo = dict_blend_shape_local[key][0]
        main_geo = dict_blend_shape_local[key][1]

        list_exist_blend_shape = BlendShape.get_blendshapes_from_mesh(main_geo)

        # add blend shape
        if list_exist_blend_shape:
            exist_bs_node = list_exist_blend_shape[0]

            bs_node = pm.blendShape(
                exist_bs_node, edit=True, t=(str(main_geo), 1, str(local_geo), 1.0)
            )[0]
            pm.setAttr("{}.{}".format(bs_node, local_geo), 1)

        # create blend shape:
        else:
            bs_node = pm.blendShape([local_geo], main_geo, o="local", at=True)[0]
            pm.setAttr("{}.{}".format(bs_node, local_geo), 1)

    print("- ✔ Connect Local Blend Shape to Current Mesh")
