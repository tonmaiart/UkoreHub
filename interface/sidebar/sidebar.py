from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget

from interface.section_registry import SectionRegistry
from interface.sidebar.active_repo_widget import ActiveRepoWidget
from interface.sidebar.section_tab_list import SectionTabList
from interface.sidebar_footer_action_registry import SidebarFooterActionRegistry

SIDEBAR_WIDTH = 230
SETTING_ICON_PATH = Path(__file__).resolve().parent.parent.parent / "assets" / "icons" / "setting.png"


class Sidebar(QWidget):
    """Left-hand navigation column — replaces the old horizontal MenuBar
    row. Top to bottom: ActiveRepoWidget (display-only repo thumbnail +
    name label — no click-to-open picker anymore, see that widget's own
    docstring), the repo-scoped SectionTabList (Explorer/Submit/About/
    Project Editor, plus a dynamic row per Browser Link — stretched to fill
    the remaining height), and a footer
    strip for sync status, SidebarFooterActionRegistry-provided widgets
    (e.g. plugins/core/CloudConfig/'s "Studio" button, opening its own
    StudioSettingsDialog — the gated Google Cloud Storage sync config,
    deliberately its own window rather than a Setting tab), a
    display-only account_label (the GitHub username — actual login/logout happens in
    the launcher exe, see updater.py (UkoreHubLauncher repo); MainWindow just
    pushes local_config_store.github_username in here, and Settings >
    Common's Logout button clears it and relaunches to the login screen —
    see main_window.py's _on_logout_requested), and the icon-only Setting
    button. Double-clicking a node in Project Editor's graph is the only
    way to change the active repo."""

    navigation_changed = Signal(str)
    external_link_activated = Signal(str)
    settings_requested = Signal()

    def __init__(
        self, parent=None, *, section_registry: SectionRegistry, sidebar_footer_action_registry: SidebarFooterActionRegistry
    ):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(SIDEBAR_WIDTH)

        self.active_repo_widget = ActiveRepoWidget()

        self.tab_list = SectionTabList(section_registry=section_registry)
        self.tab_list.navigation_changed.connect(self.navigation_changed.emit)
        self.tab_list.external_link_activated.connect(self.external_link_activated.emit)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)

        self.sync_progress_bar = QProgressBar()
        self.sync_progress_bar.setRange(0, 0)
        self.sync_progress_bar.setVisible(False)

        self.account_label = QLabel("")

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
        account_row.addWidget(self.account_label, stretch=1)
        account_row.addWidget(self.setting_button)

        footer = QWidget()
        footer.setObjectName("sidebarFooter")
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(10, 8, 10, 10)
        footer_layout.setSpacing(6)
        footer_layout.addWidget(self.status_label)
        footer_layout.addWidget(self.sync_progress_bar)
        # One widget per SidebarFooterActionRegistry entry — stored keyed by
        # spec.key so MainWindow.closeEvent can reach a plugin's own
        # background_threads without Sidebar knowing what they are.
        self.footer_action_widgets: dict[str, QWidget] = {}
        for spec in sidebar_footer_action_registry.ordered():
            widget = spec.widget_factory()
            self.footer_action_widgets[spec.key] = widget
            footer_layout.addWidget(widget)
        footer_layout.addLayout(account_row)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.active_repo_widget)
        layout.addWidget(self.tab_list, stretch=1)
        layout.addWidget(footer)

    def set_sync_message(self, text: str) -> None:
        self.status_label.setText(text)

    def set_account_username(self, username: str | None) -> None:
        self.account_label.setText(username or "")
