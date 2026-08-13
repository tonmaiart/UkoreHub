from __future__ import annotations

import qdarktheme
from PySide6.QtWidgets import QApplication


def apply_theme(app: QApplication, theme_name: str) -> None:
    # theme_name (local_config_store's persisted "grey_dark") is accepted
    # for signature/call-site compatibility with launcher.py and older
    # saved configs, but no longer selects anything — THEMES only ever had
    # the one dark entry, so qdarktheme's own "dark" mode is applied
    # unconditionally instead of a custom-built QSS stylesheet.
    del theme_name
    qdarktheme.setup_theme("dark")
