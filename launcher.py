"""UkoreHub entry point.

Bootstraps missing Python package dependencies before importing anything
that needs them, so the user never sees a ModuleNotFoundError.
"""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

REQUIRED_PACKAGES = [
    ("PySide6", "PySide6>=6.7,<7.0"),
    ("keyring", "keyring>=24.0"),
]


def ensure_dependencies() -> None:
    for import_name, pip_spec in REQUIRED_PACKAGES:
        if importlib.util.find_spec(import_name) is not None:
            continue
        print(f"UkoreHub: installing missing dependency '{pip_spec}'...")
        subprocess.run([sys.executable, "-m", "pip", "install", pip_spec], check=True)


def check_git_prerequisite() -> bool:
    return shutil.which("git") is not None


def check_git_lfs_prerequisite() -> bool:
    return shutil.which("git-lfs") is not None


def main() -> None:
    ensure_dependencies()

    from PySide6.QtWidgets import QApplication, QMessageBox

    app = QApplication(sys.argv)

    if not check_git_prerequisite():
        QMessageBox.critical(
            None,
            "Git Not Found",
            "UkoreHub requires 'git' to be installed and available on your PATH.\n"
            "Please install git and restart UkoreHub.",
        )
        sys.exit(1)

    if not check_git_lfs_prerequisite():
        QMessageBox.warning(
            None,
            "git-lfs Not Found",
            "'git-lfs' was not found on your PATH. Some repos may require it.\n"
            "You can continue, but LFS-tracked files may not sync correctly.",
        )

    from core.git_service import GitService
    from core.program_store import ProgramStore
    from core.store import LocalConfigStore, MetadataStore, SystemConfigStore
    from core.token_store import TokenStore
    from interface.main_window import MainWindow
    from interface.theme_apply import apply_theme

    data_dir = REPO_ROOT / "data"
    data_dir.mkdir(exist_ok=True)

    # projects.json, system_config.json, and programs.json are shared/tracked
    # in this repo; local_config.json and github_token.json are per-machine
    # and gitignored.
    store = MetadataStore(data_dir / "projects.json")
    system_config_store = SystemConfigStore(data_dir / "system_config.json")
    program_store = ProgramStore(data_dir / "programs.json")
    local_config_store = LocalConfigStore(data_dir / "local_config.json")
    if not local_config_store.workspace_root:
        # Sensible out-of-the-box default so a fresh install isn't blocked on
        # manually picking a folder before doing anything — still editable
        # any time via Setting > Common.
        local_config_store.set_workspace_root(str(REPO_ROOT / "projects"))
    git_service = GitService()
    token_store = TokenStore(data_dir / "github_token.json")

    apply_theme(app, local_config_store.theme)

    window = MainWindow(store, local_config_store, system_config_store, program_store, git_service, token_store)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
