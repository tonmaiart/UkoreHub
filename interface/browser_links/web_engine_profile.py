from __future__ import annotations

from pathlib import Path

from PySide6.QtWebEngineCore import QWebEngineProfile


def make_persistent_browser_link_profile(storage_dir: Path, parent) -> QWebEngineProfile:
    """One QWebEngineProfile shared by every Browser Link tab (see
    interface/browser_links/browser_link_page.py), with disk-backed persistent
    cookies so a login (Notion, Google Sheet, ...) survives quitting and
    relaunching the app instead of being cleared every session. `parent`
    should outlive every BrowserLinkPage using it — MainWindow constructs
    this once and passes it to each Browser Link tab it builds."""
    profile = QWebEngineProfile("UkoreHubBrowserLinks", parent)
    profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
    storage_dir.mkdir(parents=True, exist_ok=True)
    profile.setPersistentStoragePath(str(storage_dir))
    return profile
