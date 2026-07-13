import bpy
import os
import re
import subprocess
import platform
import json  # for config_data

# NOTE: Since this is an add-on, we assume Crux modules are available or correctly linked via __init__.py
# For demonstration, assume utility and Directory are available
# from . import utility # If utility is part of this package
# from . import Directory # If Directory is part of this package

from bpy.props import StringProperty, BoolProperty, EnumProperty
import sys

from UkoreMaya.core import Logic

# ตรวจสอบว่า subprocess มีอยู่หรือไม่ (สำหรับขั้นตอนที่ 7)
# ใน Add-on จริง ควรระมัดระวังการใช้โมดูลที่ไม่ใช่ standard Python หรือ Blender
# แต่จะคงไว้ตามโค้ดต้นฉบับ

def get_detail_choices(self, context):
    """
    ฟังก์ชันนี้จะส่งคืนรายการตัวเลือกสำหรับ Enum ที่ 2 (Detail Level)
    โดยพิจารณาจากการเลือกใน Enum ที่ 1 (Asset Type)
    """
    job_type = self.job_type  # อ่านค่าที่เลือกจาก Enum 1

    # ตัวเลือกพื้นฐานสำหรับ Model
    model_choices = [
        ("PROXY", "Proxy", "Low-detail mesh for viewport"),
        ("HI", "Hi", "High-detail mesh"),
        ("TEXTURE", "Texture", "Texture-related data"),
    ]

    # ตัวเลือกพื้นฐานสำหรับ Map (Proxy และ Hi เหมือน Model)
    map_choices = [
        ("PROXY", "Proxy", "Low-detail representation"),
        ("HI", "Hi", "High-detail representation"),
    ]

    # ตรวจสอบว่า Enum 1 ถูกเลือกเป็นอะไร
    if job_type == "MODEL":
        return model_choices
    elif job_type == "MAP":
        # ในโจทย์ระบุว่า Map มีแค่ Proxy, Hi
        return map_choices
    else:
        # กรณี default หรือค่าผิดพลาด (อาจไม่จำเป็นต้องมีถ้ากำหนด default ดีแล้ว)
        return []


def get_all_objects(col):
    objs = list(col.objects)
    for child in col.children:
        objs.extend(get_all_objects(child))
    return objs


def publish_asset(self, context, name_suffix: str, file_type: str):
    """
    ฟังก์ชันหลักสำหรับดำเนินการ publish Asset
    :param self: ตัวอ้างอิงของ Operator เพื่อใช้ self.report
    :param context: บริบทของ Blender
    :param name_suffix: คำต่อท้ายชื่อไฟล์ (เช่น 'Layout', 'Hi', 'Proxy')
    :param file_type: ประเภทไฟล์ที่จะ Export ('fbx' หรือ 'blend')
    :return: สถานะการทำงาน {'FINISHED'} หรือ {'CANCELLED'}
    """
    # -----------------------------------------
    # 1) ต้องบันทึกไฟล์ .blend ก่อน
    # -----------------------------------------
    current_path = bpy.data.filepath

    if not current_path:
        self.report({"ERROR"}, "Please save current file first before publish.")
        return {"CANCELLED"}

    # -----------------------------------------
    # 2) รับ Directory ของไฟล์
    # -----------------------------------------
    version = Logic.get_new_version(
        current_share_path=current_path, subfolder=name_suffix
    )
    export_path = Logic.get_publish_path(
        current_share_path=current_path,
        subfolder=name_suffix,
        extension=file_type,
        version=version,
    )
    Logic.make_sure_folder_exist(export_path)

    print("Publish Path : ", export_path)

    # -----------------------------------------
    # 6) Export/Save ไฟล์ตามประเภทที่กำหนด
    # -----------------------------------------
    if file_type.lower() == "fbx":
        col_map_name = "Map_Grp"
        col_map = bpy.data.collections.get(col_map_name)

        if not col_map:
            bpy.ops.export_scene.fbx(
                filepath=export_path,
                use_selection=False,
                apply_scale_options="FBX_SCALE_NONE",
            )

            bpy.ops.wm.save_as_mainfile(
                filepath=export_path.replace(".fbx", ".blend"),
                check_existing=True,
                copy=True,
            )

        else:
            objs = get_all_objects(col_map)

            bpy.ops.object.select_all(action="DESELECT")
            for obj in objs:
                obj.select_set(True)

            if objs:
                bpy.context.view_layer.objects.active = objs[0]

            bpy.ops.export_scene.fbx(
                filepath=export_path,
                use_selection=True,
                apply_scale_options="FBX_SCALE_NONE",
            )

            bpy.ops.wm.save_as_mainfile(
                filepath=export_path.replace(".fbx", ".blend"),
                check_existing=True,
                copy=True,
            )

    elif file_type.lower() == "blend":
        bpy.ops.wm.save_as_mainfile(
            filepath=export_path,
            check_existing=True,
            copy=True,
        )
    else:
        self.report({"ERROR"}, f"Unsupported file type: {file_type}")
        return {"CANCELLED"}

    # -----------------------------------------
    # 7) เปิดโฟลเดอร์ publish
    # -----------------------------------------

    subprocess.Popen(f'explorer "{os.path.normpath(os.path.dirname(export_path))}"')

    self.report({"INFO"}, f"Publish Success : {export_path}")
    return {"FINISHED"}


class OverrideCollection(bpy.types.Operator):
    """
    Select Collection to make override library
    """

    bl_idname = "common.override_collection"
    bl_label = "Override Selected Collection"

    def execute(self, context):
        for obj in context.selected_objects:

            # 🔑 จุดสำคัญจริง ๆ
            if obj.type != "EMPTY":
                continue

            if not obj.instance_collection:
                continue

            # มี override แล้ว → ข้าม
            if obj.override_library:
                print("Already overridden:", obj.name)
                continue

            # ต้องเป็น linked object
            if not obj.library:
                print("Not linked:", obj.name)
                continue

            print("Creating override:", obj.name)

            obj.override_hierarchy_create(
                scene=context.scene,
                view_layer=context.view_layer,
                do_fully_editable=True,
            )

        return {"FINISHED"}


class PublishCommonExport(bpy.types.Operator):
    """
    คลาส Operator พื้นฐานสำหรับ publish Asset
    """

    bl_idname = "crux.base_publish_asset"  # <<--- เพิ่ม bl_idname
    bl_label = "Base publish Asset"  # <<--- เพิ่ม bl_label
    bl_options = {"INTERNAL"}  # <<--- แนะนำให้เพิ่มเพื่อไม่ให้แสดงในเมนูค้นหา (Optional)

    # ... คุณสมบัติอื่น ๆ (asset_suffix, file_type) ยังคงเดิม
    asset_suffix: StringProperty(name="Asset Suffix", default="", options={"HIDDEN"})
    file_type: StringProperty(name="File Type", default="", options={"HIDDEN"})

    def execute(self, context):
        # ... โค้ดเรียก publish_asset() ยังคงเดิม
        return publish_asset(self, context, self.asset_suffix, self.file_type)


# --- Map Operators ---


class PublishMapLayout(PublishCommonExport):
    bl_idname = "crux.publish_map_layout"
    bl_label = "publish Map Layout (FBX)"
    # กำหนดค่าสำหรับ Operator นี้
    asset_suffix: StringProperty(default="Layout")
    file_type: StringProperty(default="fbx")


class PublishMapHi(PublishCommonExport):
    bl_idname = "crux.publish_map_hi"
    bl_label = "publish Map Hi (BLEND)"
    # กำหนดค่าสำหรับ Operator นี้
    asset_suffix: StringProperty(default="Hi")
    file_type: StringProperty(default="blend")


# --- Model Operators ---


class PublishModelProxy(PublishCommonExport):
    bl_idname = "crux.publish_model_proxy"
    bl_label = "publish Model Proxy (FBX)"
    # กำหนดค่าสำหรับ Operator นี้
    asset_suffix: StringProperty(default="Proxy")
    file_type: StringProperty(default="fbx")


class PublishModelHi(PublishCommonExport):
    bl_idname = "crux.publish_model_hi"
    bl_label = "publish Model Hi (FBX)"
    # กำหนดค่าสำหรับ Operator นี้
    asset_suffix: StringProperty(default="Hi")
    file_type: StringProperty(default="fbx")


class PublishModelTexture(PublishCommonExport):
    bl_idname = "crux.publish_model_texture"
    bl_label = "publish Model Texture (BLEND)"
    # กำหนดค่าสำหรับ Operator นี้
    asset_suffix: StringProperty(default="Texture")
    file_type: StringProperty(default="blend")


# TEMPORARY PLACEHOLDER for external modules (ASSUMED TO BE AVAILABLE)
class Directory:
    def get_exist_publish_file(self, job_type, job_task, job_name):
        # Placeholder for directory logic
        return None


class utility:
    def get_latest_version(self, publish_dir, file_prefix):
        # Placeholder for version logic
        return 1

    def get_increment_name(self, current_path):
        # Placeholder for increment logic
        return current_path

    def extract_job_info(self, filename):
        # Placeholder for job info extraction
        return {
            "jobName": "TestJob",
            "jobType": "Model",
            "jobStatus": "Wip",
            "jobpublishStatus": "Wip",
            "version": 1,
            "ext": ".blend",
        }


# Assume config_data and open_folder function exist globally or are imported elsewhere
config_path = "config.json"
config_data = {
    "PATH": {
        "anim_polish_publish": "C:/Temp/AnimPub",
        "model_texture_publish": "C:/Temp/MatPub",
    }
}


def open_folder(path):
    if platform.system() == "Windows":
        subprocess.Popen(["explorer", os.path.normpath(path)])
    elif platform.system() == "Darwin":  # macOS
        subprocess.Popen(["open", os.path.normpath(path)])
    else:  # Linux
        subprocess.Popen(["xdg-open", os.path.normpath(path)])


# ------------------------------------------------------------------------
# Operator Classes
# ------------------------------------------------------------------------
class PublishDialog(bpy.types.Operator):
    bl_idname = "main.publish_dialog"
    bl_label = "publish"

    def execute(self, context):
        scene_props = context.scene.my_props
        job_type_value = scene_props.job_type
        job_task_value = scene_props.job_task

        if job_type_value == "MODEL":
            if job_task_value == "PROXY":
                return bpy.ops.crux.publish_model_proxy()
            elif job_task_value == "HI":
                return bpy.ops.crux.publish_model_hi()
            elif job_task_value == "TEXTURE":
                return bpy.ops.crux.publish_model_texture()
        elif job_type_value == "MAP":
            if job_task_value == "PROXY":
                return bpy.ops.crux.publish_map_layout()
            elif job_task_value == "HI":
                return bpy.ops.crux.publish_map_hi()


class CheckLinkUpdate(bpy.types.Operator):
    """
    Check every link directory ,is have new version (detect by suffix _v00x), if have will show the popup to confirm the change of relocate linking file.
    """

    bl_idname = "wm.check_link_update"
    bl_label = "Check Link Update"

    def execute(self, context):

        # Iterate to check all file path
        self.dict_link_update = {}

        for lib in bpy.data.libraries:
            current_path = os.path.normpath(bpy.path.abspath(lib.filepath))
            current_name = os.path.basename(current_path)

            # Search Relocate Name, Path
            newest_path = os.path.normpath(
                Logic.get_latest_version_in_folder_based(current_path)
            )
            print("Path Detect : ", current_path, " > ", newest_path)

            if newest_path == current_path:
                continue

            # Update Data
            self.dict_link_update[current_name] = {
                "relocate_path": newest_path,
                "current_path": current_path,
                "lib": lib,
                "relocate_name": os.path.basename(newest_path),
                "current_name": current_name,
            }

            # Relocate path
            lib.filepath = bpy.path.relpath(newest_path)

        if self.dict_link_update:
            text_data = ""
            for key, value in self.dict_link_update.items():
                text_data += "{} > {}\n".format(
                    value["current_name"], value["relocate_name"]
                )

            res = bpy.ops.my.custom_confirm(
                "INVOKE_DEFAULT", message="Detect New Version:\n {}".format(text_data)
            )

            print("result : ", res)
        else:
            res = bpy.ops.my.custom_confirm(
                "INVOKE_DEFAULT", message="All Link Already up to date"
            )

        return {"FINISHED"}


class PublishProperties(bpy.types.PropertyGroup):

    # 1. Enum ตัวที่ 1: Asset Type
    job_type: bpy.props.EnumProperty(
        name="",
        items=[
            ("MODEL", "Model", "Select mesh or model data"),
            ("MAP", "Map", "Select map or scene data"),
        ],
        default="MODEL",
        # ไม่จำเป็นต้องมี update function เพราะ Enum 2 จะเรียก Getter เอง
    )

    # 2. Enum ตัวที่ 2: Detail Level (ใช้ Getter Function)
    job_task: bpy.props.EnumProperty(
        name="",
        items=get_detail_choices,  # <<--- แทนที่รายการ Choices ด้วย Getter Function
        description="Select the detail level based on Asset Type",
    )


def get_job_task_choice(self, context):
    """
    ฟังก์ชันนี้จะส่งคืนรายการตัวเลือกสำหรับ Enum ที่ 2 (Detail Level)
    โดยพิจารณาจากการเลือกใน Enum ที่ 1 (Asset Type)
    """
    asset_type = self.asset_type  # อ่านค่าที่เลือกจาก Enum 1

    # ตัวเลือกพื้นฐานสำหรับ Model
    model_choices = [
        ("PROXY", "Proxy", "Low-detail mesh for viewport"),
        ("HI", "High Poly", "High-detail mesh"),
        ("TEXTURE", "Texture", "Texture-related data"),
    ]

    # ตัวเลือกพื้นฐานสำหรับ Map (Proxy และ Hi เหมือน Model)
    map_choices = [
        ("PROXY", "Proxy", "Low-detail representation"),
        ("HI", "High Quality", "High-detail representation"),
    ]

    # ตรวจสอบว่า Enum 1 ถูกเลือกเป็นอะไร
    if asset_type == "MODEL":
        return model_choices
    elif asset_type == "MAP":
        # ในโจทย์ระบุว่า Map มีแค่ Proxy, Hi
        return map_choices
    else:
        # กรณี default หรือค่าผิดพลาด (อาจไม่จำเป็นต้องมีถ้ากำหนด default ดีแล้ว)
        return []


class MY_OT_custom_confirm(bpy.types.Operator):
    bl_idname = "my.custom_confirm"
    bl_label = "Confirm"

    message: bpy.props.StringProperty(default="")

    def draw(self, context):
        layout = self.layout
        for line in self.message.split("\n"):
            layout.label(text=line)

    def invoke(self, context, event):
        # เพิ่มความกว้าง เช่น 400, 500, 600 px
        return context.window_manager.invoke_props_dialog(self, width=500)

    def execute(self, context):
        print("OK")
        return {"FINISHED"}

    def cancel(self, context):
        print("Cancel")


class publishCompleteOperator(bpy.types.Operator):
    bl_idname = "wm.dialog_publish_complete"
    bl_label = "publish Sucessful!"

    def execute(self, context):
        return {"FINISHED"}

    def invoke(self, context, event):
        # This pops up a Yes/No dialog
        return context.window_manager.invoke_confirm(self, event)


class Configuration(bpy.types.Operator):
    bl_idname = "wm.configuration"
    bl_label = "Configuration"

    def execute(self, context):
        # os.startfile(config_path) # Removed os.startfile for cross-platform compatibility
        open_folder(
            os.path.dirname(config_path)
        )  # Assume we open the folder containing config

        return {"FINISHED"}


class OpenDirectory(bpy.types.Operator):
    bl_idname = "wm.open_directory"
    bl_label = "Directory"

    def execute(self, context):
        # os.startfile(get_export_path()) # Assume get_export_path() exists
        # Simplified: Open the current blend file's folder
        if bpy.data.filepath:
            open_folder(os.path.dirname(bpy.data.filepath))

        return {"FINISHED"}


class SaveIncrement(bpy.types.Operator):
    bl_idname = "publish.save_increment"
    bl_label = "Save Increment"

    def execute(self, context):
        current_path = bpy.data.filepath

        if not current_path:
            self.report({"ERROR"}, "publish Failed : Please save your file first.")
            return {"CANCELLED"}

        current_dir, current_name = os.path.split(current_path)
        base, ext = os.path.splitext(current_name)

        # หาเลข v###
        match = re.search(r"_v(\d{3})$", base)

        if match:
            # ถ้ามีอยู่แล้ว → เพิ่มเลข
            version = int(match.group(1)) + 1
            new_base = re.sub(r"_v\d{3}$", f"_v{version:03d}", base)
        else:
            # ถ้าไม่มี v### → ใส่ _v001 ต่อท้าย
            new_base = f"{base}_v001"

        new_path = os.path.join(current_dir, new_base + ext)

        # save file
        bpy.ops.wm.save_as_mainfile(filepath=new_path)

        self.report({"INFO"}, f"✅ Saved new version: {new_path}")
        return {"FINISHED"}


class OpenShareDirectory(bpy.types.Operator):
    "Open File in Share Directory Quickly"

    bl_idname = "main.open_share_directory"
    bl_label = "Open..."

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    share_dir = r"G:\My Drive\Projects\KafkaProj\share"

    def invoke(self, context, event):
        self.filepath = os.path.join(self.share_dir, "select_here.dummy")

        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        filepath = bpy.path.abspath(self.filepath)

        if not filepath or not os.path.isfile(filepath):
            return {"CANCELLED"}

        bpy.ops.wm.open_mainfile(filepath=filepath)

        return {"FINISHED"}


class SaveAs(bpy.types.Operator):
    "Open File in Share Directory Quickly"

    bl_idname = "main.save_as"
    bl_label = "Save as..."

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    share_dir = r"G:\My Drive\Projects\KafkaProj\share"

    def invoke(self, context, event):
        self.filepath = os.path.join(self.share_dir, "select_here.dummy")

        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        filepath = bpy.path.abspath(self.filepath)

        if not filepath or not os.path.isfile(filepath):
            return {"CANCELLED"}

        bpy.ops.wm.save_as_mainfile(filepath=filepath)

        return {"FINISHED"}


class CRUX_OT_import_or_link(bpy.types.Operator):
    """Import FBX/OBJ/ABC or Link BLEND depending on file type"""

    bl_idname = "crux.import_or_link"
    bl_label = "Import or Link File"
    bl_options = {"REGISTER", "UNDO"}

    # These must exist for file selector
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(
        default="*.blend;*.fbx;*.obj;*.abc", options={"HIDDEN"}
    )

    # ===== DEFAULT DIRECTORY =====
    DEFAULT_DIR = r"G:\My Drive\Projects\KafkaProj\publish"

    def invoke(self, context, event):
        self.filepath = os.path.join(self.DEFAULT_DIR, "select_here.dummy")

        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        filepath = bpy.path.abspath(self.filepath)

        if not filepath or not os.path.isfile(filepath):
            return {"CANCELLED"}

        ext = os.path.splitext(filepath)[1].lower()

        # ╔════════════════════════════════════╗
        #   .BLEND → LINK
        # ╚════════════════════════════════════╝
        if ext == ".blend":
            try:
                # อ่านชื่อ collection ทั้งหมดในไฟล์
                with bpy.data.libraries.load(filepath) as (data_from, data_to):
                    collection_names = list(data_from.collections)

                if not collection_names:
                    self.report({"ERROR"}, "No collections found in this .blend file.")
                    return {"CANCELLED"}

                directory = filepath + "\\Collection\\"

                # ลิงก์ทีละ collection
                for col_name in collection_names:
                    bpy.ops.wm.link(
                        filepath=directory + col_name,
                        directory=directory,
                        filename=col_name,
                    )

                self.report(
                    {"INFO"},
                    f"Linked {len(collection_names)} collections successfully.",
                )

            except Exception as e:
                self.report({"ERROR"}, f"Link failed: {e}")
                return {"CANCELLED"}

        # ╔════════════════════════════════════╗
        #   FBX / OBJ / ABC → IMPORT
        # ╚════════════════════════════════════╝
        elif ext == ".fbx":
            bpy.ops.import_scene.fbx(filepath=filepath)
            self.report({"INFO"}, "Imported FBX file.")

        elif ext == ".obj":
            bpy.ops.wm.obj_import(filepath=filepath)
            self.report({"INFO"}, "Imported OBJ file.")

        elif ext == ".abc":
            bpy.ops.wm.alembic_import(filepath=filepath)
            self.report({"INFO"}, "Imported Alembic file.")

        else:
            self.report({"ERROR"}, f"Unsupported file type: {ext}")
            return {"CANCELLED"}

        return {"FINISHED"}


# List of all operator classes to register
# NOTE: The list below assumes ALL your original operators are present and defined above
operator_classes = [
    # publish/Save Operators
    PublishProperties,
    MY_OT_custom_confirm,
    CheckLinkUpdate,
    SaveIncrement,
    publishCompleteOperator,
    PublishDialog,
    # Import/Export Operators
    PublishMapLayout,
    CRUX_OT_import_or_link,
    PublishCommonExport,
    PublishMapHi,
    PublishModelProxy,
    PublishModelHi,
    PublishModelTexture,
    # Utility Operators
    Configuration,
    OpenDirectory,
    OpenShareDirectory,
    SaveAs,
    OverrideCollection,
    # LinkAnimation, # The code for LinkAnimation is very long; assuming it's here
]
