from __future__ import annotations

import subprocess

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QListView,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from core.exceptions import NotFoundError
from core.models import Program, Project, Repo
from core.storage.metadata_store import MetadataStore
from interface.theme import DEFAULT_THEME_NAME, get_theme
from interface.program_launch_registry import ProgramLaunchRegistry
from interface.section_registry import UICommandService, SectionSpec

PLUGIN_ID = "program_launcher"
# Convention-only string match with plugins/core/software_linker/plugin.py
# — both resolve to the same cache/plugin_local_config/software_linker.json
# via PluginConfigStore, no coupling API needed. Same pattern
# plugins/repo_internal/maya_launcher uses to find a linked executable.
SOFTWARE_LINKER_PLUGIN_ID = "software_linker"

_CARD_SIZE = QSize(120, 120)
_CARD_ICON_SIZE = QSize(56, 56)


def _linked_key(program: Program, version: str = "") -> str:
    """Per-machine Software Linker config key for a Program (+ version).
    Convention-only duplicate of plugins/core/software_linker/plugin.py's
    own _linked_key() (and plugins/repo_internal/maya_launcher/link_resolution.py's
    linked_key()) — keep all three in sync if this shape ever changes."""
    if len(program.versions) <= 1:
        return program.id
    return f"{program.id}:{version}"


def _pinned_version(repo: Repo, program: Program) -> str:
    """Which version of a multi-version Program this repo launches —
    repo.program_version_pins wins if it names a version the Program still
    has; otherwise the catalog's first version (or "" if it has none).
    Convention-only duplicate of
    plugins/repo_internal/maya_launcher/link_resolution.py's pinned_version()."""
    pin = repo.program_version_pins.get(program.id)
    if pin and pin in program.versions:
        return pin
    return program.versions[0] if program.versions else ""


class _ProgramCard(QWidget):
    """One square card: the Program's own icon (Program Database, same
    icon Settings > Program Database shows) on top, name + version below.
    Double-click opens the linked executable if this Program/version is
    linked in Settings > Software Linker, or emits the same signal so the
    page can jump straight to that tab if it isn't linked yet — the card
    itself carries no separate button."""

    double_clicked = Signal()

    def __init__(self, *, icon_pixmap: QPixmap, name: str, version: str, linked: bool, parent=None):
        super().__init__(parent)
        self.setFixedSize(_CARD_SIZE)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(
            "Double-click to open."
            if linked
            else "Not linked yet — double-click to open Software Linker settings."
        )

        icon_label = QLabel()
        icon_label.setPixmap(icon_pixmap)
        icon_label.setAlignment(Qt.AlignCenter)

        name_label = QLabel(name)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setWordWrap(True)
        name_font = name_label.font()
        name_font.setBold(True)
        name_label.setFont(name_font)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        layout.addWidget(icon_label)
        layout.addWidget(name_label)

        colors = get_theme(DEFAULT_THEME_NAME)
        if version:
            version_label = QLabel(f"v{version}")
            version_label.setAlignment(Qt.AlignCenter)
            version_label.setStyleSheet(f"color: {colors.text_secondary};")
            layout.addWidget(version_label)
        if not linked:
            status_label = QLabel("Not linked")
            status_label.setAlignment(Qt.AlignCenter)
            status_label.setStyleSheet(f"color: {colors.warning}; font-size: 10px;")
            layout.addWidget(status_label)

    def mouseDoubleClickEvent(self, event) -> None:
        self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)


class ProgramLauncherPage(QWidget):
    """A grid of square cards, one per Program the active repo requires
    (Repo.required_program_ids) — double-click a linked card to launch it,
    or a not-yet-linked one to jump straight to Settings > Software Linker
    (via bind_open_settings_tab). The header's "Software Linker Setting"
    button is the same shortcut, always available regardless of which
    cards are linked."""

    def __init__(
        self,
        parent=None,
        *,
        store: MetadataStore,
        config_store,
        program_launch_registry: ProgramLaunchRegistry,
    ):
        super().__init__(parent)
        self._store = store
        self._config_store = config_store
        self._program_launch_registry = program_launch_registry
        self._project: Project | None = None
        self._repo: Repo | None = None
        self._open_settings_tab = None

        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Program Launcher"))
        header_layout.addStretch()
        software_linker_button = QPushButton("Software Linker Setting")
        software_linker_button.clicked.connect(self._on_open_software_linker)
        header_layout.addWidget(software_linker_button)

        self._status_label = QLabel("No active repo selected.")

        self._grid = QListWidget()
        self._grid.setViewMode(QListView.IconMode)
        self._grid.setFlow(QListView.LeftToRight)
        self._grid.setWrapping(True)
        self._grid.setResizeMode(QListView.Adjust)
        self._grid.setMovement(QListView.Static)
        self._grid.setSelectionMode(QAbstractItemView.NoSelection)
        self._grid.setSpacing(12)
        self._grid.setUniformItemSizes(True)

        layout = QVBoxLayout(self)
        layout.addLayout(header_layout)
        layout.addWidget(self._status_label)
        layout.addWidget(self._grid)

    def bind_open_settings_tab(self, open_settings_tab) -> None:
        self._open_settings_tab = open_settings_tab

    def set_repo(self, project: Project | None, repo: Repo | None, workspace_root: str | None) -> None:
        self._project = project
        self._repo = repo
        self._refresh()

    def _refresh(self) -> None:
        self._grid.clear()

        if self._repo is None or self._project is None:
            self._status_label.setText("No active repo selected.")
            self._status_label.show()
            self._grid.hide()
            return

        programs = []
        for program_id in self._repo.required_program_ids:
            try:
                programs.append(self._store.get_program(self._project.id, program_id))
            except NotFoundError:
                continue

        if not programs:
            self._status_label.setText(
                "This repo has no required Programs yet. Add some under "
                "Repository Setting > Requirements."
            )
            self._status_label.show()
            self._grid.hide()
            return

        self._status_label.hide()
        self._grid.show()
        for program in sorted(programs, key=lambda p: p.name.lower()):
            self._add_card(program)

    def _add_card(self, program: Program) -> None:
        version = _pinned_version(self._repo, program)
        exe_path = self._config_store.get(_linked_key(program, version))
        card = _ProgramCard(
            icon_pixmap=self._resolve_icon_pixmap(program),
            name=program.name,
            version=version,
            linked=bool(exe_path),
        )
        card.double_clicked.connect(lambda: self._on_card_double_clicked(program, exe_path))

        item = QListWidgetItem()
        item.setSizeHint(card.sizeHint())
        self._grid.addItem(item)
        self._grid.setItemWidget(item, card)

    def _resolve_icon_pixmap(self, program: Program) -> QPixmap:
        icon_path = self._store.resolve_program_icon_path(program)
        if icon_path and icon_path.exists():
            pixmap = QPixmap(str(icon_path))
            if not pixmap.isNull():
                return pixmap.scaled(_CARD_ICON_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        # No custom icon set under Settings > Program Database — a generic
        # placeholder beats an empty label.
        fallback = self.style().standardIcon(QStyle.SP_ComputerIcon)
        return fallback.pixmap(_CARD_ICON_SIZE)

    def _on_card_double_clicked(self, program: Program, exe_path: str | None) -> None:
        if not exe_path:
            self._on_open_software_linker()
            return
        # A plugin (e.g. maya_launcher) may need to launch this Program
        # with its own setProject/env-merge wiring instead of a bare
        # process launch — see interface/program_launch_registry.py.
        launcher = self._program_launch_registry.find_launcher(program)
        if launcher is not None:
            launcher(self._repo)
            return
        try:
            subprocess.Popen([exe_path])
        except OSError as exc:
            QMessageBox.warning(self, program.name, f"Could not launch {program.name}:\n{exc}")

    def _on_open_software_linker(self) -> None:
        if self._open_settings_tab is not None:
            self._open_settings_tab(SOFTWARE_LINKER_PLUGIN_ID)


def _wire(page: ProgramLauncherPage, host: UICommandService) -> None:
    page.bind_open_settings_tab(host.open_settings_tab)


def register(api) -> None:
    icons_dir = api.app_root / "assets" / "icons"
    api.register_section(
        SectionSpec(
            key=PLUGIN_ID,
            label="Program Launcher",
            order=40,
            icon_path=icons_dir / "icons8-booster-64.png",
            page_factory=lambda: ProgramLauncherPage(
                store=api.metadata,
                config_store=api.plugin_config_store(SOFTWARE_LINKER_PLUGIN_ID, shared=False),
                program_launch_registry=api.program_launch_registry,
            ),
            wire=_wire,
        )
    )
