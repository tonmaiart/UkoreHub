import sys
import os

# sys.path.append("G:\My Drive\Mellowstar\dev\drive-scripts")


from PySide6 import QtWidgets, QtCore, QtUiTools
from collections import defaultdict
import subprocess
import webbrowser
from pathlib import Path
import re
import shutil
from gspread.exceptions import SpreadsheetNotFound
import configparser
import pickle
import webbrowser
import platform

from PySide6.QtWidgets import (
    QMessageBox,
    QHeaderView,
)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QPalette, QColor, QBrush
from PySide6.QtCore import QTimer, QThread
from PySide6 import QtGui, QtCore

from PySide6 import QtWidgets, QtCore, QtGui

from PySide6 import QtCore


class PopupMessage(QtWidgets.QDialog):
    def __init__(self, text, duration=5000, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.Dialog
            | QtCore.Qt.WindowStaysOnTopHint
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setModal(False)

        # ---------- Layout ----------
        layout = QtWidgets.QVBoxLayout(self)
        self.label = QtWidgets.QLabel(text)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setStyleSheet(
            """
            QLabel {
                background-color: rgba(30, 30, 30, 200);
                color: white;
                font-size: 22px;
                font-weight: bold;
                border-radius: 15px;
                padding: 25px;
            }
        """
        )
        layout.addWidget(self.label)
        self.setLayout(layout)

        # ---------- Animation ----------
        self.opacity_effect = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)

        self.fade_in = QtCore.QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(400)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)

        self.fade_out = QtCore.QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out.setDuration(800)
        self.fade_out.setStartValue(1)
        self.fade_out.setEndValue(0)
        self.fade_out.finished.connect(self.close)

        # ---------- Timer ----------
        QtCore.QTimer.singleShot(duration, self.fade_out.start)
        self.fade_in.start()

    def show_centered(self):
        """ให้ popup อยู่กลางหน้าจอของ parent"""
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - self.height()) // 2
        else:
            screen = QtGui.QGuiApplication.primaryScreen().availableGeometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
        self.move(x, y)
        self.show()


class JobItemModel(QStandardItemModel):

    def __init__(self, parent=None):
        super().__init__(parent)

        # proxy ไว้สำหรับ filter
        self.proxy_model = QtCore.QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self)
        self.proxy_model.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)

        # เก็บ filter เฉพาะของเรา
        self._filter_jobName = None
        self._filter_jobType = None
        self._filter_jobStatus = None
        self._filter_publishStatus = None
        self._filter_artist = None

        self.column_map = {
            "JobName": 0,
            "JobType": 1,
            "JobTask": 2,
            "PublishStatus": 3,
            "Artist": 4,
        }

        # override filterAcceptsRow
        self.proxy_model.filterAcceptsRow = self.filterAcceptsRow

        # new feature
        self._filter_single_job_task = False
        self._filter_seen_jobs = set()

    # ------------------------------
    # REMOVE ALL COLOR LOGIC HERE
    # ------------------------------
    def data(self, index, role=QtCore.Qt.DisplayRole):
        # no color logic, return as is
        return super().data(index, role)

    # ------------------------------
    # ตั้งค่า filter
    # ------------------------------
    def setFilter(
        self,
        jobName=None,
        jobType=None,
        jobStatus=None,
        publishStatus=None,
        artist=None,
        single_job_task=True,
    ):

        self._filter_jobName = jobName.lower() if isinstance(jobName, str) else None
        self._filter_jobType = self._normalize(jobType)
        self._filter_jobStatus = self._normalize(jobStatus)
        self._filter_publishStatus = self._normalize(publishStatus)
        self._filter_artist = self._normalize(artist)

        self._filter_single_job_task = single_job_task
        self._filter_seen_jobs = set()

        self.proxy_model.invalidateFilter()

    def clearFilter(self):
        self._filter_jobName = None
        self._filter_jobType = None
        self._filter_jobStatus = None
        self._filter_publishStatus = None
        self._filter_artist = None

        self._filter_seen_jobs = set()
        self.proxy_model.invalidateFilter()

    # ------------------------------
    # ฟังก์ชัน filter หลัก
    # ------------------------------
    def filterAcceptsRow(self, source_row, source_parent):

        model = self

        def get_value(column_key):
            col = self.column_map[column_key]
            index = model.index(source_row, col, source_parent)
            return model.data(index, QtCore.Qt.DisplayRole) or ""

        # partial match filters
        if self._filter_jobName:
            if self._filter_jobName not in get_value("JobName").lower():
                return False

        if self._filter_jobType and get_value("JobType") not in self._filter_jobType:
            return False

        if (
            self._filter_jobStatus
            and get_value("JobStatus") not in self._filter_jobStatus
        ):
            return False

        if (
            self._filter_publishStatus
            and get_value("PublishStatus") not in self._filter_publishStatus
        ):
            return False

        if self._filter_artist and get_value("Artist") not in self._filter_artist:
            return False

        # NEW FEATURE: only show first JobTask
        if self._filter_single_job_task:
            job_key = (get_value("JobName"), get_value("JobType"))

            if job_key in self._filter_seen_jobs:
                return False

            self._filter_seen_jobs.add(job_key)

        return True

    # ------------------------------
    # Helper
    # ------------------------------
    def _normalize(self, value):
        if value is None:
            return None
        if isinstance(value, (list, tuple, set)):
            return list(value)
        return [value]
