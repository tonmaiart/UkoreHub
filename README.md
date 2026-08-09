# UkoreHub

Pipeline tool to launch project in Ukore Studio.

UkoreHub is a Git repo launcher: it keeps a database-driven registry of Projects,
each containing one or more Repos. Pick a repo by clicking its node in the
Project Editor's graph (1 node = 1 repo) — the first click on an uncloned repo
asks to confirm — and it's cloned (first time) or pulled (every time after)
automatically
into a workspace folder of your choosing, no manual `git clone`/`git pull`
needed. From there you can browse the repo's files, and on the Repo Git Status
tab: scroll through its full commit history, stage modified files, and commit →
pull → push back to the remote — including a file-level (not line-level)
conflict resolution prompt if a pull produces a merge conflict, appropriate for
mostly-binary animation production assets.

## Prerequisites

- [git](https://git-scm.com/downloads)
- [git-lfs](https://git-lfs.com/)
- Python 3.10+

`UkoreHub.exe` checks for `git` and Python itself on startup and won't
auto-install either — if one's missing, it shows a "Download" button
linking straight to the official installer and stops there until you
install it and restart. Use the links above if you'd rather install
everything by hand up front (or need `git-lfs`, which is optional and
only warned about, never blocking).

## Running

`UkoreHub.exe` lives in its own repo,
[`UkoreHubLauncher`](https://github.com/tonmaiart/UkoreHubLauncher) — split
out so an ordinary app-code release can never try to overwrite the exe
file that's busy running it (see `developer/bug-history/2026-08-08-self-update-locked-own-exe.md`).
Double-click `UkoreHub.exe` (or pin it to the taskbar) — this is the
normal way to run UkoreHub, and the only way to complete a first-time
GitHub login (see below). In order: it checks `git` is present (showing a
Download button and stopping if not), brings its own folder up to date
with its own repo (rare — only on a launcher release), then bootstraps or
updates a nested `app/` folder from *this* repo (`UkoreHub`, a.k.a.
"UkoreHubRelease") the same way — even converting a plain GitHub "Download
ZIP" extract into a real git clone in place if that's how `app/` started —
before anything else, so a pending app update is never skipped, then
checks Python is present (same Download-button treatment) and `git-lfs`
(optional), handles GitHub login and caches the token, then launches the
real app from `app/` — see `UkoreHubLauncher`'s own README.md for the full
breakdown (`exe_entry.py`/`updater.py`).

Once logged in, you can also run the app directly from inside that `app/`
folder:

```bash
python launcher.py
```

This checks for Python package dependencies (PySide6, keyring) and installs
any that are missing automatically — no manual `pip install` step required.
It reads whatever GitHub token `UkoreHub.exe` already cached; **it cannot
complete a first-time login itself** — there is no login UI left in the
plain-Python app anymore, so run `UkoreHub.exe` at least once first. The
workspace folder (where cloned repos live) is fixed to `<this repo>/storage`.
Managers add Projects/Repos via the Project Editor section (a node graph, 1
node = 1 repo). Whatever's added there becomes available to pick as the
active repo by clicking its node in Project Editor — there is no separate
sidebar repo-picker button.

Admins rebuild and recommit `UkoreHub.exe` via `python build_exe.py` on
the separate `UkoreHubLauncher` repo's own `main` branch when rebranding
the icon, or when changing `exe_entry.py`/`updater.py` themselves (see
that repo's README.md) — routine code updates to this repo still flow
through **Update and Restart** / `git pull` as plain `.py` changes, exactly
as before; the exe itself rarely needs to change, and this repo no longer
carries it at all.

Setting > Program Database keeps a shared catalog of pipeline software (name,
icon, description) that repos can list as requirements at repo-creation
time (`RepoDialog`'s Requirements tree).

## System config vs. local config

Settings are split into two files with different sharing behavior:

- **System config** — `data/projects.json` (the Project/Repo registry, including
  each repo's thumbnail filename and required Program IDs), `data/system_config.json`
  (GitHub OAuth Client ID, GCS Bucket Name), and `data/programs.json` (the shared
  Program Database) are synced to/from a shared Google Cloud Storage bucket
  (`core/cloud_sync.py`) — pulled fresh on every launch, pushed automatically
  on every edit, no manual commit/push step needed. `assets/thumbnails/` and
  `assets/program_icons/` (repo thumbnails / program icons) are still **tracked
  in this git repo** instead, since they're binary images rather than the
  live-edited registries — a manager adding one still needs to
  `git add`/`commit`/`push`, and other artists get it via **Update and
  Restart** like before. Every artist needs to click **Login with
  Google** (the "Studio" button in the sidebar footer, next to Setting)
  once for the cloud-synced files to work — see "Google Cloud Sync Setup"
  below; without it, those stores just stay local-only on that machine.
- **Local config** — `cache/local_config.json` (workspace folder, color theme,
  which repo you currently have selected, cached GitHub username) and
  `cache/github_token.json` (GitHub token, only if the OS keyring isn't
  available). These live under `cache/`, not `data/`, and are gitignored and
  stay per-machine — everyone picks their own workspace folder and theme.
  Keeping them out of `data/` means a stray folder copy of the app (as
  opposed to a fresh `git clone`) never carries your login along with it.

## GitHub Login Setup (optional, needed for private repos)

The status bar's Login button uses GitHub's OAuth Device Flow. Logging in
does two things:

1. Shows your GitHub identity in the status bar.
2. **Lets UkoreHub clone/pull private `github.com` repos you have access to**,
   using your logged-in token automatically — no separate token or credential
   setup needed. This only applies to HTTPS `github.com` URLs; SSH URLs and
   any non-GitHub host still rely entirely on your system git credentials
   (SSH key / credential helper), exactly as before. If you're not logged in,
   private-repo clone/pull falls back to your system git credentials too — so
   logging in is optional, not required, if you already have those set up
   (e.g. an SSH key added to your GitHub account).

The token is stored via your OS keyring (or a gitignored local file if the
keyring isn't available) — never in `data/system_config.json` or
`data/projects.json`, since those are shared with the whole studio via
Google Cloud Storage.

To enable Login, register a public GitHub OAuth App (free, no approval needed):

1. Go to https://github.com/settings/developers → "New OAuth App".
2. Fill in any name/homepage URL (a callback URL is required by the form but
   unused by Device Flow — any placeholder URL works).
3. After creating the app, open its settings and enable **"Device Flow"**.
4. Copy the app's Client ID and paste it into **Setting > Common > GitHub OAuth
   Client ID** — no code changes needed.

Until this is configured, clicking Login shows a message pointing you to that
setting instead of attempting to log in.

## Google Cloud Sync Setup (needed for the shared registries to sync)

`data/projects.json`, `data/programs.json`, `data/system_config.json`, and
each `shared=True` `PluginConfigStore` file sync through a shared Google
Cloud Storage bucket instead of git (see "System config vs. local config"
above). Each artist authenticates as their own Google identity via an
OAuth browser login (opens automatically, same idea as GitHub Login above)
— because the studio's GCP organization enforces
`iam.disableServiceAccountKeyCreation`, so a shared service-account key
file isn't an option.

A studio admin sets this up once (see `data/README.md` for the exact
fields):

1. Create a GCS bucket and note its name + the GCP project ID it lives in.
2. In Google Cloud Console, set the OAuth consent screen's User Type —
   **Internal** if every artist is inside the same Google Workspace org
   (skips Google's verification review entirely); **External** if login
   needs to work for personal Google accounts outside the org too, which
   requires extra care around Google's unverified-app refresh-token expiry
   — see the note in `core/google_auth.py`'s module docstring before
   choosing this.
3. Create an OAuth client of type **"Desktop app"** and note its Client
   ID/Secret.
4. Create a Google Group with every artist's Google account as a member,
   and grant it the **Storage Object Admin** role on the bucket's own
   Permissions tab (not project-wide IAM).

Each artist then opens the **"Studio" button in the sidebar footer**
(next to the gear-icon Setting button — a separate window, not a Settings
tab) — the first time, this shows a login gate: paste in the Client
ID/Secret from step 3 (or use **Import from JSON...** to read them
straight from the `client_secret_*.json` Google Cloud Console offers to
download, which also fills in GCS Project ID) and click **Login with
Google**. That opens a browser to approve access, same idea as GitHub
Login above, and caches a refresh token via your OS keyring (or a
gitignored local file if the keyring isn't available). Once logged in,
the same window goes straight to the full form — GCS Bucket Name/Project
ID/Client ID/Secret, with an explicit **Save** button (not self-saving
per field, unlike every other Settings tab — a mistaken edit here would
repoint the whole studio's shared registry sync) — every time it's
reopened afterward, no gate shown again. Until an artist logs in, the
shared registries just stay local-only on their machine — nothing
crashes or blocks the app.

## Project layout

- `core/` — metadata store, git operations, theming, GitHub auth; no UI code.
- `interface/` — PySide6 GUI (sidebar, content pages, settings dialog, repo browser).
- `data/` — `projects.json`, `system_config.json`, `programs.json` (shared,
  synced via Google Cloud Storage), `thumbnails/`, `program_icons/` (shared,
  still git-tracked).
- `cache/` — `local_config.json`, `github_token.json`,
  `gcs_refresh_token.json`, `webengine_profile/`, `plugin_local_config/`
  (gitignored, per-machine — see `cache/README.md`), plus `plugins/`,
  per-repo plugin git clones.
- `launcher.py` — entry point.
- `developer/` — dev-only tooling (bug-history, glossary); lives only in
  this repo (UkoreHubDev), stripped when publishing to the separate
  UkoreHubRelease repo's `main` by `developer/commit-main.ps1` — see
  `developer/README.md`. `UkoreHub.exe` and its build tooling live in a
  separate repo entirely, `UkoreHubLauncher` — not part of this tree at
  all.
- `storage/` — workspace folder (gitignored; actual cloned repos live here).
  Named `storage/` rather than `projects/` so it can't be confused with
  `data/projects/`, the per-project metadata blobs (see `data/README.md`).

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```