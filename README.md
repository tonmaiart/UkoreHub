# UkoreHub

Pipeline tool to launch project in Ukore Studio.

UkoreHub is a Git repo launcher: it keeps a database-driven registry of Projects,
each containing one or more Repos. Click "Select Repo..." in the sidebar to pick
one — it's cloned (first time) or pulled (every time after) automatically into a
workspace folder of your choosing, no manual `git clone`/`git pull` needed. From
there you can browse the repo's files, check its git status (latest commit,
untracked/modified/staged files), and see repo details, all from the sidebar tabs.

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

- **System config** — `data/projects.json` (the Project/Repo registry) and
  `data/system_config.json` (GitHub OAuth Client ID). These are **tracked in
  this git repo**, not gitignored, because they're meant to be the same for
  everyone at the studio. When a manager adds a Project/Repo or sets the
  Client ID, someone needs to `git add`/`commit`/`push` those two files for
  the change to reach other machines — other artists then get it the normal
  way, e.g. by clicking **Update and Restart** (which runs `git pull`) or any
  other `git pull` of this repo. UkoreHub itself does not auto-commit or push
  on your behalf.
- **Local config** — `data/local_config.json` (workspace folder, color theme,
  which repo you currently have selected, cached GitHub username) and
  `data/github_token.json` (GitHub token, only if the OS keyring isn't
  available). These are gitignored and stay per-machine — everyone picks
  their own workspace folder and theme.

## GitHub Login Setup (optional)

The status bar's Login button uses GitHub's OAuth Device Flow to display your
GitHub identity. It does not affect git clone/pull, which always uses your
system git credentials (SSH key or credential helper) regardless of whether
you're logged in here — a Client ID is required only for the Login button
itself to work; everything else in UkoreHub works without it.

To enable it, register a public GitHub OAuth App (free, no approval needed):

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
- `data/` — `projects.json` and `system_config.json` (tracked, shared);
  `local_config.json` and `github_token.json` (gitignored, per-machine).
- `launcher.py` — entry point.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```