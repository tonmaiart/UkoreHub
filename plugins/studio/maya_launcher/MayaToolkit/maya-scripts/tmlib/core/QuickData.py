from tmlib.core import Scene, Utility, File, SkinWeight, Controller, Transform,Selection
import os, json
import maya.cmds as cmds
import importlib.util
import tmlib

import ngSkinTools2
from ngSkinTools2.api import import_export
from ngSkinTools2.operations import removeLayerData
from ngSkinTools2.api import transfer


def create_quick_data_folder_template():
    """Make Sure the quick data path is exist, Create from current openning file."""
    current_file_path = cmds.file(q=True, sceneName=True)

    if not current_file_path:
        cmds.confirmDialog(m="Please save this file before create quick data.")
        return False

    dir_path = os.path.dirname(current_file_path)

    # Define the subfolder structure
    subfolders = [
        "QuickData/Python",
        "QuickData/Skin",
        "QuickData/Controller",
        "QuickData/SkinTransfer",
        "QuickData/SkinNG",
    ]

    # Create folders
    for folder in subfolders:
        full_path = os.path.join(dir_path, folder)
        os.makedirs(full_path, exist_ok=True)


def get_quick_data_dir():
    current_file_path = cmds.file(q=True, sceneName=True)

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
    cmds.select(cmds.ls(typ="transform"))
    export_skin_quick()


def apply_controller_and_skin():
    """Apply both controller and skin data (Dont have to select mesh to apply skin)"""

    import_shape_quick()

    # select skin cluster node
    cmds.select(cmds.ls(typ="transform"))
    import_skin_quick()


def get_missing_joint_by_json_data(skin_dict, transfer_dict={}):
    """Return missing joint in scene by given json dictionary"""

    dict_weight = skin_dict["deformerWeight"]["weights"]

    list_missing_joints = []

    for weight in dict_weight:
        joint_name = weight["source"]
        if not cmds.objExists(joint_name):
            if joint_name in transfer_dict.keys():
                if not cmds.objExists(transfer_dict[joint_name]):
                    list_missing_joints.append(joint_name)

            else:
                list_missing_joints.append(joint_name)

    return list_missing_joints


def normalize_dict(data):
    return {k: v for k, v in data.items() if v != ""}


def get_bind_joints_by_json_data(skin_dict):
    """Return bind joint list by given json dictionary"""

    dict_weight = skin_dict["deformerWeight"]["weights"]

    list_bind_joints = []

    for weight in dict_weight:
        joint_name = weight["source"]
        list_bind_joints.append(joint_name)

    return list_bind_joints


# def create_joint_transfer(joint_main_name,joint_transfer_name):
#     dict_rename_to_restore = {}
#     dict_rename_to_transfer = {}

#     joint = cmds.createNode("joint", n=joint_transfer_name)
#     dict_rename_to_transfer[name] = dict_transfer[name]
#     cmds.rename(name,dict_transfer)

#     return joint,

def import_skin_quick(enable_transfer=False, import_ng=True):
    grp_missing_joint = "missing_joint_grp"
    quick_data_path = get_quick_data_dir()
    quick_data_skin_path = os.path.join(quick_data_path, "Skin")
    quick_data_skin_transfer_path = os.path.join(quick_data_path, "SkinTransfer")

    selection = cmds.ls(sl=True)

    if not selection:
        cmds.displayWarning("Selection required before import")
        return

    list_not_found = []

    for sel in selection:
        sel_name = Utility.cut(sel, hierarchy=True)
        sel_name_cutted = Utility.cut(sel, hierarchy=True, namespace=True)

        json_file = os.path.join(quick_data_skin_path, "{}.json".format(sel_name_cutted))
        json_transfer_file = os.path.join(quick_data_skin_transfer_path, "{}.json".format(sel_name_cutted))

        if not cmds.objExists(sel_name):
            list_not_found.append(sel)
            continue

        if not os.path.exists(json_file):
            list_not_found.append(sel)
            continue

        dict_data = File.load_json_file_to_dict(json_file)

        if enable_transfer is False:
            dict_transfer = {}
        elif os.path.exists(json_transfer_file):
            dict_transfer = File.load_json_file_to_dict(json_transfer_file)
        else:
            dict_transfer = {}

        dict_transfer = normalize_dict(dict_transfer)

        list_bind_joints = get_bind_joints_by_json_data(dict_data)

        # delete old skin cluster
        old_skin_cluster = SkinWeight.get_skin_cluster_node(sel_name)
        if old_skin_cluster:
            cmds.delete(old_skin_cluster)

        # if nurbsSurface, get transform parent
        if cmds.objectType(sel_name, isAType="nurbsSurface"):
            sel_name = cmds.listRelatives(sel_name, parent=True)[0]

        # check missing joints and create placeholders
        for joint in list_bind_joints:
            if not cmds.objExists(joint):
                if not cmds.objExists(grp_missing_joint):
                    cmds.group(name=grp_missing_joint, empty=True)
                joint = cmds.createNode("joint", name=joint)
                cmds.parent(joint, grp_missing_joint)

        # create new skin cluster — extract [0] since cmds returns a list
        node_skin_cluster = cmds.skinCluster(
            sel_name,
            list_bind_joints,
            name=dict_data["deformerWeight"]["weights"][0]["deformer"],
            toSelectedBones=True,
            ignoreHierarchy=True,
            bindMethod=0,
        )[0]

        # import weights
        dir_path = os.path.dirname(json_file)
        file_name = os.path.basename(json_file)

        cmds.deformerWeights(
            file_name,
            im=True,
            method="index",
            deformer=node_skin_cluster,
            path=dir_path,
        )

        cmds.select(sel_name)
        cmds.skinPercent(node_skin_cluster, normalize=True)


        # import ng skin
        if import_ng:
            ng_path = json_file.replace("Skin", "SkinNG")
            print("ng_path : ", ng_path)

            if os.path.exists(ng_path):
                json_ng_data = File.load_json_file_to_dict(ng_path)
                vertex_count_ng = len(json_ng_data["layers"][0]["influences"]["0"])
                vertex_count_mesh = cmds.polyEvaluate(cmds.listRelatives(sel_name, s=True)[0], v=True)

                print(vertex_count_ng,vertex_count_mesh)
                cmds.select(sel_name)
                removeLayerData.remove_custom_nodes_from_selection()

                if vertex_count_mesh != vertex_count_ng:
                    result = cmds.confirmDialog( title='Confirm', message='{} is have diffrent vertex count , what method do you prefer?'.format(sel_name), button=['Index','Distance'], defaultButton='Yes', cancelButton='No', dismissString='No' )
                else:
                    result = "Index"
                    
                if result == "Index":
                    import_export.import_json(sel_name,
                                            vertex_transfer_mode=transfer.VertexTransferMode.vertexId,
                                              file=ng_path)
                elif result == "Distance":
                    import_export.import_json(sel_name,
                                              vertex_transfer_mode=transfer.VertexTransferMode.closestPoint,
                                              file=ng_path)

    cmds.inViewMessage(
        amg="<hl>Skin Apply!</hl>", pos="botCenter", fit=20, fts=16, fade=True
    )


def export_skin_quick(export_ng=True):
    """
    Use for export selected skin cluster
    """

    list_skin_cluster = []
    list_mesh_name = []

    selection = cmds.ls(sl=True, type="transform")
    # selection = 
    if not selection:
        cmds.displayWarning("Selection required before export")
        return

    for sel in selection:
        if (
            cmds.listRelatives(sel, children=True, type="mesh")
            or cmds.listRelatives(sel, children=True, type="nurbsSurface")
            or cmds.listRelatives(sel, children=True, type="nurbsCurve")
        ):
            skin_cluster_node = SkinWeight.get_skin_cluster_node(mesh_node=sel)

            if skin_cluster_node:
                list_skin_cluster.append(skin_cluster_node)
                list_mesh_name.append(Utility.cut(sel, hierarchy=True, namespace=True))

    if not list_skin_cluster:
        cmds.displayWarning("Skin cluster node not found on selection")
        return

    # export maya skin weight .json
    quick_data_path = get_quick_data_dir()
    file_path = os.path.normpath(os.path.join(quick_data_path, "Skin"))
    ng_file_path = os.path.normpath(os.path.join(quick_data_path, "SkinNG"))

    for skin_cluster_node, mesh_name in zip(list_skin_cluster, list_mesh_name):

        save_name = "{}.json".format(mesh_name)

        cmds.deformerWeights(
            save_name,
            export=True,
            deformer=skin_cluster_node,
            format="JSON",
            path=file_path,
        )

        # export ngskin tools weight
        if export_ng:
            ng_save_name = os.path.join(ng_file_path, mesh_name)

            mesh_main_name = cmds.ls("*{}".format(mesh_name),"*:{}".format(mesh_name))[0]
            cmds.select(mesh_main_name)
            import_export.export_json(mesh_name, file=ng_save_name + ".json")

    print("Exported Skin Weight Complete!")

    cmds.inViewMessage(
        amg="<hl>Write Skin Weight!</hl>", pos="botCenter", fit=20, fts=16, fade=True
    )


def import_shape_quick():
    quick_data_path = get_quick_data_dir()

    current_file_path = cmds.file(q=True, sceneName=True)
    current_file_name = os.path.basename(current_file_path)
    current_file_name_only = os.path.splitext(current_file_name)[0]
    key_name = current_file_name.split("_")[0]
    read_path = os.path.join(quick_data_path, "Controller", "{}.json".format(key_name))

    if os.path.exists(read_path):
        import_shape_custom(file_path=read_path)
        cmds.inViewMessage(
            amg="<hl> Controller Apply!</hl>",
            pos="botCenter",
            fit=20,
            fts=16,
            fade=True,
        )

    else:
        print("{}.json not found".format(key_name))


def build_and_read():
    build_current()
    apply_controller_and_skin()


def build_current():
    selection = [str(node) for node in cmds.ls(sl=1)]

    if not cmds.objExists("guide"):
        cmds.error()
        return

    from mgear import shifter

    cmds.select(cl=1)

    if cmds.objExists("rig"):
        cmds.delete("rig")

    Help.reload_scripts()

    shifter.reloadComponents()

    from mgear.shifter import guide_manager

    guide_manager.build_from_selection()

    if cmds.objExists("guide"):
        cmds.setAttr("guide.v", False)

    cmds.select(cl=True)

    for sel in selection:
        if cmds.objExists(sel):
            cmds.select(sel, add=True)

    cmds.inViewMessage(
        amg="<hl> Build Complete!</hl>", pos="botCenter", fit=20, fts=16, fade=True
    )


def remove_rig():
    if cmds.objExists("rig"):
        cmds.delete("rig")

    if cmds.objExists("guide"):
        cmds.setAttr("guide.v", True)

    cmds.inViewMessage(
        amg="<hl> Rig Removed!</hl>", pos="botCenter", fit=20, fts=16, fade=True
    )


def remove_all_shaders_pm():
    # Get all shading engines
    shading_engines = cmds.ls(type="shadingEngine")

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
            cmds.delete(list(set(materials + [sg])))
            print("Deleted:", sg, "with:", materials)
        except:
            print("Could not delete:", sg)

    print("✅ Removed all non-default shaders (pymel).")


def cleanup_scene():
    # --- Remove Grease Pencil nodes ---
    grease_pencils = cmds.ls(type="greasePencil")
    if grease_pencils:
        cmds.delete(grease_pencils)
        print("Removed grease pencil nodes:", grease_pencils)
    else:
        print("No grease pencil nodes found.")

    grease_pencils = cmds.ls(type="greasePlane")
    if grease_pencils:
        cmds.delete(grease_pencils)
        print("Removed grease pencil nodes:", grease_pencils)
    else:
        print("No grease pencil nodes found.")

    # --- Remove Display Layers (except defaultLayer) ---
    display_layers = cmds.ls(type="displayLayer")
    for layer in display_layers:
        if layer != "defaultLayer":
            try:
                cmds.delete(layer)
                print("Removed display layer:", layer)
            except:
                print("Could not delete display layer:", layer)

    print("Scene cleanup completed!")


def reload_all_references():
    # list all references
    refs = cmds.file(query=True, reference=True)

    if not refs:
        cmds.warning("No references found in the scene.")
        return

    for ref in refs:
        try:
            # reload reference
            cmds.file(ref, loadReference=True)
            print("Reloaded reference:", ref)
        except Exception as e:
            cmds.warning("Failed to reload reference: {} | {}".format(ref, e))


def hero_ctrl():
    if not cmds.objExists("guide"):
        raise Exception("not found Guide")

    # create folder
    quick_data_path = get_quick_data_dir()

    if not quick_data_path:
        raise (Exception("Create Quick Data First"))

    hero_ctrl_path = os.path.join(quick_data_path, "Hero")
    os.makedirs(hero_ctrl_path, exist_ok=True)

    # run mgear
    build_and_read()

    if cmds.objExists("Delete_Grp"):
        cmds.delete("Delete_Grp")

    if cmds.objExists("guide"):
        cmds.delete("guide")

    cmds.rename("rig", "Rig_Grp")

    remove_all_shaders_pm()
    cleanup_scene()

    # save to new path // force overwrite
    current_name = get_current_file_keyword()
    save_name = "{}_HeroCtrl.ma".format(current_name)
    new_file_path = os.path.join(hero_ctrl_path, save_name)

    print("hero ctrl path : ", hero_ctrl_path)
    cmds.displayInfo("Save name : {}".format(save_name))
    cmds.displayInfo("Hero Ctrl to path : {}".format(new_file_path))

    # Rename the current scene to the new path
    cmds.file(rename=new_file_path)
    # Save the file with the specified type and force overwrite
    cmds.file(save=True, type="mayaAscii", force=True)

    cmds.inViewMessage(
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
    if cmds.objExists("Delete_Grp"):
        cmds.delete("Delete_Grp")

    # remove_all_shaders_pm()
    General.sort_by_type(typ="anim_curve")
    controllers = cmds.ls(sl=1)

    for ctrl in controllers:
        Transform.reset_transform(ctrl)

    Scene.clear_controller_animation()
    Scene.import_all_references()
    Scene.remove_all_namespaces()
    cleanup_scene()

    cmds.setAttr("Rig_Grp.jnt_vis", False)
    cmds.setAttr("Rig_Grp.ctl_vis_on_playback", True)

    # # save to new path // force overwrite
    # current_name = get_current_file_keyword()
    # save_name = "{}_HeroHi.ma".format(current_name)
    # new_file_path = os.path.join(heor_hi_path, save_name)

    # cmds.file(rename=new_file_path)
    # cmds.file(save=True, type="mayaAscii", force=True)

    # cmds.inViewMessage(
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
    current_file_path = cmds.file(q=True, sceneName=True)
    current_file_name = os.path.basename(current_file_path)
    current_file_name_only = os.path.splitext(current_file_name)[0]
    key_name = current_file_name.split("_")[0]

    return key_name


def export_shape_quick():
    quick_data_path = get_quick_data_dir()

    current_file_path = cmds.file(q=True, sceneName=True)
    current_file_name = os.path.basename(current_file_path)
    current_file_name_only = os.path.splitext(current_file_name)[0]
    key_name = current_file_name.split("_")[0]
    path = os.path.join(quick_data_path, "Controller", "{}.json".format(key_name))

    export_shape_custom(file_path=path)

    cmds.inViewMessage(
        amg="<hl>Controller Backup!</hl>", pos="botCenter", fit=20, fts=16, fade=True
    )

def export_shape_advanced_skeleton_quick():
    quick_data_path = get_quick_data_dir()

    current_file_path = cmds.file(q=True, sceneName=True)
    current_file_name = os.path.basename(current_file_path)
    current_file_name_only = os.path.splitext(current_file_name)[0]
    key_name = current_file_name.split("_")[0]
    path = os.path.join(quick_data_path, "Controller", "{}.json".format(key_name))

    export_shape_custom(file_path=path)

    cmds.inViewMessage(
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

    controllers = Selection.sort_by_type(list_target=cmds.ls(), typ="anim_curve")
    if isinstance(controllers, str):
        controllers = [controllers]

    # append advance skeleton shape
    if cmds.objExists("ControlSet"):
        cmds.select("ControlSet")
        advance_ctrls = cmds.ls(sl=1)

        for ctrl in advance_ctrls:
            if cmds.listRelatives(ctrl, c=1, s=1, typ="nurbsCurve"):
                controllers.append(ctrl)

    data = {}

    for ctrl_name in controllers:
        try:
            ctrl = cmds.PyNode(ctrl_name)
        except:
            cmds.warning(f"Controller '{ctrl_name}' does not exist.")
            continue

        if not ctrl.getShapes():
            cmds.warning(f"'{ctrl}' has no shapes.")
            continue

        # Write Data
        for shape in ctrl.getShapes(noIntermediate=True):
            if isinstance(shape, cmds.nodetypes.NurbsCurve):
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
                    for p in [cmds.pointPosition(cv, local=True) for cv in shape.cv[:]]
                ]

                # Line width
                shape_data["lineWidth"] = shape.lineWidth.get()

                # Degree
                shape_data["degree"] = cmds.getAttr("{}.degree".format(shape))

                # Spans
                shape_data["spans"] = cmds.getAttr("{}.spans".format(shape))

                # Form
                shape_data["form"] = cmds.getAttr("{}.form".format(shape))

                data.setdefault(ctrl.name(), {})[shape.name()] = shape_data

    if not data:
        cmds.warning("No valid controllers found. Nothing to export.")
        return

    # Determine default path
    if not file_path:
        scene_path = cmds.file(q=True, sceneName=True)
        default_dir = (
            os.path.dirname(scene_path)
            if scene_path
            else cmds.workspace(q=True, rootDirectory=True)
        )

        file_path = cmds.fileDialog2(
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

    cmds.displayInfo("Exported Controller to : {}".format(file_path))


def import_shape_custom(file_path=""):
    if not file_path:
        file_path = cmds.fileDialog2(
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
        if cmds.objExists(ctrl_name):
            dict_curve_data = dict_json[ctrl_name]

            # create new controller shape
            tmp_ctrl = Controller.create_curve_from_data(dict_curve_data)

            if not tmp_ctrl:
                continue

            Transform.match_cvs(ctrl_name, tmp_ctrl)
            Controller.clone_style([ctrl_name, tmp_ctrl])

            cmds.delete(tmp_ctrl)

        else:
            list_not_exist.append(ctrl_name)

    if list_not_exist:
        cmds.warning("Does not exist control : {}".format(list_not_exist))


def create_script(name=None):
    quick_data_path = get_quick_data_dir()

    if not quick_data_path:
        raise Exception(
            "Quick Data Path not found. make sure you have save current file and create quick data."
        )

    script_path = os.path.join(quick_data_path, "Python")
    scene_path = cmds.file(q=True, sceneName=True)
    scene_name = os.path.basename(scene_path)
    scene_name_raw = os.path.splitext(scene_name)[0]
    scene_name_keyword = scene_name_raw.split("_")[0]

    local_script_main_path = os.path.join(script_path, scene_name_keyword)
    # make sure path exist
    os.makedirs(local_script_main_path, exist_ok=True)

    if name:
        python_file_name = name
    else:
        python_file_name = scene_name_keyword
    # check is scene raw name.py exist
    python_path = os.path.join(local_script_main_path, "{}.py".format(python_file_name))

    # if python path not exist, create the new one
    if os.path.exists(python_path):
        pass
    else:
        script_content = """
from tmlib.core import Selection, Attribute,,BlendShape,Connection,Create,Misc,Transform,Utility,SkinWeight,File,Controller,QuickData,System,Geometry,Visualized

import maya.cmds as cmds
import maya.api.OpenMaya as om
import maya.mel as mel

System.reload_scripts()

def run():
    return
        """

        with open(python_path, "w") as f:
            f.write(script_content)

        print("Created new script : {}".format(python_path))

    # make sure .env is created
    env_path = os.path.join(script_path, ".env")
    tonmai_toolkit_dir = os.path.dirname(tmlib.__file__)
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
        cmds.warning("Cannot Start File (Only Support in Windows Os)")


def open_script_folder():
    quick_data_path = get_quick_data_dir()
    path = os.path.join(quick_data_path, "Python")

    os.makedirs(path, exist_ok=True)

    os.startfile(path)


def run_script_file(script_path, order=None):
    if not os.path.exists(script_path):
        cmds.warning(f"Directory not found: {script_path}")
        return

    execution_list = []

    if order and isinstance(order, list):
        for name in order:
            file_name = name if name.endswith(".py") else f"{name}.py"
            full_path = os.path.join(script_path, file_name)
            if os.path.exists(full_path):
                execution_list.append(full_path)
    else:
        files = [f for f in os.listdir(script_path) if f.endswith(".py")]
        files.sort()
        execution_list = [os.path.join(script_path, f) for f in files]

    if not execution_list:
        return

    cmds.undoInfo(openChunk=True, chunkName="RunScriptFileOrdered")

    try:
        for python_path in execution_list:
            file_name = os.path.basename(python_path)
            module_name = os.path.splitext(file_name)[0]

            spec = importlib.util.spec_from_file_location(module_name, python_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, "run"):
                module.run()

        cmds.inViewMessage(
            amg=f"<hl>Run Scripts : {order} , {len(execution_list)} files</hl>",
            pos="midCenter",
            fade=True,
        )

    except Exception as e:
        cmds.warning(f"Execution failed: {str(e)}")

    finally:
        cmds.undoInfo(closeChunk=True)

    return