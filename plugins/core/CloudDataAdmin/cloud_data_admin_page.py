from __future__ import annotations

import tempfile
from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.exceptions import ConflictError

# The three fixed top-level blobs launcher.py always pulls, regardless of
# which plugins are loaded this run — see data/README.md.
_FIXED_BLOB_NAMES = ["projects.json", "programs.json", "system_config.json"]


class CloudDataAdminPage(QWidget):
    """Settings > Developer tab for directly pulling/pushing one raw
    cloud-synced JSON blob, independent of the running app's own
    load/save cycle.

    Exists for the "I have an old data/ backup, how do I get it back onto
    the shared bucket" case that just restoring data/ locally and
    reopening UkoreHub can't solve: launcher.py always pulls the cloud
    copy over data/*.json before anything gets a chance to read it (see
    core/cloud_sync.py's GcsJsonSync.pull — unconditional overwrite, no
    timestamp check, no confirmation), so a locally-restored file gets
    silently clobbered before it's ever pushed back up. Pull and Push here
    both work on a file the artist explicitly chooses via a file dialog,
    never touching this app's own data/*.json — nothing here takes effect
    for the running session; restart UkoreHub afterward to load whatever
    got pushed."""

    def __init__(self, *, api, parent=None):
        super().__init__(parent)
        self._api = api

        layout = QVBoxLayout(self)

        intro = QLabel(
            "Directly pull or push one raw cloud-synced JSON blob — for restoring\n"
            "an old data/ backup, or checking what's currently live without\n"
            "disturbing this running session. Neither action touches this app's\n"
            "own data/ files; restart UkoreHub afterward to load whatever you push."
        )
        intro.setWordWrap(True)
        intro.setProperty("secondary", True)
        layout.addWidget(intro)

        form = QFormLayout()
        self._blob_combo = QComboBox()
        self._blob_combo.setEditable(True)
        self._blob_combo.addItems(self._known_blob_names())
        form.addRow("Blob name:", self._blob_combo)
        layout.addLayout(form)

        button_row = QHBoxLayout()
        pull_button = QPushButton("Pull from Cloud, Save As...")
        pull_button.clicked.connect(self._on_pull)
        button_row.addWidget(pull_button)
        push_button = QPushButton("Push File to Cloud...")
        push_button.clicked.connect(self._on_push)
        button_row.addWidget(push_button)
        layout.addLayout(button_row)

        self._status_label = QLabel()
        self._status_label.setWordWrap(True)
        self._status_label.setProperty("secondary", True)
        layout.addWidget(self._status_label)

        layout.addStretch()
        self._refresh_status()

    def _known_blob_names(self) -> list[str]:
        """Fixed top-level blobs first, then whatever plugins/core/*.json
        files happen to exist locally right now — a convenience list for
        the combo box's dropdown, not a hard constraint (it stays
        editable, since a blob for a plugin config that hasn't been
        pulled/created locally yet still needs to be typeable)."""
        names = list(_FIXED_BLOB_NAMES)
        plugins_core_dir = self._api.app_root / "data" / "plugins" / "core"
        if plugins_core_dir.is_dir():
            for json_path in sorted(plugins_core_dir.glob("*.json")):
                names.append(f"plugins/core/{json_path.name}")
        return names

    def _refresh_status(self) -> None:
        cloud_sync = self._api.cloud_sync
        if cloud_sync is None:
            self._status_label.setText(
                "Cloud sync isn't available this run (not configured, or the last pull failed at startup)."
            )
        elif not cloud_sync.can_push:
            self._status_label.setText(
                "Read-only this run — not logged in with Google (see the \"Studio\" button). Pull still works."
            )
        else:
            self._status_label.setText("Logged in — pull and push both available.")

    def _on_pull(self) -> None:
        blob_name = self._blob_combo.currentText().strip()
        if not blob_name:
            return
        cloud_sync = self._api.cloud_sync
        if cloud_sync is None:
            QMessageBox.warning(self, "Pull from Cloud", "Cloud sync isn't available this run.")
            return
        default_name = blob_name.replace("/", "_")
        save_path, _filter = QFileDialog.getSaveFileName(self, "Save cloud copy as...", default_name, "JSON (*.json)")
        if not save_path:
            return
        try:
            generation = cloud_sync.pull(blob_name, Path(save_path))
        except Exception as exc:
            QMessageBox.critical(self, "Pull from Cloud", f"Pull failed: {exc}")
            return
        if generation == 0:
            QMessageBox.information(
                self, "Pull from Cloud", f"'{blob_name}' doesn't exist on the cloud bucket yet — nothing saved."
            )
        else:
            QMessageBox.information(
                self, "Pull from Cloud", f"Saved the current cloud copy of '{blob_name}' to:\n{save_path}"
            )

    def _on_push(self) -> None:
        blob_name = self._blob_combo.currentText().strip()
        if not blob_name:
            return
        cloud_sync = self._api.cloud_sync
        if cloud_sync is None or not cloud_sync.can_push:
            QMessageBox.warning(
                self, "Push to Cloud", "Not logged in with Google — sign in via the Studio Setting window first."
            )
            return
        file_path, _filter = QFileDialog.getOpenFileName(self, "Choose file to push", "", "JSON (*.json)")
        if not file_path:
            return
        confirmed = QMessageBox.question(
            self,
            "Push to Cloud",
            f"This overwrites '{blob_name}' for the whole studio with:\n{file_path}\n\n"
            "Every other artist's next launch will pull this version. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirmed != QMessageBox.StandardButton.Yes:
            return
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                # Refresh this blob's known generation first. push() sends
                # whatever generation the last pull() on *this* GcsJsonSync
                # instance saw for this blob_name — 0 if this session never
                # pulled it — and a generation of 0 means "must not exist
                # yet". Without this, pushing a blob nothing in this
                # session has touched would look like a false conflict
                # against the real, already-existing blob.
                cloud_sync.pull(blob_name, Path(tmp_dir) / "_generation_check.json")
            cloud_sync.push(blob_name, Path(file_path))
        except ConflictError as exc:
            QMessageBox.warning(self, "Push to Cloud", f"Someone else updated '{blob_name}' first: {exc}\nTry again.")
            return
        except Exception as exc:
            QMessageBox.critical(self, "Push to Cloud", f"Push failed: {exc}")
            return
        QMessageBox.information(
            self, "Push to Cloud", f"Pushed '{file_path}' to '{blob_name}'.\nRestart UkoreHub to load it."
        )
