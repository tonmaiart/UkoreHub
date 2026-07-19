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

You don't need to install these yourself on Windows — `launcher.py` (git,
git-lfs) and `UkoreHub.exe` (Python itself, see `packaging/exe_entry.py`)
each auto-install whichever of these is missing via `winget` (Windows'
built-in package manager) before continuing. If `winget` isn't available or
an install fails, you'll get a message asking you to install that one
yourself instead. On other platforms, or if you'd rather install everything
by hand up front, use the links above.

## Running

```bash
python launcher.py
```

On first run, UkoreHub checks for its Python package dependencies (PySide6,
keyring) and installs any that are missing automatically — no manual
`pip install` step required. The workspace folder (where cloned repos live)
is fixed to `<this repo>/projects`. If you're not logged in yet, a Quick
Start dialog offers GitHub login and picking a project up front — every
field is optional and a single Continue skips all of it. Managers add
Projects/Repos via the Project Editor section (a node graph, 1 node = 1
repo); anyone can check sync status read-only via Setting > Project Status.
Whatever's added there becomes available to pick as the active repo by
clicking its node in Project Editor — there is no separate sidebar
repo-picker button anymore.

Alternatively, double-click `UkoreHub.exe` at the repo root (or pin it to
the taskbar) — a thin native wrapper that launches `launcher.py` with no
terminal window. Admins rebuild and recommit this exe via
`python packaging/build_exe.py` only when rebranding the icon (see
`packaging/README.md`) — routine code updates still flow through
**Update and Restart** / `git pull` as plain `.py` changes, exactly as
before; the exe itself rarely needs to change.

Setting > Program Database keeps a shared catalog of pipeline software (name,
icon, description) that repos can list as requirements in Project Data
Editor — shown on the Repo About tab for each repo.

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
- `data/` — `projects.json`, `system_config.json`, `thumbnails/`, `programs.json`,
  `program_icons/` (tracked, shared); `local_config.json` and `github_token.json`
  (gitignored, per-machine).
- `launcher.py` — entry point.
- `packaging/` — admin-only tooling to build `UkoreHub.exe` (see
  `packaging/README.md`); not part of the running app.
- `projects/` — workspace folder (gitignored; actual cloned repos live here).

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```