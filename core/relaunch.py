"""Spawns UkoreHubLauncher.exe (the built launcher exe) from within a running
UkoreHub process. No Qt imports — pure os/subprocess helper.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path


def relaunch_ukorehub_exe(repo_root: Path) -> bool:
    """Spawns UkoreHubLauncher.exe detached and returns True, or returns False if no
    built exe exists one directory above repo_root (app/).
    """
    # repo_root คือ root/app
    # repo_root.parent คือ root/ ซึ่งเป็นที่อยู่ของ UkoreHubLauncher.exe
    exe_path = repo_root.parent / "UkoreHubLauncher.exe"

    if not exe_path.is_file():
        return False

    # ล้างค่า Environment Variable ของ PyInstaller ป้องกันการเปิดแล้วล้มเหลว
    clean_env = {k: v for k, v in os.environ.items() if not k.startswith("_PYI_")}
    
    # เรียกเปิด UkoreHubLauncher.exe ตัวนอกขึ้นมาใหม่
    subprocess.Popen([str(exe_path)], cwd=str(exe_path.parent), env=clean_env)
    return True