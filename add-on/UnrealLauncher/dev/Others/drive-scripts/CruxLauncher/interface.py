# =============================
# PART 1 / 3
# Imports + Init + Menu + Signals + Helpers
# =============================

import os
import json
import logging

from PySide6 import QtCore, QtWidgets, QtUiTools
from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QColor, QAction
from PySide6.QtWidgets import QHeaderView

import pyperclip

from Crux.common import Project
from CruxLauncher.custom_pyside import JobItemModel, PopupMessage

# ===============================================================
# LOGGING
# ===============================================================
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ===============================================================
# MAIN WINDOW
# ===============================================================


class MainWindow(QtWidgets.QMainWindow):
    """
    Main Crux Launcher Window.
    Handles initialization, UI loading, and basic job state storage.
    """

    def __init__(self):
        super().__init__()

        # -----------------------------
        # Load UI
        # -----------------------------
        ui_path = os.path.join(os.path.dirname(__file__), "ui.ui")
        file = QtCore.QFile(ui_path)
        if file.open(QtCore.QFile.ReadOnly):
            loader = QtUiTools.QUiLoader()
            self.ui = loader.load(file)
            file.close()
        else:
            log.error(f"ไม่สามารถเปิดไฟล์ UI ได้: {ui_path}")
            return

        self.setCentralWidget(self.ui)
        self.setWindowTitle("Crux Launcher")

        # -----------------------------
        # Runtime
        # -----------------------------
        self.current_job_data = {}
        self.proj = Project.Project()
        self.jobs_data = self.proj.get_job_data_dict()
        self.job_model = None

        # -----------------------------
        # Init systems
        # -----------------------------
        self.setup_textbrowser()
        self.set_up_menu_button()
        self.connect_signals()
        self.reload_widget()

    # ===============================================================
    # MENU SETUP
    # ===============================================================
    def set_up_menu_button(self):
        """Create and attach dropdown menu to the settings button."""

        self.menu_setting = QtWidgets.QMenu(self)
        self.ui.pushButton_setting.setMenu(self.menu_setting)
        # Open Google Doc
        action_google_doc = QAction("Open Current Job Document", self)
        action_google_doc.triggered.connect(self.open_google_document)
        self.menu_setting.addAction(action_google_doc)

        # Separator
        sep = QAction("--- Project ---", self)
        sep.setEnabled(False)
        self.menu_setting.addAction(sep)

        # Edit Google Sheet
        action_edit_sheet = QAction("Edit Google Sheet", self)
        action_edit_sheet.triggered.connect(lambda x: self.proj.launch_google_sheet())
        self.menu_setting.addAction(action_edit_sheet)

        # Reload all
        action_reload = QAction("Pull Sheet Data", self)
        action_reload.triggered.connect(self.reload_data_and_ui)
        self.menu_setting.addAction(action_reload)

        # Set up job type
        self.ui.listWidget_job_type_filter.addItems(
            job_type.capitalize() for job_type in self.proj.proj_workspace_config.keys()
        )
        if self.ui.listWidget_job_type_filter.count() > 0:
            self.ui.listWidget_job_type_filter.setCurrentRow(0)

    # ===============================================================
    # SIGNAL CONNECTION
    # ===============================================================
    def connect_signals(self):
        """Connect UI buttons and widgets to their logic functions."""

        self.ui.checkBox_advance_detail_mode.clicked.connect(self.update_detail_view)
        self.ui.lineEdit_search_job.textChanged.connect(
            self.update_table_view_job_filter
        )
        self.ui.pushButton_job_workspace_dir.clicked.connect(self.open_workspace_folder)
        # self.ui.checkBox_show_only_workable.clicked.connect(
        #     self.update_table_view_job_filter
        # )
        self.ui.pushButton_copy_workspace_path.clicked.connect(self.copy_workspace_path)
        self.ui.listWidget_job_type_filter.currentTextChanged.connect(
            self.update_table_view_job_filter
        )

    # ===============================================================
    # HELPERS
    # ===============================================================

    def copy_workspace_path(self):
        """Copy workspace folder path to clipboard and show popup."""
        self.show_popup("ก้อปปี้ Path โฟลเดอร์งาน")
        pyperclip.copy(self.current_job_data.get("JobDirectory"))

    def get_list_widget_selected(self, widget):
        item = widget.currentItem()
        return item.text() if item else None

    def set_current_item_by_name(self, list_widget, name):
        items = list_widget.findItems(name, Qt.MatchExactly)
        if items:
            list_widget.setCurrentItem(items[0])

    # =============================
    # PART 2 / 3
    # Table View + Filters + Task Bar
    # =============================

    # ===============================================================
    # JOB TABLE SETUP
    # ===============================================================
    def update_table_view_job(self):
        """Populate job table with all job entries from project data."""

        self.job_model = JobItemModel()
        self.job_model.setHorizontalHeaderLabels(
            [
                "JobName",
                "JobType",
                "JobTask",
                "PublishStatus",
                "Artist",
                "JobNote",
                "JobRequiredCode",
            ]
        )

        for list_job in self.jobs_data.values():
            for job in list_job:
                self.job_model.appendRow(
                    [
                        QStandardItem(job["JobName"]),
                        QStandardItem(job["JobType"]),
                        QStandardItem(job["JobTask"]),
                        QStandardItem(job["JobPublishStatus"]),
                        QStandardItem(job["Artist"]),
                        QStandardItem(job["JobNote"]),
                        QStandardItem(",".join(job["JobRequiredCode"])),
                    ]
                )

        self.ui.tableView_jobs.setModel(self.job_model.proxy_model)
        self.selection_model = self.ui.tableView_jobs.selectionModel()
        self.selection_model.selectionChanged.connect(
            self.on_selected_table_view_changed
        )

        header = self.ui.tableView_jobs.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.ui.tableView_jobs.verticalHeader().hide()

    def on_selected_table_view_changed(self):
        """Triggered when table row selection changes."""
        self.update_current_job_data_from_model()
        self.update_job_widget()

    def update_current_job_data_from_model(self):
        """Read currently selected row from the job table and update stored job info."""
        selected = self.selection_model.selectedIndexes()
        if not selected:
            self.current_job_data = None
            return

        proxy = self.job_model.proxy_model
        source_index = proxy.mapToSource(selected[0])
        row = source_index.row()

        job_name = self.job_model.data(self.job_model.index(row, 0))
        job_type = self.job_model.data(self.job_model.index(row, 1))
        job_task = self.job_model.data(self.job_model.index(row, 2))

        for job in self.jobs_data.get(job_type, []):
            if (
                job["JobName"] == job_name
                and job["JobType"] == job_type
                and job["JobTask"] == job_task
            ):
                self.current_job_data = job
                return

        self.current_job_data = None

    # ===============================================================
    # FILTERING
    # ===============================================================
    def update_table_view_job_filter(self):
        """Apply job name search + workable filter to the job list."""

        search_text = self.ui.lineEdit_search_job.text() or None
        # publish_status = (
        #     ["NotStart", "Working"]
        #     if self.ui.checkBox_show_only_workable.isChecked()
        #     else None
        # )

        if self.job_model:
            self.job_model.setFilter(
                jobName=search_text,
                jobType=(
                    self.ui.listWidget_job_type_filter.currentItem().text()
                    if self.ui.listWidget_job_type_filter.currentItem()
                    else None
                ),
                jobStatus=None,
                publishStatus=None,
                artist=None,
                single_job_task=True,
            )

        if self.job_model:
            self.select_first_row()

    def select_first_row(self):
        """Automatically select first job after filter/search."""
        proxy = self.job_model.proxy_model
        if proxy.rowCount() > 0:
            idx = proxy.index(0, 0)
            self.ui.tableView_jobs.selectRow(idx.row())
            self.ui.tableView_jobs.setCurrentIndex(idx)

    def on_list_widget_job_task_change(self):
        """Triggered when clicking a task in task bar."""
        item = self.ui.listWidget_job_task.currentItem()
        if not item:
            return

        self.update_current_job_data_from_custom(
            self.current_job_data.get("JobName", ""),
            self.current_job_data.get("JobType", ""),
            item.text(),
        )
        self.update_job_widget()

    def update_current_job_data_from_custom(self, job_name, job_type, job_task):
        """Update current job info using direct jobName/jobType/jobTask match."""
        for job in self.jobs_data.get(job_type, []):
            if (
                job["JobName"] == job_name
                and job["JobType"] == job_type
                and job["JobTask"] == job_task
            ):
                self.current_job_data = job
                return

        self.current_job_data = None

    # =============================
    # PART 3 / 3
    # Job Info Panel + Widget Update + Folder Actions + Reload System + Worker
    # =============================

    # ===============================================================
    # JOB INFO PANEL
    # ===============================================================
    def on_anchor_clicked(self, url):
        url_str = url.toString()
        parts = url_str.split("/")

        # ========== Clicked publish status of requirement ==========
        if url_str.startswith("crux://reqpub/"):
            req_job_name, req_job_type, req_job_task = parts[-3:]
            self.open_publish_for_task(req_job_name, req_job_type, req_job_task)
            return

        # ========== Clicked WIP folder of requirement ==========
        if url_str.startswith("crux://reqwip/"):
            req_job_name, req_job_type = parts[-2:]
            self.open_workspace_for_job(req_job_name, req_job_type)
            return

        # ========== Clicked task status ==========
        if url_str.startswith("crux://task/"):
            job_name, job_type, job_task = parts[-3:]
            self.open_publish_for_task(job_name, job_type, job_task)
            return

    def open_publish_for_task(self, job_name, job_type, job_task):
        self.show_popup(f"กำลังเปิดโฟลเดอร์ Publish ของ {job_name}-{job_task}")
        self.proj.open_publish_dir(
            job_name=job_name,
            job_type=job_type,
            job_task=job_task,
        )

    def open_workspace_for_job(self, job_name, job_type):
        self.show_popup(f"กำลังเปิดโฟลเดอร์งาน (WIP) ของ {job_name}")
        self.proj.open_workspace_dir(
            job_name=job_name,
            job_type=job_type,
        )

    def setup_textbrowser(self):
        tb = self.ui.textBrowser_description
        tb.setOpenLinks(False)
        tb.anchorClicked.connect(self.on_anchor_clicked)

    def update_job_info(self):
        if not self.current_job_data:
            return

        ui = self.ui
        data = self.current_job_data

        job_name = data.get("JobName", "")
        job_type = data.get("JobType", "")
        note_text = data.get("JobNote", "")

        # ======================================================
        # 🔥 Rebuild JobTasks from ALL tasks in self.jobs_data
        # ======================================================
        all_tasks = {}

        for job_list in self.jobs_data.values():
            for job in job_list:
                if job["JobName"] == job_name and job["JobType"] == job_type:

                    task_name = job["JobTask"]
                    status = job.get("JobPublishStatus", "Unknown")
                    software = job.get("Software", "-")
                    req_code_list = job.get("JobRequiredCode", [])
                    req_status_dict = job.get("JobRequiredStatus", {})

                    all_tasks[task_name] = {
                        "Status": status,
                        "Software": software,
                        "ReqCodes": req_code_list,
                        "ReqStatus": req_status_dict,
                    }

        # ======================================================
        # 🔥 Status Colors
        # ======================================================
        status_color = {
            "Publish": "#00ff2a",
            "Finish": "#00ff2a",
            "Working": "#ffbb00",
            "NotStart": "#ffbb00",
            "Wait": "#ff5757",
        }

        # ======================================================
        # 🔥 Build Task Blocks
        # ======================================================
        task_blocks = ""

        for task_name, info in all_tasks.items():
            status = info["Status"]
            software = info["Software"]
            req_codes = info["ReqCodes"]
            req_status = info["ReqStatus"]

            color = status_color.get(status, "white")

            # -----------------------------
            # Format Requirement List
            # -----------------------------
            # -----------------------------
            # Format Requirement List (CLICKABLE)
            # -----------------------------
            if req_codes:
                req_list_html = "<ul style='font-size:16px; margin-left:20px;'>"

                for code in req_codes:

                    # convert name
                    human_name = self.convert_require_code(code)

                    # requirement status
                    is_done = req_status.get(code, False)
                    status_text = "Published" if is_done else "Not Publish"
                    status_color_text = "#00ff2a" if is_done else "#ff5757"

                    # ===== decode requirement code =====
                    try:
                        req_job_name, req_job_type, req_job_task = code.split("_")
                    except ValueError:
                        req_job_name = req_job_type = req_job_task = "Unknown"

                    # ===== clickable publish folder =====
                    publish_link = (
                        f"<a href='crux://reqpub/{req_job_name}/{req_job_type}/{req_job_task}' "
                        f"style='color:{status_color_text}; text-decoration:none;'>"
                        f"{status_text}</a>"
                    )

                    # ===== clickable WIP folder =====
                    wip_link = (
                        f"<a href='crux://reqwip/{req_job_name}/{req_job_type}' "
                        f"style='color:#7ebaff; text-decoration:none;'>"
                        f"Wip Folder</a>"
                    )

                    # ===== final line =====
                    req_list_html += (
                        "<li>" f"{human_name} : {publish_link} : {wip_link}" "</li>"
                    )

                req_list_html += "</ul>"

            else:
                req_list_html = "<p style='font-size:16px;'>None</p>"

            # -----------------------------
            # Task Block with CLICKABLE STATUS
            # -----------------------------
            status_link = (
                f"<a href='crux://task/{job_name}/{job_type}/{task_name}' "
                f"style='color:{color}; font-weight:bold; text-decoration:none;'>"
                f"{status}</a>"
            )

            task_blocks += (
                "<p style='font-weight:bold;'>░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░</p>"
                f"<p style='color:{color};font-size:25px; font-weight:bold;'>"
                f"{task_name} ({software}) : {status_link}"
                f"</p>"
                f"{req_list_html}"
            )

        # ======================================================
        # 🔥 Final HTML
        # ======================================================
        html = f"""
        <html>
        <body style='font-size:22px;'>
        {task_blocks}
        <br>
        ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
        <br>
        
        {note_text}

                </body>
        </html>
        """

        ui.textBrowser_description.setHtml(html)

    def convert_require_code(self, code):
        # Kafka_Model_Proxy → Kafka - Model : Proxy
        try:
            name, typ, task = code.split("_")
            return f"{name} - {typ} : {task}"
        except:
            return code

    # ===============================================================
    # JOB WIDGET UPDATE
    # ===============================================================
    def update_job_widget(self):
        """Update both job info panel and task bar."""
        self.update_job_info()

    # ===============================================================
    # OPEN FOLDERS / DIRECTORIES
    # ===============================================================
    def open_workspace_folder(self):
        """Open workspace directory of current job."""
        self.show_popup("กำลังเปิดโฟลเดอร์งาน")
        self.proj.open_workspace_dir(
            job_name=self.current_job_data.get("JobName"),
            job_type=self.current_job_data.get("JobType"),
        )

    def open_publish_folder(self):
        """Open publish directory for current job + task."""
        self.show_popup("กำลังเปิดโฟลเดอร์งาน")
        self.proj.open_publish_dir(
            job_name=self.current_job_data.get("JobName"),
            job_type=self.current_job_data.get("JobType"),
            job_task=self.current_job_data.get("JobTask"),
        )

    # ===============================================================
    # POPUP SYSTEM
    # ===============================================================
    def show_popup(self, text, duration=5000):
        """Show a floating popup message inside window."""
        popup = PopupMessage(text, duration, self)
        popup.adjustSize()
        popup.show_centered()

    # ===============================================================
    # RELOAD SYSTEM
    # ===============================================================
    def reload_data_and_ui(self):
        """Reload project data and refresh interface widgets."""

        self.show_popup("กำลัง Reload ข้อมูลภารกิจ...")
        QtWidgets.QApplication.processEvents()

        try:
            self.proj.reload()
            log.info("รีโหลดข้อมูลโปรเจคสำเร็จ")
        except Exception as e:
            log.error(f"Reload โปรเจคล้มเหลว: {e}")

        self.jobs_data = self.proj.get_job_data_dict()
        self.reload_widget()

    def reload_widget(self):
        """Refresh all table/widgets UI after reloading project data."""
        self.update_table_view_job()
        self.update_table_view_job_filter()
        self.update_detail_view()

    def update_detail_view(self):
        """Toggle detail columns in job table based on user preference."""
        show = self.ui.checkBox_advance_detail_mode.isChecked()
        for col in [1, 2, 3, 4, 5, 6]:
            self.ui.tableView_jobs.setColumnHidden(col, not show)

    # ===============================================================
    # GOOGLE DOCS
    # ===============================================================
    def open_google_document(self):
        """Open Google document for the current job."""
        self.proj.open_google_document(job_name=self.current_job_data.get("JobName"))


# ===============================================================
# WORKER THREAD
# ===============================================================


class JobWorker(QtCore.QThread):
    """Background thread for starting jobs without freezing UI."""

    finished = QtCore.Signal(dict)
    error = QtCore.Signal(str)

    def __init__(self, proj, job_data):
        super().__init__()
        self.proj = proj
        self.job_data = job_data

    def run(self):
        try:
            self.proj.start_job(
                job_name=self.job_data["JobName"],
                job_type=self.job_data["JobType"],
                job_task=self.job_data["JobTask"],
            )

            self.proj.reload_job_data_dict()
            jobs_data = self.proj.get_job_data_dict()

            log.info(f"เริ่มงาน {self.job_data['JobName']} สำเร็จ")
            self.finished.emit(jobs_data)

        except Exception as e:
            log.error(f"เกิดข้อผิดพลาดใน Worker: {e}")
            self.error.emit(str(e))
