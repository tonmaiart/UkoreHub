import json
import os  # ใช้สำหรับตรวจสอบว่าไฟล์มีอยู่จริง
import re
import shutil
from pathlib import Path
import os
import re
import subprocess
import platform
from Crux.core import Directory, ProjectSetting


def create_publish_path(
    base_folder_path: str,
    job_name: str,
    job_type: str,
    job_task: str,
    job_desc: str,
    extension: str,
    state: str = "Pub",
):
    """
    สร้าง Path สำหรับไฟล์ Publish ใหม่ พร้อมหาเวอร์ชัน (vXXX) ถัดไปโดยอัตโนมัติ

    Args:
        base_folder_path: Path ของโฟลเดอร์หลัก เช่น 'D:/Project/Assets'
        job_name: ชื่อ Job (e.g., 'Minty')
        job_type: ประเภท Job (e.g., 'Rig')
        job_task: Task ของ Job (e.g., 'Proxy')
        job_desc: รายละเอียด Job (e.g., 'Prop') (อาจใช้หรือไม่ใช้ในชื่อไฟล์ก็ได้)
        extension: นามสกุลไฟล์ที่ต้องการ (e.g., '.ma', '.fbx')
        state: สถานะไฟล์ ('Pub' สำหรับ Published)

    Returns:
        Path object ของไฟล์ Publish ใหม่พร้อมเวอร์ชันถัดไป
    """

    # 1. กำหนดรูปแบบโฟลเดอร์ย่อย (ถ้ามีการจัดโครงสร้างย่อย)
    # ในตัวอย่างนี้ ใช้ base_folder_path เป็นที่เก็บไฟล์โดยตรง
    folder = Path(base_folder_path)
    os.makedirs(folder, exist_ok=True)

    # 2. กำหนดรูปแบบชื่อไฟล์พื้นฐาน
    # รูปแบบชื่อไฟล์: {job_name}_{job_type}_{job_task}_{job_desc}_{state}_vXXX.ext
    # เราจะใช้รูปแบบที่ใกล้เคียงกับภาพที่คุณให้มา: {job_name}_{job_type}_{job_task}_{state}
    base_file_prefix = f"{job_name}_{job_type}_{job_task}_{state}"

    # 3. ค้นหาเวอร์ชันล่าสุดที่มีอยู่

    latest_version = 0
    version_pattern = re.compile(
        r"_v(\d+)" + re.escape(extension) + r"$"
    )  # ค้นหา _v(ตัวเลข) ตามด้วยนามสกุลไฟล์ที่ถูก Escape และอยู่ท้ายสุดของสตริง

    # กรองไฟล์ที่มีชื่อขึ้นต้นที่ถูกต้อง
    files = [
        f
        for f in folder.iterdir()
        if f.is_file()
        and f.name.startswith(base_file_prefix)
        and f.name.endswith(extension)
    ]

    for each_file in files:
        file_name = each_file.name

        # ค้นหาหมายเลขเวอร์ชัน
        match = version_pattern.search(file_name)

        if match:
            version_str = match.group(1)
            try:
                current_version = int(version_str)
                # หาเวอร์ชันสูงสุด
                if current_version > latest_version:
                    latest_version = current_version
            except ValueError:
                # ข้ามไฟล์ที่ดึงตัวเลขเวอร์ชันไม่ได้
                continue

    # 4. สร้าง Path สำหรับเวอร์ชันถัดไป

    # เวอร์ชันใหม่ = เวอร์ชันล่าสุด + 1
    next_version = latest_version + 1

    # จัดรูปแบบเป็นตัวเลข 3 หลัก (v001, v002, ...)
    version_suffix = f"_v{next_version:03d}"

    # สร้างชื่อไฟล์สมบูรณ์: Minty_Rig_Proxy_Pub_v003.ma
    new_file_name = f"{base_file_prefix}{version_suffix}{extension}"

    # สร้าง Path ที่สมบูรณ์
    new_publish_path = folder / new_file_name

    return new_publish_path


def open_folder(path):
    """Open folder on Win / Mac / Linux."""
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":  # macOS
        subprocess.Popen(["open", path])
    else:  # Linux
        subprocess.Popen(["xdg-open", path])


def get_latest_version(path, prefix):
    """
    Return next version number as integer.
    Check existing files: prefix_v001.fbx → next = 2
    """
    if not os.path.exists(path):
        return 1

    version_pattern = re.compile(rf"{re.escape(prefix)}_v(\d+)\.fbx", re.IGNORECASE)
    max_ver = 0

    for f in os.listdir(path):
        m = version_pattern.match(f)
        if m:
            v = int(m.group(1))
            if v > max_ver:
                max_ver = v

    return max_ver + 1


def get_increment_name(file_path, increment_main=False):
    """
    Smart version increment:
      - If file has ONLY main version: always increment main (never create sub)
      - If file has main + sub version:
            increment_main=True  → increment main (remove sub)
            increment_main=False → increment sub
    """

    dir_name = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)
    name, ext = os.path.splitext(base_name)

    match = re.match(r"^(.*)_v(\d{3})(?:_(\d{3}))?$", name)
    if not match:
        raise ValueError("Filename must contain version pattern _v### or _v###_###")

    prefix, main_str, sub_str = match.groups()
    main_ver = int(main_str)
    sub_ver = int(sub_str) if sub_str else None

    # ---------------------------------------------------------
    # CASE 1: File has ONLY main version (v001)
    #         → ALWAYS increment main, ignore increment_main flag
    # ---------------------------------------------------------
    if sub_ver is None:
        main_ver += 1
        new_name = f"{prefix}_v{main_ver:03d}{ext}"
        return os.path.join(dir_name, new_name)

    # ---------------------------------------------------------
    # CASE 2: File has sub version (v001_003)
    # ---------------------------------------------------------

    # Increase MAIN version
    if increment_main:
        main_ver += 1
        new_name = f"{prefix}_v{main_ver:03d}{ext}"
        return os.path.join(dir_name, new_name)

    # Increase SUB version
    else:
        sub_ver += 1
        new_name = f"{prefix}_v{main_ver:03d}_{sub_ver:03d}{ext}"
        return os.path.join(dir_name, new_name)


def set_current_tab_by_name(tab_widget, tab_name):
    for i in range(tab_widget.count()):
        if tab_widget.tabText(i) == tab_name:
            tab_widget.setCurrentIndex(i)
            return True
    return False


def duplicate_file(src, dst, new_name=None):
    print("Copy : {} , to {}".format(src, dst))
    if os.path.isdir(dst):
        name = new_name or os.path.basename(src)
        dst = os.path.join(dst, name)
    elif new_name:
        dst = os.path.join(os.path.dirname(dst), new_name)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    return shutil.copy2(src, dst)


def get_current_publish_data(jobName, jobType, jobTask, ext=".ma"):
    """
    Return publish file path & new version name for publishing.

    Args:
        config_path (str): Path to config.json
        jobName (str): Name of job (e.g., "SCH020")
        jobType (str): Type of job (e.g., "Anim", "Model")
        jobTask (str): Task of job (e.g., "Block", "Layout")
        ext (str): File extension (e.g., ".ma")

    Returns:
        dict:
            {
                "publish_path": str,
                "publish_name": str,
                "version": int,
                "ext": str
            }
    """

    # --- Load config ---

    project_setting = ProjectSetting.ProjectSetting()

    project_config = project_setting.get_project_config_data()
    publish_config = project_setting.get_publish_paths_config()

    proj_name = project_config["name"]
    proj_dir = project_config["project_directory_path"]
    proj_path = os.path.join(proj_dir, proj_name)

    # --- Build target publish directory ---
    # Lowercase keys to match your config structure
    pub_dir = publish_config[jobType.lower()][jobTask.lower()]

    target_dir = os.path.join(proj_path, pub_dir, jobName)
    os.makedirs(target_dir, exist_ok=True)

    # --- Detect existing versions ---
    max_version = 0
    prefix = f"{jobName}_{jobType}_{jobTask}_Pub"

    for f in os.listdir(target_dir):
        if f.startswith(prefix) and f.endswith(ext):
            m = re.search(r"_v(\d+)", f)
            if m:
                max_version = max(max_version, int(m.group(1)))

    # --- Determine next version ---
    version = 1 if max_version == 0 else max_version + 1

    pub_name = f"{prefix}_v{version:03d}{ext}"
    pub_path = os.path.join(target_dir, pub_name)

    return {
        "publish_path": pub_path,
        "publish_name": pub_name,
        "version": version,
        "ext": ext,
    }


def extract_job_info(path_or_name):
    """
    Parse file naming convention:
    <jobName>_<jobType>_<jobStatus>_<jobPublishStatus>_(<jobDesc>_)v###.<ext>

    Example:
        Minty_Rig_Proxy_Wip_extra_v001.blend
        Glass_Rig_Proxy_Wip_v001.ma
        SCH020_Anim_Block_Wip_v005.ma
        School_Map_Layout_Pub_v001.blend
        Minty_Rig_Hi_Pub_animCache_v012.abc
    """

    base = os.path.basename(path_or_name)
    name, ext = os.path.splitext(base)

    # --- Regular expression for new pattern ---
    pattern = re.compile(
        r"^(?P<jobName>[A-Za-z0-9]+)_"  # e.g. Minty
        r"(?P<jobType>[A-Za-z0-9]+)_"  # e.g. Rig
        r"(?P<jobStatus>[A-Za-z0-9]+)_"  # e.g. Proxy / Block / Layout
        r"(?P<jobPublishStatus>Wip|Pub)"  # Must be Wip or Pub
        r"(?:_(?P<jobDesc>[A-Za-z0-9]+))?"  # Optional description (e.g. extra / animCache)
        r"_v(?P<version>\d{3})$",  # Version number
        re.IGNORECASE,
    )

    m = pattern.match(name)
    if not m:
        raise ValueError(f"Invalid naming convention: {path_or_name}")

    return {
        "jobName": m.group("jobName"),
        "jobType": m.group("jobType"),
        "jobStatus": m.group("jobStatus"),
        "jobPublishStatus": m.group("jobPublishStatus"),
        "jobDesc": m.group("jobDesc"),
        "version": int(m.group("version")),
        "ext": ext,
    }


def get_job_data_from_path(path):
    project_config = Directory.Directory()

    return project_config.get_job_data_from_path(path)


def import_json_to_dict(file_path: str) -> dict:
    """
    อ่านข้อมูลจากไฟล์ JSON ที่ระบุและแปลงเป็น Python Dictionary

    Args:
        file_path: ตำแหน่งของไฟล์ JSON ที่ต้องการอ่าน

    Returns:
        Python Dictionary ที่ได้จากข้อมูลในไฟล์ JSON

    Raises:
        FileNotFoundError: หากไม่พบไฟล์ตาม path ที่ระบุ
        json.JSONDecodeError: หากไฟล์มีอยู่แต่รูปแบบ JSON ไม่ถูกต้อง
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"❌ ไม่พบไฟล์ที่ตำแหน่ง: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            # ใช้ json.load() ในการอ่านและแปลงข้อมูลจากไฟล์
            data_dict = json.load(f)

        # ตรวจสอบเพื่อให้แน่ใจว่าผลลัพธ์คือ dict
        if not isinstance(data_dict, dict):
            # บางไฟล์ JSON อาจเป็น list หรือค่าพื้นฐานอื่นๆ
            # แต่ถ้าผู้ใช้ต้องการ dict เท่านั้น อาจจะต้องปรับปรุงการจัดการ error
            print(
                f"⚠️ คำเตือน: ไฟล์ JSON ถูกอ่านสำเร็จ แต่รากของข้อมูลไม่ใช่ Dictionary (เป็น {type(data_dict).__name__})"
            )

        return data_dict

    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"🚫 ข้อผิดพลาดในการถอดรหัส JSON: รูปแบบไฟล์ไม่ถูกต้อง: {e}", e.doc, e.pos
        )
