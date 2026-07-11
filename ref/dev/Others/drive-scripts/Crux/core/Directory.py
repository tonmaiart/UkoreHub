import sys
import os
import logging
import subprocess
from pathlib import Path
import re
import shutil
import webbrowser

from Crux.core import ProjectSetting
from Crux.utils import utility
import logging

logging.basicConfig(level=logging.INFO)


class Directory:
    def __init__(self):
        self.crux_config = ProjectSetting.ProjectSetting()

        self.project_config_dict = self.crux_config.get_project_config()
        self.workspace_config_dict = self.crux_config.get_workspace_config()
        self.publish_paths_config_dict = self.crux_config.get_publish_paths_config()

        self.proj_name = self.project_config_dict["name"]
        self.project_directory_path = Path(
            self.project_config_dict["project_directory_path"]
        )
        self.project_path = self.project_directory_path / self.proj_name

    def get_workspace_folder_path(self, job_name, job_type, onlyDir=False):
        dir_path = self.workspace_config_dict[job_type.lower()]

        if onlyDir:
            return self.project_path / dir_path
        else:
            return self.project_path / dir_path / job_name

    def get_publish_folder_path(self, job_name, job_type, job_task, onlyDir=False):
        dir_path = self.publish_paths_config_dict[job_type.lower()][job_task.lower()]

        if onlyDir:
            return self.project_path / dir_path
        else:
            return self.project_path / dir_path / job_name

    def get_job_data_from_path(self, path):
        parent_path_job_name = os.path.dirname(path)
        parent_path_job_type = os.path.normpath(os.path.dirname(parent_path_job_name))
        project_path = self.project_config_dict["project_directory_path"]
        project_name = self.project_config_dict["name"]

        job_type = None

        print(parent_path_job_type, self.workspace_config_dict.values())

        for job_type, workspace_path in self.workspace_config_dict.items():
            full_workspace_path_check = os.path.normpath(
                os.path.join(project_path, project_name, workspace_path)
            )
            print(parent_path_job_type, full_workspace_path_check)
            if parent_path_job_type == full_workspace_path_check:
                job_type = job_type.capitalize()
                break

        if not job_type:
            return None
        else:
            job_name = os.path.basename(parent_path_job_name)

        return job_name, job_type

    def get_job_file_ext(self, job_type, job_task, publish=False):
        # Get File Ext Type for given job

        if publish:
            mode = "pub"
        else:
            mode = "wip"
        exts = self.config[job_type.lower()][mode][job_task.lower()]["ext"]

        return exts

    def get_exist_publish_file(
        self,
        job_type: str,
        job_task: str,
        job_name: str,
    ):
        """
        Return Rencent Given Job File Name
        """

        folder = self.get_publish_folder_path(
            job_name=job_name, job_type=job_type, job_task=job_task, onlyDir=False
        )

        os.makedirs(folder, exist_ok=True)

        # ------------------
        # Search Valid File
        # ------------------
        # เตรียมข้อมูล
        files = list(folder.iterdir())
        prefix = f"{job_name}_{job_type}_{job_task}_Pub"

        # regex หา _vNNN ที่ต่อท้าย stem (เช่น MyFile_v002)
        version_pattern = re.compile(r"_v(\d+)$", re.IGNORECASE)

        # เก็บไฟล์ที่ตรงเงื่อนไข
        valid_files = []
        for p in files:
            if not p.is_file():
                continue
            # เช็ก prefix กับ stem (ไม่รวมนามสกุล)
            if not p.stem.startswith(prefix):
                continue
            valid_files.append(p)

        # หาไฟล์เวอร์ชันล่าสุด
        if valid_files:

            def _ver(path):
                m = version_pattern.search(path.stem)
                return int(m.group(1)) if m else -1

            latest_file = max(valid_files, key=_ver)
        else:
            latest_file = None

        return latest_file

    def create_file_name(
        self, job_type, job_task, job_name, extra="", publish=False, version=1
    ):
        """Return Correct File Name"""

        # Validate inputs (optional, to keep names clean)
        job_name = re.sub(r"\W+", "", job_name)  # Remove invalid characters
        job_type = re.sub(r"\W+", "", job_type)
        job_task = re.sub(r"\W+", "", job_task)
        extra = re.sub(r"\W+", "", extra)

        # Determine publish state
        pub_status = "Pub" if publish else "Wip"

        # Format version
        version_str = f"v{version:03d}"

        # Build file name parts
        parts = [f"{job_name}_{job_type}_{job_task}_{pub_status}"]

        if extra:
            parts.append(extra)
        parts.append(version_str)

        # Join parts into final name
        filename = "_".join(parts)

        return filename

    def open_file_with_software(self, file_path):
        """This Try to open with maya 2022"""

        root, ext = os.path.splitext(file_path)

        if ext == ".ma":
            maya_app_2022_path = None
            if os.name == "nt":
                maya_path = r"C:\Program Files\Autodesk\Maya2022\bin\maya.exe"
                if os.path.exists(maya_path):
                    maya_app_2022_path = maya_path

            if not maya_app_2022_path:
                os.startfile(file_path)
            else:
                subprocess.Popen([maya_app_2022_path, file_path])

        elif ext == ".blend":
            os.startfile(file_path)

    def start_job_file_auto(self, job_name, job_type, job_task):
        """
        Force to open Job File in workspace directory automatically
        """

        logging.info("Start Job File : {}_{}_{}".format(job_name, job_type, job_task))

        job_wip_folder = self.get_workspace_folder_path(
            job_name=job_name, job_type=job_type
        )
        os.makedirs(job_wip_folder, exist_ok=True)

        job_file = self.get_exist_job_file(
            job_type=job_type, job_task=job_task, job_name=job_name, publish=False
        )

        if job_file:

            logging.info("Found Exist Job File : {}".format(job_file))
            logging.info("Opening Job File : {}".format(job_file))

            self.open_file_with_software(job_file)

            return True

        else:
            self.create_new_wip_job_file(
                job_name=job_name, job_type=job_type, job_task=job_task
            )
            logging.info("Create New Job File Complete!")

            job_file = self.get_exist_job_file(
                job_name=job_name, job_type=job_type, job_task=job_task, publish=False
            )

            logging.info("Opening Job File : {}".format(job_file))

            self.open_file_with_software(job_file)

            return True

    def create_new_wip_job_file(self, job_name, job_type, job_task):
        """
        Use for create new job file, return new job file name
        """

        file_name = self.create_file_name(
            job_name=job_name,
            job_type=job_type,
            job_task=job_task,
            publish=False,
        )

        file_exts = self.get_job_file_ext(
            job_type=job_type, job_task=job_task, publish=False
        )

        file_path = self.get_workspace_folder_path(job_name=job_name, job_type=job_type)

        file_ext = file_exts[0]
        template_file = self.config["template_file"][file_ext]

        file_lastest_version = utility.duplicate_file(
            template_file,
            os.path.join(file_path, file_name + file_ext),
        )

        return file_lastest_version
