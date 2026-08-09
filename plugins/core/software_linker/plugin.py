from __future__ import annotations

import os
import shutil
import winreg

from PySide6.QtCore import QFileInfo, QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFileIconProvider,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QScrollArea,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from interface.settings_tab_registry import SettingsTabSpec

PLUGIN_ID = "software_linker"
_CARD_ICON_SIZE = 40

# The same registry locations Windows' own "Programs and Features" /
# Settings > Apps reads from.
_UNINSTALL_ROOTS = [
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
    (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
]


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
    plugins/repo_internal/maya_launcher/link_resolution.py's linked_key() — keep
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


class _ProgramLinkCard(QFrame):
    """One program's link status: its own icon (Program Database's
    icon_filename, resolved via store.resolve_program_icon_path — falls
    back to a generic icon when the program has none set), name, linked
    path, and status each on their own line, plus this row's own actions.
    Replaces the old single-selection QListWidget + page-level button row:
    "Browse Program..." and "Browse Path..." used to be two separate
    buttons acting on whatever list row happened to be selected; here
    "Browse Path..." is folded into the "Browse Program..." split button's
    dropdown (QToolButton menu) and both act on this card's own program
    directly, no selection state needed."""

    def __init__(self, parent, *, store, config_store, key: str, program, label: str):
        super().__init__(parent)
        self.setObjectName("softwareLinkCard")
        self._config_store = config_store
        self._key = key

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

        browse_btn = QToolButton()
        browse_btn.setText("Browse Program...")
        browse_btn.setPopupMode(QToolButton.MenuButtonPopup)
        browse_btn.clicked.connect(self._on_browse_program)
        browse_menu = QMenu(browse_btn)
        browse_menu.addAction("Browse Path...", self._on_browse_path)
        browse_btn.setMenu(browse_menu)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._on_clear)

        button_col = QVBoxLayout()
        button_col.setSpacing(4)
        button_col.addWidget(browse_btn)
        button_col.addWidget(clear_btn)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)
        layout.addWidget(icon_label)
        layout.addLayout(text_layout, 1)
        layout.addLayout(button_col)

        self.refresh()

    def refresh(self) -> None:
        linked_path = self._config_store.get(self._key)
        if linked_path:
            self._path_label.setText(linked_path)
            self._status_label.setText("Linked")
            self._status_label.setProperty("linkStatus", "linked")
        else:
            self._path_label.setText("No path linked")
            self._status_label.setText("Not linked")
            self._status_label.setProperty("linkStatus", "not_linked")
        self._status_label.style().unpolish(self._status_label)
        self._status_label.style().polish(self._status_label)

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
    """Lets the user link each Program Database entry to a local executable
    path on this machine — per-machine data (PluginConfigStore, shared=False),
    since "what's installed here" is never team-shared. Other plugins/add-ons
    (e.g. MayaLauncher) read the same mapping by calling
    api.plugin_config_store("software_linker", shared=False) themselves —
    no coupling API needed, just agreeing on that id string. Renders one
    _ProgramLinkCard per linkable (Program, version) slot instead of a
    plain list row.

    Program Database is per-Project now (core/models.py's Project.programs).
    As of the single-project-per-session change, this always operates on
    local_config_store.active_project_id — the one project fixed for the
    whole run by launcher.py's mandatory Project Selector gate — rather
    than its own independent project picker (removed; there's nothing to
    pick anymore, every page in the app reads through the same fixed
    project id now)."""

    def __init__(self, parent=None, *, store, local_config_store, config_store):
        super().__init__(parent)
        self._store = store
        self._local_config_store = local_config_store
        self._config_store = config_store

        self.project_label = QLabel()

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
        layout.addWidget(QLabel("Project:"))
        layout.addWidget(self.project_label)
        layout.addWidget(scroll_area)

        self.refresh()

    def refresh(self) -> None:
        """Re-reads the active project's current name and rebuilds the
        link cards. Called on construction and via
        SettingsTabSpec.on_activated."""
        project_id = self._local_config_store.active_project_id
        project = self._store.get_project(project_id) if project_id else None
        self.project_label.setText(project.name if project is not None else "(no project)")
        self._rebuild_cards()

    def _rebuild_cards(self) -> None:
        while self._cards_layout.count() > 1:  # keep the trailing addStretch
            item = self._cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        project_id = self._local_config_store.active_project_id
        if project_id is None:
            return

        self._auto_detect_missing(project_id)
        for key, program, _version, label in _link_rows(self._store, project_id):
            card = _ProgramLinkCard(
                self._cards_container,
                store=self._store,
                config_store=self._config_store,
                key=key,
                program=program,
                label=label,
            )
            self._cards_layout.insertWidget(self._cards_layout.count() - 1, card)

    def _auto_detect_missing(self, project_id: str) -> None:
        # Best-effort only — checks the system PATH for an executable that
        # looks like the program's name, nothing more. Programs with no
        # match just stay unlinked until the user links one manually.
        for key, program, _version, _label in _link_rows(self._store, project_id):
            if self._config_store.get(key):
                continue
            guess = shutil.which(program.name.lower().replace(" ", ""))
            if guess:
                self._config_store.set(key, guess)


def register(api) -> None:
    api.register_settings_tab(
        SettingsTabSpec(
            key=PLUGIN_ID,
            label="Software Linker",
            order=100,
            page_factory=lambda: SoftwareLinkerPage(
                store=api.metadata,
                local_config_store=api.local_config,
                config_store=api.plugin_config_store(PLUGIN_ID, shared=False),
            ),
            on_activated=lambda page: page.refresh(),
        )
    )
