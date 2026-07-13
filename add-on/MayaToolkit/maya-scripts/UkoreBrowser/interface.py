# ================================================
#   UKORE FILE BROWSER — SIMPLE PATH SYNC VERSION
# ================================================

import os
import json
import logging
import subprocess
from functools import partial
import tmlib
import re

from tmlib.module.PySide import QtCore, QtGui, QtWidgets, QAction, PySideMod

import maya.cmds as cmds

from tmlib.ui.interface_template import ToolkitWindow
from UkoreBrowser import utils
from importlib import reload

from UkoreMaya.core import template_ui, menu_utils,function

reload(utils)
reload(template_ui)
reload(menu_utils)
reload(function)


import UkoreBrowser

RE_VERSION = re.compile(r"([_-]?v)(\d{3})", re.IGNORECASE)


class MainWindow(ToolkitWindow):
    CONFIG_FILE = os.path.join(
        os.path.expanduser("~"), "ukore_file_browser.json"
    )

    dir_folder = os.path.dirname(UkoreBrowser.__file__.replace("__init__.py", ""))

    BROWSER_ROOT_PATH = r"G:/My Drive/Projects/"
    BLENDER_TEMPLATE = f"{dir_folder}/template/template.blend"
    MAYA_TEMPLATE = f"{dir_folder}/template/template.ma"

    GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1yJsVb-b53yrFhuD0X6_qaLDVH0YAoIKLhHMvRm63CcE/edit?gid=0#gid=0"

    MAX_RECENT = 10

    # ------------------------------------------------------------
    # INIT
    # ------------------------------------------------------------
    def __init__(self):
        super(MainWindow, self).__init__(os.path.basename(os.path.dirname(__file__)))

        # Load config (recent files only)
        config = self.load_config()
        self.recent_files = config.get("recent_files", [])

        # Always start here
        self.root_path = self.BROWSER_ROOT_PATH.replace("\\", "/")
        self.current_browse_path = self.get_default_startup_project()
        print("Default Directory : {}".format(self.current_browse_path))

        self.ui.lineEdit_current_path.setText(self.current_browse_path)

        # Setup FileSystemModel
        self.fs_model = QtWidgets.QFileSystemModel()
        self.fs_model.setRootPath(self.root_path)
        self.fs_model.setFilter(QtCore.QDir.NoDotAndDotDot | QtCore.QDir.AllEntries)

        self.proxy = CleanExtFilter()
        self.proxy.setSourceModel(self.fs_model)
        self.proxy.filter_latest_version = False

        self.ui.tableView_files.setModel(self.proxy)
        self.ui.tableView_files.setSortingEnabled(True)

        self.ui.tableView_files.setRootIndex(
            self.proxy.mapFromSource(self.fs_model.index(self.root_path))
        )

        # Columns
        self.columns = [
            self.ui.listWidget_project,
            self.ui.listWidget_class,
            self.ui.listWidget_scene,
            self.ui.listWidget_shot,
            self.ui.listWidget_element,
        ]

        self.search_boxes = [
            self.ui.lineEdit_search_project,
            self.ui.lineEdit_search_class,
            self.ui.lineEdit_search_scene,
            self.ui.lineEdit_search_shot,
            self.ui.lineEdit_search_element,
        ]

        self.fs_model.directoryLoaded.connect(self.on_directory_loaded)

        # SIGNALS
        self.connect_signals()

        # Context menu
        self.ui.tableView_files.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.tableView_files.customContextMenuRequested.connect(
            self.open_context_menu
        )
        self.ui.tableView_files.setColumnHidden(2, True)

        # Recent
        self.build_setting_menu()

        # INITIAL LOAD
        self.set_shortcut_path(type="current")
        self.set_project_on_change_project_browser()

    # ------------------------------------------------------------
    # CONFIG
    # ------------------------------------------------------------
    def on_latest_version_filter_toggled(self, state):
        """Toggle the latest version filter in the proxy model and refresh."""
        # state is 0 (Unchecked), 2 (Checked)
        is_checked = state == QtCore.Qt.Checked
        self.proxy.filter_latest_version = is_checked

        # ⚠️ สำคัญมาก: ต้องเรียก invalidate() เพื่อให้ QSortFilterProxyModel ทำการกรองใหม่
        self.proxy.invalidate()

    def load_config(self):
        if not os.path.isfile(self.CONFIG_FILE):
            return {}
        try:
            with open(self.CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            return {}

    def save_config(self):
        data = {"recent_files": self.recent_files}
        with open(self.CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=4)

    def show_popup(self, text, duration=5000):
        """Show a floating popup message inside window."""
        popup = PopupMessage(text, duration, self)
        popup.adjustSize()
        popup.show_centered()

    def get_default_startup_project(self):
        project_path = cmds.workspace(q=1, rd=1)

        print("Current Project Path : ", project_path)
        # is current project in g drive , will set first project instead
        if not project_path.startswith(self.BROWSER_ROOT_PATH):
            print("Default Project not in Gdrive : ,", project_path)
            project_path = "G:\My Drive\Projects\default"

        project_path_share = os.path.join(project_path, "share")

        if os.path.exists(project_path_share):
            return project_path_share
        else:
            return project_path.replace("\\", "/")

    # ------------------------------------------------------------
    # RECENT FILES  (FIXED VERSION)
    # ------------------------------------------------------------
    def add_recent_file(self, path):
        if path in self.recent_files:
            self.recent_files.remove(path)
        self.recent_files.insert(0, path)
        self.recent_files = self.recent_files[: self.MAX_RECENT]
        self.save_config()
        self.build_setting_menu()

    def build_setting_menu(self):
        """Create menu object but DO NOT attach to QPushButton (it won't work)."""

        # Create Recent Menu
        self.recent_menu = QtWidgets.QMenu("ไฟล์ล่าสุด...", self)
        self.recent_menu.setStyleSheet(template_ui.get_menu_stylesheet())
        self.dict_recent_path = {}

        for path in self.recent_files:
            file_name = os.path.basename(path)
            act = QAction(file_name, self)
            self.dict_recent_path[file_name] = path
            act.triggered.connect(partial(self.open_recent, file_name))
            self.recent_menu.addAction(act)

        # Create More Menu
        self.more_menu = QtWidgets.QMenu(self)
        # self.more_menu.addMenu(self.recent_menu)

        open_google_drive = QAction("เช็คสถานะซิงค์ Drive", self)
        open_google_drive.triggered.connect(self.open_google_drive_app)
        self.more_menu.addAction(open_google_drive)

        self.more_menu.addSeparator()

        self.more_menu.addSeparator()
        reload_action = QAction("รีโหลด", self)
        reload_action.triggered.connect(self.reload)
        self.more_menu.addAction(reload_action)

        # Create Create New Menu
        self.create_new_menu = QtWidgets.QMenu(self)
        create_folder = QAction("Folder", self)
        create_folder.triggered.connect(lambda: self.create_new("folder"))
        self.create_new_menu.addAction(create_folder)
        create_maya = QAction("Maya", self)
        create_maya.triggered.connect(lambda: self.create_new("maya"))
        self.create_new_menu.addAction(create_maya)
        create_blender = QAction("Blender", self)
        create_blender.triggered.connect(lambda: self.create_new("blender"))
        self.create_new_menu.addAction(create_blender)

    def show_recent_menu(self):
        btn = self.ui.pushButton_shortcut_recent
        pos = btn.mapToGlobal(btn.rect().bottomLeft())
        self.recent_menu.exec_(pos)

    def show_more_menu(self):
        btn = self.ui.pushButton_setting
        pos = btn.mapToGlobal(btn.rect().bottomLeft())
        self.more_menu.exec_(pos)

    def show_change_path_menu(self):
        btn = self.ui.pushButton_change_path
        pos = btn.mapToGlobal(btn.rect().bottomLeft())
        self.switch_path_menu.exec_(pos)

    def show_create_new_menu(self):
        btn = self.ui.pushButton_create_new
        pos = btn.mapToGlobal(btn.rect().bottomLeft())
        self.create_new_menu.exec_(pos)

    def open_recent(self, file_name):
        path = self.dict_recent_path[file_name]
        self.update_current_path(path)

    def open_publish_tool(self):
        menu_utils.publisher()

    def get_default_startup_path(self):
        current_maya_workspace_path = cmds.workspace(q=True, dir=True)
        return current_maya_workspace_path

    def save_as(self):
        current_file_name = os.path.basename(cmds.file(q=True, sn=True))

        name, ok = QtWidgets.QInputDialog.getText(
            self, f"Save as New File ", "Name:", text=current_file_name
        )

        if not ok or not name.strip():
            return

        save_path = os.path.join(self.current_browse_path, name)
        cmds.file(rename=save_path + ".ma")
        cmds.file(save=True, force=True, type="mayaAscii")

    # ------------------------------------------------------------
    # SIGNALS
    # ------------------------------------------------------------
    def connect_signals(self):
        for i, lw in enumerate(self.columns):
            lw.itemClicked.connect(partial(self.on_column_clicked, i))

        for i, le in enumerate(self.search_boxes):
            le.textChanged.connect(partial(self.filter_column, i))

        self.ui.lineEdit_current_path.returnPressed.connect(self.on_path_entered)
        self.ui.pushButton_go_back.clicked.connect(self.go_back)

        self.ui.lineEdit_search_file.textChanged.connect(self.search_current_folder)
        self.ui.tableView_files.doubleClicked.connect(self.on_file_double_clicked)

        self.ui.pushButton_publish_tool.clicked.connect(self.open_publish_tool)
        self.ui.pushButton_setting.clicked.connect(self.show_more_menu)
        self.ui.pushButton_shortcut_recent.clicked.connect(self.show_recent_menu)
        self.ui.pushButton_create_new.clicked.connect(self.show_create_new_menu)

        self.ui.listWidget_project.itemClicked.connect(
            self.set_project_on_change_project_browser
        )
        self.ui.listWidget_project.currentTextChanged.connect(
            self.set_project_on_change_project_browser
        )
        self.ui.pushButton_open_current_folder.clicked.connect(
            lambda x: utils.open_directory(self.current_browse_path)
        )

        # Change Path Menu
        self.ui.pushButton_shortcut_publish.clicked.connect(
            lambda x: self.set_shortcut_path(type="publish")
        )
        self.ui.pushButton_shortcut_share.clicked.connect(
            lambda x: self.set_shortcut_path(type="share")
        )
        self.ui.pushButton_google_sheet.clicked.connect(self.open_google_sheet)

        self.ui.pushButton_save_file.clicked.connect(self.save_as)

    def on_path_entered(self):
        print(
            "======= # Path Entered : {} # =======".format(
                self.ui.lineEdit_current_path.text()
            )
        )
        self.update_current_path(self.ui.lineEdit_current_path.text())

    # ------------------------------------------------------------
    # DIRECTORY LOADED
    # ------------------------------------------------------------
    def on_directory_loaded(self, path):
        h = self.ui.tableView_files.horizontalHeader()
        h.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        h.setFixedHeight(22)

    # ------------------------------------------------------------
    # COLUMN SYSTEM (NEW SIMPLE VERSION)
    # ------------------------------------------------------------
    def load_column_items(self, level, path):
        lw = self.columns[level]
        lw.clear()

        if not os.path.isdir(path):
            return

        try:
            entries = sorted(os.listdir(path))
        except:
            return

        for name in entries:
            fp = os.path.join(path, name)
            if os.path.isdir(fp):
                lw.addItem(name)

    def update_button_mode(self):
        default_share_style = """
QPushButton {
    color: black;
    background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(185, 185, 185, 255), stop:1 rgba(129, 129, 129, 255));
    border: 1px solid rgba(255, 255, 255, 0.5);
    font-weight: 600;
    letter-spacing: 0.5px;
	border:None;
	border-radius: 4px;
}

QPushButton:hover {
        background: qlineargradient(spread:pad, x1:1, y1:0, x2:1, y2:1, stop:0 rgba(243, 159, 89, 255), stop:1 rgba(197, 131, 76, 255));
}

QPushButton:pressed {
        background: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(189, 123, 69, 255), stop:1 rgba(134, 88, 50, 255));
}



"""
        share_style = """
        QPushButton {
    color: black;
    background: qlineargradient(spread:pad, x1:1, y1:0, x2:1, y2:1, stop:0 rgba(243, 159, 89, 255), stop:1 rgba(197, 131, 76, 255));
    border: 1px solid rgba(255, 255, 255, 0.5);
    font-weight: 600;
    letter-spacing: 0.5px;
	border:None;
	border-radius: 4px;
}
QPushButton:hover {
        background: qlineargradient(spread:pad, x1:1, y1:0, x2:1, y2:1, stop:0 rgba(243, 159, 89, 255), stop:1 rgba(197, 131, 76, 255));
}

QPushButton:pressed {
        background: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(189, 123, 69, 255), stop:1 rgba(134, 88, 50, 255));
}
    
"""
        publish_style = """
QPushButton {
    color: black;
    background:qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(134, 155, 222, 255), stop:1 rgba(165, 217, 255, 255));
    border: 1px solid rgba(255, 255, 255, 0.5);
    font-weight: 600;
    letter-spacing: 0.5px;
	border:None;
	border-radius: 4px;
}

QPushButton:hover {
        background: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(134, 155, 222, 255), stop:1 rgba(165, 217, 255, 255));
}

QPushButton:pressed {
        background: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(123, 162, 191, 255), stop:1 rgba(69, 84, 135, 255));
}

"""

        default_publish_style = """
QPushButton {
    color: black;
    background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(185, 185, 185, 255), stop:1 rgba(129, 129, 129, 255));
    border: 1px solid rgba(255, 255, 255, 0.5);
    font-weight: 600;
    letter-spacing: 0.5px;
	border:None;
	border-radius: 4px;
}

QPushButton:hover {
        background: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(134, 155, 222, 255), stop:1 rgba(165, 217, 255, 255));
}

QPushButton:pressed {
        background: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(123, 162, 191, 255), stop:1 rgba(69, 84, 135, 255));
}

"""
        if "publish" in self.current_browse_path:
            self.ui.pushButton_shortcut_publish.setStyleSheet(publish_style)
            self.ui.pushButton_shortcut_share.setStyleSheet(default_share_style)
        elif "share" in self.current_browse_path:
            self.ui.pushButton_shortcut_publish.setStyleSheet(default_publish_style)
            self.ui.pushButton_shortcut_share.setStyleSheet(share_style)
        else:
            self.ui.pushButton_shortcut_publish.setStyleSheet(default_publish_style)
            self.ui.pushButton_shortcut_share.setStyleSheet(default_share_style)

    def sync_columns_from_path(self):
        """Rebuild ALL columns entirely from current_path."""
        for lw in self.columns:
            lw.blockSignals(True)
            lw.clear()

        try:
            rel = os.path.relpath(self.current_browse_path, self.root_path)
            parts = [] if rel == "." else rel.split(os.sep)

            self.load_column_items(0, self.root_path)
            p = self.root_path

            for level, name in enumerate(parts):
                if level >= len(self.columns):
                    break

                lw = self.columns[level]

                items = lw.findItems(name, QtCore.Qt.MatchExactly)
                if items:
                    lw.setCurrentItem(items[0])

                p = os.path.join(p, name)

                next_level = level + 1
                if next_level < len(self.columns):
                    self.load_column_items(next_level, p)

        finally:
            for lw in self.columns:
                lw.blockSignals(False)

    def on_column_clicked(self, level, current):
        if not current:
            return

        p = self.root_path
        for i in range(level + 1):
            it = self.columns[i].currentItem()
            if it:
                p = os.path.join(p, it.text())

        self.update_current_path(p.replace("\\", "/"))

    def filter_column(self, level, text):
        lw = self.columns[level]
        txt = text.lower()
        for i in range(lw.count()):
            item = lw.item(i)
            item.setHidden(txt not in item.text().lower())

    # ------------------------------------------------------------
    # PATH ENTRY + BACK
    # ------------------------------------------------------------
    def update_current_path(self, path):
        def update_path(path):
            self.current_browse_path = path
            self.ui.lineEdit_current_path.setText(self.current_browse_path)

            self.sync_columns_from_path()
            self.update_file_list()
            self.update_button_mode()
            self.update_thumbnail()

            # reset seartch box
            for i, lw in enumerate(self.search_boxes):
                lw.setText("")

        # path = path.strip()
        path = os.path.normpath(path).replace("\\", "/")

        print("****** Update Current Path : {} ******".format(path))

        # --- if path is file ----
        if os.path.isfile(path):
            print("Update Type : Set File : {}".format(path))

            folder = os.path.dirname(path)
            filename = os.path.basename(path)

            update_path(folder)

            # --- DELAY selection until table is fully refreshed ---
            QtCore.QTimer.singleShot(150, lambda: self.select_file_in_table(filename))
            return

        # --- if path is directory ----
        elif os.path.isdir(path):
            print("Update Type : Set Directory : {}".format(path))
            update_path(path)
            return

        else:
            QtWidgets.QMessageBox.warning(
                self, "Error", f"Path does not exist:\n{path}"
            )

    def update_thumbnail(self):
        if os.path.isdir(self.current_browse_path):
            search_path = self.current_browse_path
        else:
            search_path = os.path.dirname(self.current_browse_path)

        thumbnail_path = os.path.join(search_path, "thumbnail.jpg")
        thumbnail_path = thumbnail_path.replace("\\", "/")
        print("find : ", thumbnail_path)
        if os.path.exists(thumbnail_path):
            stylesheet = (
                template_ui.get_table_view_browser_stylesheet()
                + f"""
            QTableView#tableView_files {{
                background-image: url("{thumbnail_path}");
                background-repeat: no-repeat;
                background-position: center;
            background-size: 100px 100px;
                background-color: #1e1e1e;
            }}


            """
            )
            self.ui.tableView_files.setStyleSheet(stylesheet)
        else:
            self.ui.tableView_files.setStyleSheet(
                template_ui.get_table_view_browser_stylesheet()
            )

    def select_file_in_table(self, filename):
        """
        Select the given filename inside tableView_files.
        """
        tv = self.ui.tableView_files
        model = self.fs_model
        proxy = self.proxy

        parent_index = model.index(self.current_browse_path)

        row_count = model.rowCount(parent_index)

        for row in range(row_count):
            index_source = model.index(row, 0, parent_index)
            name = model.fileName(index_source)

            if name.lower() == filename.lower():
                # map source → proxy
                index_proxy = proxy.mapFromSource(index_source)
                tv.setCurrentIndex(index_proxy)
                tv.scrollTo(index_proxy)
                return

    def go_back(self):
        if os.path.abspath(self.current_browse_path) == os.path.abspath(self.root_path):
            return

        parent = os.path.dirname(self.current_browse_path).replace("\\", "/")

        self.update_current_path(parent)

    # ------------------------------------------------------------
    # FILE TABLE
    # ------------------------------------------------------------
    def update_file_list(self):
        if not os.path.isdir(self.current_browse_path):
            return

        # idx = self.fs_model.index(self.current_path)
        # self.ui.tableView_files.setRootIndex(idx)

        idx = self.fs_model.index(self.current_browse_path)

        proxy_idx = self.proxy.mapFromSource(idx)
        self.ui.tableView_files.setRootIndex(proxy_idx)

        h = self.ui.tableView_files.horizontalHeader()
        h.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        h.setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        h.setSectionResizeMode(3, QtWidgets.QHeaderView.Fixed)

        h.resizeSection(1, 150)
        # h.resizeSection(1, 40)
        h.resizeSection(3, 150)

        tv = self.ui.tableView_files
        tv.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        tv.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        tv.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        tv.verticalHeader().hide()
        tv.verticalHeader().setDefaultSectionSize(1)
        tv.setIconSize(QtCore.QSize(10, 10))

    # ------------------------------------------------------------
    # FILE SEARCH
    # ------------------------------------------------------------
    def search_current_folder(self, text):
        txt = text.lower()
        parent_index = self.fs_model.index(self.current_browse_path)
        row_count = self.fs_model.rowCount(parent_index)

        for row in range(row_count):
            idx = self.fs_model.index(row, 0, parent_index)
            name = self.fs_model.fileName(idx).lower()
            self.ui.tableView_files.setRowHidden(row, txt not in name)

    # ------------------------------------------------------------
    def open_file_in_new_window(self, path):
        """
        Opens a file using os.startfile without any Maya logic or confirmation dialogs.
        This behaves like a standard system file open.
        """
        filename = os.path.basename(path)

        self.show_popup(f"Opening File (Default) : {filename}")

        try:
            os.startfile(path)
            self.add_recent_file(path)
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Error: System Open Failed",
                f"ไม่สามารถเปิดไฟล์ในระบบได้:\n{filename}\n\nError: {e}",
            )

    def on_file_double_clicked(self, index):
        # map proxy -> source
        src_index = self.proxy.mapToSource(index.sibling(index.row(), 0))
        path = self.fs_model.filePath(src_index)
        filename = os.path.basename(path)

        if os.path.isdir(path):
            self.update_current_path(path.replace("\\", "/"))
            return

        # 2. จัดการไฟล์ (File)
        ext = os.path.splitext(filename)[1].lower()
        is_maya_file = ext in [".ma", ".mb"]

        self.show_popup(f"Opening File : {filename}")

        try:
            if is_maya_file:
                # ------------------------------------------------------------------
                # 🚀 ส่วนที่แก้ไข: จัดการ Unsaved Changes ด้วย PySide Dialog
                # ------------------------------------------------------------------

                # A. ตรวจสอบว่า Scene ปัจจุบันมีการแก้ไขหรือไม่
                if cmds.file(query=True, modified=True):

                    # B. สร้าง PySide Dialog ของเราเองเพื่อถามผู้ใช้
                    current_scene_path = cmds.file(query=True, sceneName=True)
                    current_scene_name = (
                        os.path.basename(current_scene_path) or "Untitled Scene"
                    )

                    # กำหนดปุ่มและค่าคืนกลับ
                    save_btn = QtWidgets.QMessageBox.Save
                    discard_btn = QtWidgets.QMessageBox.Discard
                    cancel_btn = QtWidgets.QMessageBox.Cancel

                    ask = QtWidgets.QMessageBox.warning(
                        self,
                        "Save Changes",
                        f"Save changes to current scene?\n{current_scene_name}",
                        save_btn | discard_btn | cancel_btn,
                        save_btn,  # กำหนดปุ่มเริ่มต้น
                    )

                    if ask == cancel_btn:
                        self.show_popup("การเปิดไฟล์ถูกยกเลิก", duration=1500)
                        return  # ยกเลิกการเปิดไฟล์

                    elif ask == save_btn:
                        # บันทึก Scene ปัจจุบันก่อน
                        cmds.file(save=True)
                        # เปิดไฟล์ใหม่โดยไม่ต้องใช้ force
                        cmds.file(path, open=True)

                        menu_utils.update_references()

                    elif ask == discard_btn:
                        # เปิดไฟล์ใหม่ทันทีโดยใช้ force=True เพื่อทิ้งการแก้ไขปัจจุบัน
                        cmds.file(path, open=True, force=True)

                        menu_utils.update_references()

                else:
                    # ถ้า Scene ปัจจุบันไม่มีการแก้ไข ให้เปิดไฟล์ใหม่ได้ทันที
                    cmds.file(path, open=True)

                    menu_utils.update_references()
                # ------------------------------------------------------------------

            else:
                # 🌐 หากไม่ใช่ไฟล์ Maya: แสดงกล่องโต้ตอบยืนยัน PySide
                ask = QtWidgets.QMessageBox.question(
                    self,
                    "ยืนยันการเปิดไฟล์",
                    f"ต้องการเปิดไฟล์:\n{filename}\n\nในโปรแกรมใหม่หรือไม่?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.No,
                )

                if ask != QtWidgets.QMessageBox.Yes:
                    return

                # เปิดด้วยโปรแกรมที่ผูกกับระบบปฏิบัติการ
                os.startfile(path)

            # บันทึกไฟล์ล่าสุดเมื่อเปิดสำเร็จ
            self.add_recent_file(path)

        except Exception as e:
            # ดักจับ Error ทั่วไป (เช่น ไฟล์เสีย)
            # log.error(f"File Operation Error: {e}")
            QtWidgets.QMessageBox.critical(
                self,
                "Error: File Operation Failed",
                f"ไม่สามารถดำเนินการได้:\n{filename}\n\nError: {e}",
            )

    # ------------------------------------------------------------
    # CONTEXT MENU
    # ------------------------------------------------------------
    def open_context_menu(self, pos):
        proxy_index = self.ui.tableView_files.indexAt(pos)
        if not proxy_index.isValid():
            return

        # MUST map to source
        src_index = self.proxy.mapToSource(proxy_index.sibling(proxy_index.row(), 0))
        file_path = self.fs_model.filePath(src_index)

        menu = QtWidgets.QMenu(self)
        menu.setStyleSheet(template_ui.get_menu_stylesheet())

        act_copy_name = menu.addAction("Copy Name")
        act_copy = menu.addAction("Copy File Path")
        menu.addSeparator()
        act_delete = menu.addAction("Delete")
        act_rename = menu.addAction("Rename")
        menu.addSeparator()
        act_create_reference = menu.addAction("Import as Reference")
        menu.addSeparator()
        act_open_file_in_new_window = menu.addAction("Open File in New Section...")
        act = menu.exec_(self.ui.tableView_files.mapToGlobal(pos))

        if act == act_copy:
            QtWidgets.QApplication.clipboard().setText(file_path)
            self.show_popup("Copy Path", duration=500)
        elif act == act_delete:
            self.delete_with_confirm(file_path)
        elif act == act_rename:
            self.rename_dialog(file_path)
        elif act == act_create_reference:
            utils.create_reference(path=file_path)
            function.import_all_picker()
        elif act == act_open_file_in_new_window:
            self.open_file_in_new_window(path=file_path)
        elif act == act_copy_name:
            QtWidgets.QApplication.clipboard().setText(
                os.path.basename(file_path).split(".")[0]
            )
            self.show_popup("Copy Name", duration=500)

    def delete_with_confirm(self, path):
        name = os.path.basename(path)
        ask = QtWidgets.QMessageBox.question(
            self,
            "Delete",
            f"ต้องการลบสิ่งนี้จริงหรือไม่?\n{name}",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        if ask != QtWidgets.QMessageBox.Yes:
            return

        try:
            if os.path.isfile(path):
                os.remove(path)
            else:
                import shutil

                shutil.rmtree(path)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))

        self.update_file_list()

    # ------------------------------------------------------------
    # BUTTONS
    # ------------------------------------------------------------
    def open_google_sheet(self):
        import webbrowser

        webbrowser.open(self.GOOGLE_SHEET_URL)

    def reload(self):
        self.sync_columns_from_path()
        self.update_file_list()

    def open_google_drive_app(self):
        os.startfile("C:\Program Files\Google\Drive File Stream\launch.bat")
        self.show_popup("กำลังเปิด Google Drive App", duration=2000)

    def copy_current_path(self):
        QtWidgets.QApplication.clipboard().setText(self.current_browse_path)
        self.show_popup("คัดลอก Path โฟลเดอร์", duration=2000)

    def rename_dialog(self, path):
        folder = os.path.dirname(path)
        old_name = os.path.basename(path)

        new_name, ok = QtWidgets.QInputDialog.getText(
            self,
            "Rename",
            f"Rename:\n{old_name}",
            text=old_name,
        )

        if not ok or not new_name.strip():
            return

        new_path = os.path.join(folder, new_name)

        try:
            os.rename(path, new_path)
            self.update_file_list()
            self.show_popup("Rename เสร็จแล้ว", duration=1500)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))

    def create_new(self, type="folder"):
        """
        type: "folder", "maya", "blender"
        """

        # Default name from current folder
        default_name = os.path.basename(self.current_browse_path.rstrip("/"))

        # Ask user for name
        name, ok = QtWidgets.QInputDialog.getText(
            self, f"Create New {type.title()}", "Name:", text=default_name
        )

        if not ok or not name.strip():
            return

        # -----------------------------------------------------
        # CREATE FOLDER
        # -----------------------------------------------------
        if type == "folder":
            new_path = os.path.join(self.current_browse_path, name)
            try:
                os.makedirs(new_path, exist_ok=False)
                self.show_popup("สร้างโฟลเดอร์สำเร็จ", duration=1500)
                self.update_file_list()
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", str(e))
            return

        # -----------------------------------------------------
        # CREATE MAYA FILE (.ma)
        # -----------------------------------------------------
        if type == "maya":
            new_file = os.path.join(self.current_browse_path, f"{name}.ma")
            try:
                import shutil

                shutil.copy(self.MAYA_TEMPLATE, new_file)
                self.show_popup(f"สร้าง Maya file: {name}.ma", duration=1500)
                self.update_file_list()
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", str(e))
            return

        # -----------------------------------------------------
        # CREATE BLENDER FILE (.blend)
        # -----------------------------------------------------
        if type == "blender":
            new_file = os.path.join(self.current_browse_path, f"{name}.blend")
            try:
                import shutil

                shutil.copy(self.BLENDER_TEMPLATE, new_file)
                self.show_popup(f"สร้าง Blender file: {name}.blend", duration=1500)
                self.update_file_list()
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", str(e))
            return

    def set_project_on_change_project_browser(self):
        """This will set current maya workspace when change project"""

        cur = os.path.normpath(self.current_browse_path)
        root = os.path.normpath(self.BROWSER_ROOT_PATH)

        if os.path.isfile(cur):
            cur_dir = os.path.dirname(cur)
        else:
            cur_dir = cur

        if cur_dir.startswith(root):
            relative = os.path.relpath(cur_dir, root)
            proj_name = relative.split(os.sep)[0]
            self.project_path = os.path.join(root, proj_name) + os.sep

            # result = cmds.confirmDialog("Do you wanna change project to ")
            cmds.workspace(self.project_path, openWorkspace=True)
            project_name = self.project_path.rstrip(os.sep).split(os.sep)[-1]

            self.show_popup("Set Project : {}".format(project_name), duration=1000)
            print("Set Project Complete : ", self.project_path)

    def set_shortcut_path(self, type="publish"):
        """This will shortcut set the path to current browser's path"""

        current_browser_path = os.path.normpath(self.current_browse_path)
        current_workspace_path = os.path.normpath(cmds.workspace(q=True, rd=True))
        current_file_path = os.path.normpath(cmds.file(query=True, sceneName=True))

        new_browser_path = current_browser_path

        # Create relative path
        if not current_workspace_path.startswith("G"):
            current_workspace_path = "G:\My Drive\Projects\default"

        base_path = os.path.relpath(current_browser_path, current_workspace_path)
        parts = re.split(r"share|publish", base_path, maxsplit=1)
        relative_path = os.path.normpath(parts[-1])

        if relative_path.startswith("\\"):
            relative_path = relative_path[1:]

        dict_folder_name = {"publish": "publish", "share": "share"}

        if type == "publish" or type == "share":
            folder_type = os.path.normpath(dict_folder_name[type])

            new_browser_path = os.path.join(
                current_workspace_path, folder_type, relative_path
            )

            while True:
                if os.path.exists(new_browser_path):
                    break
                else:
                    new_browser_path = os.path.dirname(new_browser_path)

        elif type == "current":
            if current_file_path:
                if current_file_path.startswith(
                    os.path.normpath(self.BROWSER_ROOT_PATH)
                ):
                    new_browser_path = current_file_path

        print(
            "======== # Setting Shortcut Path : {} : {} # ========".format(
                type, new_browser_path
            )
        )

        print("Current Browser Path : ", current_browser_path)
        print("Current Opening Maya Scene : ", current_file_path)

        self.update_current_path(new_browser_path)

        self.show_popup("This is {} Path".format(type.upper()), duration=1000)


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


class CleanExtFilter(QtCore.QSortFilterProxyModel):
    ALLOWED_EXT = QtCore.QRegularExpression(
        r".*\.(ma|mb|blend|fbx|obj|avi|mp4|jpg|png|mov|prproj|mp3|py|json|ini|txt|tga)$",
        QtCore.QRegularExpression.CaseInsensitiveOption,
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.filter_latest_version = False
        self._latest_versions_map = {}
        self._current_parent_ptr = None

        # fast ext filter
        self.setFilterRegularExpression(self.ALLOWED_EXT)

    # ------------------------------------------------------
    # SORTING SPEED-UP
    # ------------------------------------------------------
    def lessThan(self, left, right):
        model = self.sourceModel()
        col = left.column()

        if col == 0:  # Name
            return model.data(left).lower() < model.data(right).lower()

        elif col == 1:  # Size
            return model.size(left) < model.size(right)

        elif col == 3:  # Date Modified
            return model.lastModified(left) < model.lastModified(right)

        return super().lessThan(left, right)

    # ------------------------------------------------------
    # FILTER ROW
    # ------------------------------------------------------
    def filterAcceptsRow(self, row, parent):
        model = self.sourceModel()
        idx = model.index(row, 0, parent)

        if not idx.isValid():
            return False

        # Show all folders
        if model.isDir(idx):
            return True

        filename = model.data(idx)

        # Extension filter (already regex-matched)
        if not self.filterRegularExpression().match(filename).hasMatch():
            return False

        # Latest version filter
        if self.filter_latest_version:
            parent_ptr = parent.internalPointer()

            # recalc only when folder changes
            if parent_ptr != self._current_parent_ptr:
                self._recalc_latest_versions(parent)
                self._current_parent_ptr = parent_ptr

            # keep only files in the latest version map
            if filename not in self._latest_versions_map:
                return False

        return True

    # ------------------------------------------------------
    # LATEST VERSION CALC
    # ------------------------------------------------------
    def _recalc_latest_versions(self, parent):
        model = self.sourceModel()
        row_count = model.rowCount(parent)

        latest = {}  # base -> (version, filename)

        for r in range(row_count):
            idx = model.index(r, 0, parent)
            if model.isDir(idx):
                fn = model.data(idx)
                latest[fn.lower()] = (999999, fn)  # folder always keep
                continue

            filename = model.data(idx)

            # skip non-matching ext (already filtered above)
            if not self.filterRegularExpression().match(filename).hasMatch():
                continue

            # check version
            match = RE_VERSION.search(filename)
            if match:
                base_name = filename[: match.start()].rstrip("_-").lower()
                version = int(match.group(2))
            else:
                base_name = filename.lower()
                version = 999999  # treat non-version file as highest

            old_ver, _ = latest.get(base_name, (-1, ""))
            if version > old_ver:
                latest[base_name] = (version, filename)

        # store only final filenames
        self._latest_versions_map = {name: True for _, name in latest.values()}

    # ------------------------------------------------------
    def invalidate(self):
        self._current_parent_ptr = None
        self._latest_versions_map.clear()
        super().invalidate()
