from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from core.exceptions import UkoreHubError
from core.store import MetadataStore
from interface.shared.widget_helpers import confirm_action
from plugins.core.project_editor.dialogs import ProjectDialog

_ADD_NEW_PROJECT = "__add_new_project__"


class ProjectSettingsPage(QWidget):
    """CATEGORY_PROJECT Settings tab ("Project") — moved here 2026-08-03
    from ProjectEditorPage's always-visible top bar: first the project
    picker + Rename/Delete Project buttons, then the Add Repo button too
    (same day, second pass) once the user asked for it to move as well —
    the graph view's own top bar is gone entirely now, this tab is the only
    place all four actions live. This page holds no real state of its
    own — `get_current_project_id`/`set_current_project_id` (bound in
    plugin.py to ProjectEditorPage.current_project_id/set_current_project)
    are the single source of truth, same self-resolving-active-state
    convention every CATEGORY_REPO tab already uses; `add_repo` (bound to
    ProjectEditorPage.add_repo, which just delegates to
    ProjectGraphView.add_repo) always acts on whichever project
    `get_current_project_id` currently reports, same as the old top-bar
    button did. Calling `set_current_project_id` reloads the graph
    immediately (ProjectEditorPage.set_current_project calls
    graph_view.load_project), even while this Settings dialog is still
    open, so switching the project here has an instantly visible effect
    rather than waiting for the dialog to close — the same is true of
    `add_repo`, which shows its own RepoDialog on top of this (already
    modal) Settings dialog; nested QDialog.exec() calls are fine in Qt.
    Because this page is stateless and always re-reads through those
    callbacks, a freshly-constructed page on every Settings open (see
    settings_view.py's "fresh page every open" convention) always starts
    in sync with whatever project the graph is actually showing — no extra
    wiring needed for that."""

    def __init__(
        self,
        parent=None,
        *,
        store: MetadataStore,
        get_current_project_id: Callable[[], str | None],
        set_current_project_id: Callable[[str | None], None],
        add_repo: Callable[[], None],
    ):
        super().__init__(parent)
        self.store = store
        self._get_current_project_id = get_current_project_id
        self._set_current_project_id = set_current_project_id
        self._add_repo = add_repo

        self.project_combo = QComboBox()
        self.project_combo.currentIndexChanged.connect(self._on_combo_changed)

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

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Project shown in the Graph View:"))
        layout.addWidget(self.project_combo)
        layout.addLayout(button_row)
        layout.addStretch(1)

        self.refresh()

    def refresh(self) -> None:
        """Rebuilds the project list and re-selects whatever project the
        graph is currently showing — called on construction and via
        SettingsTabSpec.on_activated (this tab becoming visible), so a
        project added/renamed/deleted elsewhere is picked up even though
        this page isn't a persistent singleton."""
        current_id = self._get_current_project_id()
        blocked = self.project_combo.blockSignals(True)
        self.project_combo.clear()
        for project in self.store.list_projects():
            self.project_combo.addItem(project.name, project.id)
        self.project_combo.addItem("Add New Project...", _ADD_NEW_PROJECT)
        index = self.project_combo.findData(current_id) if current_id else -1
        if index >= 0:
            self.project_combo.setCurrentIndex(index)
        elif self.project_combo.count() > 1:
            # Nothing valid was selected (e.g. first run, or the
            # previously-shown project got deleted elsewhere) but real
            # projects exist — fall back to the first one, same as the old
            # top-bar combo's own _refresh_project_combo fallback.
            self.project_combo.setCurrentIndex(0)
        self.project_combo.blockSignals(blocked)

        if index < 0:
            # Push the fallback selection (a real project, or None if the
            # registry is empty) back to the graph — signals were blocked
            # above specifically so this is the one and only call, not a
            # duplicate of whatever _on_combo_changed would have fired.
            self._set_current_project_id(self._current_selected_id())

    def _current_selected_id(self) -> str | None:
        data = self.project_combo.currentData()
        return data if data and data != _ADD_NEW_PROJECT else None

    def _on_combo_changed(self, index: int) -> None:
        if self.project_combo.itemData(index) == _ADD_NEW_PROJECT:
            self._on_add_new_project()
            return
        self._set_current_project_id(self.project_combo.itemData(index))

    def _on_add_repo(self) -> None:
        self._add_repo()

    def _on_add_new_project(self) -> None:
        dialog = ProjectDialog(self)
        if dialog.exec():
            try:
                project = self.store.add_project(dialog.name())
            except UkoreHubError as exc:
                QMessageBox.warning(self, "Add Project", str(exc))
                self.refresh()
                return
            self._set_current_project_id(project.id)
            self.refresh()
        else:
            self.refresh()

    def _on_rename(self) -> None:
        project_id = self._current_selected_id()
        if project_id is None:
            QMessageBox.information(self, "Rename Project", "Select a project first.")
            return
        project = self.store.get_project(project_id)
        dialog = ProjectDialog(self, name=project.name)
        if not dialog.exec():
            return
        try:
            self.store.rename_project(project_id, dialog.name())
        except UkoreHubError as exc:
            QMessageBox.warning(self, "Rename Project", str(exc))
            return
        self.refresh()

    def _on_delete(self) -> None:
        project_id = self._current_selected_id()
        if project_id is None:
            QMessageBox.information(self, "Delete Project", "Select a project first.")
            return
        project = self.store.get_project(project_id)
        if not confirm_action(
            self,
            "Delete Project",
            f"Delete project '{project.name}' and ALL its repos from the registry for EVERYONE at the studio?\n\n"
            "This removes them from the shared registry immediately and cannot be undone.",
        ):
            return
        self.store.delete_project(project_id)
        self._set_current_project_id(None)
        self.refresh()
