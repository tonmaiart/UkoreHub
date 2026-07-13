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
from Crux.core import ProjectSetting
from Crux.utils import utility
import logging

logging.basicConfig(level=logging.INFO)

# ==============================
# Management Class
# ==============================


class GoogleDocs:
    def __init__(self):
        # Load Api Google Docs Service
        self.project_settings = ProjectSetting.ProjectSetting()

        self.project_config_dict = self.project_settings.get_project_config()
        self.workspace_config_dict = self.project_settings.get_workspace_config()
        self.publish_paths_config_dict = (
            self.project_settings.get_publish_paths_config()
        )

        self.google_docs_service = self.get_google_docs_service()
        self.google_drive_service = self.get_google_drive_service()

    def create_new_docs(self, title):
        """
        สร้างเอกสาร Google Doc ใหม่ด้วยชื่อที่ระบุ
        """

        service = self.google_docs_service

        # 2. กำหนด Body ของคำขอ (ใส่แค่ชื่อเอกสาร)
        document_body = {"title": title}

        # 3. เรียกใช้ documents.create method
        doc = service.documents().create(body=document_body).execute()

        doc_title = doc.get("title")
        doc_id = doc.get("documentId")
        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"

        print("\n==============================================")
        print(f"✅ สร้างเอกสารใหม่สำเร็จ:")
        print(f"   ชื่อ: {doc_title}")
        print(f"   ID: {doc_id}")
        print(f"   ลิงก์: {doc_url}")
        print("==============================================")

        return doc_id

    def get_google_drive_service(self):
        """
        จัดการการตรวจสอบสิทธิ์สำหรับ Google Drive API และส่งคืน Service Object (v3)

        Returns:
            googleapiclient.discovery.Resource: Drive API Service Object
        """
        TOKEN_FILE = "token.pickle"
        CREDENTIALS_FILE = self.project_settings.get_creds_service_client()
        creds = None
        SCOPES = ["https://www.googleapis.com/auth/drive.file"]

        creds = None

        # 1.1 โหลด Credentials จากไฟล์ token.pickle (ถ้ามี)
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "rb") as token:
                creds = pickle.load(token)

        # 1.2 ถ้า Credentials ไม่ถูกต้องหรือไม่มี ให้ทำการตรวจสอบสิทธิ์ใหม่
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # ใช้ Refresh Token เพื่อต่ออายุ
                creds.refresh(Request())
            else:
                # รัน flow เพื่อขออนุญาตจากผู้ใช้ (จะเปิดหน้าต่างเบราว์เซอร์)
                if not os.path.exists(CREDENTIALS_FILE):
                    print(f"❌ ไม่พบไฟล์ {CREDENTIALS_FILE} กรุณาตรวจสอบ")
                    return None

                print(f"ℹ️ กำลังเปิดหน้าต่างเบราว์เซอร์เพื่อขออนุญาต...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES
                )
                creds = flow.run_local_server(port=0)

            # บันทึก Credentials ใหม่ลงในไฟล์ token.pickle
            with open(TOKEN_FILE, "wb") as token:
                pickle.dump(creds, token)

        # 1.3 สร้าง Service Object สำหรับ Google Drive API (v3)
        service = build("drive", "v3", credentials=creds)
        print("✅ สร้าง Google Drive Service Object สำเร็จ")
        return service

    def get_google_docs_service(self):
        """
        จัดการการตรวจสอบสิทธิ์ (Authentication) และสร้าง Service Object
        """
        TOKEN_FILE = "token.pickle"
        CREDENTIALS_FILE = self.project_settings.get_creds_oauth_client()

        creds = None
        SCOPES = [
            "https://www.googleapis.com/auth/documents",
            "https://www.googleapis.com/auth/drive.file",
        ]

        # 1.1 โหลด Credentials จากไฟล์ token.pickle (ถ้ามี)
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "rb") as token:
                creds = pickle.load(token)

        print("credentail file : ", CREDENTIALS_FILE)
        # 1.2 ถ้า Credentials ไม่ถูกต้องหรือไม่มี ให้ทำการตรวจสอบสิทธิ์ใหม่
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # ใช้ Refresh Token เพื่อต่ออายุ
                creds.refresh(Request())
            else:
                # รัน flow เพื่อขออนุญาตจากผู้ใช้ (จะเปิดหน้าต่างเบราว์เซอร์)
                print(
                    f"ℹ️ กำลังเปิดหน้าต่างเบราว์เซอร์เพื่อขออนุญาต. โปรดตรวจสอบไฟล์: {CREDENTIALS_FILE}"
                )
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES
                )
                creds = flow.run_local_server(port=0)

            # บันทึก Credentials ใหม่ลงในไฟล์ token.pickle
            with open(TOKEN_FILE, "wb") as token:
                pickle.dump(creds, token)

        # 1.3 สร้าง Service Object สำหรับ Google Docs API
        service = build("docs", "v1", credentials=creds)
        return service

    def is_doc_exists(self, doc_name):
        """
        ตรวจสอบว่ามี Google Document ที่มีชื่อตามที่ระบุอยู่หรือไม่

        Args:
            drive_service: Google Drive API Service Object (จาก build('drive', 'v3', ...)).
            document_title (str): ชื่อเอกสาร Google Docs ที่ต้องการค้นหา.

        Returns:
            tuple: (bool: True ถ้าพบเอกสาร, str: ID ของเอกสารที่พบ (ถ้ามี),
                    str: URL ของเอกสารที่พบ (ถ้ามี))
        """

        # 1. กำหนด Query String สำหรับการค้นหา
        #    - name: ชื่อไฟล์ตรงกับ document_title
        #    - mimeType: ต้องเป็น Google Docs ('application/vnd.google-apps.document')
        #    - trashed: ต้องไม่ถูกลบไปแล้ว (false)
        # เราใช้ backslash (\) ก่อน single quote (') ในชื่อเพื่อป้องกัน SQL injection และข้อผิดพลาด
        # โดยทั่วไป Google Drive API Client Library จะจัดการการเข้ารหัส (encoding) ให้เอง แต่การใช้ f-string
        # ควรระมัดระวังเมื่อชื่อมี single quote
        escaped_name = doc_name.replace("'", "\\'")
        query = f"name='{escaped_name}' and mimeType='application/vnd.google-apps.document' and trashed=false"

        drive_service = self.google_drive_service

        try:
            # 2. เรียกใช้ Drive API list() method
            results = (
                drive_service.files()
                .list(
                    q=query,
                    spaces="drive",
                    # ขอข้อมูล id และ name ของไฟล์ที่พบ
                    fields="files(id, name)",
                )
                .execute()
            )

            items = results.get("files", [])

            if items:
                # พบเอกสาร
                doc_id = items[0]["id"]
                doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
                print(f"✅ พบเอกสารชื่อ '{doc_name}'")
                return True, doc_id, doc_url
            else:
                # ไม่พบเอกสาร
                print(f"❌ ไม่พบเอกสารชื่อ '{doc_name}'")
                return False, None, None

        except Exception as error:
            print(f"❌ เกิดข้อผิดพลาดในการค้นหาเอกสาร: {error}")
            return False, None, None

    def open_doc(self, document_title):
        """
        ค้นหา Google Doc ด้วยชื่อ และเปิดลิงก์ในเบราว์เซอร์

        Args:
            drive_service: Google Drive API Service Object (v3).
            document_title (str): ชื่อเอกสาร Google Docs ที่ต้องการเปิด.
        """
        print(f"🔎 กำลังค้นหาเอกสารชื่อ: '{document_title}'...")

        # 1. ค้นหาเอกสารด้วยชื่อ (ใช้ฟังก์ชันที่คุณสร้างไว้)
        found, doc_id, doc_url = self.is_doc_exists(document_title)

        if found:
            print(f"✅ พบเอกสารแล้ว (ID: {doc_id})")

            try:
                # 2. เปิด URL ในเบราว์เซอร์
                webbrowser.open_new_tab(doc_url)
                print("🚀 เปิดเอกสารในเบราว์เซอร์สำเร็จ!")
            except Exception as error:
                print(f"❌ เกิดข้อผิดพลาดในการเปิดเบราว์เซอร์: {error}")
                print(f"กรุณาคัดลอกลิงก์: {doc_url}")
        else:
            # ไม่พบเอกสาร
            print(f"❌ ไม่สามารถเปิดได้: ไม่พบเอกสารชื่อ '{document_title}' ใน Google Drive")

    def open_doc_auto(self, document_title):
        is_exist, doc_id, doc_url = self.is_doc_exists(document_title)

        if not is_exist:
            self.create_new_docs(document_title)

            print("กำลังสร้าง Google Docs ใหม่สำหรับ : ", document_title)

        self.open_doc(document_title)
