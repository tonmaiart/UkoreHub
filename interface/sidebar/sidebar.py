from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget

from interface.login.github_auth_widget import GitHubAuthWidget
from interface.section_registry import SectionRegistry
from interface.sidebar.active_repo_widget import ActiveRepoWidget
from interface.sidebar.section_tab_list import SectionTabList

SIDEBAR_WIDTH = 260
SETTING_ICON_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "icons" / "setting.png"


class Sidebar(QWidget):
    """Left-hand navigation column — replaces the old horizontal MenuBar
    row. Top to bottom: ActiveRepoWidget (thumbnail banner + "Project /
    Repo" picker button), the repo-scoped SectionTabList (Explorer/Submit/
    About, plus a dynamic row per Browser Link — stretched to fill the
    remaining height), and a footer strip for sync status, the Update
    button, and an account row (GitHub avatar/username + an icon-only
    Setting button right after it). Logging out lives in Settings > Common
    now, not here — GitHubAuthWidget's toggle button is hidden in this
    context (Sidebar only ever shows a logged-in user)."""

    update_requested = Signal()
    repo_picker_requested = Signal()
    navigation_changed = Signal(str)
    settings_requested = Signal()

    def __init__(self, parent=None, *, section_registry: SectionRegistry):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(SIDEBAR_WIDTH)

        self.active_repo_widget = ActiveRepoWidget()
        self.active_repo_widget.repo_picker_requested.connect(self.repo_picker_requested.emit)

        self.tab_list = SectionTabList(section_registry=section_registry)
        self.tab_list.navigation_changed.connect(self.navigation_changed.emit)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)

        self.update_button = QPushButton("Update and Restart")
        self.update_button.clicked.connect(self.update_requested.emit)
        self.update_button.setVisible(False)

        self.sync_progress_bar = QProgressBar()
        self.sync_progress_bar.setRange(0, 0)
        self.sync_progress_bar.setVisible(False)

        self.github_auth_widget = GitHubAuthWidget(show_toggle_button=False)

        self.setting_button = QPushButton()
        self.setting_button.setObjectName("sidebarSettingButton")
        self.setting_button.setToolTip("Setting")
        if SETTING_ICON_PATH.exists():
            self.setting_button.setIcon(QIcon(str(SETTING_ICON_PATH)))
            self.setting_button.setIconSize(QSize(18, 18))
        else:
            self.setting_button.setText("Setting")
        self.setting_button.clicked.connect(self.settings_requested.emit)

        account_row = QHBoxLayout()
        account_row.addWidget(self.github_auth_widget, stretch=1)
        account_row.addWidget(self.setting_button)

        footer = QWidget()
        footer.setObjectName("sidebarFooter")
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(10, 8, 10, 10)
        footer_layout.setSpacing(6)
        footer_layout.addWidget(self.status_label)
        footer_layout.addWidget(self.sync_progress_bar)
        footer_layout.addWidget(self.update_button)
        footer_layout.addLayout(account_row)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.active_repo_widget)
        layout.addWidget(self.tab_list, stretch=1)
        layout.addWidget(footer)

    def set_sync_message(self, text: str) -> None:
        self.status_label.setText(text)

    def set_update_available(self, available: bool) -> None:
        self.update_button.setVisible(available)
