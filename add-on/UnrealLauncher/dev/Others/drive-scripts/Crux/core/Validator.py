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

# sys.path.append(r"G:\My Drive\Mellowstar\dev\drive-scripts")

from Crux.utils import utility
from Crux.core import Directory, ProjectSetting

import logging

logging.basicConfig(level=logging.INFO)

# ==============================
# Management Class
# ==============================


class Validator:
    """Use For Check Statement of Sheet and Directory"""

    def __init__(self, proj_dir, proj_sheet):
        self.proj_dir = proj_dir
        self.proj_sheet = proj_sheet

    def get_job_publish_status_polish(
        self, job_name, job_type, job_task, job_requirement, proj_dir
    ):
        is_pub = self.is_job_publish(job_name, job_type, job_task, proj_dir)
        is_start = self.is_job_start(job_name, job_type, job_task, proj_dir)
        is_ready = self.is_job_ready(
            job_name, job_type, job_task, job_requirement, proj_dir
        )

        if is_ready:
            if not is_start:
                return "NotStart"
            elif is_start and not is_pub:
                return "Working"
            elif is_pub:
                return "Finish"

        elif not is_ready:
            return "Wait"

    def is_job_publish(self, job_name, job_type, job_task, proj_dir):
        """
        Check is given job is publish yet
        """

        is_recent_file_exist = proj_dir.get_exist_publish_file(
            job_name=job_name, job_type=job_type, job_task=job_task
        )

        if is_recent_file_exist:
            return True
        else:
            return False

    def is_job_start(self, job_name, job_type, job_task, proj_dir):
        """
        Check is given job is have start yet
        """

        if proj_dir.get_exist_publish_file(
            job_name=job_name, job_type=job_type, job_task=job_task
        ):
            return True
        else:
            return False

    def is_job_ready(self, job_name, job_type, job_task, job_requirement, proj_dir):
        """
        Check is given job is ready to work
        """
        list_check = []

        # get requiredment
        list_requirement = job_requirement  # .split(",")

        # check is all requirement is publish all
        for job_data in list_requirement:
            job_name_ref, job_type_ref, job_task_ref = job_data.split("_")

            if proj_dir.get_exist_publish_file(
                job_name=job_name_ref, job_type=job_type_ref, job_task=job_task_ref
            ):
                list_check.append(True)
            else:
                list_check.append(False)

        if False in list_check:
            return False
        else:
            return True

    def get_job_require_status(
        self, job_name, job_type, job_task, list_require_code, proj_dir
    ):
        """
        Check is given job is ready to work
        """
        dict_check = {}

        for job_require_code in list_require_code:
            job_name_ref, job_type_ref, job_task_ref = job_require_code.split("_")

            if proj_dir.get_exist_publish_file(
                job_name=job_name_ref, job_type=job_type_ref, job_task=job_task_ref
            ):
                dict_check[job_require_code] = True
            else:
                dict_check[job_require_code] = False

        return dict_check
