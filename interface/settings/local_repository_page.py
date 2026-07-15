from __future__ import annotations

import shutil

from PySide6.QtWidgets import QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from core.exceptions import NotFoundError
from core.models import Project, Repo
from core.paths import resolve_repo_path
from core.store import LocalConfigStore, MetadataStore
from interface.shared.widget_helpers import confirm_action, show_exclusive


class LocalRepositoryPage(QWidget):
    """Lets the user delete (unclone) the active repo's local clone folder —
    scoped to a single repo, so like BrowserLinksSettingsPage it resolves
    the active project/repo itself from local_config_store on refresh()
    rather than waiting for a set_repo() call MainWindow never makes for
    Settings pages. Does not touch the Project/Repo registry record itself
    (data/projects.json) — only the on-disk clone, then marks the repo
    "not_cloned" so the rest of the app (Explorer, Project Status) picks up
    the change immediately."""

    def __init__(self, parent=None, *, store: MetadataStore, local_config_store: LocalConfigStore):
        super().__init__(parent)
        self.store = store
        self.local_config_store = local_config_store
        self._project: Project | None = None
        self._repo: Repo | None = None

        self.empty_label = QLabel("Select a repo to see this information.")

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)

        self.remove_button = QPushButton("Remove Local Repositories")
        self.remove_button.clicked.connect(self._on_remove_local_repository)

        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(self.status_label)
        content_layout.addWidget(self.remove_button)
        content_layout.addStretch()

        layout = QVBoxLayout(self)
        layout.addWidget(self.empty_label)
        layout.addWidget(self.content_widget)

        self.refresh()

    def _local_path(self):
        return resolve_repo_path(self.local_config_store.workspace_root, self._project.name, self._repo.name)

    def refresh(self) -> None:
        project_id = self.local_config_store.active_project_id
        repo_id = self.local_config_store.active_repo_id
        if not project_id or not repo_id:
            self._project = None
            self._repo = None
            show_exclusive(self.empty_label, self.content_widget)
            return
        try:
            self._project = self.store.get_project(project_id)
            self._repo = self.store.get_repo(project_id, repo_id)
        except NotFoundError:
            self._project = None
            self._repo = None
            show_exclusive(self.empty_label, self.content_widget)
            return
        show_exclusive(self.content_widget, self.empty_label)

        if not self.local_config_store.workspace_root:
            self.status_label.setText(f"{self._repo.name}: no workspace root configured.")
            self.remove_button.setEnabled(False)
            return

        local_path = self._local_path()
        is_cloned = local_path.exists()
        self.status_label.setText(
            f"{self._repo.name}\nLocal path: {local_path}\nStatus: {'Cloned' if is_cloned else 'Not cloned'}"
        )
        self.remove_button.setEnabled(is_cloned)

    def _on_remove_local_repository(self) -> None:
        if self._project is None or self._repo is None:
            return
        local_path = self._local_path()
        if not local_path.exists():
            self.refresh()
            return
        if not confirm_action(
            self,
            "Remove Local Repositories",
            f"Delete the local clone of '{self._repo.name}' at:\n{local_path}\n\n"
            "This removes the folder from disk — any uncommitted changes are lost. "
            "The repo entry itself stays in the registry and can be cloned again later.",
        ):
            return
        try:
            shutil.rmtree(local_path)
        except OSError as exc:
            QMessageBox.warning(
                self,
                "Remove Local Repositories",
                f"Could not remove '{local_path}':\n{exc}\n\n"
                "Make sure no program (Explorer, Maya, an editor, ...) has a file open in it.",
            )
            self.refresh()
            return
        self.store.mark_status(self._project.id, self._repo.id, "not_cloned")
        self.refresh()
