# ================================================
#   UKORE FILE BROWSER — SIMPLE PATH SYNC VERSION
# ================================================

import os
import json
import logging
import subprocess
from functools import partial

from PySide6 import QtCore, QtWidgets, QtUiTools
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMessageBox,
    QHeaderView,
)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QPalette, QColor, QBrush
from PySide6.QtCore import QTimer, QThread
from PySide6 import QtGui, QtCore

from PySide6 import QtWidgets, QtCore, QtGui

from PySide6 import QtCore


from PySide6.QtCore import QSortFilterProxyModel, QRegularExpression, Qt

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


class MainWindow(QtWidgets.QMainWindow):
    CONFIG_FILE = os.path.join(
        os.path.expanduser("~"), "Documents", "ukore_file_browser.json"
    )

    ROOT_PATH = r"G:/My Drive/Projects"
    DEFAULT_STARTUP_PATH = r"G:/My Drive/Projects/KafkaProj/.share/"
    MAYA_TEMPLATE = r"G:/My Drive/Projects/KafkaProj/template.ma"
    BLENDER_TEMPLATE = r"G:/My Drive/Projects/KafkaProj/template.blend"

    GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1yJsVb-b53yrFhuD0X6_qaLDVH0YAoIKLhHMvRm63CcE/edit?gid=0#gid=0"

    MAX_RECENT = 10

    # ------------------------------------------------------------
    # INIT
    # ------------------------------------------------------------
    def __init__(self):
        super().__init__()

        # Load UI
        ui_path = os.path.join(os.path.dirname(__file__), "ui.ui")
        ui_file = QtCore.QFile(ui_path)
        loader = QtUiTools.QUiLoader()
        ui_file.open(QtCore.QFile.ReadOnly)
        self.ui = loader.load(ui_file)
        ui_file.close()

        self.setCentralWidget(self.ui)
        self.setWindowTitle("Ukore File Browser")

        # Load config (recent files only)
        config = self.load_config()
        self.recent_files = config.get("recent_files", [])

        # Always start here
        self.root_path = self.ROOT_PATH.replace("\\", "/")
        self.current_path = self.DEFAULT_STARTUP_PATH.replace("\\", "/")

        self.ui.lineEdit_current_path.setText(self.current_path)

        # Setup FileSystemModel
        self.fs_model = QtWidgets.QFileSystemModel()
        self.fs_model.setRootPath(self.root_path)
        self.fs_model.setFilter(QtCore.QDir.NoDotAndDotDot | QtCore.QDir.AllEntries)

        self.proxy = CleanExtFilter()
        self.proxy.setSourceModel(self.fs_model)

        self.ui.tableView_files.setModel(self.proxy)
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

        # INITIAL LOAD
        self.sync_columns_from_path()
        self.update_file_list()

        # Context menu
        self.ui.tableView_files.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.tableView_files.customContextMenuRequested.connect(
            self.open_context_menu
        )
        self.ui.tableView_files.setColumnHidden(2, True)

        # Recent
        self.build_setting_menu()

    # ------------------------------------------------------------
    # CONFIG
    # ------------------------------------------------------------
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
        self.more_menu = QtWidgets.QMenu(self)

        self.recent_menu = QtWidgets.QMenu("Recent Opened...", self)

        for p in self.recent_files:
            act = QAction(p, self)
            act.triggered.connect(lambda c, path=p: self.open_recent(path))
            self.recent_menu.addAction(act)

        self.add_menu = QtWidgets.QMenu("Create New...", self)
        create_folder = QAction("Folder", self)
        create_folder.triggered.connect(lambda: self.create_new("folder"))
        self.add_menu.addAction(create_folder)
        create_maya = QAction("Maya", self)
        create_maya.triggered.connect(lambda: self.create_new("maya"))
        self.add_menu.addAction(create_maya)
        create_blender = QAction("Blender", self)
        create_blender.triggered.connect(lambda: self.create_new("blender"))
        self.add_menu.addAction(create_blender)
        self.more_menu.addMenu(self.add_menu)
        self.more_menu.addSeparator()


        open_google_sheet = QAction("Open Google Sheet", self)
        open_google_sheet.triggered.connect(self.open_google_sheet)
        self.more_menu.addAction(open_google_sheet)

        open_google_drive = QAction("Open Google Drive", self)
        open_google_drive.triggered.connect(self.open_google_drive_app)
        self.more_menu.addAction(open_google_drive)

        self.more_menu.addSeparator()
        self.more_menu.addMenu(self.recent_menu)

        self.more_menu.addSeparator()
        reload_action = QAction("Reload", self)
        reload_action.triggered.connect(self.reload)
        self.more_menu.addAction(reload_action)


    def open_current_path(self):
        self.show_popup("กำลังเปิดโฟลเดอร์", duration=2000)

        folder = self.current_path
        if os.path.isdir(folder):
            folder = os.path.normpath(folder)
            subprocess.Popen(f'explorer "{folder}"')

    def show_more_menu(self):
        btn = self.ui.pushButton_setting
        pos = btn.mapToGlobal(btn.rect().bottomLeft())
        self.more_menu.exec(pos)

    def open_recent(self, path):
        folder = os.path.dirname(path)
        if os.path.isdir(folder):
            self.current_path = folder.replace("\\", "/")
            self.ui.lineEdit_current_path.setText(self.current_path)
            self.sync_columns_from_path()
            self.update_file_list()

    # ------------------------------------------------------------
    # SIGNALS
    # ------------------------------------------------------------
    def connect_signals(self):
        for i, lw in enumerate(self.columns):
            lw.currentItemChanged.connect(partial(self.on_column_clicked, i))

        for i, le in enumerate(self.search_boxes):
            le.textChanged.connect(partial(self.filter_column, i))

        self.ui.lineEdit_current_path.editingFinished.connect(self.on_path_entered)
        self.ui.pushButton_go_back.clicked.connect(self.go_back)

        self.ui.pushButton_copy_current_path.clicked.connect(self.copy_current_path)

        self.ui.lineEdit_search_file.textChanged.connect(self.search_current_folder)
        self.ui.tableView_files.doubleClicked.connect(self.on_file_double_clicked)

        self.ui.pushButton_open_current_path.clicked.connect(self.open_current_path)
        # FIX: Show menu manually
        self.ui.pushButton_setting.clicked.connect(self.show_more_menu)

    # ------------------------------------------------------------
    # DIRECTORY LOADED
    # ------------------------------------------------------------
    def on_directory_loaded(self, path):
        h = self.ui.tableView_files.horizontalHeader()
        h.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        # h.resizeSection(0, 550)

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

    def sync_columns_from_path(self):
        """Rebuild ALL columns entirely from current_path."""
        for lw in self.columns:
            lw.blockSignals(True)
            lw.clear()

        try:
            rel = os.path.relpath(self.current_path, self.root_path)
            parts = [] if rel == "." else rel.split(os.sep)

            self.load_column_items(0, self.root_path)
            p = self.root_path

            for level, name in enumerate(parts):
                if level >= len(self.columns):
                    break

                lw = self.columns[level]

                items = lw.findItems(name, Qt.MatchExactly)
                if items:
                    lw.setCurrentItem(items[0])

                p = os.path.join(p, name)

                next_level = level + 1
                if next_level < len(self.columns):
                    self.load_column_items(next_level, p)

        finally:
            for lw in self.columns:
                lw.blockSignals(False)

    def on_column_clicked(self, level, current, previous):
        if not current:
            return

        p = self.root_path
        for i in range(level + 1):
            it = self.columns[i].currentItem()
            if it:
                p = os.path.join(p, it.text())

        self.current_path = p.replace("\\", "/")
        self.ui.lineEdit_current_path.setText(self.current_path)

        self.sync_columns_from_path()
        self.update_file_list()

    def filter_column(self, level, text):
        lw = self.columns[level]
        txt = text.lower()
        for i in range(lw.count()):
            item = lw.item(i)
            item.setHidden(txt not in item.text().lower())

    # ------------------------------------------------------------
    # PATH ENTRY + BACK
    # ------------------------------------------------------------
    def on_path_entered(self):
        path = self.ui.lineEdit_current_path.text().strip()
        path = os.path.normpath(path).replace("\\", "/")

        if not os.path.isdir(path):
            QtWidgets.QMessageBox.warning(
                self, "Error", f"Path does not exist:\n{path}"
            )
            return

        self.current_path = path
        self.sync_columns_from_path()
        self.update_file_list()

    def go_back(self):
        if os.path.abspath(self.current_path) == os.path.abspath(self.root_path):
            return

        parent = os.path.dirname(self.current_path).replace("\\", "/")
        self.current_path = parent
        self.ui.lineEdit_current_path.setText(parent)

        self.sync_columns_from_path()
        self.update_file_list()

    # ------------------------------------------------------------
    # FILE TABLE
    # ------------------------------------------------------------
    def update_file_list(self):
        if not os.path.isdir(self.current_path):
            return

        # idx = self.fs_model.index(self.current_path)
        # self.ui.tableView_files.setRootIndex(idx)

        idx = self.fs_model.index(self.current_path)

        proxy_idx = self.proxy.mapFromSource(idx)
        self.ui.tableView_files.setRootIndex(proxy_idx)

        h = self.ui.tableView_files.horizontalHeader()
        h.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        h.setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        h.setSectionResizeMode(3, QtWidgets.QHeaderView.Fixed)

        h.resizeSection(1, 40)
        h.resizeSection(3, 150)
        h.setDefaultSectionSize(5)

        tv = self.ui.tableView_files
        tv.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        tv.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        tv.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        tv.verticalHeader().hide()
        tv.verticalHeader().setDefaultSectionSize(10)
        tv.setIconSize(QtCore.QSize(10, 10))

    # ------------------------------------------------------------
    # FILE SEARCH
    # ------------------------------------------------------------
    def search_current_folder(self, text):
        txt = text.lower()
        parent_index = self.fs_model.index(self.current_path)
        row_count = self.fs_model.rowCount(parent_index)

        for row in range(row_count):
            idx = self.fs_model.index(row, 0, parent_index)
            name = self.fs_model.fileName(idx).lower()
            self.ui.tableView_files.setRowHidden(row, txt not in name)

    # ------------------------------------------------------------
    # DOUBLE CLICK
    # ------------------------------------------------------------
    def on_file_double_clicked(self, index):

        # map proxy -> source
        src_index = self.proxy.mapToSource(index.sibling(index.row(), 0))
        path = self.fs_model.filePath(src_index)

        if os.path.isdir(path):
            self.current_path = path.replace("\\", "/")
            self.ui.lineEdit_current_path.setText(self.current_path)
            self.sync_columns_from_path()
            self.update_file_list()
            return

        self.show_popup(f"Opening File : {os.path.basename(path)}")

        try:
            os.startfile(path)
            self.add_recent_file(path)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))

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
        act_copy = menu.addAction("Copy File Path")
        act_delete = menu.addAction("Delete")
        act_rename = menu.addAction("Rename")

        act = menu.exec_(self.ui.tableView_files.mapToGlobal(pos))

        if act == act_copy:
            QtWidgets.QApplication.clipboard().setText(file_path)
        elif act == act_delete:
            self.delete_with_confirm(file_path)
        elif act == act_rename:
            self.rename_dialog(file_path)

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
        QtWidgets.QApplication.clipboard().setText(self.current_path)
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
        default_name = os.path.basename(self.current_path.rstrip("/"))

        # Ask user for name
        name, ok = QtWidgets.QInputDialog.getText(
            self,
            f"Create New {type.title()}",
            "Name:",
            text=default_name
        )

        if not ok or not name.strip():
            return

        # -----------------------------------------------------
        # CREATE FOLDER
        # -----------------------------------------------------
        if type == "folder":
            new_path = os.path.join(self.current_path, name)
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
            new_file = os.path.join(self.current_path, f"{name}.ma")
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
            new_file = os.path.join(self.current_path, f"{name}.blend")
            try:
                import shutil
                shutil.copy(self.BLENDER_TEMPLATE, new_file)
                self.show_popup(f"สร้าง Blender file: {name}.blend", duration=1500)
                self.update_file_list()
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", str(e))
            return


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


class CleanExtFilter(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Allow only correct extensions with no extra characters
        pattern = r".*\.(ma|mb|blend|fbx|obj|avi|mp4|jpg|png|mov|prproj|mp3)$"
        regex = QRegularExpression(pattern, QRegularExpression.CaseInsensitiveOption)

        self.setFilterRegularExpression(regex)

    def filterAcceptsRow(self, source_row, source_parent):
        index = self.sourceModel().index(source_row, 0, source_parent)
        if not index.isValid():
            return False

        # ✔ Allow directories always (VERY IMPORTANT)
        if self.sourceModel().isDir(index):
            return True

        filename = self.sourceModel().data(index)
        return self.filterRegularExpression().match(filename).hasMatch()
