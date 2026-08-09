# plugins/core/Notification/

The first sidebar tab (`SectionSpec(order=1)`) — provides the shared card
template and an in-memory socket (`core/extensibility/notification_bus.py`)
that any other plugin can push into, the one page that renders entries and
tracks whether the user has seen them, **and** its own team activity feed:
`NotificationPage` polls the active repo's commit log itself (`git
fetch` + diff against a per-repo last-known hash) and pushes new commits
into the same bus — see "Team activity feed" below. It's the only producer
that runs unconditionally; every other plugin's push is opt-in.

## Using the socket from another plugin

```python
from core.extensibility import notification_bus

notification_bus.push(
    source="YourPlugin",
    project_id=project.id,
    repo_id=repo.id,       # or None — see "Scope" below
    label="Build finished for Character_Rig",
    icon_path=your_icon_path,       # optional, Path | None — a static icon file
    icon_bytes=avatar_bytes,        # optional, bytes | None — already-downloaded image
                                     # data (e.g. a GitHub avatar); takes priority over
                                     # icon_path in NotificationCard when both are set
    on_click=lambda: open_something(),  # optional, Callable[[], None]
)
```

No `api` handle needed — same direct-import, "construct/reach directly,
convention not import" pattern `core/extensibility/debug_log.py` already
uses (see `plugins/core/DebugConsole/README.md` for that precedent).
Safe to call from deep runtime code (a background worker callback, a git
hook handler, etc.), not just inside `register(api)`.

## Scope: who decides "current Repo" vs. "All Repo in this project"

The **producer** decides at push time via `repo_id`:
- A specific `repo_id` → the notification only shows while that repo is
  active.
- `repo_id=None` → the notification shows regardless of which repo in that
  `project_id` is currently active.

The Notification page has no manual "This Repo / All Repos" toggle — it
auto-filters by whichever repo is active (`notification_bus.entries_for`),
consistent with the producer already having made that call.

## Team activity feed

`notification_bus` is per-machine/in-memory only — it has no server behind
it, so a notification pushed on one person's machine (e.g. the old
submit-plugin "I just pushed" entry) was never visible to anyone else's
UkoreHub. To actually show *everyone's* commits, `NotificationPage` sources
its own entries from the repo's git history instead — that's already
shared, via the remote, without needing any new backend:

- **When it polls**: a `QTimer` every 30 minutes while the app is running,
  plus immediately on every repo switch (`set_repo`) and the page's own
  Refresh button (`_poll_now`).
- **How it fetches**: `CommitFeedWorker` (`commit_feed_worker.py`, a
  `QThread`) runs `GitService.fetch()` first — remote-tracking refs only,
  never the working tree, so it's safe to run silently in the background —
  then reads recent commits the same GitHub-API-first/local-git-fallback
  way `interface/shared/commit_history.py`'s other callers already do
  (`origin/<branch>` when
  falling back to local, so commits nobody has pulled into this clone yet
  still show up).
- **Dedup**: `_on_feed_entries` diffs the fetched list against a per-repo
  last-known commit hash (`PluginConfigStore` key
  `last_commit_hash::<repo.id>`) and only pushes hashes newer than that
  into `notification_bus`, oldest-first (so the true newest commit ends up
  on top — bus entries sort by push-time timestamp, not commit date). The
  very first poll for a repo has no baseline yet; rather than either
  flooding with the whole history or showing nothing until the *next*
  commit, it backfills the `_BACKFILL_COUNT` (10) most recent commits once
  and starts diffing from there.
- **Label**: `"{author_display}: {first line of message}"` — unlike the
  removed submit-plugin push notification, the author matters here since
  entries can now come from any teammate, not just "you".
- **Avatar**: `entry.avatar_bytes` (the author's GitHub avatar, fetched by
  `fetch_entries_via_github` — see `interface/shared/commit_history.py`) is
  forwarded as `icon_bytes` on the `notification_bus.push()` call, so
  `NotificationCard` shows the same profile picture the Explorer/Submit
  commit-history cards do. `None` when the local-git fallback path was used
  instead (offline, or no github.com remote) — the card just shows no icon
  in that case, same as any other icon-less producer.

Because this feed already reflects every push to the remote, submit's own
push-completion notification was removed (see `plugins/core/submit/README.md`)
rather than kept alongside it as a near-duplicate.

## Not persisted

`notification_bus`'s entries live in memory only for the running session —
same reasoning as `debug_log.py`: a notification's `on_click` is a live
Python callback, which can't survive an app restart anyway. Only "has the
user opened this tab" (`last_seen_at`) and the team activity feed's
per-repo `last_commit_hash::<repo.id>` baseline are persisted, in a
per-machine `PluginConfigStore` (`api.plugin_config_store("notification",
shared=False)`) — never shared between users, same as `software_linker`'s
per-machine link paths. The per-repo hash is what keeps a re-poll (30-minute
timer, repo switch, Refresh button) from re-showing commits already seen.

## Files

- `manifest.json` — plugin id `notification`.
- `plugin.py` — `register(api)`: builds one `NotificationPage`, registers it
  as a section at `order=1` (lower than any other non-persistent section,
  so it's always first), wires it to `notification_bus.add_listener`, and
  hands `page.badge_label` to `SectionSpec.trailing_widget_factory`. Also
  wires `background_threads` to `page._feed_worker` for
  `MainWindow.closeEvent`'s shutdown cleanup (same contract every
  QThread-backed page opts into).
- `notification_card.py` — `NotificationCard(QFrame)`: the shared card
  template (icon, label, date/time, optional click action). Only clickable
  (pointer cursor + hover highlight) when the pushed entry has an
  `on_click`.
- `commit_feed_worker.py` — `CommitFeedWorker(QThread)`: the team activity
  feed's own poll — fetch + commit-log read off the UI thread, emits
  `entries_ready(list[CommitHistoryEntry])`. See "Team activity feed" above.
- `notification_page.py` — `NotificationPage`: the scrollable card list.
  Filters via `notification_bus.entries_for`, refreshes on every bus push
  and every repo switch (`set_repo`, the convention every section page
  implements), and marks the cache "seen" (clearing the badge) in
  `showEvent` — i.e. whenever the tab is actually switched to. Also owns
  `badge_label`, a plain `QLabel(objectName="sectionTabBadge")` it updates
  directly (see "Unread badge" below), the Refresh button, and the
  `CommitFeedWorker` poll described above.

## Unread badge

`interface/section_registry.py`'s `SectionSpec.trailing_widget_factory` is a
general-purpose slot — a small widget shown at the right edge of a
section's own sidebar row, built once and laid out by
`interface/sidebar/section_tab_list.py`'s `SectionTabList`, which never
touches its content. It exists specifically so a future feature can put
*any* status widget there (not just a count), added while building this
plugin's unread badge but not Notification-specific.

Notification's own usage: `plugin.py` passes `lambda: page.badge_label`,
and `NotificationPage._recompute_badge` sets that label's text/visibility
directly (red background/white text via `interface/theme.py`'s
`QLabel#sectionTabBadge` rule) whenever a notification arrives, the active
repo changes, or the tab is marked seen. No `UICommandService` round-trip —
the page just owns the widget.

Every sidebar row (fixed sections and dynamic Browser Link tabs alike) is
built as one composite widget via `SectionTabList._add_row`/`setItemWidget`,
not a native `QListWidgetItem` icon/text — this is what makes a row with a
trailing widget (Notification) look identical to one without (Explorer,
Submit, ...): every row goes through the exact same construction path, none
is a special case.
