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

Double-click `UkoreHub.exe` at the repo root (or pin it to the taskbar) —
this is the normal way to run UkoreHub, and the only way to complete a
first-time GitHub login (see below). In order: it checks `git` is present
(showing a Download button and stopping if not), brings this folder up to
date with `origin/main` (even converting a plain GitHub "Download ZIP"
extract into a real git clone in place, if that's how you got this
folder) — before anything else, so a pending update is never skipped —
then checks Python is present (same Download-button treatment) and
`git-lfs` (optional), handles GitHub login and caches the token, then
launches the real app — see `developer/packaging/README.md` for the full
breakdown (`exe_entry.py`/`updater.py`).

Once logged in, you can also run the app directly:

```bash
python launcher.py
```

This checks for Python package dependencies (PySide6, keyring) and installs
any that are missing automatically — no manual `pip install` step required.
It reads whatever GitHub token `UkoreHub.exe` already cached; **it cannot
complete a first-time login itself** — there is no login UI left in the
plain-Python app anymore, so run `UkoreHub.exe` at least once first. The
workspace folder (where cloned repos live) is fixed to `<this repo>/projects`.
Managers add Projects/Repos via the Project Editor section (a node graph, 1
node = 1 repo). Whatever's added there becomes available to pick as the
active repo by clicking its node in Project Editor — there is no separate
sidebar repo-picker button.

Admins rebuild and recommit `UkoreHub.exe` via
`python developer/packaging/build_exe.py` on this repo's (UkoreHubDev)
`main` branch when rebranding the icon, or when changing
`developer/packaging/exe_entry.py`/
`updater.py` themselves (see `developer/packaging/README.md`) — routine
code updates elsewhere still flow through **Update and Restart** / `git
pull` as plain `.py` changes, exactly as before; the exe itself rarely
needs to change.

Setting > Program Database keeps a shared catalog of pipeline software (name,
icon, description) that repos can list as requirements at repo-creation
time (`RepoDialog`'s Requirements tree).

## System config vs. local config

Settings are split into two files with different sharing behavior:

- **System config** — `data/projects.json` (the Project/Repo registry, including
  each repo's thumbnail filename and required Program IDs), `data/system_config.json`
  (GitHub OAuth Client ID), `data/thumbnails/` (repo thumbnail images), and
  `data/programs.json` + `data/program_icons/` (the shared Program Database).
  These are **tracked in this git repo**, not gitignored, because they're meant
  to be the same for everyone at the studio — images are accepted as binary/
  larger files here deliberately, same reasoning as the registry itself. When
  a manager changes any of these, someone needs to `git add`/`commit`/`push`
  for the change to reach other machines — other artists then get it the
  normal way, e.g. by clicking **Update and Restart** (which runs `git pull`)
  or any other `git pull` of this repo. UkoreHub itself does not auto-commit
  or push on your behalf.
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
`data/projects.json`, since those are shared with the whole team via git.

To enable Login, register a public GitHub OAuth App (free, no approval needed):

1. Go to https://github.com/settings/developers → "New OAuth App".
2. Fill in any name/homepage URL (a callback URL is required by the form but
   unused by Device Flow — any placeholder URL works).
3. After creating the app, open its settings and enable **"Device Flow"**.
4. Copy the app's Client ID and paste it into **Setting > Common > GitHub OAuth
   Client ID** — no code changes needed.

Until this is configured, clicking Login shows a message pointing you to that
setting instead of attempting to log in.

## Project layout

- `core/` — metadata store, git operations, theming, GitHub auth; no UI code.
- `interface/` — PySide6 GUI (sidebar, content pages, settings dialog, repo browser).
- `data/` — `projects.json`, `system_config.json`, `thumbnails/`, `programs.json`,
  `program_icons/` (tracked, shared).
- `cache/` — `local_config.json`, `github_token.json`, `webengine_profile/`,
  `plugin_local_config/` (gitignored, per-machine — see `cache/README.md`),
  plus `plugins/`, per-repo plugin git clones.
- `launcher.py` — entry point.
- `developer/` — dev-only tooling (packaging, bug-history, glossary); lives
  only in this repo (UkoreHubDev), stripped when publishing to the separate
  UkoreHubRelease repo's `main` by `developer/commit-main.ps1` — see
  `developer/README.md`.
- `projects/` — workspace folder (gitignored; actual cloned repos live here).

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```