from __future__ import annotations

import glob
import os
import shutil
import subprocess
import winreg
from pathlib import Path

from PySide6.QtCore import QFile, QFileInfo, QSize, Qt
from PySide6.QtGui import QCursor, QIcon, QPalette
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QFileDialog,
    QFileIconProvider,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QStyle,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from plugin_api import ProgramLaunchRegistry, Project, Repo, SectionSpec

PLUGIN_ID = "software_linker"
_UI_FILE = Path(__file__).parent / "ProgramLauncherWindow.ui"
_BROWSE_UI_FILE = Path(__file__).parent / "BrowseProgramWindow.ui"
_ICON_SIZE = 32

# The same registry locations Windows' own "Programs and Features" /
# Settings > Apps reads from.
_UNINSTALL_ROOTS = [
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
    (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
]

# Best-effort fallback locations for a handful of common pipeline DCCs,
# tried by "Auto-Resolve Path" only after both the PATH lookup and the
# registry scan above come up empty for a given Program — see
# _resolve_path_for_program. Keyed by a lowercase substring matched against
# the Program's own name (core/models.py's Program.name), not an exact id,
# so "Autodesk Maya" / "Maya" both hit the "maya" entry.
_DEFAULT_INSTALL_GLOBS: dict[str, list[str]] = {
    "maya": [r"C:\Program Files\Autodesk\Maya*\bin\maya.exe"],
    "unreal": [r"C:\Program Files\Epic Games\UE_*\Engine\Binaries\Win64\UnrealEditor.exe"],
    "blender": [r"C:\Program Files\Blender Foundation\Blender*\blender.exe"],
    "photoshop": [r"C:\Program Files\Adobe\Adobe Photoshop*\Photoshop.exe"],
}


def _resolve_exe_path(sub_key) -> str | None:
    try:
        icon_value = winreg.QueryValueEx(sub_key, "DisplayIcon")[0]
        exe_path = icon_value.split(",")[0].strip('"')
        if exe_path.lower().endswith(".exe") and os.path.isfile(exe_path):
            return exe_path
    except OSError:
        pass
    try:
        install_location = winreg.QueryValueEx(sub_key, "InstallLocation")[0]
        if install_location and os.path.isdir(install_location):
            for name in os.listdir(install_location):
                if name.lower().endswith(".exe"):
                    return os.path.join(install_location, name)
    except OSError:
        pass
    return None


def list_installed_programs() -> list[tuple[str, str]]:
    """Best-effort scan of every program registered in Windows' Uninstall
    registry keys — the same list "Programs and Features"/Settings > Apps
    shows. Returns (display_name, resolved_exe_path) pairs, skipping any
    entry we can't resolve to an actual .exe (some only have an uninstaller
    or a generic icon, no runnable target)."""
    programs: dict[str, str] = {}
    for hive, subkey_path in _UNINSTALL_ROOTS:
        try:
            root_key = winreg.OpenKey(hive, subkey_path)
        except OSError:
            continue
        with root_key:
            count = winreg.QueryInfoKey(root_key)[0]
            for i in range(count):
                try:
                    sub_name = winreg.EnumKey(root_key, i)
                    with winreg.OpenKey(root_key, sub_name) as sub_key:
                        display_name = winreg.QueryValueEx(sub_key, "DisplayName")[0]
                        exe_path = _resolve_exe_path(sub_key)
                except OSError:
                    continue
                if exe_path:
                    programs[display_name] = exe_path
    return sorted(programs.items())


def _guess_by_default_install_path(program_name: str, version: str = "") -> str | None:
    """ค้นหาจากพาธเริ่มต้นของโปรแกรม โดยนำเวอร์ชันมาร่วมพิจารณาด้วย"""
    name = program_name.lower()
    ver_str = str(version).strip().lower() if version else ""

    for keyword, patterns in _DEFAULT_INSTALL_GLOBS.items():
        if keyword not in name:
            continue

        for pattern in patterns:
            # 1. ถ้าระบุเวอร์ชันชัดเจน ให้พยายามสร้าง pattern ที่เจาะจงเวอร์ชันนั้นก่อน (เช่น Maya2024)
            if ver_str:
                # แปลง pattern เช่น 'Maya*' เป็น 'Maya2024' หรือ 'Maya*2024*'
                specific_pattern = pattern.replace("*", f"*{ver_str}*")
                specific_matches = sorted(glob.glob(specific_pattern), reverse=True)
                if specific_matches:
                    return specific_matches[0]
                
                # ลองเช็กอีกรอบกรณี pattern ไม่ได้ใช้ wildcard ท้ายคำ
                exact_pattern = pattern.replace("*", ver_str)
                exact_matches = sorted(glob.glob(exact_pattern), reverse=True)
                if exact_matches:
                    return exact_matches[0]

                # ***สำคัญ***: ถ้าระบุเวอร์ชันชัดเจน แล้วหาโฟลเดอร์เวอร์ชันนั้นไม่เจอ 
                # ให้จบการหาของ pattern นี้ไปเลย ห้ามหลุดไปหยิบ Maya2026 จาก matches ทั่วไป
                continue

            # 2. ถ้าไม่ได้ระบุเวอร์ชันเลย ค่อยค้นหาแบบกว้าง (Wildcard) แล้วหยิบเวอร์ชันล่าสุด
            matches = sorted(glob.glob(pattern), reverse=True)
            if matches:
                return matches[0]

    return None


def _guess_by_registry(program_name: str, version: str, installed: list[tuple[str, str]]) -> str | None:
    """ค้นหาจาก Registry โดยเช็กทั้งชื่อโปรแกรมและเวอร์ชัน"""
    name = program_name.lower()
    ver = version.lower().strip()

    # 1. ถ้าระบุเวอร์ชัน ต้องเจอทั้งชื่อโปรแกรมและเวอร์ชันใน DisplayName เท่านั้น
    if ver:
        for display_name, exe_path in installed:
            disp_lower = display_name.lower()
            if name in disp_lower and ver in disp_lower:
                return exe_path
        # ถ้าระบุเวอร์ชันแล้วไม่เจอใน Registry ให้คืนค่า None ทันที
        return None

    # 2. ถ้าไม่ได้ระบุเวอร์ชันเลย ค่อยค้นหาตามชื่อโปรแกรมอย่างเดียว
    for display_name, exe_path in installed:
        if name in display_name.lower():
            return exe_path

    return None

def _resolve_path_for_program(program_name: str, version: str, installed: list[tuple[str, str]]) -> str | None:
    """ค้นหาพาธติดตั้งโดยส่งทั้งชื่อโปรแกรมและเวอร์ชันเข้าไปตรวจเช็ก"""
    # 1. ค้นหาใน Default Installation Globs ก่อน เพราะสามารถระบุโฟลเดอร์เวอร์ชันชัวร์สุด (เช่น Maya2024, Maya2026)
    guess = _guess_by_default_install_path(program_name, version)
    if guess:
        return guess

    # 2. ค้นหาใน Windows Registry
    guess = _guess_by_registry(program_name, version, installed)
    if guess:
        return guess

    # 3. Fallback: ค้นหาใน System PATH (shutil.which)
    search_term = f"{program_name}{version}".lower().replace(" ", "")
    guess = shutil.which(search_term)
    if not guess:
        guess = shutil.which(program_name.lower().replace(" ", ""))
    if guess:
        return guess

    return None

class ProgramPickerDialog(QDialog):
    """Icon+search picker over every installed program found in the Windows
    registry, plus "Browse..." for an arbitrary executable path and "Clear
    Link Path" to unlink — all three link-editing actions the tab used to
    spread across its own "Browse Path.../Browse Program.../Clear Link
    Path" buttons now live in this one dialog (BrowseProgramWindow.ui,
    loaded via QUiLoader same as the tab itself), opened from the tab's
    single "Edit Link..." button."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Link")
        self._selected_path: str | None = None
        self._clear_requested = False

        loader = QUiLoader()
        ui_file = QFile(str(_BROWSE_UI_FILE))
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, self)
        ui_file.close()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ui)
        self.resize(self.ui.size())

        self._search_edit: QLineEdit = self.ui.findChild(QLineEdit, "lineEdit_search_program")
        self._list_widget: QListWidget = self.ui.findChild(QListWidget, "listWidget_register_program")
        self._list_widget.setIconSize(QSize(_ICON_SIZE, _ICON_SIZE))
        self._list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self._browse_btn: QPushButton = self.ui.findChild(QPushButton, "pushButton_browse")
        self._clear_btn: QPushButton = self.ui.findChild(QPushButton, "pushButton_clear_link_path")
        self._ok_btn: QPushButton = self.ui.findChild(QPushButton, "pushButton_ok")
        self._cancel_btn: QPushButton = self.ui.findChild(QPushButton, "pushButton_cancel")

        icon_provider = QFileIconProvider()
        for name, path in list_installed_programs():
            item = QListWidgetItem(icon_provider.icon(QFileInfo(path)), name)
            item.setData(Qt.UserRole, path)
            item.setToolTip(path)
            self._list_widget.addItem(item)

        self._search_edit.textChanged.connect(self._apply_filter)
        self._list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._browse_btn.clicked.connect(self._on_browse)
        self._clear_btn.clicked.connect(self._on_clear)
        self._ok_btn.clicked.connect(self._on_accept)
        self._cancel_btn.clicked.connect(self.reject)

    def _apply_filter(self, text: str) -> None:
        text = text.lower()
        for row in range(self._list_widget.count()):
            item = self._list_widget.item(row)
            item.setHidden(bool(text) and text not in item.text().lower())

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        self._selected_path = item.data(Qt.UserRole)
        self.accept()

    def _on_browse(self) -> None:
        file_path, _filter = QFileDialog.getOpenFileName(self, "Select Executable")
        if not file_path:
            return
        self._selected_path = file_path
        self.accept()

    def _on_clear(self) -> None:
        self._clear_requested = True
        self.accept()

    def _on_accept(self) -> None:
        items = self._list_widget.selectedItems()
        if not items:
            return
        self._selected_path = items[0].data(Qt.UserRole)
        self.accept()

    def selected_path(self) -> str | None:
        return self._selected_path

    def clear_requested(self) -> bool:
        return self._clear_requested


def _linked_key(program, version: str = "") -> str:
    """Per-machine linked-exe config key. Stays plain program.id for a
    single/no-version Program (preserves already-linked paths); becomes
    "<id>:<version>" once a Program has multiple versions, since each
    needs its own linked executable. Convention-only duplicate of
    maya_launcher's link_resolution.py's linked_key() (now its own
    cache/plugins/ clone) — keep
    both in sync if this shape ever changes, same discipline as
    MAYA_ENV_BRIDGE_PLUGIN_ID."""
    if len(program.versions) <= 1:
        return program.id
    return f"{program.id}:{version}"


def _link_rows(store, project_id):
    """(key, program, version, label) for every linkable (Program, version)
    slot in the given Project's own Program Database — one row for a
    single/no-version Program, one row per version for a multi-version
    Program (e.g. Maya 2024 and 2026 need separate linked executables)."""
    rows = []
    for program in store.list_programs(project_id):
        versions = program.versions or [""]
        if len(versions) <= 1:
            version = versions[0]
            label = f"{program.name} (v{version})" if version else program.name
            rows.append((_linked_key(program, version), program, version, label))
        else:
            for version in versions:
                rows.append((_linked_key(program, version), program, version, f"{program.name} (v{version})"))
    return rows


class SoftwareLinkerPage(QWidget):
    """The app's main "Program Launcher" tab — lets the user link each
    Program Database entry to a local executable path on this machine
    (per-machine data, PluginConfigStore shared=False, since "what's
    installed here" is never team-shared) and double-click a linked row to
    open it. Other plugins/add-ons (e.g. maya_launcher) read the same
    linked-path mapping by calling api.plugin_config_store("software_linker",
    shared=False) themselves — no coupling API needed, just agreeing on that
    id string; this is why PLUGIN_ID stays "software_linker" even though the
    tab itself is now labeled "Program Launcher" (see this folder's
    README.md).

    UI is authored in Qt Designer (ProgramLauncherWindow.ui) and loaded at
    runtime via QUiLoader instead of being built widget-by-widget in code
    (same convention as plugins/core/explorer/browser_widget.py) — one
    QListWidget row per linkable (Program, version) slot, with the
    "Auto Resolve"/"Edit Link..." buttons acting on whichever row is
    currently selected. "Edit Link..." opens ProgramPickerDialog
    (BrowseProgramWindow.ui, its own separate Designer file) instead of the
    tab hosting its own "Browse Path.../Browse Program.../Clear Link Path"
    buttons directly. All status styling (bold for linked, QPalette.PlaceholderText
    for not-linked) uses Qt's own QFont/QPalette directly rather than
    interface/shared/widget_helpers.py's set_bold/set_secondary_text, and
    launch feedback uses QToolTip.showText — no plugin-specific QSS in
    interface/theme.py to keep in sync.

    Program Database is per-Project (core/models.py's Project.programs), so
    this page's underlying catalog is every Program in the active Project's
    own catalog — same as the retired plugins/core/program_launcher/, this
    can be narrowed down to just the active repo's required_program_ids via
    the "Show Only Requirement for current repo only" checkbox (checked by
    default; see _rebuild_list). Double-click-to-launch below still uses
    whichever repo is currently active (SectionSpec's standard set_repo
    protocol) for any Program with its own ProgramLaunchRegistry entry."""

    def __init__(self, parent=None, *, store, config_store, program_launch_registry):
        super().__init__(parent)
        self._store = store
        self._config_store = config_store
        self._program_launch_registry = program_launch_registry
        self._project: Project | None = None
        self._repo: Repo | None = None

        loader = QUiLoader()
        ui_file = QFile(str(_UI_FILE))
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, self)
        ui_file.close()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ui)

        self._list_widget: QListWidget = self.ui.findChild(QListWidget, "listWidget_program_list")
        self._list_widget.setIconSize(QSize(_ICON_SIZE, _ICON_SIZE))
        self._require_filter_checkbox: QCheckBox = self.ui.findChild(QCheckBox, "checkBox_ShowOnlyRequirement")
        self._require_filter_checkbox.setChecked(True)
        self._auto_resolve_btn: QPushButton = self.ui.findChild(QPushButton, "pushButton_auto_resolve")
        self._auto_resolve_btn.setToolTip(
            "Already runs automatically for unlinked programs — use this to "
            "re-scan on demand and see a summary of how many were resolved."
        )
        self._edit_link_btn: QPushButton = self.ui.findChild(QPushButton, "pushButton_clear_link_path")

        self._require_filter_checkbox.toggled.connect(lambda _checked: self._rebuild_list())
        self._auto_resolve_btn.clicked.connect(self._on_auto_resolve_path)
        self._edit_link_btn.clicked.connect(self._on_edit_link)
        self._list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._list_widget.currentItemChanged.connect(lambda *_args: self._update_action_buttons_enabled())

        self._update_action_buttons_enabled()

    def set_repo(self, project: Project | None, repo: Repo | None, workspace_root: str | None) -> None:
        self._project = project
        self._repo = repo
        self.refresh()

    def refresh(self) -> None:
        """Rebuilds the program list. Called from set_repo whenever this
        becomes the visible section (interface/main_window.py's
        _apply_to_current_page) and on every active-repo switch."""
        self._rebuild_list()

    def _update_action_buttons_enabled(self) -> None:
        has_selection = self._list_widget.currentItem() is not None
        self._edit_link_btn.setEnabled(has_selection)

    def _selected_row(self) -> tuple[str, object, str, str] | None:
        item = self._list_widget.currentItem()
        if item is None:
            return None
        return item.data(Qt.UserRole)

    def _icon_for_program(self, program) -> QIcon:
        icon_path = self._store.resolve_program_icon_path(program)
        if icon_path and icon_path.exists():
            return QIcon(str(icon_path))
        return self.style().standardIcon(QStyle.SP_ComputerIcon)

    def _apply_item_state(self, item: QListWidgetItem) -> None:
        key, _program, _version, label = item.data(Qt.UserRole)
        linked_path = self._config_store.get(key)
        font = item.font()
        font.setBold(bool(linked_path))
        item.setFont(font)
        if linked_path:
            item.setText(f"{label}\n{linked_path}")
            item.setForeground(self.palette().color(QPalette.Text))
            item.setToolTip(f"{linked_path}\n\nDouble-click to open.")
        else:
            item.setText(f"{label}\nNot linked")
            item.setForeground(self.palette().color(QPalette.PlaceholderText))
            item.setToolTip("Not linked yet — double-click to choose an installed program.")

    def _rebuild_list(self) -> None:
        current = self._list_widget.currentItem()
        previous_key = current.data(Qt.UserRole)[0] if current is not None else None

        self._list_widget.clear()

        if self._project is None:
            self._update_action_buttons_enabled()
            return
        project_id = self._project.id

        self._auto_detect_missing(project_id)
        rows = _link_rows(self._store, project_id)

        if self._require_filter_checkbox.isChecked() and self._repo is not None:
            required_ids = set(self._repo.required_program_ids)
            pins = self._repo.program_version_pins  # เช่น {"<maya_program_id>": "2026"}

            filtered_rows = []
            for row in rows:
                key, program, version, label = row
                # 1. ต้องเป็น Program ID ที่ Repo นี้ Require ไว้ก่อน
                if program.id not in required_ids:
                    continue

                # 2. ถ้า Program นี้มีการตั้งค่า Pin เวอร์ชันไว้สำหรับ Repo นี้
                #    ให้แสดงเฉพาะแถวที่เวอร์ชันตรงกับ Pin เท่านั้น
                pinned_ver = pins.get(program.id)
                if pinned_ver and version and version != pinned_ver:
                    continue

                filtered_rows.append(row)

            rows = filtered_rows

        restore_item = None
        for key, program, version, label in rows:
            item = QListWidgetItem()
            item.setIcon(self._icon_for_program(program))
            item.setData(Qt.UserRole, (key, program, version, label))
            self._apply_item_state(item)
            self._list_widget.addItem(item)
            if key == previous_key:
                restore_item = item

        if restore_item is not None:
            self._list_widget.setCurrentItem(restore_item)
        self._update_action_buttons_enabled()

    def _auto_detect_missing(self, project_id: str) -> None:
        installed = list_installed_programs()
        for key, program, version, _label in _link_rows(self._store, project_id):
            if self._config_store.get(key):
                continue
            # ส่ง version เพิ่มเข้าไปเป็นอาร์กิวเมนต์ที่ 2
            guess = _resolve_path_for_program(program.name, version, installed)
            if guess:
                self._config_store.set(key, guess)

    def _on_auto_resolve_path(self) -> None:
        if self._project is None:
            return
        installed = list_installed_programs()
        resolved = 0
        for key, program, version, _label in _link_rows(self._store, self._project.id):
            if self._config_store.get(key):
                continue
            # ส่ง version เพิ่มเข้าไปเป็นอาร์กิวเมนต์ที่ 2
            guess = _resolve_path_for_program(program.name, version, installed)
            if guess:
                self._config_store.set(key, guess)
                resolved += 1
        self._rebuild_list()
        QMessageBox.information(
            self,
            "Auto-Resolve Path",
            f"Resolved {resolved} program(s)." if resolved else "No new programs could be resolved automatically.",
        )

    def _on_edit_link(self) -> None:
        row = self._selected_row()
        if row is None:
            return
        key, _program, _version, _label = row
        dialog = ProgramPickerDialog(self)
        if not dialog.exec():
            return
        if dialog.clear_requested():
            self._config_store.set(key, None)
        elif dialog.selected_path():
            self._config_store.set(key, dialog.selected_path())
        self._apply_item_state(self._list_widget.currentItem())

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        key, program, _version, _label = item.data(Qt.UserRole)
        exe_path = self._config_store.get(key)
        if not exe_path:
            self._list_widget.setCurrentItem(item)
            self._on_edit_link()
            return
        QToolTip.showText(QCursor.pos(), f"Opening {program.name}...", self._list_widget)
        # A plugin (e.g. maya_launcher) may need to launch this Program
        # with its own setProject/env-merge wiring instead of a bare
        # process launch — see plugin_api/registries/program_launch_registry.py. Falls
        # back to a raw launch when no repo is active, same as no match.
        launcher = self._program_launch_registry.find_launcher(program)
        if launcher is not None and self._repo is not None:
            launcher(self._repo)
            return
        try:
            subprocess.Popen([exe_path])
        except OSError as exc:
            QToolTip.showText(QCursor.pos(), f"Could not launch {program.name}: {exc}", self._list_widget)


def register(api) -> None:
    api.register_section(
        SectionSpec(
            key=PLUGIN_ID,
            label="Program Launcher",
            order=40,
            standard_icon=QStyle.SP_ComputerIcon,
            page_factory=lambda: SoftwareLinkerPage(
                store=api.metadata,
                config_store=api.plugin_config_store(PLUGIN_ID, shared=False),
                program_launch_registry=api.program_launch_registry,
            ),
        )
    )
