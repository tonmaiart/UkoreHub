"""Entry point compiled by PyInstaller into UkoreHub.exe.

Pure hand-off: locate launcher.py next to this exe, locate a real Python
interpreter (installing one via winget if none is found — see
_install_python_via_winget), spawn launcher.py detached, then exit
immediately. This process never supervises launcher.py — self-update's
os.execv() inside the spawned Python process is entirely unaffected by how
it was started.

Deliberately self-contained (stdlib only, no imports from the rest of the
repo) — PyInstaller only bundles what this file actually imports, and the
rest of UkoreHub is meant to stay plain, distributable .py files reached
via git pull, not baked into the exe.
"""
import ctypes
import os
import shutil
import subprocess
import sys
from pathlib import Path

PYTHON_WINGET_ID = "Python.Python.3.12"


def _own_dir() -> Path:
    if getattr(sys, "frozen", False):
        # Frozen: sys.executable is the compiled exe itself, NOT a real
        # python.exe — never derive the interpreter from this.
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _fatal(message: str) -> None:
    ctypes.windll.user32.MessageBoxW(None, message, "UkoreHub", 0x10)  # MB_ICONERROR
    sys.exit(1)


def _find_interpreter() -> str | None:
    return shutil.which("pythonw") or shutil.which("python")


def _refresh_path_from_registry() -> None:
    """A winget install that just completed updates the registry, not this
    already-running process's environment (env vars are only inherited at
    process creation) — merge the machine + user PATH from the registry into
    os.environ so _find_interpreter() can see a just-installed Python
    without relaunching UkoreHub.exe."""
    import winreg

    def _read(hive: int, subkey: str) -> str:
        try:
            with winreg.OpenKey(hive, subkey) as key:
                value, _ = winreg.QueryValueEx(key, "Path")
                return value
        except OSError:
            return ""

    machine_path = _read(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment")
    user_path = _read(winreg.HKEY_CURRENT_USER, "Environment")
    combined = ";".join(p for p in (machine_path, user_path, os.environ.get("PATH", "")) if p)
    if combined:
        os.environ["PATH"] = combined


def _install_python_via_winget() -> bool:
    """Best-effort silent install via winget (ships by default on Windows
    10/11) — never raises. Returns whether winget ran the install
    successfully; the caller still needs to re-check _find_interpreter()
    afterwards since a successful install doesn't guarantee this process can
    already see the new PATH entry (see _refresh_path_from_registry)."""
    if shutil.which("winget") is None:
        return False
    try:
        subprocess.run(
            [
                "winget", "install", "--id", PYTHON_WINGET_ID, "-e",
                "--silent", "--accept-package-agreements", "--accept-source-agreements",
            ],
            check=True,
        )
    except (subprocess.CalledProcessError, OSError):
        return False
    _refresh_path_from_registry()
    return True


def main() -> None:
    repo_root = _own_dir()
    launcher_path = repo_root / "launcher.py"
    if not launcher_path.is_file():
        _fatal(f"launcher.py not found next to UkoreHub.exe:\n{launcher_path}")

    interpreter = _find_interpreter()
    if interpreter is None:
        if not _install_python_via_winget():
            _fatal(
                "No Python interpreter found on PATH, and automatic install via "
                "winget wasn't available or didn't succeed.\n"
                "Install Python 3.10+ yourself, make sure it's on PATH, then try again."
            )
        interpreter = _find_interpreter()
        if interpreter is None:
            _fatal(
                "Python was installed, but this session can't see it on PATH yet.\n"
                "Please relaunch UkoreHub."
            )

    subprocess.Popen(
        [interpreter, str(launcher_path)],
        cwd=str(repo_root),
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
