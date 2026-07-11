import pymel.core as pm
from TonmaiToolkit.core import Utility, Misc, File, SkinWeight, Controller, Transform
from TonmaiToolkit.menu import Help, General
import os, json
import maya.cmds as mc
import importlib.util
from importlib import reload
import TonmaiToolkit


def get_quick_data_dir():
    current_file_path = pm.sceneName()

    # if file not save yet
    if not current_file_path:
        return False

    dir_path = os.path.dirname(current_file_path)
    quick_data_path = os.path.join(dir_path, "QuickData")

    # if dir exist
    if os.path.exists(quick_data_path):
        return quick_data_path

    # if dir not exist
    else:
        return False


def backup_controller_and_skin():
    """Backup both controller and skin data (Dont have to select mesh to backup skin)"""

    export_shape_quick()

    # select skin cluster node
    pm.select(pm.ls(typ="transform"))
    export_skin_quick()


def apply_controller_and_skin():
    """Apply both controller and skin data (Dont have to select mesh to apply skin)"""

    import_shape_quick()

    # select skin cluster node
    pm.select(pm.ls(typ="transform"))
    import_skin_quick()


def get_missing_joint_by_json_data(skin_dict):
    """Return missing joint in scene by given json dictionary"""

    dict_weight = skin_dict["deformerWeight"]["weights"]

    list_missing_joints = []

    for weight in dict_weight:

        if not pm.objExists(weight["source"]):
            list_missing_joints.append(weight["source"])

    return list_missing_joints


@Misc.undoable
def import_skin_quick():
    quick_data_path = get_quick_data_dir()
    quick_data_skin_path = os.path.join(quick_data_path, "Skin")

    selection = pm.ls(sl=1)

    if not selection:
        pm.displayWarning("Selection required before import")
        return

    list_not_found = []
    # iterate for each selection
    for sel in selection:
        json_file = os.path.join(quick_data_skin_path, Utility.cut(str(sel)) + ".json")

        if not os.path.exists(json_file):
            list_not_found.append(sel)
            continue

        # load json file
        dict_data = File.load_json_file_to_dict(json_file)
        target_shape = dict_data["deformerWeight"]["shapes"][0]["name"]

        # find missing joint
        missing_joints = get_missing_joint_by_json_data(dict_data)

        if missing_joints:
            if not pm.objExists("missing_joint_grp"):
                pm.group(n="missing_joint_grp", em=1)

            for name in missing_joints:
                joint = pm.createNode("joint", n=name)
                pm.parent(joint, "missing_joint_grp")

            pm.displayWarning(
                "Missing Joint found for : {}".format(
                    dict_data["deformerWeight"]["headerInfo"]["fileName"]
                )
            )

        # is shape exist
        if not pm.objExists(target_shape):
            list_not_found.append(sel)
            continue

        # delete old skin cluster
        old_skin_cluster = SkinWeight.get_skin_cluster_node(target_shape)

        if old_skin_cluster:
            pm.delete(old_skin_cluster)

        # create new skin cluster node
        list_bind_joints = []

        for weight in dict_data["deformerWeight"]["weights"]:
            list_bind_joints.append(weight["source"])

        if pm.objectType(target_shape, isa="nurbsSurface"):
            target_shape = pm.listRelatives(target_shape, p=1)[0]

        node_skin_cluster = pm.skinCluster(
            target_shape,
            list_bind_joints,
            n=dict_data["deformerWeight"]["weights"][0]["deformer"],
            tsb=1,
            ih=1,
            bm=0,
        )

        # import weight
        file_path = os.path.normpath(
            dict_data["deformerWeight"]["headerInfo"]["fileName"]
        )
        dir_path = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)

        pm.deformerWeights(
            file_name,
            im=1,
            method="index",
            deformer=node_skin_cluster,
            path=dir_path,
        )

        pm.select(target_shape)
        pm.skinPercent(node_skin_cluster, normalize=True)

    if list_not_found:
        pm.warning("Not Found mesh for apply : {}".format(list_not_found))

    pm.inViewMessage(
        amg="<hl> Skin Apply!</hl>", pos="botCenter", fit=20, fts=16, fade=True
    )


@Misc.undoable
def import_skin_custom(file_paths=""):
    if not file_paths:
        # browse .json
        file_paths = pm.fileDialog2(
            fileMode=4, dialogStyle=2, fileFilter="Json Files (*.json)"
        )

        if not file_paths:
            return

    # iterate for each browse
    for path in file_paths:
        dict_data = File.load_json_file_to_dict(path)
        target_shape = dict_data["deformerWeight"]["shapes"][0]["name"]

        # find missing joint
        missing_joints = get_missing_joint_by_json_data(dict_data)

        if missing_joints:
            if not pm.objExists("missing_joint_grp"):
                pm.createNode("transform", n="missing_joint_grp")

            for name in missing_joints:
                joint = pm.createNode("joint", n=name)
                pm.parent(joint, "missing_joint_grp")

            pm.displayWarning(
                "Missing Joint found for : {}".format(
                    dict_data["deformerWeight"]["headerInfo"]["fileName"]
                )
            )

        # is shape exist
        if not pm.objExists(target_shape):
            pm.displayWarning(m="Skip, Not Found Shape : {}".format(target_shape))
            continue

        # delete old skin cluster
        old_skin_cluster = SkinWeight.get_skin_cluster_node(target_shape)

        if old_skin_cluster:
            pm.delete(old_skin_cluster)

        # create new skin cluster node
        list_bind_joints = []

        for weight in dict_data["deformerWeight"]["weights"]:
            list_bind_joints.append(weight["source"])

        node_skin_cluster = pm.skinCluster(
            target_shape,
            list_bind_joints,
            n=dict_data["deformerWeight"]["weights"][0]["deformer"],
            tsb=1,
            ih=1,
            bm=0,
        )

        # import weight
        file_path = os.path.normpath(
            dict_data["deformerWeight"]["headerInfo"]["fileName"]
        )
        dir_path = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)

        pm.deformerWeights(
            file_name,
            im=1,
            method="index",
            deformer=node_skin_cluster,
            path=dir_path,
        )
        pm.select(target_shape)
        pm.skinPercent(node_skin_cluster, normalize=True)

    pm.inViewMessage(
        amg="<hl> Apply Skin!</hl>", pos="botCenter", fit=20, fts=16, fade=True
    )


@Misc.undoable
def export_skin_quick():
    """
    Use for export selected skin cluster

    """

    quick_data_path = get_quick_data_dir()
    quick_data_skin_path = os.path.join(quick_data_path, "Skin")

    # get skin cluster
    list_skin_cluster = []
    list_mesh_name = []

    selection = pm.ls(sl=1, typ="transform")

    if not selection:
        pm.displayWarning("Selection required before import")
        return

    if not selection:
        pm.displayWarning("Skin cluster node not found on selection")
        return

    for sel in selection:
        if not pm.listRelatives(sel, c=1, typ="mesh"):
            continue

        skin_cluster_node = SkinWeight.get_skin_cluster_node(mesh_node=sel)

        if skin_cluster_node:
            list_skin_cluster.append(skin_cluster_node)
            list_mesh_name.append(Utility.cut(str(sel)))

    # export .json
    file_path = os.path.normpath(quick_data_skin_path)
    print(file_path)

    for node, mesh_name in dict(zip(list_skin_cluster, list_mesh_name)).items():
        save_name = "{}.json".format(mesh_name)

        mc.deformerWeights(
            save_name,
            export=True,
            deformer=node.longName(),
            format="JSON",
            path=file_path,
        )

    pm.inViewMessage(
        amg="<hl> Write Skin Weight!</hl>", pos="botCenter", fit=20, fts=16, fade=True
    )


@Misc.undoable
def export_skin_custom(file_path=""):
    """
    Use for export selected skin cluster

    """
    # get skin cluster
    list_skin_cluster = []
    list_mesh_name = []

    selection = pm.ls(sl=1, typ="transform")

    if not selection:
        pm.displayWarning("Skin cluster node not found on selection")
        return

    list_not_found = []
    for sel in selection:
        skin_cluster_node = SkinWeight.get_skin_cluster_node(mesh_node=sel)

        if skin_cluster_node:
            list_skin_cluster.append(skin_cluster_node)
            list_mesh_name.append(Utility.cut(str(sel)))
        else:
            list_not_found.append(sel)

    # display warning
    if list_not_found:
        pm.warning("Skin cluster not found for : {} ".format(list_not_found))

    # browse export directory
    if not file_path:
        start_dir_path = pm.workspace(q=True, rd=True)
        file_path = pm.fileDialog2(fileMode=3, dialogStyle=2, dir=start_dir_path)

        if file_path:
            file_path = file_path[0]
        else:
            return

    # export .json
    file_path = os.path.normpath(file_path)

    for node, mesh_name in dict(zip(list_skin_cluster, list_mesh_name)).items():
        save_name = "{}.json".format(mesh_name)

        mc.deformerWeights(
            save_name,
            export=True,
            deformer=node.longName(),
            format="JSON",
            path=file_path,
        )

    pm.inViewMessage(
        amg="<hl> Skin have Backup!</hl>", pos="botCenter", fit=20, fts=16, fade=True
    )


def import_shape_quick():
    quick_data_path = get_quick_data_dir()

    current_file_path = pm.sceneName()
    current_file_name = os.path.basename(current_file_path)
    current_file_name_only = os.path.splitext(current_file_name)[0]
    key_name = current_file_name.split("_")[0]
    read_path = os.path.join(quick_data_path, "Controller", "{}.json".format(key_name))

    if os.path.exists(read_path):
        import_shape_custom(file_path=read_path)
        pm.inViewMessage(
            amg="<hl> Controller Apply!</hl>",
            pos="botCenter",
            fit=20,
            fts=16,
            fade=True,
        )

    else:
        pm.displayWarning("{}.json not found".format(key_name))


def build_and_read():
    build_current()
    apply_controller_and_skin()


def build_current():
    selection = [str(node) for node in pm.ls(sl=1)]

    if not pm.objExists("guide"):
        pm.error()
        return

    from mgear import shifter

    pm.select(cl=1)

    if pm.objExists("rig"):
        pm.delete("rig")

    Help.reload_scripts()

    shifter.reloadComponents()

    from mgear.shifter import guide_manager

    guide_manager.build_from_selection()

    if pm.objExists("guide"):
        pm.setAttr("guide.v", False)

    pm.select(cl=True)

    for sel in selection:
        if pm.objExists(sel):
            pm.select(sel, add=True)

    pm.inViewMessage(
        amg="<hl> Build Complete!</hl>", pos="botCenter", fit=20, fts=16, fade=True
    )


def remove_rig():
    if pm.objExists("rig"):
        pm.delete("rig")

    if pm.objExists("guide"):
        pm.setAttr("guide.v", True)

    pm.inViewMessage(
        amg="<hl> Rig Removed!</hl>", pos="botCenter", fit=20, fts=16, fade=True
    )


def remove_all_shaders_pm():
    # Get all shading engines
    shading_engines = pm.ls(type="shadingEngine")

    # Exclude defaults
    default_sg = {"initialShadingGroup", "initialParticleSE"}
    shading_engines = [sg for sg in shading_engines if sg.name() not in default_sg]

    for sg in shading_engines:
        # Find connected materials
        materials = []
        for attr in ["surfaceShader", "volumeShader", "displacementShader"]:
            if sg.attr(attr).isConnected():
                mats = sg.attr(attr).inputs()
                materials.extend(mats)

        # Delete shading engine + connected materials
        try:
            pm.delete(list(set(materials + [sg])))
            print("Deleted:", sg, "with:", materials)
        except:
            print("Could not delete:", sg)

    print("✅ Removed all non-default shaders (pymel).")


def cleanup_scene():
    # --- Remove Grease Pencil nodes ---
    grease_pencils = mc.ls(type="greasePencil")
    if grease_pencils:
        mc.delete(grease_pencils)
        print("Removed grease pencil nodes:", grease_pencils)
    else:
        print("No grease pencil nodes found.")

    grease_pencils = mc.ls(type="greasePlane")
    if grease_pencils:
        mc.delete(grease_pencils)
        print("Removed grease pencil nodes:", grease_pencils)
    else:
        print("No grease pencil nodes found.")

    # --- Remove Display Layers (except defaultLayer) ---
    display_layers = mc.ls(type="displayLayer")
    for layer in display_layers:
        if layer != "defaultLayer":
            try:
                mc.delete(layer)
                print("Removed display layer:", layer)
            except:
                print("Could not delete display layer:", layer)

    print("Scene cleanup completed!")


def reload_all_references():
    # list all references
    refs = mc.file(query=True, reference=True)

    if not refs:
        mc.warning("No references found in the scene.")
        return

    for ref in refs:
        try:
            # reload reference
            mc.file(ref, loadReference=True)
            print("Reloaded reference:", ref)
        except Exception as e:
            mc.warning("Failed to reload reference: {} | {}".format(ref, e))


def hero_ctrl():
    if not pm.objExists("guide"):
        raise Exception("not found Guide")

    # create folder
    quick_data_path = get_quick_data_dir()

    if not quick_data_path:
        raise (Exception("Create Quick Data First"))

    hero_ctrl_path = os.path.join(quick_data_path, "Hero")
    os.makedirs(hero_ctrl_path, exist_ok=True)

    # run mgear
    build_and_read()

    if pm.objExists("Delete_Grp"):
        pm.delete("Delete_Grp")

    if pm.objExists("guide"):
        pm.delete("guide")

    pm.rename("rig", "Rig_Grp")

    remove_all_shaders_pm()
    cleanup_scene()

    # save to new path // force overwrite
    current_name = get_current_file_keyword()
    save_name = "{}_HeroCtrl.ma".format(current_name)
    new_file_path = os.path.join(hero_ctrl_path, save_name)

    print("hero ctrl path : ", hero_ctrl_path)
    pm.displayInfo("Save name : {}".format(save_name))
    pm.displayInfo("Hero Ctrl to path : {}".format(new_file_path))

    # Rename the current scene to the new path
    mc.file(rename=new_file_path)
    # Save the file with the specified type and force overwrite
    mc.file(save=True, type="mayaAscii", force=True)

    pm.inViewMessage(
        amg="<hl> Hero Ctrl Complete!</hl>", pos="botCenter", fit=20, fts=16, fade=True
    )


def hero_hi():
    # create folder
    quick_data_path = get_quick_data_dir()

    if not quick_data_path:
        raise (Exception("Create Quick Data First"))

    heor_hi_path = os.path.join(quick_data_path, "Hero")
    os.makedirs(heor_hi_path, exist_ok=True)

    # run mgear
    if pm.objExists("Delete_Grp"):
        pm.delete("Delete_Grp")

    # remove_all_shaders_pm()
    General.sort_by_type(typ="anim_curve")
    controllers = pm.ls(sl=1)

    for ctrl in controllers:
        Transform.reset_transform(ctrl)

    Misc.clear_controller_animation()
    Misc.import_all_references()
    Misc.remove_all_namespaces()
    cleanup_scene()

    pm.setAttr("Rig_Grp.jnt_vis", False)
    pm.setAttr("Rig_Grp.ctl_vis_on_playback", True)

    # # save to new path // force overwrite
    # current_name = get_current_file_keyword()
    # save_name = "{}_HeroHi.ma".format(current_name)
    # new_file_path = os.path.join(heor_hi_path, save_name)

    # mc.file(rename=new_file_path)
    # mc.file(save=True, type="mayaAscii", force=True)

    # pm.inViewMessage(
    #     amg="<hl> Hero Hi Complete!</hl>", pos="botCenter", fit=20, fts=16, fade=True
    # )


def open_quick_data_folder():
    quick_data_path = get_quick_data_dir()

    if os.path.exists(quick_data_path):
        os.startfile(quick_data_path)


def open_controller_folder():
    quick_data_path = get_quick_data_dir()
    path = os.path.join(quick_data_path, "Controller")

    if os.path.exists(path):
        os.startfile(path)


def open_local_rig_config_folder():
    quick_data_path = get_quick_data_dir()
    path = os.path.join(quick_data_path, "LocalRigConfig")

    os.makedirs(path, exist_ok=True)

    os.startfile(path)


def open_skin_folder():
    quick_data_path = get_quick_data_dir()
    path = os.path.join(quick_data_path, "Skin")

    if os.path.exists(path):
        os.startfile(path)


def get_current_file_keyword():
    current_file_path = pm.sceneName()
    current_file_name = os.path.basename(current_file_path)
    current_file_name_only = os.path.splitext(current_file_name)[0]
    key_name = current_file_name.split("_")[0]

    return key_name


def export_shape_quick():
    quick_data_path = get_quick_data_dir()

    current_file_path = pm.sceneName()
    current_file_name = os.path.basename(current_file_path)
    current_file_name_only = os.path.splitext(current_file_name)[0]
    key_name = current_file_name.split("_")[0]
    path = os.path.join(quick_data_path, "Controller", "{}.json".format(key_name))

    export_shape_custom(file_path=path)

    pm.inViewMessage(
        amg="<hl>Controller Backup!</hl>", pos="botCenter", fit=20, fts=16, fade=True
    )


def export_shape_custom(file_path=""):
    """
    Export curve shape data of one or more NURBS controllers to a JSON file.

    The exported JSON structure:
    {
        "controllerName": {
            "shapeNodeName": {
                "colorData": [
                    None, None                    -> override disabled
                    [True, colorIndex]            -> override enabled with index color
                    [False, (r, g, b)]            -> override enabled with RGB color
                ],
                "cvPositions": [[x, y, z], ...],  # World-space positions of each CV
                "lineWidth": float               # Line width of the curve
            }
        }
    }

    Args:
        controllers (str or list of str): One or more controller transform names.

    A file dialog will appear for the user to choose the save location for the JSON file.
    """

    # if selection will export selection

    controllers = Utility.sort_by_type(list_target=pm.ls(), typ="anim_curve")
    if isinstance(controllers, str):
        controllers = [controllers]

    # append advance skeleton shape
    if pm.objExists("ControlSet"):
        pm.select("ControlSet")
        advance_ctrls = pm.ls(sl=1)

        for ctrl in advance_ctrls:
            if pm.listRelatives(ctrl, c=1, s=1, typ="nurbsCurve"):
                controllers.append(ctrl)

    data = {}

    for ctrl_name in controllers:
        try:
            ctrl = pm.PyNode(ctrl_name)
        except:
            pm.warning(f"Controller '{ctrl_name}' does not exist.")
            continue

        if not ctrl.getShapes():
            pm.warning(f"'{ctrl}' has no shapes.")
            continue

        # Write Data
        for shape in ctrl.getShapes(noIntermediate=True):
            if isinstance(shape, pm.nodetypes.NurbsCurve):
                shape_data = {}

                # Color data
                if not shape.overrideEnabled.get():
                    shape_data["colorData"] = [None, None]
                else:
                    if shape.overrideRGBColors.get():
                        rgb = (
                            round(shape.overrideColorR.get(), 3),
                            round(shape.overrideColorG.get(), 3),
                            round(shape.overrideColorB.get(), 3),
                        )
                        shape_data["colorData"] = [False, rgb]
                    else:
                        shape_data["colorData"] = [True, shape.overrideColor.get()]

                # CV positions
                shape_data["cvPositions"] = [
                    [round(p.x, 4), round(p.y, 4), round(p.z, 4)]
                    for p in [pm.pointPosition(cv, local=True) for cv in shape.cv[:]]
                ]

                # Line width
                shape_data["lineWidth"] = shape.lineWidth.get()

                # Degree
                shape_data["degree"] = pm.getAttr("{}.degree".format(shape))

                # Spans
                shape_data["spans"] = pm.getAttr("{}.spans".format(shape))

                # Form
                shape_data["form"] = pm.getAttr("{}.form".format(shape))

                data.setdefault(ctrl.name(), {})[shape.name()] = shape_data

    if not data:
        pm.warning("No valid controllers found. Nothing to export.")
        return

    # Determine default path
    if not file_path:
        scene_path = pm.sceneName()
        default_dir = (
            os.path.dirname(scene_path)
            if scene_path
            else pm.workspace(q=True, rootDirectory=True)
        )

        file_path = pm.fileDialog2(
            fileMode=0,
            dialogStyle=2,
            startingDirectory=default_dir,
            fileFilter="JSON Files (*.json)",
        )

        if not file_path:
            return
        else:
            file_path = file_path[0]

    # Save JSON
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

    pm.displayInfo("Exported Controller to : {}".format(file_path))


@Misc.undoable
def import_shape_custom(file_path=""):
    if not file_path:
        file_path = pm.fileDialog2(
            fileFilter="JSON Files (*.json)",
            dialogStyle=2,
            caption="Load JSON File",
            fileMode=1,  # Open file
        )

        if not file_path:
            print("Load canceled.")
            return None
        else:
            file_path = file_path[0]

    dict_json = File.load_json_file_to_dict(file_path=file_path)
    list_not_exist = []
    # iterate to set up shape
    for ctrl_name in dict_json.keys():
        if pm.objExists(ctrl_name):
            dict_curve_data = dict_json[ctrl_name]

            # create new controller shape
            tmp_ctrl = Controller.create_curve_from_data(dict_curve_data)

            if not tmp_ctrl:
                continue

            Controller.clone_shape([ctrl_name, tmp_ctrl])
            Controller.clone_style([ctrl_name, tmp_ctrl])

            pm.delete(tmp_ctrl)

        else:
            list_not_exist.append(ctrl_name)

    if list_not_exist:
        pm.warning("Does not exist control : {}".format(list_not_exist))


def create_script():
    quick_data_path = get_quick_data_dir()

    if not quick_data_path:
        raise Exception(
            "Quick Data Path not found. make sure you have save current file and create quick data."
        )

    script_path = os.path.join(quick_data_path, "Python")

    # make sure path exist
    os.makedirs(script_path, exist_ok=True)

    # check is scene raw name.py exist
    scene_path = pm.sceneName()
    scene_name = os.path.basename(scene_path)
    scene_name_raw = os.path.splitext(scene_name)[0]
    scene_name_keyword = scene_name_raw.split("_")[0]
    python_path = os.path.join(script_path, "{}.py".format(scene_name_keyword))

    # if python path not exist, create the new one
    if os.path.exists(python_path):
        pass
        # raise Exception("Cannot overwrite the exist script .py")
    else:
        script_content = """import pymel.core as pm
from TonmaiToolkit.core import BlendShape,Connection,Create,Misc,Transform,Utility,SkinWeight,File,Controller,QuickData
from TonmaiToolkit.menu import General,Rig,Simulation,Skin,Help
import os
import json
import maya.cmds as mc
import maya.api.OpenMaya as om

Help.reload_scripts()

@Misc.undoable_jump_point
def run():
    return
        """

        with open(python_path, "w") as f:
            f.write(script_content)

        print("Created new script : {}".format(python_path))

    # make sure .env is created
    env_path = os.path.join(script_path, ".env")
    tonmai_toolkit_dir = os.path.dirname(TonmaiToolkit.__file__)
    path_level_1 = os.path.dirname(tonmai_toolkit_dir)
    path_level_2 = os.path.dirname(path_level_1)

    env_content = "PYTHONPATH={}".format(path_level_1)

    with open(env_path, "w") as f:
        f.write(env_content)

    print("env : path", env_path)
    # open the script
    try:
        os.startfile(python_path)
    except:
        pm.warning("Cannot Start File (Only Support in Windows Os)")


def open_script_folder():
    quick_data_path = get_quick_data_dir()
    path = os.path.join(quick_data_path, "Python")

    os.makedirs(path, exist_ok=True)

    os.startfile(path)


def run_script_file():
    quick_data_path = get_quick_data_dir()

    if not quick_data_path:
        raise Exception(
            "Quick Data Path not found. make sure you have save current file and create quick data."
        )

    script_path = os.path.join(quick_data_path, "Python")

    # make sure path exist
    os.makedirs(script_path, exist_ok=True)

    # check is scene raw name.py exist
    scene_path = pm.sceneName()
    scene_name = os.path.basename(scene_path)
    scene_name_raw = os.path.splitext(scene_name)[0]
    scene_name_keyword = scene_name_raw.split("_")[0]
    python_path = os.path.join(script_path, "{}.py".format(scene_name_keyword))

    # run script file
    spec = importlib.util.spec_from_file_location(scene_name_keyword, python_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # reload(module)

    module.run()

    pm.displayInfo("Run Script : {}".format(script_path))

    return
    #
    # try:
    #     # Now you can use its functions
    # except:
    #     raise Exception("Can run function , make you have define def run():")


def jump_point():
    """
    Undoes actions until it reaches an undo chunk with the specified name.
    """
    target_name = "JumpPoint"
    undo_count = 0

    # Loop as long as the undo queue is not empty
    while True:
        # Get the name of the action at the top of the queue
        current_action_name = pm.undoInfo(query=True, undoName=True)

        # If the current action is our target, we've arrived. Stop the loop.
        if current_action_name == target_name:
            pm.displayInfo("Jump Point : Undo to before run done.")
            pm.undo()

            break

        # If we've reached the end of the queue without finding the target, stop.
        if current_action_name == "Undo":
            print(f"Reached the end of the undo queue without finding '{target_name}'.")
            break

        # If it's not the target, perform one undo and let the loop continue.
        try:
            pm.undo()
        except:
            for i in range(undo_count):
                pm.redo()

            pm.warning("Jump Point Not Found")
            break

        undo_count += 1
