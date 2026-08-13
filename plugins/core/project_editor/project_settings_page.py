from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from plugin_api import ConflictError, MetadataStore, UkoreHubError, confirm_action
from plugins.core.project_editor.dialogs import ProjectDialog


class ProjectSettingsPage(QWidget):
    """CATEGORY_PROJECT Settings tab ("Project"). As of the single-project-
    per-session change, this tab no longer lets the Viewgraph switch to a
    *different* project in place (the old project_combo, removed) — Project
    is fixed for the whole run by launcher.py's mandatory Project Selector
    gate (core/store.py's LocalConfigStore.active_project_id) before this
    page is ever constructed. What's left, all still acting on that one
    fixed project via get_current_project_id (bound in plugin.py to
    ProjectEditorPage.current_project_id):
    - Rename/Delete act on the active project itself.
    - "New Project..." adds to the shared catalog without switching into
      it — it only becomes selectable the next time the Project Selector
      gate actually runs (a fresh launch, or via Switch Project below).
    - "Switch Project..." is the only way to view a different project at
      all, and does it honestly — on_switch_project (bound in plugin.py to
      ProjectEditorPage.switch_project, wrapping UICommandService.switch_project)
      triggers a full app restart back through that same gate, rather than
      swapping state in a running window full of pages that assumed the
      active project couldn't change under them.
    This page holds no state of its own — every read/write/action goes
    through the callbacks passed in, same self-resolving-active-state
    convention every CATEGORY_REPO tab already uses."""

    def __init__(
        self,
        parent=None,
        *,
        store: MetadataStore,
        get_current_project_id: Callable[[], str | None],
        add_repo: Callable[[], None],
        on_switch_project: Callable[[], None],
    ):
        super().__init__(parent)
        self.store = store
        self._get_current_project_id = get_current_project_id
        self._add_repo = add_repo
        self._on_switch_project = on_switch_project

        self.project_label = QLabel()

        rename_btn = QPushButton("Rename Project...")
        rename_btn.clicked.connect(self._on_rename)
        delete_btn = QPushButton("Delete Project...")
        delete_btn.clicked.connect(self._on_delete)
        add_repo_btn = QPushButton("Add Repo")
        add_repo_btn.clicked.connect(self._on_add_repo)

        button_row = QHBoxLayout()
        button_row.addWidget(rename_btn)
        button_row.addWidget(delete_btn)
        button_row.addWidget(add_repo_btn)
        button_row.addStretch(1)

        new_project_btn = QPushButton("New Project...")
        new_project_btn.clicked.connect(self._on_add_new_project)
        switch_btn = QPushButton("Switch Project...")
        switch_btn.clicked.connect(self._on_switch_project_clicked)

        catalog_row = QHBoxLayout()
        catalog_row.addWidget(new_project_btn)
        catalog_row.addWidget(switch_btn)
        catalog_row.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Active project (fixed for this session):"))
        layout.addWidget(self.project_label)
        layout.addLayout(button_row)
        layout.addLayout(catalog_row)
        layout.addStretch(1)

        self.refresh()

    def refresh(self) -> None:
        """Re-reads the active project's current name — called on
        construction and via SettingsTabSpec.on_activated (this tab
        becoming visible), so a rename made elsewhere is picked up even
        though this page isn't a persistent singleton."""
        project_id = self._get_current_project_id()
        project = self.store.get_project(project_id) if project_id else None
        self.project_label.setText(f"<b>{project.name}</b>" if project is not None else "(no project)")

    def _on_add_repo(self) -> None:
        self._add_repo()

    def _on_add_new_project(self) -> None:
        dialog = ProjectDialog(self)
        if not dialog.exec():
            return
        try:
            self.store.add_project(dialog.name())
        except ConflictError as exc:
            self.store.load()
            QMessageBox.warning(self, "Add Project", str(exc))
            return
        except UkoreHubError as exc:
            QMessageBox.warning(self, "Add Project", str(exc))
            return
        QMessageBox.information(
            self, "Add Project", f"'{dialog.name()}' was added. Use Switch Project to open it."
        )

    def _on_rename(self) -> None:
        project_id = self._get_current_project_id()
        if project_id is None:
            return
        project = self.store.get_project(project_id)
        dialog = ProjectDialog(self, name=project.name)
        if not dialog.exec():
            return
        try:
            self.store.rename_project(project_id, dialog.name())
        except ConflictError as exc:
            self.store.load()
            QMessageBox.warning(self, "Rename Project", str(exc))
            self.refresh()
            return
        except UkoreHubError as exc:
            QMessageBox.warning(self, "Rename Project", str(exc))
            return
        self.refresh()

    def _on_delete(self) -> None:
        project_id = self._get_current_project_id()
        if project_id is None:
            return
        project = self.store.get_project(project_id)
        if not confirm_action(
            self,
            "Delete Project",
            f"Delete project '{project.name}' and ALL its repos from the registry for EVERYONE at the "
            "studio?\n\nThis is the project currently open in this session — UkoreHub will restart to "
            "the Project Selector afterward. This cannot be undone.",
        ):
            return
        try:
            self.store.delete_project(project_id)
        except ConflictError as exc:
            self.store.load()
            QMessageBox.warning(self, "Delete Project", str(exc))
            return
        self._on_switch_project()

    def _on_switch_project_clicked(self) -> None:
        if not confirm_action(
            self, "Switch Project", "UkoreHub will restart to let you pick a different project. Continue?"
        ):
            return
        self._on_switch_project()
