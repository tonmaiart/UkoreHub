import bpy
import os
import json
import re

from UkoreMaya.core import Logic

def decode_fbx_asc(name: str) -> str:
    return re.sub(
        r'FBXASC(\d{3})',
        lambda m: chr(int(m.group(1))),
        name
    )

def export_fbx_animation_to_maya():
    # check is this file already saved
    if not bpy.data.is_saved:
        return False
    
    # get and create quick data path
    current_file_path = bpy.data.filepath
    export_directory = os.path.dirname(current_file_path)
    quick_data_path = os.path.join(export_directory, "QuickData")

    Logic.make_sure_folder_exist(os.path.join(quick_data_path, "FbxFromBlender"))
    print(f"Quick data path: {os.path.join(quick_data_path, "FbxFromBlender")}")

    # filter armature objects in the scene
    armature = [obj for obj in bpy.context.scene.objects if obj.type == 'ARMATURE']
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']

    dict_export_armature = {}

    # filter mesh by armature
    for mesh in meshes:
        # Check if the mesh has an armature modifier
        for mod in mesh.modifiers:
            if mod.type == 'ARMATURE' and mod.object is not None:
                armature_obj = mod.object
                
                if armature_obj.name not in dict_export_armature:
                    dict_export_armature[armature_obj.name] = []

                dict_export_armature[armature_obj.name].append(mesh)
                break

    # export selected armature to FBX
    for arm in armature:
        export_path = os.path.join(quick_data_path, "FbxFromBlender", "{}.fbx".format(arm.name))
        
        bpy.ops.object.select_all(action='DESELECT')
        arm.select_set(True)

        for mesh in dict_export_armature.get(arm.name, []):
            mesh.select_set(True)

        bpy.ops.export_scene.fbx(
            filepath=export_path,
            use_selection=True,
            apply_unit_scale=True,
            bake_space_transform=True,
            object_types={'ARMATURE','MESH'},
            add_leaf_bones=False,
            primary_bone_axis='Y',
            secondary_bone_axis='X',
        )
        
        print(f"Animation exported to: {export_path}")

    return True

def import_fbx_animation_from_maya():
    # Logic to import animation data from FBX format exported by Maya
    print("Importing animation data from Maya...")

    return True

def read_weight_from_maya():
    # Check if file is saved
    if not bpy.data.is_saved:
        print("File not saved yet, can't detect QuickData Folder")
        return False
    
    # Setup paths
    current_file_path = bpy.data.filepath
    export_directory = os.path.dirname(current_file_path)
    quick_data_path = os.path.join(export_directory, "QuickData")

    # Find armatures and meshes
    armatures = [obj for obj in bpy.context.scene.objects if obj.type == 'ARMATURE']
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']

    dict_export_armature = {}

    # Map meshes to their armatures
    for mesh in meshes:
        for mod in mesh.modifiers:
            if mod.type == 'ARMATURE' and mod.object:
                arm_name = mod.object.name
                if arm_name not in dict_export_armature:
                    dict_export_armature[arm_name] = []
                dict_export_armature[arm_name].append(mesh)
                break

    # Process each mesh
    for arm in armatures:
        for mesh in dict_export_armature.get(arm.name, []):
            json_path = os.path.join(quick_data_path, "Skin", f"{mesh.name}.json")
            
            if not os.path.exists(json_path):
                continue

            print(f"Updating weights for: {mesh.name}")

            with open(json_path, 'r') as f:
                data = json.load(f)

            # --- Build a per-vertex weight dict from JSON ---
            all_weight_entries = data["deformerWeight"]["weights"]

            vertex_weight_map = {}  # { v_index: { group_name: weight } }

            for entry in all_weight_entries:
                raw_name = entry.get("source")
                group_name = decode_fbx_asc(raw_name)
                points = entry.get("points", [])

                for p in points:
                    v_index = p.get("index")
                    weight_value = p.get("value")

                    if v_index not in vertex_weight_map:
                        vertex_weight_map[v_index] = {}
                    vertex_weight_map[v_index][group_name] = weight_value

            # --- Normalize weights per vertex so total <= 1.0 ---
            for v_index, bone_weights in vertex_weight_map.items():
                total = sum(bone_weights.values())
                if total > 1.0:
                    vertex_weight_map[v_index] = {
                        bone: w / total for bone, w in bone_weights.items()
                    }

            # --- Apply normalized weights to vertex groups ---
            for v_index, bone_weights in vertex_weight_map.items():
                if v_index >= len(mesh.data.vertices):
                    continue

                # Remove this vertex from ALL groups first
                for vg in mesh.vertex_groups:
                    vg.remove([v_index])

                # Then apply the normalized weights cleanly
                for group_name, weight_value in bone_weights.items():
                    if group_name not in mesh.vertex_groups:
                        mesh.vertex_groups.new(name=group_name)

                    v_group = mesh.vertex_groups[group_name]
                    v_group.add([v_index], weight_value, 'REPLACE')

                    if v_index % 100 == 0:
                        print(f"- Bone: {group_name} | Vtx: {v_index} | Weight: {weight_value}")

    print("Weight Import Successful!")
    return True