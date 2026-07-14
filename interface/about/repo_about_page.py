from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.addon_store import AddonMetadataStore, group_addon_ids_by_program
from core.exceptions import NotFoundError, UkoreHubError
from core.extensibility.loader import DiscoveredPlugin
from core.git_service import GitService
from core.models import BrowserLink, Program, Project, Repo
from core.os_utils import open_in_file_explorer
from core.paths import resolve_repo_path
from core.program_store import ProgramStore
from core.store import LocalConfigStore, MetadataStore
from interface.repo_addon_panel_registry import RepoAddonPanelRegistry
from interface.shared.dialogs import RequirementsEditDialog
from interface.shared.image_asset import pick_image_file, save_image_asset
from interface.shared.widget_helpers import show_exclusive, wrap_scrollable

ICON_SIZE = 40


class _DescriptionEditDialog(QDialog):
    """Lightweight text-only edit dialog — a smaller alternative to the
    full ProgramDialog (which also edits name/version/icon), used for the
    inline "Edit Description" affordance on a RequirementCard, and for the
    repo's own description on the About sub-tab (_RepoAboutInfoTab)."""

    def __init__(self, parent=None, *, title: str, description: str):
        super().__init__(parent)
        self.setWindowTitle(f"Edit Description — {title}")

        self.description_edit = QTextEdit(description)
        self.description_edit.setFixedHeight(80)

        form = QFormLayout()
        form.addRow("Description:", self.description_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def description(self) -> str:
        return self.description_edit.toPlainText().strip()


class RequirementCard(QFrame):
    def __init__(
        self,
        program: Program,
        icon_path,
        parent=None,
        *,
        addon_cards: list[QWidget] | None = None,
        program_store: ProgramStore | None = None,
    ):
        super().__init__(parent)
        self.setObjectName("requirementCard")
        self.setFrameShape(QFrame.StyledPanel)
        self._program = program
        self._program_store = program_store

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
        self.body_label = QLabel(program.description or "No description.")
        self.body_label.setWordWrap(True)

        header_row = QHBoxLayout()
        header_row.addWidget(header_label, stretch=1)
        if program_store is not None:
            edit_description_button = QPushButton("Edit Description")
            edit_description_button.setFlat(True)
            edit_description_button.clicked.connect(self._on_edit_description)
            header_row.addWidget(edit_description_button)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.addLayout(header_row)
        text_layout.addWidget(self.body_label)
        for addon_card in addon_cards or []:
            indented_row = QHBoxLayout()
            indented_row.addSpacing(ICON_SIZE // 2)
            indented_row.addWidget(addon_card, stretch=1)
            text_layout.addLayout(indented_row)

        row_layout = QHBoxLayout(self)
        row_layout.addWidget(icon_label, alignment=Qt.AlignTop)
        row_layout.addLayout(text_layout, stretch=1)

    def _on_edit_description(self) -> None:
        if self._program_store is None:
            return
        dialog = _DescriptionEditDialog(self, title=self._program.name, description=self._program.description)
        if not dialog.exec():
            return
        try:
            self._program_store.edit_program(
                self._program.id,
                name=self._program.name,
                description=dialog.description(),
                version=self._program.version,
            )
        except UkoreHubError as exc:
            QMessageBox.warning(self, "Edit Description", str(exc))
            return
        self._program.description = dialog.description()
        self.body_label.setText(self._program.description or "No description.")


class AddonCard(QFrame):
    def __init__(self, discovered: DiscoveredPlugin, icon_path=None, parent=None):
        super().__init__(parent)
        self.setObjectName("addonCard")
        self.setFrameShape(QFrame.StyledPanel)

        manifest = discovered.manifest

        icon_label = QLabel()
        icon_label.setFixedSize(ICON_SIZE, ICON_SIZE)
        if icon_path and icon_path.exists():
            pixmap = QPixmap(str(icon_path))
            icon_label.setPixmap(
                pixmap.scaled(ICON_SIZE, ICON_SIZE, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            )
        else:
            icon_label.setText("\U0001F9E9")
            icon_label.setAlignment(Qt.AlignCenter)

        header_label = QLabel(f"<b>{manifest.name}</b>  ·  v{manifest.version}")
        header_label.setWordWrap(True)
        body_label = QLabel(manifest.description or "No description.")
        body_label.setWordWrap(True)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.addWidget(header_label)
        text_layout.addWidget(body_label)

        row_layout = QHBoxLayout(self)
        row_layout.addWidget(icon_label, alignment=Qt.AlignTop)
        row_layout.addLayout(text_layout, stretch=1)


class _RepoAboutInfoTab(QWidget):
    """"About" sub-tab: the repo's basic info + Open Folder + Choose
    Thumbnail (moved here from Settings > Project Data Editor, see
    thumbnail_changed below)."""

    thumbnail_changed = Signal()

    def __init__(self, parent=None, *, store: MetadataStore):
        super().__init__(parent)
        self.store = store
        self._project: Project | None = None
        self._repo: Repo | None = None
        self._workspace_root: str | None = None

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

        self.description_label = QLabel("No description.")
        self.description_label.setWordWrap(True)
        edit_description_button = QPushButton("Edit Description")
        edit_description_button.setFlat(True)
        edit_description_button.clicked.connect(self._on_edit_description)
        description_header_row = QHBoxLayout()
        description_header_row.addWidget(QLabel("<b>Description</b>"), stretch=1)
        description_header_row.addWidget(edit_description_button)

        self.open_folder_button = QPushButton("Open Folder")
        self.open_folder_button.clicked.connect(self._on_open_folder)

        self.thumbnail_preview = QLabel("No image")
        self.thumbnail_preview.setFixedSize(160, 90)
        self.thumbnail_preview.setScaledContents(True)
        choose_thumbnail_button = QPushButton("Choose Thumbnail...")
        choose_thumbnail_button.clicked.connect(self._on_choose_thumbnail)
        thumbnail_row = QHBoxLayout()
        thumbnail_row.addWidget(self.thumbnail_preview)
        thumbnail_row.addWidget(choose_thumbnail_button)
        thumbnail_row.addStretch()

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(description_header_row)
        layout.addWidget(self.description_label)
        layout.addWidget(self.open_folder_button)
        layout.addLayout(thumbnail_row)
        layout.addStretch()

    def set_repo(self, project: Project | None, repo: Repo | None, workspace_root: str | None) -> None:
        self._project = project
        self._repo = repo
        self._workspace_root = workspace_root
        if repo is None:
            return
        self.name_label.setText(repo.name)
        self.git_url_label.setText(repo.git_url)
        abs_path = resolve_repo_path(workspace_root, project.name, repo.name)
        self.local_path_label.setText(str(abs_path))
        self.last_synced_label.setText(repo.last_synced or "Never")
        self.status_label.setText(repo.status)
        self.description_label.setText(repo.description or "No description.")
        self._refresh_thumbnail_preview()

    def _refresh_thumbnail_preview(self) -> None:
        thumbnail_path = self.store.resolve_thumbnail_path(self._repo) if self._repo else None
        if thumbnail_path and thumbnail_path.exists():
            self.thumbnail_preview.setPixmap(QPixmap(str(thumbnail_path)))
        else:
            self.thumbnail_preview.setText("No image")

    def _on_edit_description(self) -> None:
        if self._repo is None or self._project is None:
            return
        dialog = _DescriptionEditDialog(self, title=self._repo.name, description=self._repo.description)
        if not dialog.exec():
            return
        self.store.set_repo_description(self._project.id, self._repo.id, dialog.description())
        self._repo.description = dialog.description()
        self.description_label.setText(self._repo.description or "No description.")

    def _on_open_folder(self) -> None:
        if self._repo is None:
            return
        abs_path = resolve_repo_path(self._workspace_root, self._project.name, self._repo.name)
        if not abs_path.exists():
            QMessageBox.information(self, "Open Folder", "This repo has not been cloned yet.")
            return
        if not open_in_file_explorer(abs_path):
            QMessageBox.warning(self, "Open Folder", "Could not open the file explorer.")

    def _on_choose_thumbnail(self) -> None:
        if self._repo is None or self._project is None:
            return
        source_path = pick_image_file(self, "Choose Thumbnail Image")
        if source_path is None:
            return
        filename = save_image_asset(
            self, source_path=source_path, dest_dir=self.store.thumbnails_dir, asset_id=self._repo.id
        )
        if filename is None:
            return
        self.store.set_repo_thumbnail(self._project.id, self._repo.id, filename)
        self._repo.thumbnail_filename = filename
        self._refresh_thumbnail_preview()
        self.thumbnail_changed.emit()


class _RepoRequirementsTab(QWidget):
    """"Requirement" sub-tab: required Programs (each with its enabled
    Add-ons nested under it) + any enabled Add-ons that don't declare one
    of this repo's requirements, plus an Edit Requirements button (moved
    here from Settings > Project Data Editor, see requirements_changed
    below)."""

    requirements_changed = Signal()

    def __init__(
        self,
        parent=None,
        *,
        store: MetadataStore,
        program_store: ProgramStore,
        addon_store: AddonMetadataStore,
        addon_catalog: list[DiscoveredPlugin],
    ):
        super().__init__(parent)
        self.store = store
        self.program_store = program_store
        self.addon_store = addon_store
        self.addon_catalog = addon_catalog
        self._addon_by_id = {discovered.manifest.id: discovered for discovered in addon_catalog}
        self._project: Project | None = None
        self._repo: Repo | None = None

        edit_requirements_button = QPushButton("Edit Requirements...")
        edit_requirements_button.clicked.connect(self._on_edit_requirements)

        self.requirements_group = QGroupBox("Requirements")
        self.requirements_layout = QVBoxLayout(self.requirements_group)
        self.requirements_layout.addStretch()

        self.addons_group = QGroupBox("Other Add-ons")
        self.addons_layout = QVBoxLayout(self.addons_group)
        self.addons_layout.addStretch()

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.addWidget(self.requirements_group)
        content_layout.addWidget(self.addons_group)
        content_layout.addStretch()

        scroll = wrap_scrollable(content)

        layout = QVBoxLayout(self)
        layout.addWidget(edit_requirements_button)
        layout.addWidget(scroll)

    def set_repo(self, project: Project | None, repo: Repo | None, workspace_root: str | None) -> None:
        self._project = project
        self._repo = repo
        if repo is None:
            return
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
                AddonCard(self._addon_by_id[addon_id], icon_path=self._resolve_addon_icon(addon_id))
                for addon_id in by_program.get(program_id, [])
                if addon_id in self._addon_by_id
            ]
            requirement_cards.append(
                RequirementCard(
                    program, icon_path, addon_cards=nested_addon_cards, program_store=self.program_store
                )
            )
        self._replace_cards(self.requirements_layout, requirement_cards)

        # Add-ons with no declared required program, or whose declared
        # program isn't one of this repo's own requirements, still need to
        # show up somewhere rather than silently vanish.
        other_addon_ids = list(ungrouped_addon_ids)
        for program_id, addon_ids in by_program.items():
            if program_id not in required_ids:
                other_addon_ids.extend(addon_ids)

        addon_cards = [
            AddonCard(self._addon_by_id[addon_id], icon_path=self._resolve_addon_icon(addon_id))
            for addon_id in other_addon_ids
            if addon_id in self._addon_by_id
        ]
        self.addons_group.setVisible(bool(addon_cards))
        self._replace_cards(self.addons_layout, addon_cards)

    def _resolve_addon_icon(self, addon_id: str):
        return self.addon_store.resolve_display_icon_path(self.addon_store.get(addon_id))

    def _on_edit_requirements(self) -> None:
        if self._repo is None or self._project is None:
            return
        dialog = RequirementsEditDialog(
            self,
            program_store=self.program_store,
            addon_catalog=self.addon_catalog,
            addon_store=self.addon_store,
            selected_program_ids=self._repo.required_program_ids,
            selected_addon_ids=self._repo.enabled_addon_ids,
        )
        if not dialog.exec():
            return
        program_ids = dialog.selected_program_ids()
        addon_ids = dialog.selected_addon_ids()
        self.store.set_repo_requirements(self._project.id, self._repo.id, program_ids)
        self.store.set_repo_enabled_addons(self._project.id, self._repo.id, addon_ids)
        self._repo.required_program_ids = program_ids
        self._repo.enabled_addon_ids = addon_ids
        self.set_repo(self._project, self._repo, None)
        self.requirements_changed.emit()

    @staticmethod
    def _replace_cards(layout: QVBoxLayout, cards: list[QWidget]) -> None:
        while layout.count() > 1:  # keep the trailing stretch
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for card in cards:
            layout.insertWidget(layout.count() - 1, card)


class _RepoBrowserLinksTab(QWidget):
    """"Browser" sub-tab: add/rename/remove this repo's Browser Links —
    each shown as its own top-level tab elsewhere, see
    interface/main_window.py's dynamic tab rebuild."""

    browser_links_changed = Signal()

    def __init__(self, parent=None, *, store: MetadataStore):
        super().__init__(parent)
        self.store = store
        self._project: Project | None = None
        self._repo: Repo | None = None

        self._rows_container = QWidget()
        self._rows_layout = QVBoxLayout(self._rows_container)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)

        self.new_link_name_edit = QLineEdit()
        self.new_link_name_edit.setPlaceholderText("Name (e.g. Google Sheet)")
        self.new_link_url_edit = QLineEdit()
        self.new_link_url_edit.setPlaceholderText("https://...")
        add_link_button = QPushButton("Add Link")
        add_link_button.clicked.connect(self._on_add_browser_link)
        add_link_row = QHBoxLayout()
        add_link_row.addWidget(self.new_link_name_edit)
        add_link_row.addWidget(self.new_link_url_edit, stretch=1)
        add_link_row.addWidget(add_link_button)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.addWidget(self._rows_container)
        content_layout.addLayout(add_link_row)
        content_layout.addStretch()

        scroll = wrap_scrollable(content)

        layout = QVBoxLayout(self)
        layout.addWidget(scroll)

    def set_repo(self, project: Project | None, repo: Repo | None, workspace_root: str | None) -> None:
        self._project = project
        self._repo = repo
        self._rebuild_rows()

    def _rebuild_rows(self) -> None:
        while self._rows_layout.count():
            item = self._rows_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        if self._repo is None:
            return
        for index, link in enumerate(self._repo.browser_links):
            row_widget = QWidget()
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(0, 0, 0, 0)
            icon_label = QLabel()
            icon_label.setFixedSize(24, 24)
            icon_path = self.store.resolve_browser_link_icon_path(link)
            if icon_path and icon_path.exists():
                icon_label.setPixmap(
                    QPixmap(str(icon_path)).scaled(24, 24, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                )
            row.addWidget(icon_label)
            row.addWidget(QLabel(f"<b>{link.name}</b>"))
            url_label = QLabel(link.url)
            url_label.setWordWrap(True)
            row.addWidget(url_label, stretch=1)
            change_icon_button = QPushButton("Change Icon...")
            change_icon_button.clicked.connect(lambda _checked, i=index: self._on_change_browser_link_icon(i))
            row.addWidget(change_icon_button)
            rename_button = QPushButton("Rename")
            rename_button.clicked.connect(lambda _checked, i=index: self._on_rename_browser_link(i))
            row.addWidget(rename_button)
            remove_button = QPushButton("Remove")
            remove_button.clicked.connect(lambda _checked, i=index: self._on_remove_browser_link(i))
            row.addWidget(remove_button)
            self._rows_layout.addWidget(row_widget)

    def _on_add_browser_link(self) -> None:
        if self._repo is None or self._project is None:
            return
        name = self.new_link_name_edit.text().strip()
        url = self.new_link_url_edit.text().strip()
        if not name or not url:
            QMessageBox.information(self, "Add Link", "Enter both a name and a URL.")
            return
        links = list(self._repo.browser_links) + [BrowserLink(name=name, url=url)]
        self._save_browser_links(links)
        self.new_link_name_edit.clear()
        self.new_link_url_edit.clear()

    def _on_rename_browser_link(self, index: int) -> None:
        if self._repo is None or self._project is None:
            return
        links = list(self._repo.browser_links)
        if not (0 <= index < len(links)):
            return
        new_name, ok = QInputDialog.getText(self, "Rename Link", "New name:", text=links[index].name)
        if not ok or not new_name.strip():
            return
        links[index] = BrowserLink(
            name=new_name.strip(), url=links[index].url, icon_filename=links[index].icon_filename
        )
        self._save_browser_links(links)

    def _on_remove_browser_link(self, index: int) -> None:
        if self._repo is None or self._project is None:
            return
        links = list(self._repo.browser_links)
        if 0 <= index < len(links):
            del links[index]
        self._save_browser_links(links)

    def _on_change_browser_link_icon(self, index: int) -> None:
        if self._repo is None or self._project is None:
            return
        links = self._repo.browser_links
        if not (0 <= index < len(links)):
            return
        source_path = pick_image_file(self, "Choose Browser Link Icon")
        if source_path is None:
            return
        filename = save_image_asset(
            self,
            source_path=source_path,
            dest_dir=self.store.browser_link_icons_dir,
            asset_id=f"{self._repo.id}_{index}",
        )
        if filename is None:
            return
        self.store.set_browser_link_icon(self._project.id, self._repo.id, index, filename)
        links[index].icon_filename = filename
        self._rebuild_rows()
        self.browser_links_changed.emit()

    def _save_browser_links(self, links: list[BrowserLink]) -> None:
        self.store.set_repo_browser_links(self._project.id, self._repo.id, links)
        self._repo.browser_links = links
        self._rebuild_rows()
        self.browser_links_changed.emit()


class RepoAboutPage(QWidget):
    """Left-tab-bar shell (like SettingsView) with fixed sub-tabs About /
    Requirement / Browser, plus one dynamic sub-tab per add-on the active
    repo has enabled that registered a per-repo panel via
    PluginAPI.register_repo_addon_panel(...) — rebuilt on every set_repo()
    since that set depends on Repo.enabled_addon_ids. This is where
    MayaLauncher's own panel now shows up (it used to live under the
    now-removed Repo tab's "Repo Add-on" sub-tab)."""

    browser_links_changed = Signal()
    thumbnail_changed = Signal()

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
        repo_addon_panel_registry: RepoAddonPanelRegistry,
    ):
        super().__init__(parent)
        self._repo_addon_panel_registry = repo_addon_panel_registry
        self._addon_by_id = {discovered.manifest.id: discovered for discovered in addon_catalog}
        self._project: Project | None = None
        self._repo: Repo | None = None

        self.empty_label = QLabel("Select a repo to see this information.")

        self.info_tab = _RepoAboutInfoTab(store=store)
        self.info_tab.thumbnail_changed.connect(self.thumbnail_changed.emit)
        self.requirements_tab = _RepoRequirementsTab(
            store=store, program_store=program_store, addon_store=addon_store, addon_catalog=addon_catalog
        )
        self.requirements_tab.requirements_changed.connect(self._on_requirements_changed)
        self.browser_links_tab = _RepoBrowserLinksTab(store=store)
        self.browser_links_tab.browser_links_changed.connect(self.browser_links_changed.emit)

        self._fixed_tabs: list[tuple[str, QWidget]] = [
            ("About", self.info_tab),
            ("Requirement", self.requirements_tab),
            ("Browser", self.browser_links_tab),
        ]
        self._dynamic_addon_widgets: list[QWidget] = []

        self.tab_list = QListWidget()
        self.tab_list.setFixedWidth(160)
        self.stack = QStackedWidget()
        for label, widget in self._fixed_tabs:
            self.tab_list.addItem(label)
            self.stack.addWidget(widget)
        self.tab_list.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.tab_list.setCurrentRow(0)

        self.content_widget = QWidget()
        content_layout = QHBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(self.tab_list)
        content_layout.addWidget(self.stack, stretch=1)

        # Big left/right spacers narrow the effective width of the page
        # (Discord/VS Code Settings style) rather than letting the tab list
        # + stack stretch edge-to-edge across a maximized window.
        centered_row = QHBoxLayout()
        centered_row.addStretch(1)
        centered_row.addWidget(self.content_widget, stretch=4)
        centered_row.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addWidget(self.empty_label)
        layout.addLayout(centered_row)
        self.content_widget.setVisible(False)

    def set_repo(self, project: Project | None, repo: Repo | None, workspace_root: str | None) -> None:
        self._project = project
        self._repo = repo
        if repo is None:
            show_exclusive(self.empty_label, self.content_widget)
            return
        show_exclusive(self.content_widget, self.empty_label)

        self.info_tab.set_repo(project, repo, workspace_root)
        self.requirements_tab.set_repo(project, repo, workspace_root)
        self.browser_links_tab.set_repo(project, repo, workspace_root)
        self._rebuild_addon_tabs(repo)

    def _on_requirements_changed(self) -> None:
        # Editing enabled_addon_ids from the Requirement sub-tab can add or
        # remove one of this page's own dynamic per-add-on sub-tabs — rebuild
        # them immediately rather than waiting for the next set_repo().
        if self._repo is not None:
            self._rebuild_addon_tabs(self._repo)

    def _rebuild_addon_tabs(self, repo: Repo) -> None:
        fixed_count = len(self._fixed_tabs)
        was_on_dynamic = self.tab_list.currentRow() >= fixed_count

        while self.tab_list.count() > fixed_count:
            self.tab_list.takeItem(fixed_count)
        for widget in self._dynamic_addon_widgets:
            self.stack.removeWidget(widget)
            widget.deleteLater()
        self._dynamic_addon_widgets = []

        for addon_id in repo.enabled_addon_ids:
            spec = self._repo_addon_panel_registry.get(addon_id)
            if spec is None:
                continue  # enabled but no registered panel — silently skip
            discovered = self._addon_by_id.get(addon_id)
            title = discovered.manifest.name if discovered else addon_id
            panel = spec.panel_factory(repo)
            self.tab_list.addItem(title)
            self.stack.addWidget(panel)
            self._dynamic_addon_widgets.append(panel)

        if was_on_dynamic:
            self.tab_list.setCurrentRow(0)
