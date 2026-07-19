# ================================================
#  ANIMATION PUBLISHER — MAYA
# ================================================

# This tool created by Natchapon Srisuk, only for Ukore Studio's projects.
# contact : natchapon.18851@gmail.com

# Split out of the original UkorePublisher on 2026-07-19 — see
# plugins/studio/PublishApi/README.md for why the publish root is now
# always resolved from the active repo's pipeline output rather than a
# share/publish scene-path convention. The "which CustomPath" decision
# itself moved out of this window on 2026-07-19 too, into
# AnimationPublisher's own Repo Studio Setting tab in UkoreHub
# (settings_page.py) — this window has no custom-path input of its own
# anymore, only a Ticket to pick.
# ================================================

import os
import shutil
from importlib import reload

import maya.cmds as cmds
from AnimationPublisher import function
from PublishApi import repo_paths, versioning
from tmlib.module.PySide import QtGui
from tmlib.ui.interface_template import ToolkitWindow
from UkoreMaya.core import Pipeline

reload(function)


class MainWindow(ToolkitWindow):
    def __init__(self):
        super(MainWindow, self).__init__(os.path.basename(os.path.dirname(__file__)))

        self.snapshot_path = None

        self.initialize_ticket_list_widget()
        self.connect_signals()
        self.refresh_publish_destination()

    # ------------------------------------------------------------
    # SIGNALS
    # ------------------------------------------------------------
    def connect_signals(self):
        self.ui.listWidget_ticket.itemSelectionChanged.connect(self.refresh_publish_destination)
        self.ui.pushButton_publish.clicked.connect(self.publish_button)
        self.ui.pushButton_open_dir.clicked.connect(self.open_publish_dir)
        self.ui.pushButton_take_a_snapshot.clicked.connect(self.take_a_snapshot)

    def initialize_ticket_list_widget(self):
        self.ui.listWidget_ticket.addItems(function.TICKETS)
        self.ui.listWidget_ticket.setCurrentRow(0)

    def get_current_selected_ticket(self):
        selection = self.ui.listWidget_ticket.selectedItems()
        return selection[0].text() if selection else None

    def refresh_publish_destination(self):
        ticket = self.get_current_selected_ticket()

        try:
            publish_root = repo_paths.get_publish_root(function.TOOL_ID)
        except RuntimeError as exc:
            self.ui.label_publish_root.setText(str(exc))
            self.ui.label_job_name.setText("")
            self.ui.label_job_task.setText(ticket or "")
            self.ui.label_version_publish.setText("")
            return

        self.ui.label_publish_root.setText(publish_root)
        self.ui.label_job_name.setText(os.path.basename(publish_root))
        self.ui.label_job_task.setText(ticket or "")

        if ticket:
            next_version = versioning.get_new_version(os.path.join(publish_root, ticket))
            self.ui.label_version_publish.setText("v{:03d}".format(next_version))
        else:
            self.ui.label_version_publish.setText("")

    def take_a_snapshot(self):
        self.snapshot_path = Pipeline.playblast_screenshot_to_project_folder()

        pixmap = QtGui.QPixmap(self.snapshot_path)
        if pixmap.isNull():
            return

        btn = self.ui.pushButton_take_a_snapshot
        btn.setIcon(QtGui.QIcon(pixmap))
        btn.setIconSize(btn.size())

    def publish_button(self):
        ticket = self.get_current_selected_ticket()
        if not ticket:
            return

        result = cmds.confirmDialog(
            m="โปรดตรวจสอบและยืนยันข้อมูลการพับบลิชนี้\n\nTicket : {}".format(ticket),
            button=["Ok", "Cancel"],
            defaultButton="Cancel",
            cancelButton="Ok",
        )
        if result == "Cancel":
            return

        try:
            version_dir, version = function.publish(ticket)
        except RuntimeError as exc:
            cmds.confirmDialog(m=str(exc), button=["Ok"])
            return

        self.ui.label_publish_result.setText("Publish สำเร็จ! : {} v{:03d}".format(ticket, version))
        self.refresh_publish_destination()

        note_text = self.ui.textBrowser_publish_info.toPlainText()
        if note_text:
            with open(os.path.join(version_dir, "note.txt"), "w") as f:
                f.write(note_text)

        if self.snapshot_path:
            shutil.copyfile(self.snapshot_path, os.path.join(version_dir, "thumbnail.jpg"))

        result = cmds.confirmDialog(
            m="พับบลิชไฟล์สำเร็จแล้ว!\n : {}".format(version_dir),
            button=["Ok", "Open Publish Folder"],
            defaultButton="Ok",
            cancelButton="Ok",
        )
        if result == "Open Publish Folder":
            os.startfile(version_dir)

    def open_publish_dir(self):
        ticket = self.get_current_selected_ticket()
        if not ticket:
            return

        try:
            publish_root = repo_paths.get_publish_root(function.TOOL_ID)
        except RuntimeError as exc:
            cmds.confirmDialog(m=str(exc), button=["Ok"])
            return

        base_dir = os.path.join(publish_root, ticket)
        versioning.make_sure_folder_exist(base_dir)
        os.startfile(base_dir)
