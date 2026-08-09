from __future__ import annotations

from interface.section_registry import UICommandService, SectionSpec
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


def register(api) -> None:
    page = RepoGitStatusPage(store=api.metadata, local_config_store=api.local_config, git_service=api.git)
    icons_dir = api.app_root / "assets" / "icons"
    api.register_section(
        SectionSpec(
            key=SECTION_KEY,
            label="Submit",
            order=20,
            page_factory=lambda: page,
            background_threads=lambda p: [p._git_worker, p._status_worker, p._stream_worker],
            icon_path=icons_dir / "icons8-submit-50.png",
            wire=_wire,
            # SectionTabList lays this out at the right edge of Submit's own
            # row; the page updates its color directly (see
            # RepoGitStatusPage.status_dot / RepoStatusDot.set_state).
            trailing_widget_factory=lambda: page.status_dot,
        )
    )
