from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPalette, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.github.token_store import TokenStore, TokenStoreFallbackUsed
from core.store import LocalConfigStore, SystemConfigStore
from core.theme import DEFAULT_THEME_NAME, get_theme
from interface.login.github_login_dialog import GitHubLoginDialog

_COLORS = get_theme(DEFAULT_THEME_NAME)
_LOGO_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "icons" / "GitHubLogo.png"
_LOGO_WIDTH = 320


class LoginOverlay(QWidget):
    """Mandatory GitHub login gate — set as MainWindow's central widget by
    itself (see MainWindow._show_login_gate) instead of a separate popup
    window, and instead of being drawn on top of the real main UI: the real
    UI (sidebar, every section's page, Settings) isn't even constructed
    until login succeeds, so there's nothing underneath this to cover or
    fight with over z-order/painting. Only the initial "Login with Github"
    step lives here; the OAuth device-flow code entry (GitHubLoginDialog)
    still shows as its own small popup since the user has to read a code
    and switch to a browser tab."""

    login_completed = Signal()

    def __init__(
        self,
        parent: QWidget,
        *,
        system_config_store: SystemConfigStore,
        local_config_store: LocalConfigStore,
        token_store: TokenStore,
    ):
        super().__init__(parent)
        self.setObjectName("loginOverlay")
        # A plain QWidget's QSS background-color only paints if
        # Qt.WA_StyledBackground is set — easy to get wrong and end up with
        # an invisible "opaque" overlay that lets everything underneath
        # bleed through except the child widgets. Setting the palette
        # directly + autoFillBackground is the reliable way to just paint a
        # solid color here.
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(_COLORS.background))
        self.setPalette(palette)
        self.system_config_store = system_config_store
        self.local_config_store = local_config_store
        self.token_store = token_store
        self._login_dialog: GitHubLoginDialog | None = None

        logo = QLabel()
        logo.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(str(_LOGO_PATH)) if _LOGO_PATH.exists() else QPixmap()
        if not pixmap.isNull():
            logo.setPixmap(pixmap.scaledToWidth(_LOGO_WIDTH, Qt.SmoothTransformation))
        else:
            # Falls back to text if the asset is ever missing/renamed — same
            # convention as sidebar.py's Setting button and
            # browser_widget.py's nav icons.
            logo.setText("GitHub")
            logo.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {_COLORS.text_primary};")

        login_btn = QPushButton("Login with Github")
        login_btn.setCursor(Qt.PointingHandCursor)
        login_btn.setMinimumWidth(220)
        login_btn.clicked.connect(self._on_login_clicked)

        content = QVBoxLayout()
        content.setSpacing(0)
        content.addWidget(logo)
        content.addSpacing(28)
        content.addWidget(login_btn, alignment=Qt.AlignCenter)

        centering_row = QHBoxLayout()
        centering_row.addStretch()
        centering_row.addLayout(content)
        centering_row.addStretch()

        outer = QVBoxLayout(self)
        outer.addStretch()
        outer.addLayout(centering_row)
        outer.addStretch()

    def _on_login_clicked(self) -> None:
        if not self.system_config_store.github_client_id:
            QMessageBox.information(
                self,
                "GitHub Login",
                "No GitHub OAuth Client ID configured yet. Ask a studio admin to "
                "set one (Setting > Common, reachable once someone is logged in — "
                "or by editing data/system_config.json directly).",
            )
            return
        self._login_dialog = GitHubLoginDialog(self, client_id=self.system_config_store.github_client_id)
        if not self._login_dialog.exec():
            return
        username = self._login_dialog.username
        token = self._login_dialog.token
        try:
            self.token_store.save_token(token)
        except TokenStoreFallbackUsed as exc:
            QMessageBox.warning(self, "GitHub Login", str(exc))
        self.local_config_store.set_github_username(username)
        self.login_completed.emit()
