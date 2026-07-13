from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.addon_store import AddonMetadataStore, group_addon_ids_by_program
from core.exceptions import NotFoundError
from core.extensibility.loader import DiscoveredPlugin, plugin_source
from core.git_service import GitService
from core.models import Program, Project, Repo
from core.os_utils import open_in_file_explorer
from core.paths import resolve_repo_path
from core.program_store import ProgramStore
from core.store import LocalConfigStore, MetadataStore

ICON_SIZE = 40


class RequirementCard(QFrame):
    def __init__(self, program: Program, icon_path, parent=None, *, addon_cards: list[QWidget] | None = None):
        super().__init__(parent)
        self.setObjectName("requirementCard")
        self.setFrameShape(QFrame.StyledPanel)

        icon_label = QLabel()
        icon_label.setFixedSize(ICON_SIZE, ICON_SIZE)
        if icon_path and icon_path.exists():
            pixmap = QPixmap(str(icon_path))
            icon_label.setPixmap(
                pixmap.scaled(ICON_SIZE, ICON_SIZE, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            )
        else:
            icon_label.setText("\U0001F4E6")
            icon_label.setAlignment(Qt.AlignCenter)

        version_suffix = f"  ·  v{program.version}" if program.version else ""
        header_label = QLabel(f"<b>{program.name}</b>{version_suffix}")
        header_label.setWordWrap(True)
        body_label = QLabel(program.description or "No description.")
        body_label.setWordWrap(True)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.addWidget(header_label)
        text_layout.addWidget(body_label)
        for addon_card in addon_cards or []:
            indented_row = QHBoxLayout()
            indented_row.addSpacing(ICON_SIZE // 2)
            indented_row.addWidget(addon_card, stretch=1)
            text_layout.addLayout(indented_row)

        row_layout = QHBoxLayout(self)
        row_layout.addWidget(icon_label, alignment=Qt.AlignTop)
        row_layout.addLayout(text_layout, stretch=1)


class AddonCard(QFrame):
    def __init__(self, discovered: DiscoveredPlugin, parent=None):
        super().__init__(parent)
        self.setObjectName("addonCard")
        self.setFrameShape(QFrame.StyledPanel)

        manifest = discovered.manifest
        source_label = QLabel(plugin_source(discovered).upper())
        source_label.setFixedWidth(56)
        source_label.setAlignment(Qt.AlignCenter | Qt.AlignTop)

        header_label = QLabel(f"<b>{manifest.name}</b>  ·  v{manifest.version}")
        header_label.setWordWrap(True)
        body_label = QLabel(manifest.description or "No description.")
        body_label.setWordWrap(True)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.addWidget(header_label)
        text_layout.addWidget(body_label)

        row_layout = QHBoxLayout(self)
        row_layout.addWidget(source_label, alignment=Qt.AlignTop)
        row_layout.addLayout(text_layout, stretch=1)


class RepoAboutPage(QWidget):
    def __init__(
        self,
        parent=None,
        *,
        store: MetadataStore,
        local_config_store: LocalConfigStore,
        program_store: ProgramStore,
        addon_store: AddonMetadataStore,
        git_service: GitService,
        addon_catalog: list[DiscoveredPlugin],
    ):
        super().__init__(parent)
        self.program_store = program_store
        self.addon_store = addon_store
        self._addon_by_id = {discovered.manifest.id: discovered for discovered in addon_catalog}
        self._project: Project | None = None
        self._repo: Repo | None = None
        self._workspace_root: str | None = None

        self.empty_label = QLabel("Select a repo to see this information.")

        self.name_label = QLabel("—")
        self.git_url_label = QLabel("—")
        self.git_url_label.setWordWrap(True)
        self.local_path_label = QLabel("—")
        self.local_path_label.setWordWrap(True)
        self.last_synced_label = QLabel("—")
        self.status_label = QLabel("—")

        form = QFormLayout()
        form.addRow("Name:", self.name_label)
        form.addRow("Git URL:", self.git_url_label)
        form.addRow("Local Path:", self.local_path_label)
        form.addRow("Last Synced:", self.last_synced_label)
        form.addRow("Status:", self.status_label)

        self.open_folder_button = QPushButton("Open Folder")
        self.open_folder_button.clicked.connect(self._on_open_folder)

        self.requirements_group = QGroupBox("Requirements")
        self.requirements_layout = QVBoxLayout(self.requirements_group)
        self.requirements_layout.addStretch()

        self.addons_group = QGroupBox("Other Add-ons")
        self.addons_layout = QVBoxLayout(self.addons_group)
        self.addons_layout.addStretch()

        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.addLayout(form)
        content_layout.addWidget(self.open_folder_button)
        content_layout.addWidget(self.requirements_group)
        content_layout.addWidget(self.addons_group)
        content_layout.addStretch()

        layout = QVBoxLayout(self)
        layout.addWidget(self.empty_label)
        layout.addWidget(self.content_widget)
        self.content_widget.setVisible(False)

    def set_repo(self, project: Project | None, repo: Repo | None, workspace_root: str | None) -> None:
        self._project = project
        self._repo = repo
        self._workspace_root = workspace_root
        if repo is None:
            self.empty_label.setVisible(True)
            self.content_widget.setVisible(False)
            return
        self.empty_label.setVisible(False)
        self.content_widget.setVisible(True)
        self.name_label.setText(repo.name)
        self.git_url_label.setText(repo.git_url)
        abs_path = resolve_repo_path(workspace_root, project.name, repo.name)
        self.local_path_label.setText(str(abs_path))
        self.last_synced_label.setText(repo.last_synced or "Never")
        self.status_label.setText(repo.status)

        by_program, ungrouped_addon_ids = group_addon_ids_by_program(repo.enabled_addon_ids, self.addon_store)
        required_ids = set(repo.required_program_ids)

        requirement_cards = []
        for program_id in repo.required_program_ids:
            try:
                program = self.program_store.get_program(program_id)
            except NotFoundError:
                continue
            icon_path = self.program_store.resolve_icon_path(program)
            nested_addon_cards = [
                AddonCard(self._addon_by_id[addon_id])
                for addon_id in by_program.get(program_id, [])
                if addon_id in self._addon_by_id
            ]
            requirement_cards.append(RequirementCard(program, icon_path, addon_cards=nested_addon_cards))
        self._replace_cards(self.requirements_layout, requirement_cards)

        # Add-ons with no declared required program, or whose declared
        # program isn't one of this repo's own requirements, still need to
        # show up somewhere rather than silently vanish.
        other_addon_ids = list(ungrouped_addon_ids)
        for program_id, addon_ids in by_program.items():
            if program_id not in required_ids:
                other_addon_ids.extend(addon_ids)

        addon_cards = [
            AddonCard(self._addon_by_id[addon_id]) for addon_id in other_addon_ids if addon_id in self._addon_by_id
        ]
        self.addons_group.setVisible(bool(addon_cards))
        self._replace_cards(self.addons_layout, addon_cards)

    @staticmethod
    def _replace_cards(layout: QVBoxLayout, cards: list[QWidget]) -> None:
        while layout.count() > 1:  # keep the trailing stretch
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for card in cards:
            layout.insertWidget(layout.count() - 1, card)

    def _on_open_folder(self) -> None:
        if self._repo is None:
            return
        abs_path = resolve_repo_path(self._workspace_root, self._project.name, self._repo.name)
        if not abs_path.exists():
            QMessageBox.information(self, "Open Folder", "This repo has not been cloned yet.")
            return
        if not open_in_file_explorer(abs_path):
            QMessageBox.warning(self, "Open Folder", "Could not open the file explorer.")
