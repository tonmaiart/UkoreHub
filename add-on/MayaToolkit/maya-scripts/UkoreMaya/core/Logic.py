"""
Natchapon Srisuk for Ukore Studio , 4 December 2025

All of this script design for get publsh , validate publish path across Blender and Maya
So I will keep only import python default module, no bpy or maya.cmds
"""

import os
import re
import shutil

from . import utils

def convert_to_publish_path(path):
    """
    ตรวจสอบความถูกต้องของพาธเพื่อให้แน่ใจว่าเป็นไปตามโครงสร้างที่คาดหวัง '.../share/<Dept>/<MapName>/...'
    และแปลงพาธให้เป็นพาธราก 'publish' ที่สอดคล้องกัน โดยรวมถึงพาธย่อยทั้งหมดที่อยู่ใน
    ไดเร็กทอรี share ดั้งเดิม

    อาร์กิวเมนต์:
        path (str): พาธไฟล์ปัจจุบันหรือพาธไดเร็กทอรี
                    เช่น G:/projects/kafka/share/Character/Kafka/Model/scene.ma
                    Only Input Path in share directory and its subfolder, not publish directory

    คืนค่า:
        dict: ดิคชันนารีที่มี 'publish_root_dir' (พาธ publish พื้นฐานที่สอดคล้องกับโฟลเดอร์อินพุต)
              เช่น {"publish_root_dir": "G:/projects/kafka/publish/Character/Kafka/Model"}

    ข้อผิดพลาด:
        ValueError: หากพาธไม่ได้อยู่ในโฟลเดอร์ 'share' หรือโครงสร้างเริ่มต้นไม่ถูกต้อง
    """
    path = os.path.normpath(path).replace("\\", "/")

    # ดึงพาธไดเร็กทอรี แม้ว่าจะระบุชื่อไฟล์มาก็ตาม
    if os.path.isfile(path) or (
        not os.path.isdir(path) and len(path.split("/")[-1].split(".")) > 1
    ):
        path = os.path.dirname(path)

    parts = path.split("/")

    if "share" not in parts:
        raise ValueError(f"Current Path is not inside a 'share' folder: {path}")

    share_index = parts.index("share")

    # การตรวจสอบอย่างเข้มงวด: ยังคงต้องมี Dept และ MapName ทันทีหลัง share
    try:
        parts[share_index + 1]  # Dept (แผนก)
        parts[share_index + 2]  # MapName (ชื่อแผนที่)
    except IndexError:
        raise ValueError("Folder structure must be: .../share/<Dept>/<MapName>/...")

    # สร้างพาธ publish พื้นฐานแบบขยายโดยแทนที่ 'share' ด้วย 'publish'
    publish_parts = parts[:]
    publish_parts[share_index] = "publish"

    publish_root_dir_extended = "/".join(publish_parts)

    return {
        "publish_root_dir": publish_root_dir_extended,
    }


def get_new_version(current_share_path, subfolder):
    """
    กำหนดหมายเลขเวอร์ชันถัดไปที่พร้อมใช้งาน (เช่น 2 สำหรับ 'v002')
    โดยการตรวจสอบไดเร็กทอรีย่อย 'vXXX' ที่มีอยู่ภายในพาธโฟลเดอร์ย่อยที่กำหนด

    โครงสร้างที่ตรวจสอบคือ: .../publish/.../<subfolder>/vXXX/

    อาร์กิวเมนต์:
        current_share_path (str): พาธแบบเต็มไปยังไฟล์หรือไดเร็กทอรีที่แชร์ปัจจุบัน
        subfolder (str): ชื่อโฟลเดอร์ย่อยที่ใช้ในการจัดหมวดหมู่การ publish
                         (เช่น "Proxy", "Anim", "Layout").

    คืนค่า:
        int: หมายเลขเวอร์ชันถัดไปที่พร้อมใช้งาน (เช่น 1 สำหรับ v001, 5 สำหรับ v005).
    """
    info = convert_to_publish_path(current_share_path)

    # พาธที่จะตรวจสอบเวอร์ชัน: <publish_root_dir>/<subfolder>/
    tag_dir = os.path.join(info["publish_root_dir"], subfolder).replace("\\", "/")

    if not os.path.isdir(tag_dir):
        return 1

    max_version = 0
    version_pattern = re.compile(r"^v(\d{3})$")

    try:
        for entry in os.listdir(tag_dir):
            full_path = os.path.join(tag_dir, entry)
            if os.path.isdir(full_path):
                match = version_pattern.match(entry)
                if match:
                    version_number = int(match.group(1))
                    max_version = max(max_version, version_number)
    except Exception as e:
        print(
            f"Warning: Could not list directory {tag_dir}. Assuming version 1. Error: {e}"
        )
        return 1

    return max_version + 1


def generate_publish_version_directory_path(current_share_path, subfolder, version=None):
    """
    Create a standardized publish path based on the current share path and the specified subfolder, extension, version, and optional name.

    โครงสร้างพาธผลลัพธ์คือ:
    .../publish/<Dept>/<MapName>/<SubPath>/<name>/vXXX/<name>_vXXX.<ext>

    Args:
        current_share_path (str): พาธแบบเต็มไปยังไฟล์หรือไดเร็กทอรีที่แชร์ปัจจุบัน
        name (str): ชื่อโฟลเดอร์ย่อยที่ใช้ในการจัดหมวดหมู่การ publish.
        extension (str): นามสกุลไฟล์ที่ต้องการ (เช่น "fbx" หรือ ".abc").
        version (int): หมายเลขเวอร์ชันที่จะใช้ (ต้อง > 0), if None mean use lastest version.

    Returns:
        str: พาธแบบเต็มที่ถูกทำให้เป็นมาตรฐานไปยังไฟล์
             เช่น G:/.../publish/Character/Kafka/Model/Proxy/v001/Proxy_v001.fbx
    """
    info = convert_to_publish_path(current_share_path)

    publish_root_dir = info["publish_root_dir"]

    full_path = os.path.join(publish_root_dir, subfolder)
    make_sure_folder_exist(full_path)

    if version is None:
        find_version = get_latest_version_folder(full_path)

        if find_version is None:
            version = 1
        else:
            version = find_version+1

    publish_path = os.path.join(full_path, f"v{int(version):03d}").replace("\\", "/")
    return publish_path

def create_publish_path(current_share_path, subfolder, extension, version, name=""):
    """
    Create a standardized publish path based on the current share path and the specified subfolder, extension, version, and optional name.

    โครงสร้างพาธผลลัพธ์คือ:
    .../publish/<Dept>/<MapName>/<SubPath>/<name>/vXXX/<name>_vXXX.<ext>

    Args:
        current_share_path (str): พาธแบบเต็มไปยังไฟล์หรือไดเร็กทอรีที่แชร์ปัจจุบัน
        name (str): ชื่อโฟลเดอร์ย่อยที่ใช้ในการจัดหมวดหมู่การ publish.
        extension (str): นามสกุลไฟล์ที่ต้องการ (เช่น "fbx" หรือ ".abc").
        version (int): หมายเลขเวอร์ชันที่จะใช้ (ต้อง > 0).

    Returns:
        str: พาธแบบเต็มที่ถูกทำให้เป็นมาตรฐานไปยังไฟล์
             เช่น G:/.../publish/Character/Kafka/Model/Proxy/v001/Proxy_v001.fbx
    """
    info = convert_to_publish_path(current_share_path)

    publish_root_dir = info["publish_root_dir"]

    # ใช้ส่วนขยายที่ให้มาโดยตรง โดยตรวจสอบให้แน่ใจว่าขึ้นต้นด้วยจุด
    if not extension.startswith("."):
        ext = "." + extension.lower()
    else:
        ext = extension.lower()

    version_folder = f"v{version:03d}"

    # โครงสร้างชื่อไฟล์: <name>_vXXX.ext
    if name:
        base_filename = f"{name}_v{version:03d}{ext}"
    else:
        base_filename = f"v{version:03d}{ext}"

    # พาธสุดท้าย: <publish_root_dir>/<name>/<version_folder>/<base_filename>
    full_path = os.path.join(
        publish_root_dir, subfolder, version_folder, base_filename
    ).replace("\\", "/")

    return full_path


def get_latest_version_in_folder_based(ref_path):
    """ ค้นหาไฟล์เวอร์ชันล่าสุดในโฟลเดอร์เดียวกันกับพาธอ้างอิงที่ให้มา โดยตรวจสอบโครงสร้างเวอร์ชัน vXXX ในไดเร็กทอรีที่เกี่ยวข้อง
    Args:
        ref_path (str): พาธไฟล์หรือไดเร็กทอรีที่ใช้เป็นจุดอ้างอิงในการค้นหาเวอร์ชันล่าสุด เขช่น G:/projects/kafka/publish/Character/Kafka/Model/Proxy/scene.ma หรือ G:/projects/kafka/publish/Character/Kafka/Model/Proxy/

    Returns:
        str: พาธแบบเต็มไปยังไฟล์เวอร์ชันล่าสุดที่พบใน , if return is None , is mean not found any exists version
    """
    if not ref_path:
        raise ValueError("Reference path is empty or None.")
    print("aa",ref_path)

    ref_path = os.path.normpath(ref_path)
    if os.path.isdir(ref_path):
        ext = ""
    else:
        ext = ref_path.split(".")[-1]

    ref_path = os.path.normpath(ref_path).replace("\\", "/")

    print("## Find Lastest Version for : {}".format(ref_path))

    if "." in ref_path:
        ref_path = os.path.dirname(ref_path)

    if not os.path.exists(ref_path):
        raise FileNotFoundError(f"Path does not exist: {ref_path}")

    parts = ref_path.split("/")
    if "publish" not in parts:
        raise ValueError(f"Path must contain 'publish' folder: {ref_path}")

    pub_index = parts.index("publish")

    if len(parts) <= pub_index + 2:
        raise ValueError(
            f"Path too short. Must be at least 4 blocks deep from 'publish' folder."
        )

    # Find Version Folder
    for count in (3, 4, 5):
        parent_folder = "/".join(parts[: pub_index + count])

        if not os.path.isdir(parent_folder):
            raise FileNotFoundError(f"Target parent folder not found: {parent_folder}")

        version_folders = [
            name
            for name in os.listdir(parent_folder)
            if os.path.isdir(os.path.join(parent_folder, name))
            and re.match(r"v\d+$", name)
        ]
        if version_folders:
            break

    if not version_folders:
        return None

    version_folders.sort(key=lambda x: int(x[1:]))
    latest_ver_folder = version_folders[-1]

    latest_folder_path = os.path.join(parent_folder, latest_ver_folder).replace(
        "\\", "/"
    )

    files = [
        f
        for f in os.listdir(latest_folder_path)
        if os.path.isfile(os.path.join(latest_folder_path, f))
    ]

    if not files:
        raise FileNotFoundError(
            f"No files found in latest version folder: {latest_folder_path}"
        )

    preferred = f"{latest_ver_folder}."
    matched = [f for f in files if f.startswith(preferred) and f.endswith(ext)]

    if matched:
        print(
            "Result : ", os.path.normpath(os.path.join(latest_folder_path, matched[0]))
        )
        return os.path.normpath(os.path.join(latest_folder_path, matched[0]))
    else:
        return None


def get_latest_version_folder(root_folder):
    """
    Args:
        root_folder (str): e.g. 'G:/projects/kafka/publish/Character/Kafka/Model/Proxy'
    Returns:
        int : latest version number (e.g., 3 instead of 'v003')
    """
    if not os.path.isdir(root_folder):
        return None

    # Filter for folders matching the 'v000' pattern
    version_folders = [
        name for name in os.listdir(root_folder)
        if os.path.isdir(os.path.join(root_folder, name))
        and re.match(r"v\d+$", name)
    ]

    if not version_folders:
        return None
    
    # Sort folders based on the integer value after the 'v'
    version_folders.sort(key=lambda x: int(x[1:]))
    latest_folder_name = version_folders[-1]

    # Convert the folder name (e.g., 'v005') into an integer (5)
    return int(latest_folder_name[1:])



def update_sync_folder(directory_path):
    """ Sync latest version folder to v000 for quick reference and use in Maya and Blender.
     
    Arguments:
        directory_path (str): พาธไปยังไดเร็กทอรีที่มีโครงสร้างเวอร์ชัน (เช่น .../publish/Character/Kafka/Model/Proxy/)
        inside which the script will search for the latest version folder (v001, v002, etc.) and sync it to v000.
       """

    latest_version = 0
    latest_folder_name = None
    version_pattern = re.compile(r"^v(\d{3})$")

    dir_to_search = os.path.normpath(directory_path).replace("\\", "/")
    if not dir_to_search.endswith("/"):
        dir_to_search += "/"

    if not os.path.isdir(dir_to_search):
        print(f"❌ ERROR: Directory not found at {dir_to_search}")
        return None

    try:
        for entry in os.listdir(dir_to_search):
            full_path = os.path.join(dir_to_search, entry)
            if os.path.isdir(full_path):
                match = version_pattern.match(entry)
                if match:
                    version_number = int(match.group(1))
                    if version_number > latest_version:
                        latest_version = version_number
                        latest_folder_name = entry

    except Exception as e:
        print(f"❌ An unexpected error occurred during search: {e}")
        return None

    if not latest_folder_name:
        print("❌ No version folders (v001, v002, ...) found to sync from.")
        return None

    source_path = os.path.join(dir_to_search, latest_folder_name).replace("\\", "/")
    target_folder_name = "v000"
    target_path = os.path.join(dir_to_search, target_folder_name).replace("\\", "/")

    print(f"✅ Found latest version: **{latest_folder_name}** ({source_path})")

    if os.path.exists(target_path):
        print(f"🗑️ Deleting existing folder: **{target_folder_name}**")
        try:
            shutil.rmtree(target_path)
            print("Successfully deleted old v000 folder.")
        except OSError as e:
            print(f"❌ Error deleting folder {target_path}: {e}")
            return None
    else:
        print(f"ℹ️ Folder **{target_folder_name}** does not exist. Skipping deletion.")

    print(f"🔄 Copying **{latest_folder_name}** to **{target_folder_name}**")
    try:
        shutil.copytree(source_path, target_path)
        print(f"🎉 Successfully synced **{latest_folder_name}** to **v000**!")
    except shutil.Error as e:
        print(f"❌ Error during copy operation: {e}")
    except OSError as e:
        print(f"❌ OS Error during copy: {e}")

    print(f"🔨 Renaming all internal version tags to v000 in **{target_path}**")

    source_version_tag = f"v{latest_version:03d}"
    target_version_tag = "v000"

    for root, dirs, files in os.walk(target_path, topdown=False):
        for name in files:
            new_name = name.replace(source_version_tag, target_version_tag)

            if new_name != name:
                old_file = os.path.join(root, name)
                new_file = os.path.join(root, new_name)
                try:
                    os.rename(old_file, new_file)
                except OSError as e:
                    print(f"⚠️ Error renaming file {old_file}: {e}")

    for root, dirs, _ in os.walk(target_path, topdown=False):
        for i in range(len(dirs)):
            name = dirs[i]
            new_name = name.replace(source_version_tag, target_version_tag)

            if new_name != name:
                old_dir = os.path.join(root, name)
                new_dir = os.path.join(root, new_name)
                try:
                    if not os.path.exists(new_dir):
                        os.rename(old_dir, new_dir)
                        dirs[i] = new_name
                except OSError as e:
                    print(f"⚠️ Error renaming directory {old_dir}: {e}")

    return {"source": source_path, "target": target_path}


def make_sure_folder_exist(path):
    if os.path.isfile(path):
        path_dir = os.path.dirname(path)
    else:
        path_dir = path
        
    if not os.path.exists(path_dir):
        os.makedirs(path_dir)
