from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from core.extensibility import notification_bus
from core.extensibility.config_store import PluginConfigStore
from core.extensibility.notification_bus import NotificationEntry
from core.git_service import GitService
from core.paths import resolve_repo_path
from core.store import LocalConfigStore
from interface.shared.commit_history import CommitHistoryEntry
from plugins.core.Notification.commit_feed_worker import CommitFeedWorker
from plugins.core.Notification.notification_card import NotificationCard

SECTION_KEY = "notification"
_LAST_SEEN_KEY = "last_seen_at"
_LAST_COMMIT_KEY_PREFIX = "last_commit_hash::"
_POLL_INTERVAL_MS = 30 * 60 * 1000
_BACKFILL_COUNT = 10


class NotificationPage(QWidget):
    """Notification's one section page — a scrollable list of NotificationCard
    for whatever notification_bus.entries_for(active_project_id,
    active_repo_id) currently returns (project-wide entries plus entries
    scoped to the active repo). Tracks "has the user opened this tab" via a
    per-machine PluginConfigStore (last_seen_at). badge_label is this page's
    own unread-count widget — plugin.py hands it to SectionSpec as a
    trailing_widget_factory (interface/section_registry.py), so
    SectionTabList only ever lays it out; this page updates its text/
    visibility directly, no SectionHost round-trip needed.

    Also owns the team activity feed: a CommitFeedWorker poll (every
    _POLL_INTERVAL_MS, plus on every repo switch and the manual Refresh
    button) that diffs the active repo's commit log against a per-repo
    last-known-hash (also in config_store) and pushes any new commits into
    notification_bus itself — see _on_feed_entries."""

    def __init__(
        self,
        *,
        local_config_store: LocalConfigStore,
        config_store: PluginConfigStore,
        git_service: GitService,
        parent=None,
    ):
        super().__init__(parent)
        self._local_config = local_config_store
        self._config_store = config_store
        self._git_service = git_service
        self._project = None
        self._repo = None
        self._workspace_root = None
        self._feed_worker: CommitFeedWorker | None = None

        self.badge_label = QLabel()
        self.badge_label.setObjectName("sectionTabBadge")
        self.badge_label.setVisible(False)

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self._poll_now)
        header_row = QHBoxLayout()
        header_row.addStretch(1)
        header_row.addWidget(refresh_button)

        self._cards_container = QWidget()
        self._cards_layout = QVBoxLayout(self._cards_container)
        self._cards_layout.setContentsMargins(10, 10, 10, 10)
        self._cards_layout.setSpacing(6)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setWidget(self._cards_container)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(header_row)
        layout.addWidget(scroll_area)

        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(_POLL_INTERVAL_MS)
        self._poll_timer.timeout.connect(self._poll_now)
        self._poll_timer.start()

        self._refresh()

    # -- wiring (see plugin.py's _wire) --------------------------------------

    def on_bus_event(self, _entry: NotificationEntry) -> None:
        self._refresh()

    # -- section-page convention (MainWindow calls this on every repo switch)

    def set_repo(self, project, repo, workspace_root) -> None:
        self._project = project
        self._repo = repo
        self._workspace_root = workspace_root
        self._refresh()
        self._poll_now()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._mark_seen()

    # -- team activity feed ----------------------------------------------

    def _poll_now(self) -> None:
        if self._project is None or self._repo is None or self._workspace_root is None:
            return
        if self._feed_worker is not None and self._feed_worker.isRunning():
            return
        dest_path = resolve_repo_path(self._workspace_root, self._project.name, self._repo.name)
        if not self._git_service.is_cloned(dest_path):
            return
        project, repo = self._project, self._repo
        self._feed_worker = CommitFeedWorker(self._git_service, dest_path, self._git_service.get_github_token())
        self._feed_worker.entries_ready.connect(lambda entries: self._on_feed_entries(project, repo, entries))
        self._feed_worker.start()

    def _on_feed_entries(self, project, repo, entries: list[CommitHistoryEntry]) -> None:
        if not entries:
            return
        key = f"{_LAST_COMMIT_KEY_PREFIX}{repo.id}"
        last_hash = self._config_store.get(key)
        if last_hash is None:
            # First time this repo's feed has ever been polled — show a
            # small amount of recent history instead of either flooding with
            # the whole repo's history or (with no baseline at all) silently
            # waiting for the *next* commit to show anything.
            new_entries = entries[:_BACKFILL_COUNT]
        else:
            hashes = [entry.hash for entry in entries]
            new_entries = entries[: hashes.index(last_hash)] if last_hash in hashes else entries
        self._config_store.set(key, entries[0].hash)
        for entry in reversed(new_entries):
            message = entry.message.splitlines()[0] if entry.message else ""
            notification_bus.push(
                source="git",
                project_id=project.id,
                repo_id=repo.id,
                label=f"{entry.author_display}: {message}",
                icon_bytes=entry.avatar_bytes,
            )

    # -- internals ------------------------------------------------------

    def _visible_entries(self) -> list[NotificationEntry]:
        project_id = self._local_config.active_project_id
        if not project_id:
            return []
        return notification_bus.entries_for(project_id, self._local_config.active_repo_id)

    def _refresh(self) -> None:
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        entries = self._visible_entries()
        if not entries:
            empty_label = QLabel("No notifications yet.")
            empty_label.setProperty("secondary", True)
            self._cards_layout.addWidget(empty_label)
        else:
            for entry in entries:
                self._cards_layout.addWidget(NotificationCard(entry))
        self._cards_layout.addStretch(1)
        self._recompute_badge()

    def _mark_seen(self) -> None:
        self._config_store.set(_LAST_SEEN_KEY, datetime.now().isoformat())
        self._recompute_badge()

    def _recompute_badge(self) -> None:
        last_seen = self._config_store.get(_LAST_SEEN_KEY)
        unseen = [e for e in self._visible_entries() if last_seen is None or e.timestamp.isoformat() > last_seen]
        count = len(unseen)
        if count:
            self.badge_label.setText(str(count) if count <= 99 else "99+")
            self.badge_label.setVisible(True)
        else:
            self.badge_label.setVisible(False)
