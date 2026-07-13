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

from Crux.utils import utility
from Crux.core import Directory, ProjectSetting

import logging

logging.basicConfig(level=logging.INFO)

# ==============================
# Management Class
# ==============================


class GoogleSheet:
    """
    จัดการการเชื่อมต่อ Google Sheets และการดำเนินการกับ Spreadsheet
    """

    def __init__(self):
        self.proj_settings = ProjectSetting.ProjectSetting()
        self.proj_project_config = self.proj_settings.get_project_config_data()
        self.proj_workspace_config = self.proj_settings.get_workspace_config()
        self.proj_publish_config = self.proj_settings.get_publish_paths_config()

        self.list_displayable_publish_status = ["NotStart", "Working"]
        self.cred_path = self.proj_settings.get_creds_service_client()
        self.spreadsheet_title = self.proj_project_config["name"]
        self.gspread_client = None
        self.spreadsheet = None
        self.setup_gspread_client()

        self.list_dev_record = []
        self.list_shot_dict_record = []
        self.list_model_dict_record = []
        self.list_map_dict_record = []

        self.sheet_model = None
        self.sheet_shot = None
        self.sheet_map = None
        self.sheet_dev = None

        if self.gspread_client:
            self.open_spreadsheet()
        else:
            print("Error to Get gspread client")

    ## การเชื่อมต่อ
    # --------------------------------------------------------------------------------
    def setup_gspread_client(self):
        """
        เชื่อมต่อกับ Google Sheets API และเก็บ client ไว้ใน self.gspread_client
        """
        print("กำลังเชื่อมต่อกับ Google Sheets...")
        try:
            # ใช้ os.path.join เพื่อให้โค้ดทำงานได้ทั้งบน Windows และ Linux/macOS
            # ตรวจสอบให้แน่ใจว่าไฟล์ 'key.json' อยู่ในตำแหน่งที่ถูกต้อง

            # แก้ไข scope ให้เหมาะสมกับความต้องการของคุณ
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive.file",
                "https://www.googleapis.com/auth/drive",
            ]

            creds = ServiceAccountCredentials.from_json_keyfile_name(
                self.cred_path, scope
            )

            self.gspread_client = gspread.authorize(creds)
            print("เชื่อมต่อ Google Sheets สำเร็จ! ✅")
        except FileNotFoundError:
            print(
                "!! ข้อผิดพลาด: ไม่พบไฟล์ 'key.json, กรุณาวางไฟล์ key .json ไว้ในโฟลเดอร์ที่รันโปรแกรม หรือระบุ path ให้ถูกต้อง"
            )
            print("Path ปัจจุบัน {}".format(self.cred_path))
        except Exception as e:
            print(f"!! ข้อผิดพลาดในการเชื่อมต่อ gspread: {e}")
            self.gspread_client = None  # ตั้งค่าให้เป็น None เพื่อป้องกันการใช้งาน client ที่ล้มเหลว

    ## การจัดการ Spreadsheet
    # --------------------------------------------------------------------------------

    def launch_website(self):
        webbrowser.open_new_tab(self.spreadsheet.url)

    def open_spreadsheet(self):
        """
        เปิด Spreadsheet ตามชื่อที่กำหนดและเก็บไว้ใน self.spreadsheet
        """
        if not self.gspread_client:
            print("!! ไม่สามารถเปิด Spreadsheet ได้: การเชื่อมต่อ gspread ล้มเหลว")
            return

        print(f"กำลังเปิด Spreadsheet: **{self.spreadsheet_title}** ...")
        try:
            # ใช้ open() เพื่อเปิด Spreadsheet ด้วยชื่อ
            self.spreadsheet = self.gspread_client.open(self.spreadsheet_title)
            print(
                f"เปิด Spreadsheet สำเร็จ: **{self.spreadsheet_title}** {self.spreadsheet}"
            )
        except SpreadsheetNotFound:
            print(f"!! ข้อผิดพลาด: ไม่พบ Spreadsheet ชื่อ **'{self.spreadsheet_title}'**")
            self.spreadsheet = None
        except Exception as e:
            print(f"!! ข้อผิดพลาดในการเปิด Spreadsheet: {e}")
            self.spreadsheet = None

        # load once time data

        self.sheet_model = self.spreadsheet.worksheet("Model")
        self.sheet_shot = self.spreadsheet.worksheet("Shot")
        self.sheet_map = self.spreadsheet.worksheet("Map")
        self.sheet_dev = self.spreadsheet.worksheet("Dev")

        self.list_dev_record = self.spreadsheet.worksheet("Dev").get_all_records()
        self.list_shot_dict_record = self.spreadsheet.worksheet(
            "Shot"
        ).get_all_records()
        self.list_model_dict_record = self.spreadsheet.worksheet(
            "Model"
        ).get_all_records()
        self.list_map_dict_record = self.spreadsheet.worksheet("Map").get_all_records()

    def reload(self):
        """
        🔄 โหลด Spreadsheet ใหม่ (เปิดใหม่) เพื่อดึงข้อมูลล่าสุด หรือกรณีชื่อไฟล์เปลี่ยน

        Note: สำหรับการดึงข้อมูลใน Worksheet ล่าสุด ควรใช้เมธอด get_all_values()
        หรือ get_all_records() ของ Worksheet Object โดยตรง

        Returns:
            gspread.Spreadsheet: Spreadsheet Object ที่โหลดใหม่
        """
        print("--- เริ่ม Reload Spreadsheet ---")
        self.open_spreadsheet()  # เรียกใช้ open_spreadsheet อีกครั้ง
        print("--- Reload Spreadsheet เสร็จสิ้น ---")
        return self.spreadsheet

    def get_spreadsheet(self):
        return self.spreadsheet

    def get_artist_names(self):
        def normalize_dict_to_list(data):
            """
            แปลง List ของ Dictionaries (ข้อมูลแบบแถว) ให้เป็น Dictionary ของ Lists (ข้อมูลแบบคอลัมน์)
            และลบค่าที่เป็น String ว่าง ("") ออกจาก List ของทุกคอลัมน์โดยอัตโนมัติ

            :param data: List of Dictionaries (เช่น ผลลัพธ์จาก gspread.get_all_records())
            :return: Dictionary ที่ key เป็นชื่อคอลัมน์ และ value เป็น List ของค่าในคอลัมน์นั้น (ไม่รวม "")
            """
            if not data:
                return {}

            column_data = defaultdict(list)

            # 1. รวบรวมข้อมูลทั้งหมด (เหมือนฟังก์ชันเดิม)
            for row_dict in data:
                for key, value in row_dict.items():
                    column_data[key].append(value)

            # 2. กรองค่าที่เป็น String ว่าง ("") ออกจาก List ของทุกคอลัมน์
            filtered_column_data = {}
            for key, values_list in column_data.items():
                # ใช้ List Comprehension เพื่อกรอง: เก็บไว้เฉพาะค่าที่ไม่เท่ากับ ""
                filtered_list = [value for value in values_list if value != ""]
                filtered_column_data[key] = filtered_list

            return filtered_column_data

        return normalize_dict_to_list(self.list_dev_record)["Artist"]

    def update_google_sheet_publish_status(
        self, proj_dir, proj_validator, proj_job_generator
    ):
        def add_update(col, val, sheet_name):
            sheet_updates.setdefault(sheet_name, []).append((job_name, col, val))

        dict_job_data = proj_job_generator.get_job_data_dict()
        dict_target_set = {
            "Model": "Model",
            "Rig": "Model",
            "Map": "Map",
            "Anim": "Shot",
            "Render": "Shot",
        }

        # เตรียมอัปเดตเป็น batch ต่อชีต
        sheet_updates = {}

        for key in dict_job_data.keys():
            for list_job_data in dict_job_data[key]:
                job_name = list_job_data["JobName"]
                job_type = list_job_data["JobType"]
                job_task = list_job_data["JobTask"]
                job_publish_status = list_job_data["JobPublishStatus"]

                sheet_name = dict_target_set[job_type]

                if job_publish_status == "NotStart":
                    add_update(f"{job_type}{job_task}Publish", False, sheet_name)
                    add_update(f"{job_type}{job_task}Status", "NotStart", sheet_name)
                elif job_publish_status == "Working":
                    add_update(f"{job_type}{job_task}Publish", False, sheet_name)
                    add_update(f"{job_type}{job_task}Status", "Working", sheet_name)

                elif job_publish_status == "Finish":
                    add_update(f"{job_type}{job_task}Publish", True, sheet_name)
                    add_update(f"{job_type}{job_task}Status", "Finish", sheet_name)
                elif job_publish_status == "Wait":
                    add_update(f"{job_type}{job_task}Publish", False, sheet_name)
                    add_update(f"{job_type}{job_task}Status", "Wait", sheet_name)

        # อัปเดตทั้งหมดครั้งเดียวต่อชีต
        print("---- Validating Google Sheet ----")

        for sheet_name, updates in sheet_updates.items():
            self.batch_set_values(sheet_name, updates)

    def batch_set_values(self, sheet_name, updates: list):
        """
        updates = [
            (row_name, column_name, new_value),
            ...
        ]
        """
        ws = self.spreadsheet.worksheet(sheet_name)
        header = ws.row_values(1)
        data = ws.get_all_records()
        key_column = header[0]

        # สร้าง mapping ของชื่อ row → index
        row_map = {r[key_column]: i + 2 for i, r in enumerate(data)}

        cell_updates = []
        for row_name, column_name, new_value in updates:
            if row_name not in row_map:
                print(f"⚠️ ไม่พบแถว {row_name}")
                continue
            if column_name not in header:
                print(f"⚠️ ไม่พบคอลัมน์ {column_name}")
                continue

            r = row_map[row_name]
            c = header.index(column_name) + 1
            cell_updates.append(
                {
                    "range": f"{sheet_name}!{gspread.utils.rowcol_to_a1(r, c)}",
                    "values": [[new_value]],
                }
            )

        # ✅ ใช้ values_batch_update แทน batch_update
        if cell_updates:
            body = {"valueInputOption": "USER_ENTERED", "data": cell_updates}
            ws.spreadsheet.values_batch_update(body)
            print(f"✅ Updated {len(cell_updates)} cells in {sheet_name}")

    def set_value(self, sheet_name, row_name, column_name, new_value):
        """
        อัปเดตค่าใน Google Sheet โดยระบุชื่อชีต, ชื่อแถว (จากคอลัมน์แรก), ชื่อคอลัมน์, และค่าที่ต้องการอัปเดต
        """
        try:
            ws = self.spreadsheet.worksheet(sheet_name)
        except Exception as e:
            raise ValueError(f"❌ ไม่พบชีต '{sheet_name}' หรือเข้าถึงไม่ได้: {e}")

        # ดึง header และข้อมูลทั้งหมด
        header = ws.row_values(1)
        data = ws.get_all_records()

        # ตรวจสอบคอลัมน์เป้าหมาย
        if column_name not in header:
            raise ValueError(f"❌ ไม่พบคอลัมน์ '{column_name}'")

        key_column = header[0]  # ใช้คอลัมน์แรกเป็น key (เช่น MapName)
        row_index = next(
            (i + 2 for i, r in enumerate(data) if r.get(key_column) == row_name), None
        )
        if not row_index:
            raise ValueError(f"⚠️ ไม่พบแถวที่มีค่า '{row_name}' ในคอลัมน์ '{key_column}'")

        col_index = header.index(column_name) + 1
        ws.update_cell(row_index, col_index, new_value)
        print(f"✅ อัปเดต '{sheet_name}' | {row_name} → {column_name} = {new_value}")

    def get_all_sheets_record(self):
        return (
            self.list_shot_dict_record
            + self.list_model_dict_record
            + self.list_map_dict_record
        )
