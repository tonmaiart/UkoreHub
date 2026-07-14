from __future__ import annotations

import shutil
from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget

IMAGE_FILE_FILTER = "Images (*.png *.jpg *.jpeg)"


def pick_image_file(parent: QWidget, title: str) -> Path | None:
    """Opens a file picker restricted to the image extensions every icon/
    thumbnail chooser in this app uses (repo thumbnail, Browser Link icon,
    Program icon, Add-on icon). Returns None if cancelled."""
    file_path, _filter = QFileDialog.getOpenFileName(parent, title, "", IMAGE_FILE_FILTER)
    return Path(file_path) if file_path else None


def save_image_asset(parent: QWidget, *, source_path: Path, dest_dir: Path, asset_id: str) -> str | None:
    """Copies source_path into dest_dir as f"{asset_id}{ext}" (creating
    dest_dir if needed) and returns the saved filename — the shape every
    thumbnail/icon "save" flow in this app follows. Shows a QMessageBox
    warning and returns None on failure rather than raising, matching
    every existing call site's error handling; the caller still owns
    calling the right store setter (set_repo_thumbnail, set_program_icon,
    etc.) with the returned filename."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / f"{asset_id}{source_path.suffix or '.png'}"
    try:
        shutil.copyfile(source_path, dest_path)
    except OSError as exc:
        QMessageBox.warning(parent, "Image", f"Could not save image: {exc}")
        return None
    return dest_path.name
