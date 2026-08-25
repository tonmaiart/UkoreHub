from __future__ import annotations

from PySide6.QtWidgets import QStyle

from plugin_api import NotificationSpec, SectionSpec, UICommandService
from plugins.core.submit.repo_git_status_page import RepoGitStatusPage

SECTION_KEY = "repo_git_status"


def _wire(page: RepoGitStatusPage, host: UICommandService) -> None:
    page.sync_started.connect(lambda: host.set_status_message(f"Syncing {page._repo.name}..."))
    page.sync_finished.connect(lambda: host.set_status_message(""))
    page.sync_failed.connect(lambda _message: host.set_status_message(""))
    # "repo_browser" is Explorer's SectionRegistry key
    # (plugins/core/explorer/plugin.py) — a literal string, not an
    # import, so this plugin's register(api) doesn't fail to load if
    # Explorer's plugin were ever missing/broken.
    page.browse_file_requested.connect(lambda path: host.navigate_and_focus("repo_browser", path))
    # Sync clones/pulls files on disk without switching the active repo, so
    # nothing else would ever tell Explorer's QFileSystemModel to rescan —
    # its own watcher can miss/lag a bulk change like this. Doesn't switch
    # Explorer's tab (see UICommandService.refresh_section), just tells it
    # to re-read its current folder if/when the user looks.
    page.sync_finished.connect(lambda: host.refresh_section("repo_browser"))


def register(api) -> None:
    page = RepoGitStatusPage(store=api.metadata, local_config_store=api.local_config, git_service=api.git)
    api.register_section(
        SectionSpec(
            key=SECTION_KEY,
            label="Submit",
            order=20,
            page_factory=lambda: page,
            background_threads=lambda p: [
                p._git_worker,
                p._status_worker,
                p._stream_worker,
                p._stage_worker,
                p._unstage_worker,
                p._revert_worker,
                p._diagnostics_worker,
                p._commit_log_worker,
            ],
            standard_icon=QStyle.SP_DialogSaveButton,
            wire=_wire,
        )
    )
    # listWidget_notification row — replaces the old tab-row status dot
    # (trailing_widget_factory) with a descriptive text row; the page
    # updates it directly (see RepoGitStatusPage.notification_widget /
    # _set_notification_state).
    api.register_notification(
        NotificationSpec(
            key=SECTION_KEY,
            order=20,
            widget_factory=lambda: page.notification_widget,
        )
    )
