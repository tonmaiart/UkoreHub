from __future__ import annotations

from PySide6.QtWidgets import QPushButton, QWidget

from interface.sidebar_footer_action_registry import SidebarFooterActionSpec
from plugins.core.CloudConfig.studio_settings_dialog import StudioSettingsDialog

FOOTER_ACTION_KEY = "cloud_config_studio_setting"


def register(api) -> None:
    def _build_footer_widget() -> QWidget:
        button = QPushButton("Studio")
        button.setObjectName("sidebarStudioSettingButton")
        button.setToolTip("Studio Setting")
        button.clicked.connect(lambda: _open_dialog(button))
        return button

    def _open_dialog(owner: QWidget) -> None:
        # Constructed fresh on every open — no state carried between opens,
        # same convention every other Settings entry point follows.
        dialog = StudioSettingsDialog(
            owner.window(), system_config_store=api.system_config_store, cache_dir=api.cache_dir
        )
        dialog.exec()

    api.register_sidebar_footer_action(
        SidebarFooterActionSpec(
            key=FOOTER_ACTION_KEY,
            order=100,
            widget_factory=_build_footer_widget,
        )
    )
