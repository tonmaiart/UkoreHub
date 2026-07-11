from __future__ import annotations

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QListWidget,
    QStackedWidget,
    QVBoxLayout,
)

from core.git_service import GitService
from core.store import LocalConfigStore, MetadataStore, SystemConfigStore
from interface.settings_pages.color_theme_page import ColorThemePage
from interface.settings_pages.common_settings_page import CommonSettingsPage
from interface.settings_pages.project_data_editor_page import ProjectDataEditorPage
from interface.settings_pages.project_status_page import ProjectStatusPage
from interface.theme_apply import apply_theme

TAB_NAMES = ["Common", "Project Status", "Project Data Editor", "Color Theme"]


class SettingsDialog(QDialog):
    def __init__(
        self,
        parent=None,
        *,
        store: MetadataStore,
        local_config_store: LocalConfigStore,
        system_config_store: SystemConfigStore,
        git_service: GitService,
    ):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(700, 500)
        self.local_config_store = local_config_store
        self.system_config_store = system_config_store
        self._initial_theme = local_config_store.theme

        self.tab_list = QListWidget()
        self.tab_list.addItems(TAB_NAMES)
        self.tab_list.setFixedWidth(180)

        self.common_page = CommonSettingsPage(
            workspace_root=local_config_store.workspace_root or "",
            github_client_id=system_config_store.github_client_id or "",
        )
        self.project_status_page = ProjectStatusPage(store=store, local_config_store=local_config_store)
        self.project_data_page = ProjectDataEditorPage(store=store, local_config_store=local_config_store)
        self.color_theme_page = ColorThemePage(current_theme=local_config_store.theme)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.common_page)
        self.stack.addWidget(self.project_status_page)
        self.stack.addWidget(self.project_data_page)
        self.stack.addWidget(self.color_theme_page)

        self.tab_list.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.tab_list.currentRowChanged.connect(self._on_tab_changed)
        self.tab_list.setCurrentRow(0)

        top_row = QHBoxLayout()
        top_row.addWidget(self.tab_list)
        top_row.addWidget(self.stack, stretch=1)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self._on_cancel)

        layout = QVBoxLayout(self)
        layout.addLayout(top_row)
        layout.addWidget(buttons)

    def _on_tab_changed(self, _row: int) -> None:
        if self.stack.currentWidget() is self.project_status_page:
            self.project_status_page.refresh()

    def _on_save(self) -> None:
        self.local_config_store.set_workspace_root(self.common_page.workspace_root())
        self.local_config_store.set_theme(self.color_theme_page.selected_theme_name())
        self.system_config_store.set_github_client_id(self.common_page.github_client_id())
        self.accept()

    def _on_cancel(self) -> None:
        app = QApplication.instance()
        if app:
            apply_theme(app, self._initial_theme)
        self.reject()
