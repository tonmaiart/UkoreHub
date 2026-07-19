"""Playblast Options... dialog — the studio-facing configuration UI for
UkoreShotPlayblast, living entirely inside Maya (confirmed with the user
2026-07-19: this tool's options belong in Maya, not a UkoreHub Repository
Setting tab — the desktop-side settings_page.py that used to be here was
removed). Opened via the option-box next to "Playblast" in UkoreMaya's
Animation menu (see plugins/studio/MayaToolkit/maya-plug-ins/ukoreMaya.py,
menu_utils.py's playblast_options()). Same field set the old desktop
settings page had, same PluginConfigStore-backed persistence
(options_store.py) — only the UI moved."""

from __future__ import annotations

import maya.cmds as cmds
from PublishApi import repo_paths
from tmlib.module.PySide import QtWidgets
from tmlib.ui.interface_template import get_maya_window
from UkoreShotPlayblast import options_store

_FORMATS = ["avi", "qt", "image"]


class PlayblastOptionsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent=parent or get_maya_window())
        self.setWindowTitle("Playblast Options")
        self.setMinimumWidth(360)

        project, repo, _repo_path = repo_paths.get_active_repo()
        self._project_id = project.id if project is not None else None
        self._repo_id = repo.id if repo is not None else None

        options = (
            options_store.get_options(self._project_id, self._repo_id)
            if self._project_id and self._repo_id
            else dict(options_store.DEFAULT_OPTIONS)
        )

        # -- Resolution ----------------------------------------------------
        self.resolution_render_radio = QtWidgets.QRadioButton("Use render settings")
        self.resolution_custom_radio = QtWidgets.QRadioButton("Custom")
        resolution_group = QtWidgets.QButtonGroup(self)
        resolution_group.addButton(self.resolution_render_radio)
        resolution_group.addButton(self.resolution_custom_radio)
        self.width_spin = QtWidgets.QSpinBox()
        self.width_spin.setRange(16, 8192)
        self.height_spin = QtWidgets.QSpinBox()
        self.height_spin.setRange(16, 8192)
        self.resolution_custom_radio.toggled.connect(self.width_spin.setEnabled)
        self.resolution_custom_radio.toggled.connect(self.height_spin.setEnabled)

        resolution_box = QtWidgets.QGroupBox("Resolution")
        resolution_form = QtWidgets.QFormLayout(resolution_box)
        resolution_form.addRow(self.resolution_render_radio)
        resolution_form.addRow(self.resolution_custom_radio)
        resolution_form.addRow("Width", self.width_spin)
        resolution_form.addRow("Height", self.height_spin)

        # -- Format / quality ------------------------------------------------
        self.format_combo = QtWidgets.QComboBox()
        self.format_combo.addItems(_FORMATS)
        self.compression_edit = QtWidgets.QLineEdit()
        self.compression_edit.setPlaceholderText("blank = uncompressed")
        self.quality_spin = QtWidgets.QSpinBox()
        self.quality_spin.setRange(0, 100)
        self.quality_spin.setSuffix("%")
        self.percent_spin = QtWidgets.QSpinBox()
        self.percent_spin.setRange(1, 100)
        self.percent_spin.setSuffix("%")

        format_box = QtWidgets.QGroupBox("Format / Quality")
        format_form = QtWidgets.QFormLayout(format_box)
        format_form.addRow("Format", self.format_combo)
        format_form.addRow("Compression", self.compression_edit)
        format_form.addRow("Quality", self.quality_spin)
        format_form.addRow("Viewport Scale", self.percent_spin)

        # -- Frame range -----------------------------------------------------
        self.frame_range_current_radio = QtWidgets.QRadioButton("Current timeline")
        self.frame_range_custom_radio = QtWidgets.QRadioButton("Custom")
        frame_range_group = QtWidgets.QButtonGroup(self)
        frame_range_group.addButton(self.frame_range_current_radio)
        frame_range_group.addButton(self.frame_range_custom_radio)
        self.start_frame_spin = QtWidgets.QSpinBox()
        self.start_frame_spin.setRange(-100000, 100000)
        self.end_frame_spin = QtWidgets.QSpinBox()
        self.end_frame_spin.setRange(-100000, 100000)
        self.frame_range_custom_radio.toggled.connect(self.start_frame_spin.setEnabled)
        self.frame_range_custom_radio.toggled.connect(self.end_frame_spin.setEnabled)

        frame_range_box = QtWidgets.QGroupBox("Frame Range")
        frame_range_form = QtWidgets.QFormLayout(frame_range_box)
        frame_range_form.addRow(self.frame_range_current_radio)
        frame_range_form.addRow(self.frame_range_custom_radio)
        frame_range_form.addRow("Start", self.start_frame_spin)
        frame_range_form.addRow("End", self.end_frame_spin)

        # -- Other ------------------------------------------------------------
        self.camera_edit = QtWidgets.QLineEdit()
        self.camera_edit.setPlaceholderText("Active viewport camera")
        self.sound_check = QtWidgets.QCheckBox("Include sound")
        self.ornaments_check = QtWidgets.QCheckBox("Show ornaments (HUD)")

        other_box = QtWidgets.QGroupBox("Other")
        other_form = QtWidgets.QFormLayout(other_box)
        other_form.addRow("Camera", self.camera_edit)
        other_form.addRow(self.sound_check)
        other_form.addRow(self.ornaments_check)

        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout(self)
        if not (self._project_id and self._repo_id):
            warning = QtWidgets.QLabel(
                "No active repo selected in UkoreHub — showing defaults, changes won't be saved."
            )
            warning.setWordWrap(True)
            layout.addWidget(warning)
        layout.addWidget(resolution_box)
        layout.addWidget(format_box)
        layout.addWidget(frame_range_box)
        layout.addWidget(other_box)
        layout.addWidget(buttons)

        self._load(options)

    def _load(self, options: dict) -> None:
        self.resolution_render_radio.setChecked(options["resolution_mode"] == "render_settings")
        self.resolution_custom_radio.setChecked(options["resolution_mode"] == "custom")
        self.width_spin.setValue(options["width"])
        self.height_spin.setValue(options["height"])
        self.width_spin.setEnabled(options["resolution_mode"] == "custom")
        self.height_spin.setEnabled(options["resolution_mode"] == "custom")
        self.format_combo.setCurrentText(options["format"])
        self.compression_edit.setText(options["compression"])
        self.quality_spin.setValue(options["quality"])
        self.percent_spin.setValue(options["percent"])
        self.frame_range_current_radio.setChecked(options["frame_range_mode"] == "current_timeline")
        self.frame_range_custom_radio.setChecked(options["frame_range_mode"] == "custom")
        self.start_frame_spin.setValue(options["start_frame"])
        self.end_frame_spin.setValue(options["end_frame"])
        self.start_frame_spin.setEnabled(options["frame_range_mode"] == "custom")
        self.end_frame_spin.setEnabled(options["frame_range_mode"] == "custom")
        self.camera_edit.setText(options["camera"])
        self.sound_check.setChecked(options["sound"])
        self.ornaments_check.setChecked(options["show_ornaments"])

    def _on_accept(self) -> None:
        if not (self._project_id and self._repo_id):
            cmds.confirmDialog(
                title="Playblast Options", message="No active repo selected in UkoreHub — nothing to save to."
            )
            self.reject()
            return
        options = {
            "resolution_mode": "custom" if self.resolution_custom_radio.isChecked() else "render_settings",
            "width": self.width_spin.value(),
            "height": self.height_spin.value(),
            "format": self.format_combo.currentText(),
            "compression": self.compression_edit.text().strip(),
            "quality": self.quality_spin.value(),
            "percent": self.percent_spin.value(),
            "frame_range_mode": "custom" if self.frame_range_custom_radio.isChecked() else "current_timeline",
            "start_frame": self.start_frame_spin.value(),
            "end_frame": self.end_frame_spin.value(),
            "camera": self.camera_edit.text().strip(),
            "sound": self.sound_check.isChecked(),
            "show_ornaments": self.ornaments_check.isChecked(),
        }
        options_store.set_options(self._project_id, self._repo_id, options)
        self.accept()


def show() -> None:
    dialog = PlayblastOptionsDialog()
    dialog.exec_()
