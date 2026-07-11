# UkoreHub

Pipeline tool to launch project in Ukore Studio.

UkoreHub is a Git repo launcher: it keeps a database-driven registry of Projects,
each containing one or more Repos. Pick a repo from the sidebar — a dropdown of
already-cloned repos once you have at least one, or "Select Repo..." the first
time — and it's cloned (first time) or pulled (every time after) automatically
into a workspace folder of your choosing, no manual `git clone`/`git pull`
needed. From there you can browse the repo's files, and on the Repo Git Status
tab: scroll through its full commit history, stage modified files, and commit →
pull → push back to the remote — including a file-level (not line-level)
conflict resolution prompt if a pull produces a merge conflict, appropriate for
mostly-binary animation production assets.

## Prerequisites

Install these yourself before running UkoreHub — the app does not install them:

- [git](https://git-scm.com/downloads)
- [git-lfs](https://git-lfs.com/)
- Python 3.10+

## Running

```bash
python launcher.py
```

On first run, UkoreHub checks for its Python package dependencies (PySide6,
keyring) and installs any that are missing automatically — no manual
`pip install` step required. Open Setting > Common to choose a workspace folder
(where cloned repos will live). Managers add Projects/Repos via
Setting > Project Data Editor; anyone can check sync status read-only via
Setting > Project Status. Whatever's added there becomes available to pick
from "Select Repo..." in the sidebar.

## System config vs. local config

Settings are split into two files with different sharing behavior:

- **System config** — `data/projects.json` (the Project/Repo registry, including
  each repo's thumbnail filename), `data/system_config.json` (GitHub OAuth
  Client ID), and `data/thumbnails/` (the actual repo thumbnail images set via
  Setting > Project Data Editor). These are **tracked in this git repo**, not
  gitignored, because they're meant to be the same for everyone at the studio
  — thumbnails are accepted as binary/larger files here deliberately, same
  reasoning as the registry itself. When a manager adds a Project/Repo, sets
  a thumbnail, or sets the Client ID, someone needs to `git add`/`commit`/`push`
  those files for the change to reach other machines — other artists then get
  it the normal way, e.g. by clicking **Update and Restart** (which runs
  `git pull`) or any other `git pull` of this repo. UkoreHub itself does not
  auto-commit or push on your behalf.
- **Local config** — `data/local_config.json` (workspace folder, color theme,
  which repo you currently have selected, cached GitHub username) and
  `data/github_token.json` (GitHub token, only if the OS keyring isn't
  available). These are gitignored and stay per-machine — everyone picks
  their own workspace folder and theme.

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
- `data/` — `projects.json`, `system_config.json`, `thumbnails/` (tracked,
  shared); `local_config.json` and `github_token.json` (gitignored, per-machine).
- `launcher.py` — entry point.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```