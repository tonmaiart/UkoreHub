from tmlib.core import (
    Scene,
    Utility,
    Transform,
    Connection,
    SkinWeight,
    Controller,
    File,
    QuickData,
    BlendShape,
)
from tmlib.module.PySide import QtCore, QtGui, QtWidgets, QAction

import os, importlib, webbrowser, inspect, configparser, re, json
from tmlib.ui.interface_template import ToolkitWindow
import maya.cmds as cmds
import subprocess
import shutil

from UkoreMaya.core import template_ui
from ShotSplitter import function

importlib.reload(function)


class MainWindow(ToolkitWindow):
    def __init__(self):
        # Set-up Interface
        super(MainWindow, self).__init__(os.path.basename(os.path.dirname(__file__)))

        self.header_labels = ["Shot", "StartFrame", "EndFrame"]

        self.reload_table_data()

        self.connect_signals()
        self.current_shot_name = ""

        cmds.scriptJob(
            event=["NewSceneOpened", self.reload_table_data],
            parent=self.objectName(),
        )
        cmds.scriptJob(
            event=["SceneOpened", self.reload_table_data],
            parent=self.objectName(),
        )
        cmds.scriptJob(
            event=["SceneSaved", self.save_before_reload],
            parent=self.objectName(),
        )

        header = self.ui.tableView.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)

    def save_before_reload(self):

        print("Save before relaod : ", cmds.file(q=1, sn=True))
        self.save_table_to_json()
        self.reload_table_data()

    def connect_signals(self):
        self.ui.tableView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.tableView.customContextMenuRequested.connect(self.show_context_menu)

        self.ui.pushButton_split_to_file.clicked.connect(self.split_shot)
        self.ui.pushButton_reload.clicked.connect(self.reload_table_data)

    def reload_table_data(self):
        print("# Reload Saved Data #")
        self.initalize_table_view()
        self.load_json_to_tableview()

        self.load_current_shot_label()

    def load_current_shot_label(self):

        current_file_path = cmds.file(q=True, sn=True)
        if not current_file_path:
            self.current_shot_name = ""
            return
        self.current_shot_name = (
            os.path.basename(current_file_path).split(".")[0].split("_")[0]
        )

        self.ui.lineEdit_current_shot.setText(self.current_shot_name)

    def initalize_table_view(self):
        self.base_model = QtGui.QStandardItemModel()
        self.table_model = QtCore.QSortFilterProxyModel()
        self.table_model.setSourceModel(self.base_model)
        self.base_model.dataChanged.connect(self.save_table_to_json)

        # =========================
        # setup model
        # =========================
        self.ui.tableView.setModel(self.table_model)
        self.ui.tableView.setSortingEnabled(True)
        self.ui.tableView.horizontalHeader().sectionClicked.connect(
            self.ui.tableView.sortByColumn
        )
        self.table_model.sort(0, QtCore.Qt.AscendingOrder)
        self.base_model.setHorizontalHeaderLabels(self.header_labels)

    def launch_file_explorer_linux(self, target_path="."):
        """
        เปิด File Explorer (GUI) ใน Linux ที่ Path ที่กำหนด

        Args:
            target_path (str): Path ของ Folder ที่ต้องการเปิด หากเป็น "." จะเปิดใน Directory ปัจจุบัน
        """

        # 1. ตรวจสอบและทำให้ Path เป็นแบบ Absolute Path ที่ถูกต้อง
        target_path = os.path.abspath(target_path)

        # 2. กำหนดคำสั่ง File Explorer ที่แตกต่างกันไปตาม Desktop Environment
        # คำสั่ง 'xdg-open' เป็นวิธีที่เป็นมาตรฐานและแนะนำที่สุด
        # เพราะมันจะเรียกใช้โปรแกรมที่ User ตั้งค่าไว้สำหรับเปิด Folder โดยอัตโนมัติ

        commands = [
            "xdg-open",  # มาตรฐานทั่วไป (แนะนำที่สุด)
            "nautilus",  # Gnome / Ubuntu
            "dolphin",  # KDE
            "thunar",  # XFCE
            "pcmanfm",  # LXDE
        ]

        # 3. ลองรันคำสั่งทีละตัว
        for command in commands:
            try:
                # รันคำสั่ง File Explorer โดยให้ Process ทำงานเบื้องหลัง
                # (stdout=subprocess.DEVNULL ทำให้ไม่แสดง Output ของ Shell ในคอนโซล)
                subprocess.Popen(
                    [command, target_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                print(
                    f"✅ เปิด File Explorer โดยใช้คำสั่ง: {command} ที่ Path: {target_path}"
                )
                return True
            except FileNotFoundError:
                # หากคำสั่งนั้นไม่พบ (เช่น User ไม่ได้ติดตั้ง Dolphin) ให้ลองคำสั่งถัดไป
                continue
            except Exception as e:
                print(f"❌ Error ในการรันคำสั่ง {command}: {e}")
                return False

        # หากรันคำสั่งทั้งหมดแล้วไม่สำเร็จ
        print("❌ ไม่พบคำสั่ง File Explorer ที่รองรับในระบบนี้")
        return False

    def split_shot(self):
        # Save Table and get base file path
        base_file_path = cmds.file(q=1, sn=True)
        if not base_file_path:
            cmds.confirmDialog(m="Current File Must Saved", button=["Ok"])
            return

        list_target_data = self.get_current_selected_data()

        if not list_target_data:
            list_target_data = self.get_current_table_data()

        if not list_target_data:
            cmds.confirmDialog(m="Not found any shot to split.", button=["Ok"])
            return

        # get deploy directory
        deploy_dir = os.path.join(os.path.dirname(base_file_path), "SplitResult")

        # get current data text
        text = ""
        for data in list_target_data:
            text += "- " + data["Shot"] + "\n"

        text += "The Path will deploy to directory : {}".format(deploy_dir)

        #
        result = cmds.confirmDialog(
            title="Confirm to Split Shot",
            message="Split File for :\n {}".format(text),
            button=["Yes", "No"],
            defaultButton="Yes",
            cancelButton="No",
            dismissString="No",
        )
        if result == "No":
            return

        # Check is override current shot
        if self.current_shot_name in [shot["Shot"] for shot in list_target_data]:
            result = cmds.confirmDialog(
                title="Confirm to overwrite current file",
                message="ในรายการ Split Shot มีไฟล์ปัจจุบันของคุณอยู่แล้ว {}, ต้องการที่จะแทนที่ไฟล์ปัจจุบันนี้ด้วย Time Range ใหม่เลยไหม? ถ้าไม่ก็จะทำการสร้างไฟล์แยกตามแบบเดิม".format(
                    self.current_shot_name
                ),
                button=[
                    "Overwrite Current",
                    "Split to New File",
                    "Cancel",
                ],
                defaultButton="Overwrite Current",
                cancelButton="Cancel",
                dismissString="Cancel",
            )

            if result == "Split to New File":
                overwrite_current_file = False
            elif result == "Overwrite Current":
                overwrite_current_file = True
            else:
                return
        else:
            overwrite_current_file = False

        # make sure base file is saved
        os.makedirs(deploy_dir, exist_ok=True)

        cmds.file(s=True)

        if not list_target_data:
            cmds.confirmDialog(title="No Data", message="No shots to split")
            return

        progress_unit = 100.0 / len(list_target_data) / 5.0
        amount = 0.0

        cmds.progressWindow(
            title="Creating New Shot File",
            progress=amount,
            status="Preparing : {}%".format(int(amount)),
            isInterruptable=True,
        )

        # ===============================
        # Create New .ma ,json, wav file
        # ===============================
        dict_new_ma_file_path = {}
        dict_new_keyframe = {}
        dict_old_keyframe = {}

        for value in list_target_data:
            shot = value["Shot"]
            start_frame = int(value["StartFrame"])
            end_frame = int(value["EndFrame"])
            frame_count = end_frame - start_frame
            new_start_frame = 1001
            new_end_frame = (end_frame - start_frame) + 1001

            new_dir_path = os.path.join(deploy_dir, shot)
            os.makedirs(new_dir_path, exist_ok=True)

            open_ma_file_path = os.path.join(new_dir_path, "{}.ma".format(shot))

            dict_old_keyframe[shot] = (start_frame, end_frame)
            dict_new_keyframe[shot] = (new_start_frame, new_end_frame)

            if shot == self.current_shot_name and overwrite_current_file:
                open_ma_file_path = base_file_path
            else:
                new_json_file_path = os.path.join(new_dir_path, "{}.json".format(shot))
                new_wav_file_path = os.path.join(new_dir_path, "{}.wav".format(shot))

                # ==================================
                # Create New .json
                # ==================================

                value_new_file = value
                value_new_file["StartFrame"] = new_start_frame
                value_new_file["EndFrame"] = new_end_frame

                try:
                    with open(new_json_file_path, "w") as f:
                        json.dump([value_new_file], f, indent=4)
                    print(f"✅ Data saved successfully to: {new_json_file_path}")
                except Exception as e:
                    print(f"❌ Error saving data: {e}")

                # ==================================
                # Create New .ma
                # ==================================

                amount += progress_unit
                cmds.progressWindow(
                    edit=True,
                    progress=amount,
                    status=f"Opening File {shot}.ma : {int(amount)}%",
                )

                # copy then open the copied file
                shutil.copy2(base_file_path, open_ma_file_path)

            dict_new_ma_file_path[value["Shot"]] = open_ma_file_path

        for value in list_target_data:
            # Prepare variables
            shot = value["Shot"]

            start_frame, end_frame = dict_old_keyframe[shot]
            new_start_frame, new_end_frame = dict_new_keyframe[shot]
            open_ma_file_path = dict_new_ma_file_path[shot]

            # Open Target File
            cmds.file(open_ma_file_path, open=True, force=True)

            # ==================================
            # Emphasize keyframes (add keys at new start/end if missing)
            # ==================================

            amount += progress_unit
            cmds.progressWindow(
                edit=True,
                progress=amount,
                status=f"Emphasize Keyframe {shot}.ma : {int(amount)}%",
            )

            function.emphazise_keyframes(
                new_start_frame=start_frame, new_end_frame=end_frame
            )

            # ==================================
            # Offset all keyframes (edit animCurve nodes directly)
            # ==================================
            amount += progress_unit
            cmds.progressWindow(
                edit=True,
                progress=amount,
                status=f"Offset All Keyframe {shot}.ma : {int(amount)}%",
            )

            time_shift = 1001 - start_frame
            function.offset_all_keyframes(time_shift=time_shift)

            # ==================================
            # Set time ranges
            # ==================================

            function.set_time_range(
                start_frame=new_start_frame, end_frame=new_end_frame
            )

            # ==================================
            # Trim before/after
            # ==================================

            amount += progress_unit
            cmds.progressWindow(
                edit=True,
                progress=amount,
                status=f"Trimming Out Range Keyframe {shot}.ma : {int(amount)}%",
            )

            function.trim_all_keyframes(
                start_frame=new_start_frame, end_frame=new_end_frame
            )

            # ==================================
            # reset audio
            # ==================================

            function.set_audio_ranges(
                t_start=new_start_frame,
                t_end=new_end_frame,
                i_start=start_frame,
                i_end=end_frame,
            )

            # ==================================
            # Save file
            # ==================================

            amount += progress_unit
            cmds.progressWindow(
                edit=True,
                progress=amount,
                status=f"Saving File {shot}.ma : {int(amount)}%",
            )
            cmds.file(s=True)

        cmds.progressWindow(endProgress=1)
        self.reload_table_data()

        print("------------- # Split Shot Successful # -------------")
        print("# Deploy Path : {}".format(deploy_dir))
        for value in list_target_data:
            shot = value["Shot"]

            new_path = dict_new_ma_file_path[shot]
            start, end = dict_old_keyframe[shot]
            start_new, end_new = dict_new_keyframe[shot]

            print(
                "- Shot : {} ,from ({},{}) to ({},{}) to path : {}".format(
                    shot, start, end, start_new, end_new, new_path
                )
            )
        result = cmds.confirmDialog(
            title="Split Shot Success!",
            message="Split Shot Success! Please Check the directory : {}".format(
                deploy_dir,
            ),
            button=["Ok", "Open Folder"],
        )

        if result == "Open Folder":
            pass
            # self.launch_file_explorer_linux(deploy_dir)

    def do_each_shot(self):
        pass
        # ====================
        # Prepare Time Range
        # ====================

    def increment_string_number(self, s, inc=10):
        match = re.search(r"(\d+)", s)
        if not match:
            return s

        num_str = match.group(1)
        num_int = int(num_str)
        length = len(num_str)

        new_num = num_int + inc
        new_num_str = f"{new_num:0{length}d}"

        # แทนที่ตัวเลขแรกที่พบด้วยค่าใหม่
        return re.sub(r"\d+", new_num_str, s, count=1)

    def add_shot(self):
        # check exist shot
        all_data = self.get_current_table_data()
        list_recent_shot = [i["Shot"] for i in all_data]
        list_recent_shot.sort()
        if not list_recent_shot:
            if self.current_shot_name:
                shot_name = self.current_shot_name
            else:
                shot_name = "XXX010"
        else:
            shot_name = list_recent_shot[-1]
            shot_name = self.increment_string_number(shot_name, inc=10)

        print("Recent Shot : ", shot_name)
        row = [
            QtGui.QStandardItem(shot_name),
            QtGui.QStandardItem("1"),
            QtGui.QStandardItem("50"),
        ]
        self.base_model.appendRow(row)

        self.save_table_to_json()

    # def split_shot(self):

    def get_current_selected_data(self):
        selected_indexes = self.ui.tableView.selectionModel().selectedIndexes()

        if not selected_indexes:
            return

        # normalize row
        selected_rows = set(index.row() for index in selected_indexes)

        TARGET_COLUMN_INDICES = [0, 1, 2]  # คอลัมน์ที่ 3 (Index 2)
        selected_data = []

        output_data = []

        for row_index in selected_rows:
            row_dict = {}

            # วนลูปดึงค่าตาม Index ที่ต้องการ
            for i, col_index in enumerate(TARGET_COLUMN_INDICES):

                target_index = self.table_model.index(row_index, col_index)
                value = self.table_model.data(target_index, QtCore.Qt.DisplayRole)
                header_name = self.header_labels[i]

                row_dict[header_name] = value

            output_data.append(row_dict)

        return output_data

    def remove_shot(self):
        selected_indexes = self.ui.tableView.selectionModel().selectedIndexes()

        if not selected_indexes:
            return

        print(selected_indexes)

        # 2. ค้นหาหมายเลขแถว (Row Number) ที่ไม่ซ้ำกันจากรายการ Index
        # เนื่องจากเราต้องการลบทั้งแถว จึงสนใจแค่หมายเลขแถวเท่านั้น
        rows_to_delete = set()
        for index in selected_indexes:
            rows_to_delete.add(index.row())

        print(rows_to_delete)

        # 3. เรียงลำดับหมายเลขแถวจากมากไปน้อย (Descending Order)
        # นี่คือขั้นตอนที่สำคัญมาก! เมื่อลบแถวแล้ว Index ของแถวที่เหลือจะเลื่อนขึ้น
        # เราต้องลบจากแถวหมายเลขมากที่สุดก่อน (ล่างสุด) เพื่อไม่ให้ Index ผิดพลาด
        sorted_rows = sorted(list(rows_to_delete), reverse=True)

        # 4. ลบแถวออกจาก Model
        num_deleted = 0
        for row in sorted_rows:
            # removeRow(row_index, parent_index)
            self.table_model.removeRow(row)
            num_deleted += 1

        self.save_table_to_json()

    def show_context_menu(self, position):
        """
        เมธอดนี้จะถูกเรียกเมื่อมีการคลิกขวาในตาราง
        """

        # 1. สร้าง Menu Object
        context_menu = QtWidgets.QMenu(self)
        context_menu.setStyleSheet(template_ui.get_menu_stylesheet())
        # 2. ตรวจสอบว่าคลิกถูก Cell หรือคลิกถูกพื้นที่ว่าง
        # indexAt(position) จะคืนค่า QModelIndex ที่ตำแหน่งนั้นๆ
        index = self.ui.tableView.indexAt(position)

        # 3. สร้าง Action ต่างๆ ในเมนู

        # Action 1: Add Row (มักจะให้เพิ่มได้ไม่ว่าจะคลิกที่ไหน)
        add_action = context_menu.addAction("สร้าง Shot ใหม่")
        context_menu.addSeparator()

        increment_five_action = context_menu.addAction("เพิ่ม 5")

        decrease_five_action = context_menu.addAction("ลด 5")

        context_menu.addSeparator()

        remove_action = context_menu.addAction("ลบ Shot ที่เลือก")

        # 4. ตั้งค่าเงื่อนไขการเปิด/ปิด Action
        # ถ้าไม่มีแถวถูกเลือก ให้ปิดการใช้งานปุ่ม Remove
        if not self.ui.tableView.selectionModel().selectedIndexes():
            remove_action.setEnabled(False)

        selected_action = context_menu.exec_(self.ui.tableView.mapToGlobal(position))

        # 6. จัดการการกระทำเมื่อผู้ใช้เลือก Action
        if selected_action == add_action:
            self.add_shot()

        elif selected_action == remove_action:
            self.remove_shot()

    def get_current_table_data(self):
        row_count = self.base_model.rowCount()
        col_count = self.base_model.columnCount()
        data_to_save = []

        # 1. วนลูปผ่านทุกแถวใน Model
        for row in range(row_count):
            row_data = {}
            for col in range(col_count):
                item = self.base_model.item(row, col)
                if item:
                    # ดึงข้อมูลที่แสดงผล (DisplayRole)
                    header = self.base_model.headerData(col, QtCore.Qt.Horizontal)
                    row_data[header] = item.data(QtCore.Qt.DisplayRole)

            data_to_save.append(row_data)

        return data_to_save

    def save_table_to_json(self):
        # if current file not save will return
        file_path = cmds.file(q=1, sn=True)

        if not file_path:
            cmds.confirmDialog(m="Please Save This file before")
            return

        data_to_save = self.get_current_table_data()
        scene_name = os.path.basename(file_path).split(".")[0].split("_")[0]
        json_path = os.path.join(os.path.dirname(file_path), scene_name + ".json")

        try:
            with open(json_path, "w") as f:
                json.dump(data_to_save, f, indent=4)
            print(f"# Data saved successfully to: {json_path}")
        except Exception as e:
            print(f"# Error saving data: {e}")

    def load_json_to_tableview(self):
        ############################
        # Auto Load Json Saved File
        ############################

        scene_path = cmds.file(q=1, sn=True)

        if not scene_path:
            return

        scene_name = os.path.basename(scene_path).split(".")[0].split("_")[0]
        json_path = os.path.join(os.path.dirname(scene_path), scene_name + ".json")

        if os.path.exists(json_path):
            loaded_data = File.load_json_file_to_dict(file_path=json_path)

            try:
                for row_dict in loaded_data:
                    row_items = []
                    for header in self.header_labels:
                        value = row_dict.get(header, "")
                        item = QtGui.QStandardItem(str(value))

                        # Optional: หากคุณต้องการให้คอลัมน์ Translate X สามารถเรียงได้
                        if header == "Translate X":
                            try:
                                float_val = float(value)
                                item.setData(float_val, QtCore.Qt.UserRole)
                            except ValueError:
                                pass

                        row_items.append(item)

                    self.base_model.appendRow(row_items)
            except Exception as e:
                raise Exception(e)
