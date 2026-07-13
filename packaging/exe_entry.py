"""Entry point compiled by PyInstaller into UkoreHub.exe.

Pure hand-off: locate launcher.py next to this exe, locate a real Python
interpreter, spawn launcher.py detached, then exit immediately. This
process never supervises launcher.py — self-update's os.execv() inside the
spawned Python process is entirely unaffected by how it was started.
"""
import ctypes
import shutil
import subprocess
import sys
from pathlib import Path


def _own_dir() -> Path:
    if getattr(sys, "frozen", False):
        # Frozen: sys.executable is the compiled exe itself, NOT a real
        # python.exe — never derive the interpreter from this.
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _fatal(message: str) -> None:
    ctypes.windll.user32.MessageBoxW(None, message, "UkoreHub", 0x10)  # MB_ICONERROR
    sys.exit(1)


def main() -> None:
    repo_root = _own_dir()
    launcher_path = repo_root / "launcher.py"
    if not launcher_path.is_file():
        _fatal(f"launcher.py not found next to UkoreHub.exe:\n{launcher_path}")

    interpreter = shutil.which("pythonw") or shutil.which("python")
    if interpreter is None:
        _fatal(
            "No Python interpreter found on PATH.\n"
            "Install Python 3.10+ and make sure it's on PATH, then try again."
        )

    subprocess.Popen(
        [interpreter, str(launcher_path)],
        cwd=str(repo_root),
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
