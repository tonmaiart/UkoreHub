from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from core.exceptions import GoogleAuthError
from core.google_auth import GoogleTokenStore, run_installed_app_login
from core.store import SystemConfigStore


class _GoogleLoginWorker(QThread):
    """Runs the Google OAuth loopback login flow off the UI thread — same
    network-off-main-thread pattern as common_settings_page.py's
    _AvatarFetchWorker. core/google_auth.py's run_installed_app_login()
    opens the system browser itself and blocks until the artist finishes
    (or the flow times out), so there's nothing else for this worker to do
    besides report the outcome."""

    login_succeeded = Signal(str)  # refresh_token
    login_failed = Signal(str)

    def __init__(self, client_id: str, client_secret: str, parent=None):
        super().__init__(parent)
        self._client_id = client_id
        self._client_secret = client_secret

    def run(self) -> None:
        try:
            refresh_token = run_installed_app_login(self._client_id, self._client_secret)
            self.login_succeeded.emit(refresh_token)
        except GoogleAuthError as exc:
            self.login_failed.emit(str(exc))


class StudioSettingsDialog(QDialog):
    """Separate top-level window (not a SettingsDialog tab) for the shared
    Google Cloud Storage sync config (core/cloud_sync.py) — its own gated
    entry point, opened via the "Studio Setting" footer button this plugin
    contributes through PluginAPI.register_sidebar_footer_action() (see
    plugin.py), deliberately outside the normal Setting popup: this config
    needs a real login step before it makes sense to edit anything, and —
    unlike every other Settings tab, which self-persists on every field
    blur (see interface/settings/README.md) — an explicit Save button,
    since an accidental edit here would repoint the whole studio's shared
    registry sync, not just this machine's own preference.

    Two states, decided once at construction time by whether a Google
    refresh token is already cached (core/google_auth.py's
    GoogleTokenStore):
    - No token yet -> the gate: Import from JSON (or manual Client ID/
      Secret entry) + Login with Google. Nothing is written to
      data/system_config.json until login actually succeeds — client_id/
      client_secret and the refresh token are saved together on success,
      then this same dialog swaps to the full form below rather than
      requiring a reopen.
    - A token already exists (including right after that first login) ->
      the full form: every field editable, an explicit Save button
      persists them all together. Re-running Login with Google is still
      available here too (e.g. switching accounts, or a revoked token)."""

    def __init__(self, parent=None, *, system_config_store: SystemConfigStore, cache_dir: Path):
        super().__init__(parent)
        self.setWindowTitle("Studio Setting")
        self.resize(480, 420)
        self._system_config_store = system_config_store
        self._token_store = GoogleTokenStore(cache_dir / "gcs_refresh_token.json")
        self._login_worker: _GoogleLoginWorker | None = None
        # Set by _on_import_from_json only — the JSON download carries a
        # project_id, saved as a courtesy default on first login if the
        # artist hasn't already got one set. None if they typed the
        # Client ID/Secret in by hand instead.
        self._pending_project_id: str | None = None

        self._layout = QVBoxLayout(self)
        if self._token_store.load_token():
            self._build_form()
        else:
            self._build_gate()

    def _clear_layout(self) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    # -- gate: import/login, shown only until the first successful login --

    def _build_gate(self) -> None:
        self._clear_layout()

        intro = QLabel(
            "Log in with Google to sync the shared Project/Program\n"
            "registries through Google Cloud Storage instead of git."
        )
        intro.setWordWrap(True)
        self._layout.addWidget(intro)

        form = QFormLayout()
        self._gate_client_id_edit = QLineEdit(self._system_config_store.google_oauth_client_id or "")
        self._gate_client_id_edit.setPlaceholderText('OAuth client, type "Desktop app"')
        self._gate_client_secret_edit = QLineEdit(self._system_config_store.google_oauth_client_secret or "")
        form.addRow("Google OAuth Client ID:", self._gate_client_id_edit)
        form.addRow("Google OAuth Client Secret:", self._gate_client_secret_edit)
        self._layout.addLayout(form)

        import_button = QPushButton("Import from JSON...")
        import_button.clicked.connect(self._on_import_from_json)
        self._layout.addWidget(import_button)
        import_hint = QLabel(
            "Reads the client_secret_*.json Google Cloud Console offers to\n"
            "download after creating the \"Desktop app\" OAuth client, instead\n"
            "of copy-pasting Client ID/Secret by hand."
        )
        import_hint.setProperty("secondary", True)
        import_hint.setWordWrap(True)
        self._layout.addWidget(import_hint)

        self._login_button = QPushButton("Login with Google")
        self._login_button.clicked.connect(self._on_login_with_google)
        self._layout.addWidget(self._login_button)

        self._layout.addStretch()
        buttons = QDialogButtonBox(QDialogButtonBox.Cancel)
        buttons.rejected.connect(self.reject)
        self._layout.addWidget(buttons)

    def _on_import_from_json(self) -> None:
        file_path, _filter = QFileDialog.getOpenFileName(self, "Import Google OAuth Client JSON", "", "JSON (*.json)")
        if not file_path:
            return
        try:
            data = json.loads(Path(file_path).read_text(encoding="utf-8"))
            # Google's download names the top-level key after the client
            # type — "installed" for Desktop app (what this dialog asks
            # for), "web" for a Web application client someone might paste
            # here by mistake; accept either rather than forcing them to notice.
            client_config = data.get("installed") or data.get("web")
            client_id = client_config["client_id"]
            client_secret = client_config["client_secret"]
        except (OSError, json.JSONDecodeError, KeyError, TypeError):
            QMessageBox.warning(
                self,
                "Import from JSON",
                "Could not read a client_id/client_secret from that file — make sure it's the "
                "JSON Google Cloud Console offers to download for this OAuth client.",
            )
            return
        self._gate_client_id_edit.setText(client_id)
        self._gate_client_secret_edit.setText(client_secret)
        self._pending_project_id = client_config.get("project_id")

    def _on_login_with_google(self) -> None:
        client_id = self._gate_client_id_edit.text().strip()
        client_secret = self._gate_client_secret_edit.text().strip()
        if not client_id or not client_secret:
            QMessageBox.information(
                self, "Login with Google", "Set the Google OAuth Client ID and Client Secret above first."
            )
            return
        self._login_button.setEnabled(False)
        self._login_button.setText("Waiting for browser login...")
        self._login_worker = _GoogleLoginWorker(client_id, client_secret, self)
        self._login_worker.login_succeeded.connect(lambda token: self._on_gate_login_succeeded(token, client_id, client_secret))
        self._login_worker.login_failed.connect(self._on_gate_login_failed)
        self._login_worker.start()

    def _on_gate_login_succeeded(self, refresh_token: str, client_id: str, client_secret: str) -> None:
        self._token_store.save_token(refresh_token)
        self._system_config_store.set_google_oauth_client_id(client_id)
        self._system_config_store.set_google_oauth_client_secret(client_secret)
        if self._pending_project_id and not self._system_config_store.gcs_project_id:
            self._system_config_store.set_gcs_project_id(self._pending_project_id)
        QMessageBox.information(
            self,
            "Login with Google",
            "Login successful. Restart UkoreHub after saving the fields below for cloud sync to take effect.",
        )
        self._build_form()

    def _on_gate_login_failed(self, message: str) -> None:
        self._login_button.setEnabled(True)
        self._login_button.setText("Login with Google")
        QMessageBox.warning(self, "Login with Google", f"Login failed: {message}")

    # -- full form: every field, explicit Save ------------------------------

    def _build_form(self) -> None:
        self._clear_layout()

        form = QFormLayout()
        self.gcs_bucket_edit = QLineEdit(self._system_config_store.gcs_bucket_name or "")
        self.gcs_bucket_edit.setPlaceholderText("e.g. ukorehub-studio-config")
        self.gcs_project_edit = QLineEdit(self._system_config_store.gcs_project_id or "")
        self.gcs_project_edit.setPlaceholderText("The GCP project ID the bucket lives in")
        self.google_client_id_edit = QLineEdit(self._system_config_store.google_oauth_client_id or "")
        self.google_client_secret_edit = QLineEdit(self._system_config_store.google_oauth_client_secret or "")
        form.addRow("GCS Bucket Name:", self.gcs_bucket_edit)
        form.addRow("GCS Project ID:", self.gcs_project_edit)
        form.addRow("Google OAuth Client ID:", self.google_client_id_edit)
        form.addRow("Google OAuth Client Secret:", self.google_client_secret_edit)
        self._layout.addLayout(form)

        hint = QLabel(
            "Every artist logs in with their own Google account (added to the\n"
            "bucket's IAM group by a studio admin) — no key file involved.\n"
            "Changes here only take effect after Save, and after restarting\n"
            "UkoreHub."
        )
        hint.setProperty("secondary", True)
        hint.setWordWrap(True)
        self._layout.addWidget(hint)

        self._relogin_button = QPushButton("Login with Google")
        self._relogin_button.clicked.connect(self._on_relogin_with_google)
        self._layout.addWidget(self._relogin_button)

        self._layout.addStretch()
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        self._layout.addWidget(buttons)

    def _on_relogin_with_google(self) -> None:
        client_id = self.google_client_id_edit.text().strip()
        client_secret = self.google_client_secret_edit.text().strip()
        if not client_id or not client_secret:
            QMessageBox.information(
                self, "Login with Google", "Set the Google OAuth Client ID and Client Secret above first."
            )
            return
        self._relogin_button.setEnabled(False)
        self._relogin_button.setText("Waiting for browser login...")
        self._login_worker = _GoogleLoginWorker(client_id, client_secret, self)
        self._login_worker.login_succeeded.connect(self._on_relogin_succeeded)
        self._login_worker.login_failed.connect(self._on_relogin_failed)
        self._login_worker.start()

    def _on_relogin_succeeded(self, refresh_token: str) -> None:
        self._token_store.save_token(refresh_token)
        self._relogin_button.setEnabled(True)
        self._relogin_button.setText("Login with Google")
        QMessageBox.information(self, "Login with Google", "Login successful.")

    def _on_relogin_failed(self, message: str) -> None:
        self._relogin_button.setEnabled(True)
        self._relogin_button.setText("Login with Google")
        QMessageBox.warning(self, "Login with Google", f"Login failed: {message}")

    def _on_save(self) -> None:
        self._system_config_store.set_gcs_bucket_name(self.gcs_bucket_edit.text().strip())
        self._system_config_store.set_gcs_project_id(self.gcs_project_edit.text().strip())
        self._system_config_store.set_google_oauth_client_id(self.google_client_id_edit.text().strip())
        self._system_config_store.set_google_oauth_client_secret(self.google_client_secret_edit.text().strip())
        QMessageBox.information(self, "Studio Setting", "Saved — restart UkoreHub for cloud sync to take effect.")
        self.accept()
