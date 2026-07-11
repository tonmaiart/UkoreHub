import sys
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import logging
from PySide6 import QtWidgets, QtCore, QtUiTools
from collections import defaultdict
import subprocess
import webbrowser
from pathlib import Path
import re
import shutil
from gspread.exceptions import SpreadsheetNotFound
import pickle
import webbrowser
import platform
from gspread.utils import rowcol_to_a1
import json

from Crux.utils import utility
from Crux.core import Directory, ProjectSetting, Validator,GoogleSheet

import logging

logging.basicConfig(level=logging.INFO)

# ==============================
# Management Class
# ==============================


class JobGenerator:
    """
    ดึงข้อมูลของ Job ทั้งจาก Google Sheet , Directory ออกมาเป็นข้อมูล dict แบบ มีมาตรฐานหลัก
    มีข้อมูลทุกอย่างที่ต้องการใช้ โดยไม่ต้อง querry ใหม่ทุกครั้ง เพื่อนำไปใช้งานต่อไป

    """

    def __init__(self):
        self.ProjectSetting = ProjectSetting.ProjectSetting()
        self.requirement_config = self.ProjectSetting.get_job_requirements_config()
        self.software_config = self.ProjectSetting.get_software_config()

        self.proj_dir = Directory.Directory()
        self.proj_sheet = GoogleSheet.GoogleSheet()
        self.proj_validator = Validator.Validator(
            proj_dir=self.proj_dir, proj_sheet=self.proj_sheet
        )

        
    def update_job_data_dict_cache(self):
        """
        Generate all job data and overwrite the cache file.
        This function runs ONLY when user explicitly requests an update.
        """

        dict_data_job_output = {
            k: [] for k in ["Model", "Rig", "Map", "Anim", "Render"]
        }

        # Reload sheet to get latest data
        self.proj_sheet.reload()

        for record in self.proj_sheet.get_all_sheets_record():

            # -------------------------------
            # 🧩 MODEL / RIG / MAP JOBS
            # -------------------------------
            if "ModelName" in record and record["ModelName"]:
                if record.get("ModelEnable") == "False":
                    continue

                job_name = record["ModelName"]

                dict_data_job_output["Model"] += self.generate_job_data(
                    "model", job_name, record
                )

                # Rig tasks
                if record.get("RigEnable") == "TRUE":
                    dict_data_job_output["Rig"] += self.generate_job_data(
                        "rig", job_name, record
                    )

            elif "MapName" in record and record["MapName"]:
                if record.get("MapEnable") == "False":
                    continue

                job_name = record["MapName"]
                dict_data_job_output["Map"] += self.generate_job_data(
                    "map", job_name, record
                )

            # -------------------------------
            # 🧩 ANIM & RENDER JOBS
            # -------------------------------
            elif "ShotName" in record and record["ShotName"]:
                if record.get("ShotEnable") == "False":
                    continue

                job_name = record["ShotName"]

                anim_tasks = self.generate_job_data(
                    "anim", job_name, record, add_custom=True
                )
                render_tasks = self.generate_job_data(
                    "render", job_name, record, add_custom=True
                )

                dict_data_job_output["Anim"] += anim_tasks
                dict_data_job_output["Render"] += render_tasks

        # -------------------------------
        # SAVE TO CACHE (atomic safe)
        # -------------------------------
        job_data_cache_path = self.ProjectSetting.job_data_cache_path

        with open(job_data_cache_path, 'w', encoding='utf-8') as f:
            json.dump(dict_data_job_output, f, indent=4, ensure_ascii=False, default=str)

        print("✅ Job data cache updated:", job_data_cache_path)



    def get_job_data_dict(self):
        """
        Read job data ONLY from cache file.
        NEVER auto-update here.
        """

        job_data_cache_path = self.ProjectSetting.job_data_cache_path
        job_data_cache_dict = utility.import_json_to_dict(job_data_cache_path)

        return job_data_cache_dict

        def generate_job_data(
            self,
            job_type,
            job_name,
            record,
            add_custom=False,
        ):
            """Generate all job information using:
            - job_requirements.json
            - job_software.json
            """

            tasks = []

            # ---------------------------
            # โหลด config
            # ---------------------------
            job_requirement_data = self.requirement_config.get(job_type, {})
            job_software_data = self.software_config.get(job_type, {})

            # task names จาก requirement file
            for task_name in list(job_requirement_data.keys()):

                # ---------------------------------------------------
                # REQUIRED TASKS (dependencies from job_requirements)
                # ---------------------------------------------------
                req_codes = []

                dependency_list = job_requirement_data.get(task_name, [])

                for dep in dependency_list:
                    # dep => "model.proxy"
                    try:
                        dep_job, dep_task = dep.split(".")
                    except ValueError:
                        continue

                    req_codes.append(
                        f"{job_name}_{dep_job.capitalize()}_{dep_task.capitalize()}"
                    )

                # ---------------------------------------------------
                # CUSTOM REQUIRE LOGIC (anim, render)
                # ---------------------------------------------------
                if add_custom and job_type == "anim":
                    req_codes += self._get_custom_anim_require(record, task_name)

                elif add_custom and job_type == "render":
                    req_codes += self._get_custom_render_require(record, task_name)

                # ---------------------------------------------------
                # SOFTWARE (from job_software.json)
                # ---------------------------------------------------
                software = job_software_data.get(task_name, "")
                if isinstance(software, list):  # ถ้าอนาคตใส่หลายโปรแกรม
                    software = software[0] if software else ""

                # ---------------------------------------------------
                # BUILD TASK INFO
                # ---------------------------------------------------
                key_prefix = job_type.capitalize()

                task_info = {
                    "JobName": job_name,
                    "JobType": job_type.capitalize(),
                    "JobTask": task_name.capitalize(),
                    "JobPublishStatus": self.proj_validator.get_job_publish_status_polish(
                        job_name=job_name,
                        job_type=job_type.capitalize(),
                        job_task=task_name.capitalize(),
                        proj_dir=self.proj_dir,
                        job_requirement=req_codes,
                    ),
                    "Artist": record.get(f"{key_prefix}Artist", ""),
                    "JobNote": record.get(f"{key_prefix}Note", ""),
                    "JobRequiredCode": req_codes,
                    "Software": software,
                    "JobDirectory": self.proj_dir.get_workspace_folder_path(
                        job_name=job_name,
                        job_type=job_type.capitalize(),
                        onlyDir=False,
                    ),
                    "JobRequiredStatus": self.proj_validator.get_job_require_status(
                        job_name=job_name,
                        job_type=job_type.capitalize(),
                        job_task=task_name.capitalize(),
                        proj_dir=self.proj_dir,
                        list_require_code=req_codes,
                    ),
                }

                tasks.append(task_info)

            return tasks

    def _get_custom_anim_require(self, record, task):
        deps = []
        if task.lower() == "layout":
            # require rigs (proxy) & maps (layout)
            for rig_name in record.get("RigRequired", "").split(", "):
                if rig_name:
                    deps.append(f"{rig_name}_Rig_Proxy")
            for map_name in record.get("MapRequired", "").split(", "):
                if map_name:
                    deps.append(f"{map_name}_Map_Layout")

        elif task.lower() == "blocking":
            for rig_name in record.get("RigRequired", "").split(", "):
                if rig_name:
                    deps.append(f"{rig_name}_Rig_Hi")
            deps.append(f"{record['ShotName']}_Anim_Layout")

        elif task.lower() == "polish":
            deps.append(f"{record['ShotName']}_Anim_Blocking")

        return deps

    def _get_custom_render_require(self, record, task):
        deps = []
        if task.lower() == "render":
            for rig_name in record.get("RigRequired", "").split(", "):
                if rig_name:
                    deps.append(f"{rig_name}_Model_Texture")
            deps.append(f"{record['ShotName']}_Anim_Polish")
        return deps
