from __future__ import annotations

from core.extensibility import notification_bus
from interface.section_registry import SectionHost, SectionSpec
from plugins.core.Notification.notification_page import SECTION_KEY, NotificationPage

PLUGIN_ID = "notification"


def _wire(page: NotificationPage, host: SectionHost) -> None:
    notification_bus.add_listener(page.on_bus_event)


def register(api) -> None:
    icons_dir = api.app_root / "assets" / "icons"
    page = NotificationPage(
        local_config_store=api.local_config,
        config_store=api.plugin_config_store(PLUGIN_ID, shared=False),
        git_service=api.git,
    )
    api.register_section(
        SectionSpec(
            key=SECTION_KEY,
            label="Notification",
            # Lower than every other non-persistent section's order (Explorer
            # is the current lowest at 10) so this lands first in the sidebar.
            order=1,
            icon_path=icons_dir / "icons8-notification-50.png",
            page_factory=lambda: page,
            wire=_wire,
            # SectionTabList lays this out at the right edge of Notification's
            # own row and never touches its content — the page updates
            # badge_label's text/visibility itself (see
            # NotificationPage._recompute_badge).
            trailing_widget_factory=lambda: page.badge_label,
            # Page owns a CommitFeedWorker (team activity feed poll) that can
            # be mid-run when the app closes — same closeEvent
            # terminate()+wait() contract as every other QThread-backed page.
            background_threads=lambda p: [p._feed_worker],
        )
    )
