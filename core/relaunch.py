"""Spawns UkoreHub.exe (the built launcher exe) from within a running
UkoreHub process. No Qt imports (see core/README.md's Qt-free rule) — pure
os/subprocess helper; callers own their own UI (message boxes, etc.).

Shared by interface/main_window.py's logout flow and launcher.py's mandatory
login gate, so there is exactly one place that knows how to spawn
UkoreHub.exe safely — see relaunch_ukorehub_exe's docstring for why a bare
subprocess.Popen() here is not safe.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path


def relaunch_ukorehub_exe(repo_root: Path) -> bool:
    """Spawns UkoreHub.exe detached and returns True, or returns False if no
    built exe exists one directory above repo_root (e.g. a dev environment
    running via `python launcher.py` directly) — the caller is responsible
    for telling the user what to do in that case.

    `UkoreHub.exe` lives in its own repo (UkoreHubLauncher) now, one
    directory above this app repo's own root: artists get a
    `UkoreHub.exe` next to an `app/` folder that's this repo's clone (see
    UkoreHubLauncher's README.md) — repo_root here is that `app/` folder,
    so the exe is at repo_root.parent, not repo_root itself.

    Strips every _PYI_-prefixed env var before spawning: the calling
    process's own environment still carries PyInstaller onefile bootloader
    variables (_PYI_APPLICATION_HOME_DIR, _PYI_ARCHIVE_FILE,
    _PYI_PARENT_PROCESS_LEVEL) inherited from the original UkoreHub.exe
    launch — Popen inherits the full environment by default. A onefile
    bootloader that sees these already set skips its own self-extraction and
    tries to reuse the *original* process's already-deleted temp folder,
    crashing with "Failed to load Python DLL" — see
    developer/bug-history/2026-08-04-relaunch-inherits-pyinstaller-onefile-env.md.
    Any call site that spawns UkoreHub.exe from within a running UkoreHub
    process must go through this helper rather than a bare
    subprocess.Popen, or it will reintroduce that exact bug.
    """
    exe_path = repo_root.parent / "UkoreHub.exe"
    if not exe_path.is_file():
        return False
    clean_env = {k: v for k, v in os.environ.items() if not k.startswith("_PYI_")}
    subprocess.Popen([str(exe_path)], cwd=str(exe_path.parent), env=clean_env)
    return True
