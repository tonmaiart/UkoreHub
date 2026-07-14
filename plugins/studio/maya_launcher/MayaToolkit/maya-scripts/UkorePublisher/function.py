import maya.cmds as mc
import os
from UkoreMaya.core import Pipeline, utils,Logic


def publish_dialog(result_job_type, result_job_task):
    """This is function going to publish any job task or job task from current file"""

    # ======================
    # Prepare Publish Path
    # ======================

    scene_path = mc.file(q=True, sn=True)
    if not scene_path:
        mc.warning("กรุณาบันทึกไฟล์ก่อนดำเนินการ Publish!")
        return

    new_version = utils.get_new_version(scene_path, result_job_task)

    # Model, Proxy,Hi > Fbx,ma
    if result_job_type == "Model":
        publish_file_path = publish_common(
            subfolder=result_job_task,
            extension="fbx",
            export_type="fbx",
            version=new_version,
        )
        publish_file_path = publish_common(
            subfolder=result_job_task,
            extension="ma",
            export_type="ma",
            version=new_version,
        )

    # Rig , Proxy,Hi > Maya Ascii
    elif result_job_type == "Rig":
        publish_file_path = publish_common(
            subfolder=result_job_task,
            extension="ma",
            export_type="rig",
            version=new_version,
        )

    # Anim , Multiple Type of Exporting , use custom function
    elif result_job_type == "Anim" and result_job_task == "Main":
        publish_file_path = publish_common(
            subfolder=export_path,
            extension="avi",
            export_type="playblast",
            version=new_version,
        )
        
    elif result_job_type == "Anim" and result_job_task == "Playblast":
        publish_file_path = publish_common(
            subfolder=export_path,
            extension="avi",
            export_type="playblast",
            version=new_version,
        )

    elif result_job_type == "Anim":
        print("# Start Publish Animation Data")
        export_path = get_export_path(
            subfolder=result_job_task, extension="abc", version=new_version
        )
        publish_file_path = Pipeline.export_shot_to_ue(export_path=export_path)
    job_task_path = os.path.dirname(os.path.dirname(publish_file_path))
    print("# Update Sync Folder (v000)")
    print("Job Task Path : {}".format(job_task_path))
    # utils.update_sync_folder(job_task_path)

    return publish_file_path


def get_export_path(subfolder, extension, version, name=""):
    scene_path = mc.file(q=True, sn=True)
    export_path = utils.get_publish_path(
        current_share_path=scene_path,
        name=name,
        subfolder=subfolder,
        extension=extension,
        version=version,
    )

    if not os.path.exists(os.path.dirname(export_path)):
        os.makedirs(os.path.dirname(export_path))

    print("# Generate New Publish Path : {}".format(export_path))
    return export_path


def publish_common(subfolder, export_type,version,name,extension=None):
    """
    This function designed for publish file based on export type, since regular file type to custom export type.
    """
    scene_path = mc.file(q=True, sn=True)
    export_path = Logic.generate_publish_version_directory_path(
        current_share_path=scene_path,
        name=name,
        subfolder=subfolder,
        version=version,
    )

    if not os.path.exists(os.path.dirname(export_path)):
        os.makedirs(os.path.dirname(export_path))

    print("# Generate New Publish Path : {}".format(export_path))

    # Export
    try:
        if export_type == "fbx":
            Pipeline.export_fbx_common(export_path=export_path)

        elif export_type == "abc":
            Pipeline.export_abc_common(export_path=export_path)

        elif export_type == "playblast":
            Pipeline.export_playblast(export_path=export_path)

        # Export Maya File
        elif export_type in ("ma", "mb"):
            Pipeline.export_maya_common(export_path=export_path)

        # Export Fbx for Custom Animation
        elif export_type == "anim_fbx":
            Pipeline.export_anim_fbx(export_path=export_path)

        elif export_type == "anim_abc":
            Pipeline.export_anim_abc(export_path=export_path)

        # Export Metadata.json for Custom Animation
        elif export_type == "anim_metadata":
            Pipeline.export_anim_metadata(export_path=export_path)

        # Export Camera Animation
        elif export_type == "anim_camera":
            Pipeline.export_anim_camera(export_fbx_path=export_path)

        # find baked list locator
        elif export_type == "anim_vis":
            Pipeline.export_anim_vis(export_path=export_path)

        elif export_type == "rig":
            Pipeline.export_maya_common(export_path=export_path)

        else:
            mc.error(f"ไม่รองรับการส่งออกประเภท: {export_type}")
            return

    except Exception as e:
        mc.error(f"การ Export ล้มเหลว: {e}")
        return

    return export_path
