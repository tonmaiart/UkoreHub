# ================================================
#  UKORE PUBLISHER — MAYA
# ================================================

# This tools created by Natchapon Srisuk ,Only using for Ukore Studio's projects.
# contact : natchapon.18851@gmail.com

# ================================================

import shutil
import os
import json
import logging
import subprocess
from functools import partial

from importlib import reload
from UkorePublisher import function
from UkoreMaya.core import utils, Pipeline,Logic
from tmlib.ui.interface_template import ToolkitWindow, uitools

from tmlib.module.PySide import QtWidgets, QtGui, QtCore

import maya.cmds as cmds

reload(utils)
reload(function)


class MainWindow(ToolkitWindow):
    # ------------------------------------------------------------
    # INIT
    # ------------------------------------------------------------
    def __init__(self):
        super(MainWindow, self).__init__(os.path.basename(os.path.dirname(__file__)))

        # Pattern of choice for each departments
        self.dict_publish_choice = {
            "Model": ["Main","Proxy", "Hi"],
            "Rig": ["Main","Proxy", "Hi"],
            "Anim": ["Main","Layout", "Blocking", "Polish", "Playblast"],
        }

        self.next_version = 0

        # INITIALIZE
        self.initialize_type_list_widget()
        self.initialize_ticket_list_widget()
        self.update_publish_target_info()

        # SIGNALS
        self.connect_signals()

    # ------------------------------------------------------------
    # SIGNALS
    # ------------------------------------------------------------
    def connect_signals(self):
        self.ui.listWidget_type.itemSelectionChanged.connect(
            self.initialize_ticket_list_widget
        )

        self.ui.listWidget_type.itemSelectionChanged.connect(
            self.update_publish_target_info
        )
        self.ui.listWidget_ticket.itemSelectionChanged.connect(
            self.update_publish_target_info
        )

        self.ui.listWidget_ticket.itemSelectionChanged.connect(
            self.update_publish_target_info
        )

        self.ui.pushButton_publish.clicked.connect(self.publish_button)
        self.ui.pushButton_open_dir.clicked.connect(self.open_publish_dir)
        self.ui.pushButton_take_a_snapshot.clicked.connect(self.take_a_snapshot)

    def update_publish_target_info(self):
        current_path = cmds.file(q=True, sn=True)
        current_path = os.path.normpath(current_path)
        print("Current Project Path : ", current_path)

        # Current Path Not Found
        if not current_path:
            self.ui.label_version_publish.setText("")
            self.ui.label_job_name.setText("")
            self.ui.label_job_task.setText("")
            self.ui.label_job_type.setText("")

        # Found Current Path
        elif current_path:
            # Update Version Label
            print("current maya path :  ", current_path)
            print("selected sub folder : ", self.get_current_selected_ticket())
            self.next_version = utils.get_new_version(
                current_share_path=current_path,
                subfolder=self.get_current_selected_ticket(),
            )

            self.ui.label_version_publish.setText("v{:03d}".format(self.next_version))

            # get job catagory
            parts = (
                current_path.split("publish")[-1].split("share")[-1].split(os.path.sep)
            )

            # get job type
            self.ui.label_job_name.setText(parts[2])

            # get job task
            self.ui.label_job_type.setText(self.get_current_selected_ticket())

            # get job name
            self.ui.label_job_task.setText(self.get_current_selected_type())

    def take_a_snapshot(self):
        self.snapshot_path = Pipeline.playblast_screenshot_to_project_folder()

        print("get img path : ", self.snapshot_path)
        pixmap = QtGui.QPixmap(self.snapshot_path)
        if pixmap.isNull():
            return

        btn = self.ui.pushButton_take_a_snapshot  # <-- QPushButton

        btn.setIcon(QtGui.QIcon(pixmap))
        btn.setIconSize(btn.size())

    def initialize_type_list_widget(self):
        self.ui.listWidget_type.addItems(list(self.dict_publish_choice.keys()))
        self.ui.listWidget_type.setCurrentRow(0)

    def initialize_ticket_list_widget(self):
        current_type = self.get_current_selected_type()

        self.ui.listWidget_ticket.clear()
        self.ui.listWidget_ticket.addItems(self.dict_publish_choice[current_type])

        self.ui.listWidget_ticket.setCurrentRow(0)

    def get_current_selected_type(self):
        selection = self.ui.listWidget_type.selectedItems()
        if selection:
            return selection[0].text()
        else:
            return None

    def get_current_selected_ticket(self):
        selection = self.ui.listWidget_ticket.selectedItems()
        if selection:
            return selection[0].text()
        else:
            return None

    def get_current_job_name(self):
        return self.label_job_name.text()
    
    def publish_button(self):
        current_job_type = self.get_current_selected_type()
        current_job_task = self.get_current_selected_ticket()

        # check is user already select job task and job type
        current_job_type = self.get_current_selected_type()
        current_job_task = self.get_current_selected_ticket()

        if not ( current_job_task and current_job_type ):
            return
        
        # ==========================
        # start publish operation
        # ==========================

        publish_info = f"""
"โปรดตรวจสอบและยืนยันข้อมูลการพับบลิชนี้ \n
ชื่องานหลัก : {self.get_current_job_name()}\n
ประเภทงาน : {current_job_task}\n
แผนกงาน : {current_job_type}\n
"""
        result = cmds.confirmDialog(
            m=publish_info,
            button=["Ok", "Cancel"],
            defaultButton="Cancel",
            cancelButton="Ok",
        )

        if result == "Cancel":
            return
        
        publish_file_path = function.publish_dialog(
            result_job_type=current_job_type, result_job_task=current_job_task
        )
            
        # =================
        # Dialog Success
        # =================

        result = cmds.confirmDialog(
            m="พับบลิชไฟล์สำเร็จแล้ว! \n : {}".format(publish_file_path),
            button=["Ok", "Open Publish Folder"],
            defaultButton="Ok",
            cancelButton="Ok",
        )

        if result == "Open Publish Folder":
            os.startfile(os.path.dirname(publish_file_path))

        self.ui.label_publish_result.setText(
            "Publish สำเร็จ! : {} {} v{:03d}".format(
                current_job_type, current_job_task, self.next_version
            )
        )

        self.update_publish_target_info()

        # ===============
        # Export note
        # ===============

        note_text = self.ui.textBrowser_publish_info.toPlainText()
        text_path = os.path.join(os.path.dirname(publish_file_path), "note.txt")

        if note_text:
            with open(text_path, "w") as f:
                f.write(note_text)

        # =================
        # Export thumbnail
        # =================

        thumbnail_export = os.path.join(
            os.path.dirname(publish_file_path), "thumbnail.jpg"
        )
        if self.snapshot_path:
            shutil.copyfile(self.snapshot_path, thumbnail_export)

    def open_publish_dir(self):
        """
        Use to open publish directory that stored all of the published versions.
        """

        # check is user already select job task and job type
        current_job_type = self.get_current_selected_type()
        current_job_task = self.get_current_selected_ticket()

        if not ( current_job_task and current_job_type ):
            return

        # open folder
        publish_file_path = utils.get_publish_path(
            current_share_path=cmds.file(q=True, sn=True),
            subfolder=current_job_task,
            extension="ma",
            version=1,
        )

        open_folder_path = os.path.dirname(os.path.dirname(publish_file_path))
        Logic.make_sure_folder_exist(open_folder_path)
        os.startfile(open_folder_path)
