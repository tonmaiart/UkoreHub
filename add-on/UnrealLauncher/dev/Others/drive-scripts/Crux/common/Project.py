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
from Crux.core import (
    Directory,
    ProjectSetting,
    GoogleDocs,
    GoogleSheet,
    Validator,
    JobGenerator,
)

import logging

logging.basicConfig(level=logging.INFO)

# ==============================
# Management Class
# ==============================


class Project:
    """
    Use to manage the project
    """

    def __init__(self):
        # Define All Needed Class
        self.proj_settings = ProjectSetting.ProjectSetting()
        self.proj_project_config = self.proj_settings.get_project_config_data()
        self.proj_workspace_config = self.proj_settings.get_workspace_config()
        self.proj_publish_config = self.proj_settings.get_publish_paths_config()

        self.proj_name = self.proj_settings.project_config["name"]
        self.proj_dir = Directory.Directory()
        self.proj_job_generator = JobGenerator.JobGenerator()

        self.job_data_dict = self.proj_job_generator.get_job_data_dict()


    # Action
    def open_google_document(self, job_name):
        self.proj_google_dos = GoogleDocs.GoogleDocs()
        doc_name = "{}_docs".format(job_name)
        self.proj_google_dos.open_doc_auto(doc_name)

    def launch_google_sheet(self):
        self.proj_sheet = GoogleSheet.GoogleSheet()
        self.proj_sheet.launch_website()
        # self.proj_sheet.update_google_sheet_publish_status(
        #     self.proj_dir, self.proj_validator, self.proj_job_generator
        # )

    def open_workspace_dir(self, job_name, job_type):
        job_folder = self.proj_dir.get_workspace_folder_path(
            job_name=job_name, job_type=job_type
        )
        os.makedirs(job_folder, exist_ok=True)

        subprocess.Popen(f'explorer "{job_folder}"')

    def open_publish_dir(self, job_name, job_type, job_task):
        job_folder = self.proj_dir.get_publish_folder_path(
            job_name=job_name, job_type=job_type, job_task=job_task
        )

        os.makedirs(job_folder, exist_ok=True)

        subprocess.Popen(f'explorer "{job_folder}"')

    def start_job(self, job_name, job_type, job_task):
        is_start = self.proj_dir.start_job_file_auto(
            job_name=job_name, job_type=job_type, job_task=job_task
        )
        return is_start

    # Update
    def update_cache(self):
        self.proj_job_generator.update_job_data_dict_cache()

    # Get
    def get_job_data_dict(self):
        return self.job_data_dict

    # Reload
    def reload_job_data_dict(self):
        self.job_data_dict = self.proj_job_generator.get_job_data_dict()
    