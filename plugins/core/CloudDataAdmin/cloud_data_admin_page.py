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
from core.os_utils import open_with_default_app

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
    core/vcs/cloud_sync.py's R2JsonSync.pull — unconditional overwrite, no
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
        open_button = QPushButton("Open Local Synced File")
        open_button.setToolTip(
            "Open this blob's own local cache under data/ (the file this running app actually reads/writes) "
            "in its default app."
        )
        open_button.clicked.connect(self._on_open_file)
        button_row.addWidget(open_button)
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
        """Fixed top-level blobs first, then whatever projects/*.json and
        plugins/core/*.json files happen to exist locally right now — a
        convenience list for the combo box's dropdown, not a hard constraint
        (it stays editable, since a blob that hasn't been pulled/created
        locally yet still needs to be typeable). projects.json itself is
        just the lightweight index now — each project's real data lives in
        its own projects/<id>.json blob, same split-blob shape as
        plugins/core/*.json (see core/store.py's MetadataStore)."""
        names = list(_FIXED_BLOB_NAMES)
        projects_dir = self._api.app_root / "data" / "projects"
        if projects_dir.is_dir():
            for json_path in sorted(projects_dir.glob("*.json")):
                names.append(f"projects/{json_path.name}")
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
        else:
            self._status_label.setText("Cloud sync available — pull and push both work.")

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
            etag = cloud_sync.pull(blob_name, Path(save_path))
        except Exception as exc:
            QMessageBox.critical(self, "Pull from Cloud", f"Pull failed: {exc}")
            return
        if etag is None:
            QMessageBox.information(
                self, "Pull from Cloud", f"'{blob_name}' doesn't exist on the cloud bucket yet — nothing saved."
            )
        else:
            QMessageBox.information(
                self, "Pull from Cloud", f"Saved the current cloud copy of '{blob_name}' to:\n{save_path}"
            )

    def _on_open_file(self) -> None:
        blob_name = self._blob_combo.currentText().strip()
        if not blob_name:
            return
        # blob_name is always "/"-separated (see _known_blob_names/R2JsonSync
        # convention) — Path() normalizes that to the OS separator, and this
        # mirrors data_dir / blob_name exactly as launcher.py/plugin_api.py
        # already build it, so it's always this blob's real local cache path.
        local_path = self._api.app_root / "data" / Path(blob_name)
        if not local_path.exists():
            QMessageBox.information(
                self,
                "Open Local Synced File",
                f"No local copy of '{blob_name}' at:\n{local_path}\n\n"
                "It may not have synced to this machine yet — try Pull from Cloud first.",
            )
            return
        if not open_with_default_app(local_path):
            QMessageBox.warning(self, "Open Local Synced File", f"Could not open:\n{local_path}")

    def _on_push(self) -> None:
        blob_name = self._blob_combo.currentText().strip()
        if not blob_name:
            return
        cloud_sync = self._api.cloud_sync
        if cloud_sync is None:
            QMessageBox.warning(self, "Push to Cloud", "Cloud sync isn't available this run.")
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
                # Refresh this blob's known ETag first. push() conditions its
                # write on whatever ETag the last pull() on *this*
                # R2JsonSync instance saw for this blob_name — None if this
                # session never pulled it, which push() treats as
                # "must not exist yet". Without this, pushing a blob nothing
                # in this session has touched would look like a false
                # conflict against the real, already-existing blob.
                cloud_sync.pull(blob_name, Path(tmp_dir) / "_etag_check.json")
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
