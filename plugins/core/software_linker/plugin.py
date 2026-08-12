from __future__ import annotations

import glob
import os
import shutil
import subprocess
import winreg

from PySide6.QtCore import QFileInfo, QPropertyAnimation, QSize, Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFileIconProvider,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from core.models import Project, Repo
from interface.program_launch_registry import ProgramLaunchRegistry
from interface.section_registry import SectionSpec

PLUGIN_ID = "software_linker"
_CARD_ICON_SIZE = 40

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
    for keyword, patterns in _DEFAULT_INSTALL_GLOBS.items():
        if keyword not in name:
            continue
        for pattern in patterns:
            matches = sorted(glob.glob(pattern), reverse=True)
            if not matches:
                continue
            
            # ถ้ามีการระบุเวอร์ชัน ให้ค้นหาพาธที่มีเลขเวอร์ชันนั้นก่อน
            if version:
                for match in matches:
                    if version.lower() in match.lower():
                        return match
            
            # ถ้าไม่พบพาธที่ตรงเวอร์ชัน หรือไม่มีเวอร์ชัน ให้ใช้พาธล่าสุดที่เจอ
            return matches[0]
    return None


def _guess_by_registry(program_name: str, version: str, installed: list[tuple[str, str]]) -> str | None:
    """ค้นหาจาก Registry โดยเช็กทั้งชื่อโปรแกรมและเวอร์ชัน"""
    name = program_name.lower()
    ver = version.lower()
    
    # 1. พยายามหาตัวที่ตรงทั้งชื่อและเวอร์ชันก่อน
    if ver:
        for display_name, exe_path in installed:
            disp_lower = display_name.lower()
            if name in disp_lower and ver in disp_lower:
                return exe_path

    # 2. ถ้าไม่เจอ ให้หาตามชื่อโปรแกรมอย่างเดียวเป็น fallback
    for display_name, exe_path in installed:
        if name in display_name.lower():
            return exe_path
    return None


def _resolve_path_for_program(program_name: str, version: str, installed: list[tuple[str, str]]) -> str | None:
    """ค้นหาพาธติดตั้งโดยส่งทั้งชื่อโปรแกรมและเวอร์ชันเข้าไปตรวจเช็ก"""
    # 1. ค้นหาใน PATH
    search_term = f"{program_name}{version}".lower().replace(" ", "")
    guess = shutil.which(search_term)
    if not guess:
        guess = shutil.which(program_name.lower().replace(" ", ""))
    if guess:
        return guess

    # 2. ค้นหาใน Windows Registry
    guess = _guess_by_registry(program_name, version, installed)
    if guess:
        return guess

    # 3. ค้นหาใน Default Installation Globs
    return _guess_by_default_install_path(program_name, version)


class ProgramPickerDialog(QDialog):
    """Simple icon+search picker over every installed program found in the
    Windows registry — not a file-path browse (see "Browse Path..." for
    that), this is specifically "pick from what's already installed"."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choose Installed Program")
        self.resize(480, 520)
        self._selected_path: str | None = None

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search installed programs...")
        self.search_edit.textChanged.connect(self._apply_filter)

        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QSize(32, 32))
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)

        icon_provider = QFileIconProvider()
        for name, path in list_installed_programs():
            item = QListWidgetItem(icon_provider.icon(QFileInfo(path)), name)
            item.setData(Qt.UserRole, path)
            item.setToolTip(path)
            self.list_widget.addItem(item)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.search_edit)
        layout.addWidget(self.list_widget)
        layout.addWidget(buttons)

    def _apply_filter(self, text: str) -> None:
        text = text.lower()
        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)
            item.setHidden(bool(text) and text not in item.text().lower())

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        self._selected_path = item.data(Qt.UserRole)
        self.accept()

    def _on_accept(self) -> None:
        items = self.list_widget.selectedItems()
        if not items:
            return
        self._selected_path = items[0].data(Qt.UserRole)
        self.accept()

    def selected_path(self) -> str | None:
        return self._selected_path


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


class _ToastNotification(QFrame):
    """Small self-dismissing popup used for click-to-launch feedback below,
    instead of a blocking QMessageBox — appears near the card that
    triggered it, holds briefly, then fades out on its own with nothing to
    click through (a notification, not a confirmation)."""

    def __init__(self, text: str, anchor: QWidget):
        super().__init__(anchor, Qt.ToolTip | Qt.FramelessWindowHint)
        self.setObjectName("softwareLinkToast")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self._anchor = anchor

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel(text, self))

        opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(opacity_effect)
        self._fade_animation = QPropertyAnimation(opacity_effect, b"opacity", self)
        self._fade_animation.setDuration(600)
        self._fade_animation.setStartValue(1.0)
        self._fade_animation.setEndValue(0.0)
        self._fade_animation.finished.connect(self.close)

    def present(self, *, hold_ms: int = 900) -> None:
        self.adjustSize()
        center = self._anchor.mapToGlobal(self._anchor.rect().center())
        self.move(center.x() - self.width() // 2, center.y() - self.height() - 12)
        self.show()
        QTimer.singleShot(hold_ms, self._fade_animation.start)


class _ProgramLinkCard(QFrame):
    """One program's link status: its own icon (Program Database's
    icon_filename, resolved via store.resolve_program_icon_path — falls
    back to a generic icon when the program has none set), name, linked
    path, and status each on their own line, plus this row's own actions —
    "Browse Program...", "Browse Path...", and "Clear" each their own
    button in their own column (a plain QHBoxLayout), no dropdown/split
    button. Highlights on hover (QFrame#softwareLinkCard:hover in
    interface/theme.py) to make clear the whole card is clickable.

    A single left-click anywhere on the card outside those buttons opens
    the linked executable directly (same as the retired plugins/core/
    program_launcher/'s card grid) — or, if nothing is linked yet, jumps
    straight into the same "Browse Program..." picker instead of leaving
    the click a no-op. Qt delivers the click to whichever child widget is
    under the cursor first, so clicking the Browse/Clear buttons themselves
    still just activates that button. Launch feedback is a
    _ToastNotification, not a blocking QMessageBox — errors get the same
    fade-out treatment as the success case, nothing needs to be dismissed
    by hand."""

    def __init__(
        self,
        parent,
        *,
        store,
        config_store,
        key: str,
        program,
        label: str,
        program_launch_registry: ProgramLaunchRegistry,
        repo: Repo | None,
    ):
        super().__init__(parent)
        self.setObjectName("softwareLinkCard")
        self.setCursor(Qt.PointingHandCursor)
        self._config_store = config_store
        self._key = key
        self._program = program
        self._program_launch_registry = program_launch_registry
        self._repo = repo

        icon_label = QLabel()
        icon_label.setFixedSize(_CARD_ICON_SIZE, _CARD_ICON_SIZE)
        icon_label.setScaledContents(True)
        icon_path = store.resolve_program_icon_path(program)
        if icon_path and icon_path.exists():
            icon_label.setPixmap(QPixmap(str(icon_path)))
        else:
            fallback_icon = self.style().standardIcon(QStyle.SP_ComputerIcon)
            icon_label.setPixmap(fallback_icon.pixmap(_CARD_ICON_SIZE, _CARD_ICON_SIZE))

        name_label = QLabel(label)
        name_label.setProperty("cardTitle", True)

        self._path_label = QLabel()
        self._path_label.setProperty("secondary", True)
        self._path_label.setWordWrap(True)

        self._status_label = QLabel()

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)
        text_layout.addWidget(name_label)
        text_layout.addWidget(self._path_label)
        text_layout.addWidget(self._status_label)

        browse_program_btn = QPushButton("Browse Program...")
        browse_program_btn.clicked.connect(self._on_browse_program)

        browse_path_btn = QPushButton("Browse Path...")
        browse_path_btn.clicked.connect(self._on_browse_path)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._on_clear)

        button_row = QHBoxLayout()
        button_row.setSpacing(4)
        button_row.addWidget(browse_program_btn)
        button_row.addWidget(browse_path_btn)
        button_row.addWidget(clear_btn)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)
        layout.addWidget(icon_label)
        layout.addLayout(text_layout, 1)
        layout.addLayout(button_row)

        self.refresh()

    def refresh(self) -> None:
        linked_path = self._config_store.get(self._key)
        if linked_path:
            self._path_label.setText(linked_path)
            self._status_label.setText("Linked")
            self._status_label.setProperty("linkStatus", "linked")
            self.setToolTip("Click to open.")
        else:
            self._path_label.setText("No path linked")
            self._status_label.setText("Not linked")
            self._status_label.setProperty("linkStatus", "not_linked")
            self.setToolTip("Not linked yet — click to choose an installed program.")
        self._status_label.style().unpolish(self._status_label)
        self._status_label.style().polish(self._status_label)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._on_click()
        super().mousePressEvent(event)

    def _on_click(self) -> None:
        exe_path = self._config_store.get(self._key)
        if not exe_path:
            self._on_browse_program()
            return
        _ToastNotification(f"Opening {self._program.name}...", self).present()
        # A plugin (e.g. maya_launcher) may need to launch this Program
        # with its own setProject/env-merge wiring instead of a bare
        # process launch — see interface/program_launch_registry.py. Falls
        # back to a raw launch when no repo is active, same as no match.
        launcher = self._program_launch_registry.find_launcher(self._program)
        if launcher is not None and self._repo is not None:
            launcher(self._repo)
            return
        try:
            subprocess.Popen([exe_path])
        except OSError as exc:
            _ToastNotification(f"Could not launch {self._program.name}: {exc}", self).present()

    def _on_browse_program(self) -> None:
        dialog = ProgramPickerDialog(self)
        if dialog.exec() and dialog.selected_path():
            self._config_store.set(self._key, dialog.selected_path())
            self.refresh()

    def _on_browse_path(self) -> None:
        file_path, _filter = QFileDialog.getOpenFileName(self, "Select Executable")
        if not file_path:
            return
        self._config_store.set(self._key, file_path)
        self.refresh()

    def _on_clear(self) -> None:
        self._config_store.set(self._key, None)
        self.refresh()


class SoftwareLinkerPage(QWidget):
    """The app's main "Program Launcher" tab — lets the user link each
    Program Database entry to a local executable path on this machine
    (per-machine data, PluginConfigStore shared=False, since "what's
    installed here" is never team-shared) and click a linked card once to
    open it. Other plugins/add-ons (e.g. maya_launcher) read the same
    linked-path mapping by calling api.plugin_config_store("software_linker",
    shared=False) themselves — no coupling API needed, just agreeing on that
    id string; this is why PLUGIN_ID stays "software_linker" even though the
    tab itself is now labeled "Program Launcher" (see this folder's
    README.md). Renders one _ProgramLinkCard per linkable (Program,
    version) slot.

    Program Database is per-Project (core/models.py's Project.programs), so
    this page's underlying catalog is every Program in the active Project's
    own catalog — same as the retired plugins/core/program_launcher/, this
    can be narrowed down to just the active repo's required_program_ids via
    the "Show Only Requirement for current repo only" checkbox (checked by
    default; see _rebuild_cards). The click-to-launch below still uses
    whichever repo is currently active (SectionSpec's standard set_repo
    protocol) for any Program with its own ProgramLaunchRegistry entry."""

    def __init__(self, parent=None, *, store, config_store, program_launch_registry):
        super().__init__(parent)
        self._store = store
        self._config_store = config_store
        self._program_launch_registry = program_launch_registry
        self._project: Project | None = None
        self._repo: Repo | None = None

        self._require_filter_checkbox = QCheckBox("Show Only Requirement for current repo only")
        self._require_filter_checkbox.setChecked(True)
        self._require_filter_checkbox.toggled.connect(lambda _checked: self._rebuild_cards())

        self.project_label = QLabel()

        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Project:"))
        header_layout.addWidget(self.project_label)
        header_layout.addStretch()
        auto_resolve_btn = QPushButton("Auto-Resolve Path")
        auto_resolve_btn.setToolTip(
            "Already runs automatically for unlinked programs — use this to "
            "re-scan on demand and see a summary of how many were resolved."
        )
        auto_resolve_btn.clicked.connect(self._on_auto_resolve_path)
        header_layout.addWidget(auto_resolve_btn)

        self._cards_container = QWidget()
        self._cards_layout = QVBoxLayout(self._cards_container)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        self._cards_layout.setSpacing(6)
        self._cards_layout.addStretch(1)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setWidget(self._cards_container)

        layout = QVBoxLayout(self)
        layout.addWidget(self._require_filter_checkbox)
        layout.addLayout(header_layout)
        layout.addWidget(scroll_area)

    def set_repo(self, project: Project | None, repo: Repo | None, workspace_root: str | None) -> None:
        self._project = project
        self._repo = repo
        self.refresh()

    def refresh(self) -> None:
        """Re-reads the active project's current name and rebuilds the
        link cards. Called from set_repo whenever this becomes the visible
        section (interface/main_window.py's _apply_to_current_page) and on
        every active-repo switch."""
        self.project_label.setText(self._project.name if self._project is not None else "(no project)")
        self._rebuild_cards()

    def _rebuild_cards(self) -> None:
        while self._cards_layout.count() > 1:  # keep the trailing addStretch
            item = self._cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if self._project is None:
            return
        project_id = self._project.id

        self._auto_detect_missing(project_id)
        rows = _link_rows(self._store, project_id)
        if self._require_filter_checkbox.isChecked() and self._repo is not None:
            required_ids = set(self._repo.required_program_ids)
            rows = [row for row in rows if row[1].id in required_ids]
        for key, program, _version, label in rows:
            card = _ProgramLinkCard(
                self._cards_container,
                store=self._store,
                config_store=self._config_store,
                key=key,
                program=program,
                label=label,
                program_launch_registry=self._program_launch_registry,
                repo=self._repo,
            )
            self._cards_layout.insertWidget(self._cards_layout.count() - 1, card)

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
        self._rebuild_cards()
        QMessageBox.information(
            self,
            "Auto-Resolve Path",
            f"Resolved {resolved} program(s)." if resolved else "No new programs could be resolved automatically.",
        )


def register(api) -> None:
    icons_dir = api.app_root / "assets" / "icons"
    api.register_section(
        SectionSpec(
            key=PLUGIN_ID,
            label="Program Launcher",
            order=40,
            icon_path=icons_dir / "icons8-booster-64.png",
            page_factory=lambda: SoftwareLinkerPage(
                store=api.metadata,
                config_store=api.plugin_config_store(PLUGIN_ID, shared=False),
                program_launch_registry=api.program_launch_registry,
            ),
        )
    )
