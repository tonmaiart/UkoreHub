"""
Used to export Animation / validate pipeline file, this is Add-On Script for Ukore Pipeline

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

from UkoreMaya.core import Pipeline,Logic
from UkoreMaya.menu import General

import maya.cmds as cmds
import maya.mel as mel
import os, shutil
import maya.mel as mel


def export_anim_fbx(
    export_folder,
    pick_character=["Kafka"]):
    """
    Use to Export Animation to fbx

    pick_character : if False , will select all character , if list ["Kafka","Jacob"] ia mean pick kafka and jacob
    version : if have number input the name will be version
    
    Output example
    KBA030_Kafka_anim.fbx
    KBA030_Jacob_anim.fbx
    KBA030_Jacob_camera.fbx

    """

    print("# Exporting Animation Fbx #")
    # make sure the export path is directory
    # check is export path is directory
    if not os.path.isdir(export_folder):
        export_folder = os.path.dirname(export_folder)

    # ===================================================
    # get mesh dict , seperated by character prefix name
    # ===================================================

    dict_mesh = Pipeline.get_character_meshes(
        pick_character_enable=False, pick_character=pick_character
    )

    for key in dict_mesh.keys():
        print("Anim Alembic Character : ", key)

        for mesh in dict_mesh[key]:
            print("- ", Utility.cut(mesh))

    # =======================
    # iterate for each character
    # =======================

    for key in dict_mesh.keys():
        list_mesh_anim = dict_mesh[key]
        root_flags = " ".join(f"-root {obj}" for obj in list_mesh_anim)
        start_frame = cmds.playbackOptions(q=True, min=True)
        end_frame = cmds.playbackOptions(q=True, max=True)

        # generate export name
        prefix_shot = os.path.basename(cmds.file(q=True, sn=True)).split("_")[0]
        export_name = f"{prefix_shot}_{key}_anim.fbx"
        export_fbx_file_path = export_folder + "/" + export_name
        export_fbx_file_path = export_fbx_file_path.replace("\\", "/")

        print("fbx export path : ",export_fbx_file_path)
        # FBX export settings
        mel.eval('FBXExportSmoothingGroups -v true')
        mel.eval('FBXExportHardEdges -v false')
        mel.eval('FBXExportTangents -v false')
        mel.eval('FBXExportSmoothMesh -v false')
        mel.eval('FBXExportInstances -v false')
        mel.eval('FBXExportBakeComplexAnimation -v true')
        mel.eval('FBXExportSkeletonDefinitions -v true')
        mel.eval('FBXExportSkins -v true')
        mel.eval('FBXExportShapes -v true')  # blendshapes
        mel.eval('FBXExportConstraints -v false')
        mel.eval('FBXExportCameras -v false')
        mel.eval('FBXExportLights -v false')
        mel.eval('FBXExportEmbeddedTextures -v false')
        mel.eval('FBXExportInputConnections -v false')
        mel.eval('FBXExportUpAxis y')


        cmds.select(clear=True)
        cmds.select("*:DeformSet",add=True)
        General.sort_by_type(typ="joint")

        cmds.select(list_mesh_anim,add=True)
        # Export selected
        mel.eval(f'FBXExport -f "{export_fbx_file_path}" -s')
        print(f"Exported: {export_fbx_file_path}")

def export_anim_abc(
    export_path,
    prefix_seperate=True,
    smooth_mesh=False,
    pick_character_enable=False,
    pick_character=["Kafka"],
    version="",
    prefix_shot="",
):
    """
    Used for export alembic cache

    This will automatic detect and export each character seperately
    - only detect mesh that have suffix "_Geo"
    - seperate character based on prefix name like "Kafka_Eye_Geo" will be file Kafka
    """

    print("# Exporting Anim Alembic #")
    # make sure the export path is directory
    # check is export path is directory
    if not os.path.isdir(export_path):
        export_path = os.path.dirname(export_path)

    # get mesh dict
    dict_mesh = {}

    if prefix_seperate:
        dict_mesh = Pipeline.get_character_meshes(
            pick_character_enable=pick_character_enable, pick_character=pick_character
        )
    else:
        dict_mesh = {"anim": Logic.list_meshes_with_suffix_geo()}

    for key in dict_mesh.keys():
        print("Anim Alembic Character : ", key)

        for mesh in dict_mesh[key]:
            print("- ", Utility.cut(mesh))

    # iterate for each mesh
    for key in dict_mesh.keys():
        list_mesh_anim = dict_mesh[key]
        root_flags = " ".join(f"-root {obj}" for obj in list_mesh_anim)
        start_frame = cmds.playbackOptions(q=True, min=True)
        end_frame = cmds.playbackOptions(q=True, max=True)

        if version:
            export_name = f"{key}_anim_{version:03}.abc"
        else:
            export_name = f"{key}_anim.abc"

        if prefix_shot:
            export_name = prefix_shot + "_" + export_name

        export_path_key = export_path + "/" + export_name

        job = " -frameRange {} {} -worldSpace -stripNamespaces -writeFaceSets  -writeColorSets -uvWrite -writeVisibility -dataFormat ogawa {} -file '{}'".format(
            start_frame, end_frame, root_flags, export_path_key
        )

        # add smooth node
        list_smooth_node = []

        if smooth_mesh:
            for mesh in list_mesh_anim:
                shape_node = Utility.cut(mesh) + "Shape"

                if not cmds.objExists(shape_node):
                    print("Not found shape node for smooth: ", shape_node)
                    continue

                get_smooth_level = cmds.getAttr(f"{shape_node}.smoothLevel")

                if get_smooth_level != 0:
                    cmds.select(mesh)
                    node = cmds.polySmooth()[0]
                    cmds.setAttr(node + ".divisions", get_smooth_level)
                    list_smooth_node.append(node)

                    print(f"Add smooth node : {node} to {mesh}")

        # export
        cmds.AbcExport(j=job)

        # remove smooth node
        for node in list_smooth_node:
            cmds.delete(node)


def export_anim_metadata(export_path):
    """
    Export json file with metadata
    """

    metadata = {"object_paths": {}}
    list_mesh_anim =  Logic.list_meshes_with_suffix_geo()

    for obj in list_mesh_anim:
        obj_shapes = cmds.listRelatives(obj, c=1, s=1)
        obj_shape_name = None
        for shape in obj_shapes:
            if cmds.getAttr("{}.intermediateObject".format(shape)) is False:
                obj_shape_name = Utility.cut(shape, hierarchy=True, namespace=True)

        if not obj_shape_name:
            print("Not found Shape cache for : {}".format(obj))

        obj_name = obj.split("|")[-1].split(":")[-1]
        metadata["object_paths"][obj_name] = "/{}/{}".format(obj_name, obj_shape_name)

    with open(export_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)


def export_anim_camera(export_fbx_path):
    """Designed for camera named RenderCam , this will export camera fbx file"""

    cams = cmds.ls("camshot", "*:camshot", "*:*:camshot", transforms=True)

    if not cams:
        cmds.warning("ไม่พบกล้อง camshot")
    else:
        # Search Cam Shot
        cam_shot = cams[0]
        cam_shot_shape = cmds.listRelatives(cam_shot, shapes=True)[0]

        # Create Render Cam
        cam_render_name = "RenderCam"

        min_time = cmds.playbackOptions(query=True, minTime=True)
        max_time = cmds.playbackOptions(query=True, maxTime=True)

        cam_render, cam_render_shape = cmds.camera(n=cam_render_name)

        constraint_list = cmds.parentConstraint(cam_shot, cam_render)
        cmds.connectAttr(
            "{}.focalLength".format(cam_shot_shape),
            "{}.focalLength".format(cam_render_shape),
            f=True,
        )
        cmds.connectAttr(
            "{}.overscan".format(cam_shot_shape),
            "{}.overscan".format(cam_render_shape),
            f=True,
        )
        cmds.connectAttr(
            "{}.cameraAperture".format(cam_shot_shape),
            "{}.cameraAperture".format(cam_render_shape),
            f=True,
        )

        # Select and rename camera
        cmds.rename(cam_render, cam_render_name)
        cmds.select(cam_render_name, replace=True)

        print(f"Exporting Camera to Path : {export_fbx_path}")
        mel.eval("FBXExportBakeComplexAnimation -v true")
        cmds.file(
            export_fbx_path,
            force=True,  # -force (บังคับเขียนทับไฟล์เดิม)
            options="fbx",  # -options "fbx" (กำหนดตัวเลือกการ Export)
            type="FBX export",  # -typ "FBX export" (ประเภทไฟล์)
            preserveReferences=True,  # -pr (รักษา Reference files ไว้)
            exportSelected=True,  # -es (Export เฉพาะสิ่งที่ถูกเลือก)
        )

        # Delete temp camera
        cmds.delete(cam_render_name)


def export_head_skeleton(
    export_fbx_path, head_joint="Head_M", head_joint_export_name="head"
):
    if cmds.objExists(head_joint_export_name):
        cmds.error(f"Joint '{head_joint}' already exists")
        return

    target_head_joints = cmds.ls(head_joint, f"*:{head_joint}")

    if not target_head_joints:
        cmds.error(f"Joint '{head_joint}' not found.")
        return
    else:
        target_joint = target_head_joints[0]

    print(f"# Exporting Head Locator FBX to {export_fbx_path}")

    # build joint structure
    joint_root = cmds.createNode("joint", name="root")
    joint_head = cmds.createNode("joint", name="head")
    cmds.parentConstraint(target_joint, joint_head, maintainOffset=False)

    cmds.parent(joint_head, joint_root)
    cmds.select(joint_root)

    # export file
    mel.eval("FBXExportBakeComplexAnimation -v true")
    cmds.file(export_fbx_path, force=True, typ="FBX export", pr=True, es=True)

    # remove tmp joint
    cmds.delete(joint_root)

def export_shot_to_ue_fbx():
    validate_material = True
    prefix_seperate = True
    smooth_mesh = False
    export_anim = True
    export_head_locator = False
    pick_character_enable = False
    export_camera = True
    pick_character = False

    # get current file path
    current_file_full_path = cmds.file(sn=True, q=1)
    current_file_dir_basename = os.path.basename(os.path.dirname(current_file_full_path))
    shot_name = os.path.basename(current_file_full_path).split("_")[0]
    publish_folder =  Logic.convert_to_publish_path(current_file_full_path)["publish_root_dir"]


    # =======================
    # Generate Export Folder
    # =======================

    export_folder = Logic.generate_publish_version_directory_path(
    current_share_path=current_file_full_path,
    subfolder="Main")
    
    Logic.make_sure_folder_exist(export_folder)

    # display infomation
    print("# Export Shot to UE (Fbx Version) #")
    print("- Export Path : ", export_folder)
    print("- Prefix Seperate : ", prefix_seperate)
    print("- Smooth Mesh : ", smooth_mesh)
    print("- Validate Material : ", validate_material)
    print("- Export Anim : ", export_anim)
    print("- Export Camera : ", export_camera)
    print("- Export Head Locator : ", export_head_locator)
    print("- Pick Character Enable : ", pick_character_enable)
    print("- Pick Character : ", pick_character)


    # validate face set
    if validate_material:
        dict_mesh = Pipeline.get_character_meshes(
            pick_character_enable=pick_character_enable, pick_character=pick_character
        )

        for key in dict_mesh.keys():
            geos = dict_mesh[key]
            Validate.fix_material_names(selection=geos)
            Validate.validate_material_face_set(selection=geos)
    # =================
    # export anim fbx
    # =================
    export_anim_fbx(export_folder=export_folder,
                    pick_character=False)
    
    # ==============
    # Export Camera
    # ===========+==
    if export_camera:
        export_anim_camera(
            export_fbx_path=os.path.join(
                export_folder, f"{shot_name}_camera.fbx"
            )
        )

    return export_folder



def export_shot_to_ue(
    export_path=None,
    prefix_seperate=True,
    smooth_mesh=True,
    version="",
    validate_material=True,
    export_anim=True,
    export_camera=True,
    export_head_locator=True,
    pick_character_enable=False,
    pick_character=["Kafka"],
):

    print("# Export Shot to UE #")
    print("- Export Path : ", export_path)
    print("- Prefix Seperate : ", prefix_seperate)
    print("- Smooth Mesh : ", smooth_mesh)
    print("- Validate Material : ", validate_material)
    print("- Export Anim : ", export_anim)
    print("- Export Camera : ", export_camera)
    print("- Export Head Locator : ", export_head_locator)
    print("- Pick Character Enable : ", pick_character_enable)
    print("- Pick Character : ", pick_character)

    # verify path
    if os.path.isdir(export_path):
        os.makedirs(export_path, exist_ok=True)
    else:
        os.makedirs(os.path.dirname(export_path), exist_ok=True)

    # import all
    # Scene.import_all_references()
    # Scene.remove_all_namespaces()

    # get current file path
    current_file_path = cmds.file(sn=True, q=1)
    current_file_dir_name = os.path.basename(os.path.dirname(current_file_path))

    # validate face set
    if validate_material:
        dict_mesh = Pipeline.get_character_meshes(
            pick_character_enable=pick_character_enable, pick_character=pick_character
        )

        for key in dict_mesh.keys():
            geos = dict_mesh[key]
            Validate.fix_material_names(selection=geos)
            Validate.validate_material_face_set(selection=geos)

    # export anim abc , camera and head locator
    if export_anim:
        export_anim_abc(
            export_path,
            prefix_seperate=prefix_seperate,
            smooth_mesh=smooth_mesh,
            pick_character_enable=pick_character_enable,
            pick_character=pick_character,
            prefix_shot=current_file_dir_name,
        )

    if not os.path.isdir(export_path):
        export_path = os.path.dirname(export_path)

    if export_camera:
        export_anim_camera(
            export_fbx_path=os.path.join(
                export_path, "{}_camera.fbx".format(current_file_dir_name)
            )
        )

    if export_head_locator:
        export_head_skeleton(
            export_fbx_path=os.path.join(
                export_path, "{}_head_locator.fbx".format(current_file_dir_name)
            )
        )

    return export_path

