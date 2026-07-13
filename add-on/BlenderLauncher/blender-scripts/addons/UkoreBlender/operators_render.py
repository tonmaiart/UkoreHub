'''
Made by Natchapon Srisuk , Operator for rendering department , Ukore Studio
'''
import bpy
import os
import re
import subprocess
import platform
import json
import inspect

from bpy.props import StringProperty, BoolProperty, EnumProperty

from UkoreMaya.core import Logic


class ReloadScripts(bpy.types.Operator):
    """
    This will reload all add-on and scripts
    """

    bl_idname = "render.reload_scripts"
    bl_label = "Reload Scripts"

    def execute(self,context):
        bpy.ops.script.reload()

        return {"FINISHED"}

class LinkMeshData(bpy.types.Operator):
    """
    Select two object (only parent object), it's will automatically search for children in hierarchy and pairing by name.
    if have (.) in name will split it to get only basename, then will transfer modifier, material and vertex group data

    To use : 
    1. select the source object parent
    2. select the target object parent

    Note:
    If some mesh can't find pair of them will be reported.
    """

    bl_idname = "render.link_mesh_data"
    bl_label = "Link Mesh Data"

    def create_dict_data(self,list_obj):
        """ Generate dict data for basename"""
        list_return = []

        for obj in list_obj:
            if obj.type != 'MESH':
                continue
            else:
                obj_name = obj.name
                obj_base_name = obj.name.split(".")[0]
                obj_node = obj
                
                list_return.append({"name":obj_name,"basename":obj_base_name,"node":obj_node})

        return list_return
        
    def create_dict_pair_data(self, list_objA, list_objB):
            """ Pairing Dict base by basename """
            lookup = {d["basename"]: d for d in list_objB if "basename" in d}
            
            not_found = []
            pairs = []
            for item in list_objA:
                val = item.get("basename")
                if val in lookup:
                    pairs.append((item, lookup[val]))
                else:
                    not_found.append(val)
            
            if not_found:
                print("# Not Found Mesh #")
                for v in not_found:
                    print("- {}".format(v))
                    
            return pairs

    def execute(self,context):
        # ==========
        # Preparing
        # ==========

        print("============ Link Mesh Data ============")
        sel = bpy.context.selected_objects
        
        if len(sel) != 2:
            self.report({"ERROR"},"Required two selection.")
            return{"ERROR"}

        print("Source Selection : {}".format(sel[0].name))
        print("Target Selection : {}".format(sel[1].name))

        list_dict_target_obj = self.create_dict_data(sel[1].children_recursive)
        list_dict_source_obj = self.create_dict_data(sel[0].children_recursive)
        list_dict_pair_obj = self.create_dict_pair_data(list_dict_target_obj,list_dict_source_obj)
        
        # ===============
        # Main Operation
        # ===============

        for list_pair in list_dict_pair_obj:
            print("# LINKING MESH #")
            print("- ",list_pair[0]["name"]," > ",list_pair[1]["name"])

            target_node = list_pair[0]["node"]
            source_node = list_pair[1]["node"]

            # re-selection
            bpy.ops.object.select_all(action='DESELECT')
            target_node.select_set(True)
            source_node.select_set(True)
            bpy.context.view_layer.objects.active = target_node

            # Link Material
            bpy.ops.object.make_links_data(type='MATERIAL')

            # Transfer Group Data
            bpy.ops.object.data_transfer(
            data_type='VGROUP_WEIGHTS', 
                layers_select_src='ALL', 
                layers_select_dst='NAME', 
                mix_mode='REPLACE')

            # Copy Modifier
            bpy.ops.object.make_links_data(type='MODIFIERS')

        return {"FINISHED"}

# class UpdateAnimCache(bpy.types.Operator):
#     """
#     Browser Anim .abc file , (require .json for store metadata for shape cache name)
#     """

#     bl_idname = "render.update_anim_cache"  
#     bl_label = "Update Anim Cache..."

#     filepath: bpy.props.StringProperty(subtype="FILE_PATH")

#     def invoke(self, context, event):
#         current_filepath = bpy.data.filepath

#         if not current_filepath:
#             self.DEFAULT_DIR = "G:\My Drive\Projects\KafkaProj\publish"
#         else:
#             path = current_filepath.replace("share", "publish").replace(
#                 "Render", "Anim"
#             )
#             self.DEFAULT_DIR = os.path.dirname(os.path.dirname(path))
#             self.DEFAULT_DIR = os.path.dirname(os.path.dirname(path))
#             self.DEFAULT_DIR = os.path.dirname(os.path.dirname(path))


#         if not os.path.exists(self.DEFAULT_DIR):
#             self.report(
#                 {"ERROR"},
#                 "Default Browse Path is invalid : {}.".format(self.DEFAULT_DIR),
#             )
#             return {"CANCELLED"}

#         self.filepath = os.path.join(self.DEFAULT_DIR, "select_here.dummy")
#         context.window_manager.fileselect_add(self)
#         return {"RUNNING_MODAL"}

#     def execute(self, context):
#         print("### Update Anim Cache ###")

#         filepath = bpy.path.abspath(self.filepath)
#         metadata_path = filepath.replace(".abc", ".json")

#         if not filepath or not os.path.isfile(filepath):
#             self.report({"ERROR"}, "No valid file selected.")
#             return {"CANCELLED"}

#         if not os.path.exists(metadata_path):
#             self.report({"ERROR"}, "No metadata file found: {}".format(metadata_path))
#             return {"CANCELLED"}

#         # =================
#         # Get Alembic Cache Meta Data
#         # =================

#         with open(metadata_path, "r", encoding="utf-8") as f:
#             metadata = json.load(f)

#         # =================
#         # Assign Alembic Cache
#         # =================
#         list_mesh_paths = metadata["object_paths"].keys()

#         for obj in bpy.data.objects:
#             if obj.type == "MESH":
#                 if obj.name in list_mesh_paths:
#                     # Create Seq cache modifier , and assign value
#                     mesh_seq_cache = next(
#                         (c for c in obj.modifiers if c.type == "MESH_SEQUENCE_CACHE"),
#                         None,
#                     )

#                     if not mesh_seq_cache:
#                         mesh_seq_cache = obj.modifiers.new(
#                             name="Alembic Cache", type="MESH_SEQUENCE_CACHE"
#                         )

#                     mesh_seq_cache.cache_file = load_cache_file(filepath=filepath)
#                     mesh_seq_cache.object_path = metadata["object_paths"][obj.name]

#                     print("- {} : {}".format(obj.name,metadata["object_paths"][obj.name]))

#                     # Try to move mesh seq cache modifier to first index

#                     try:
#                         current_index = list(obj.modifiers).index(mesh_seq_cache)
#                     except ValueError:
#                         pass

#                     target_index = 0
#                     if current_index != target_index:
#                         obj.modifiers.move(
#                             from_index=current_index, to_index=target_index
#                         )

#         return {"FINISHED"}



class UpdateAnimCache(bpy.types.Operator):
    """
    Browser Anim .abc file , (require .json for store metadata for shape cache name)
    """

    bl_idname = "render.update_anim_cache"  
    bl_label = "Update Anim Cache..."

    def execute(self, context):
        def load_cache_file(filepath):
            # เช็คว่ามีไฟล์นี้อยู่ใน Blender หรือยัง
            filename = os.path.basename(filepath)
            cache_file = bpy.data.cache_files.get(filename)
            
            if not cache_file:
                # ใช้ Operator ในการเปิดไฟล์เพื่อสร้าง Data Block ที่สมบูรณ์
                bpy.ops.cachefile.open(filepath=filepath)
                cache_file = bpy.data.cache_files.get(filename)
                
            return cache_file
        
        print("### Update Anim Cache ###")

        # get current version path 
        recent_file_path = Logic.get_latest_version_in_folder_based(
            ref_path=bpy.data.filepath.replace("share", "publish").replace("Render", "Layout"),)
        recent_file_dir = os.path.dirname(recent_file_path)

        print("Current File Path : ", bpy.data.filepath)
        print("Detect Recent File Path : ", recent_file_path)

        filepath = os.path.normpath(os.path.join(recent_file_dir,"v005.abc"))
        metadata_path = os.path.normpath(os.path.join(recent_file_dir,"v005.json"))

        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        list_mesh_paths = metadata["object_paths"].keys()

        # 1. เคลียร์ selection เก่าทั้งหมด
        bpy.ops.object.select_all(action='DESELECT')

        # 2. วนลูปเช็คเฉพาะ Object ที่อยู่ใน View Layer ปัจจุบันเท่านั้น
        for obj in bpy.context.view_layer.objects:
            if obj.type == "MESH" and obj.name in list_mesh_paths:
                obj.select_set(True)
                # ตั้งค่า Active Object ไว้ที่ตัวล่าสุดที่เลือก
                bpy.context.view_layer.objects.active = obj

        # 3. ดึงกลุ่มที่ถูกเลือกมาใช้งานต่อ
        selected_meshes = [obj for obj in bpy.context.selected_objects if obj.type == "MESH"]

        for obj in selected_meshes:
            if obj.name in list_mesh_paths:
                mesh_seq_cache = next((c for c in obj.modifiers if c.type == "MESH_SEQUENCE_CACHE"), None)
                
                if not mesh_seq_cache:
                    mesh_seq_cache = obj.modifiers.new(name="Alembic Cache", type="MESH_SEQUENCE_CACHE")

                # เรียกใช้ฟังก์ชันที่แก้ไขใหม่
                cache_data = load_cache_file(filepath)
                if cache_data:
                    mesh_seq_cache.cache_file = cache_data
                    mesh_seq_cache.object_path = metadata["object_paths"][obj.name]

                try:
                    current_index = list(obj.modifiers).index(mesh_seq_cache)
                    if current_index != 0:
                        obj.modifiers.move(from_index=current_index, to_index=0)
                except:
                    pass

        return {"FINISHED"}

print("Process Completed!")

class UpdateAnimCamera(bpy.types.Operator):
    """
    Browse alembic cache file, and assign it to exist object in the scene.
    """

    bl_idname = "render.update_anim_camera"  # <<--- เพิ่ม bl_idname
    bl_label = "Import/Update Camera..."  # <<--- เพิ่ม bl_label

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def invoke(self, context, event):
        # Fix: Blender will always open at last used dir unless filepath has value.
        # So force it by setting filepath to dummy file inside our wanted directory.
        current_filepath = bpy.data.filepath

        if not current_filepath:
            self.DEFAULT_DIR = "G:\My Drive\Projects\KafkaProj\publish"
        else:
            path = current_filepath.replace("share", "publish").replace(
                "Render", "Anim"
            )
            self.DEFAULT_DIR = os.path.dirname(os.path.dirname(path))
            self.DEFAULT_DIR = os.path.dirname(os.path.dirname(path))
            self.DEFAULT_DIR = os.path.dirname(os.path.dirname(path))

            print(self.DEFAULT_DIR)

        if not os.path.exists(self.DEFAULT_DIR):
            self.report(
                {"ERROR"},
                "Default Browse Path is invalid : {}.".format(self.DEFAULT_DIR),
            )
            return {"CANCELLED"}

        self.filepath = os.path.join(self.DEFAULT_DIR, "select_here.dummy")
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        filepath = bpy.path.abspath(self.filepath)

        if not filepath or not os.path.isfile(filepath):
            self.report({"ERROR"}, "No valid file selected.")
            return {"CANCELLED"}

        # =================
        # Import FBX Camera
        # =================

        bpy.ops.import_scene.fbx(filepath=filepath)

        return {"FINISHED"}


def load_cache_file(filepath):
    # 1. เช็คก่อนว่าเคยโหลดไฟล์นี้ไว้หรือยัง (เพื่อป้องกันการโหลดซ้ำซ้อน)
    # Blender path อาจเป็น Relative (//) เลยต้องแปลงเป็น Abspath เพื่อเทียบให้ชัวร์
    abs_filepath = os.path.abspath(bpy.path.abspath(filepath))

    for cache in bpy.data.cache_files:
        if os.path.abspath(bpy.path.abspath(cache.filepath)) == abs_filepath:
            return cache

    # 2. ถ้ายังไม่เคยมี ให้ใช้ Operator เปิด
    # เทคนิค: จับภาพรายการ cache ก่อนและหลัง เพื่อหาตัวใหม่ที่เพิ่งงอกออกมา
    caches_before = set(bpy.data.cache_files)

    bpy.ops.cachefile.open(filepath=filepath)

    caches_after = set(bpy.data.cache_files)
    new_caches = caches_after - caches_before

    if new_caches:
        return new_caches.pop()
    else:
        # Fallback กรณีหาไม่เจอ (ปกติจะเป็นตัวสุดท้าย)
        return bpy.data.cache_files[-1] if bpy.data.cache_files else None


class SetupOutliner(bpy.types.Operator):
    """
    Create Solidify Modifer to selected objects (Set to material outliner)
    """

    bl_idname = "render.set_up_outliner"  # <<--- เพิ่ม bl_idname
    bl_label = "Set-up Outliner"  # <<--- เพิ่ม bl_label
    # bl_options = {"INTERNAL"}  # <<--- แนะนำให้เพิ่มเพื่อไม่ให้แสดงในเมนูค้นหา (Optional)

    def execute(self, context):
        selected_objects = bpy.context.selected_objects

        if selected_objects:
            for obj in bpy.context.selected_objects:

                # Add Modiifier
                if obj.type == "MESH":
                    # Add Vertex Group for Custom Outliner
                    vertex_group_outliner = None
                    for vertex_group in obj.vertex_groups:
                        if vertex_group.name == "Outliner":
                            vertex_group_outliner = vertex_group

                    if vertex_group_outliner is None:
                        vertex_group_outliner = obj.vertex_groups.new(name="Outliner")
                        all_verts = [v.index for v in obj.data.vertices]
                        vertex_group_outliner.add(all_verts, 1.0, "REPLACE")

                    mod_solidify = obj.modifiers.new(name="Outliner", type="SOLIDIFY")
                    mod_solidify.thickness = 0.1
                    mod_solidify.offset = 0
                    mod_solidify.material_offset = 1
                    mod_solidify.use_flip_normals = True
                    mod_solidify.vertex_group = "Outliner"

            self.report({"INFO"}, "Set-up Solidfy Modifiers Complete!")
        else:
            self.report({"ERROR"}, "Nothing Selected!")

        return {"FINISHED"}

operator_classes = [
    obj for name, obj in globals().items()
    if inspect.isclass(obj) and issubclass(obj, bpy.types.Operator)
]