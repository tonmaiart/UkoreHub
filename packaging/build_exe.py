"""Admin-only tool: builds UkoreHub.exe from packaging/exe_entry.py.

Run after rebranding packaging/icon.ico, or after changing exe_entry.py
itself — NOT part of routine development. Ordinary code changes still
reach artists via git pull / Update and Restart as plain .py files.

Installs pyinstaller into the CURRENT environment only if missing, kept
deliberately separate from launcher.py's REQUIRED_PACKAGES bootstrap.
"""
from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ICON = Path(__file__).resolve().parent / "icon.ico"


def ensure_pyinstaller() -> None:
    if importlib.util.find_spec("PyInstaller") is not None:
        return
    print("build_exe.py: installing PyInstaller into the current environment...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)


def build(icon: Path, name: str) -> Path:
    build_dir = REPO_ROOT / "build"
    entry = Path(__file__).resolve().parent / "exe_entry.py"
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--noconsole",
        f"--name={name}",
        f"--distpath={REPO_ROOT}",
        f"--workpath={build_dir}",
        f"--specpath={build_dir}",
    ]
    if icon.is_file():
        cmd.append(f"--icon={icon}")
    else:
        print(f"build_exe.py: warning — icon not found at {icon}, building without a custom icon.")
    cmd.append(str(entry))

    subprocess.run(cmd, check=True, cwd=str(REPO_ROOT))
    return REPO_ROOT / f"{name}.exe"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--icon", type=Path, default=DEFAULT_ICON, help="Path to a .ico file")
    parser.add_argument("--name", default="UkoreHub", help="Output exe base name")
    args = parser.parse_args()

    ensure_pyinstaller()
    exe_path = build(args.icon, args.name)
    print(f"build_exe.py: built {exe_path}")


if __name__ == "__main__":
    main()
