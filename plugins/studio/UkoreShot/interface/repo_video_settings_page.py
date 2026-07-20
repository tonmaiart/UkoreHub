from __future__ import annotations

from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget

from plugins.studio.UkoreShot.core import video_path_store


class RepoVideoSettingsPage(QWidget):
    """Repository Setting > UkoreShot — lets a studio admin pick which of
    the active repo's own declared Custom Paths (Repository Setting >
    Custom Paths > Create Input Path) UkoreShot treats as this repo's
    playblast video library root. Confirmed with the user: picks from the
    repo's OWN Custom Paths catalog, not a "Connect Input Path" connection
    to a different repo (that's what RigPublisher/ModelPublisher/
    AnimationPublisher's own Repo Studio Setting tabs do instead — see
    plugins/studio/RigPublisher/settings_page.py) — playblasts stay inside
    the same repo they were shot in.

    Same self-resolving-active-repo `refresh()` pattern every CATEGORY_REPO
    tab in this app uses (e.g. RigPublisherSettingsPage), and the same
    "auto-use if there's only one, list + let admin pick if more than one"
    UX — see video_path_store.resolve_video_root for the matching
    resolution order."""

    def __init__(self, parent=None, *, api):
        super().__init__(parent)
        self._api = api
        self._project_id: str | None = None
        self._repo_id: str | None = None
        self._custom_paths: list[dict] = []

        self.hint_label = QLabel("")
        self.hint_label.setWordWrap(True)
        self.list_widget = QListWidget()
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        self.clear_button = QPushButton("Clear Choice")
        self.clear_button.clicked.connect(self._on_clear)

        layout = QVBoxLayout(self)
        layout.addWidget(self.hint_label)
        layout.addWidget(self.list_widget)
        layout.addWidget(self.clear_button)

        self.refresh()

    def refresh(self) -> None:
        """Re-resolves the active project/repo and rebuilds the list of
        Custom Path choices — called on construction and every time this
        tab becomes active (SettingsTabSpec.on_activated)."""
        project_id = self._api.local_config.active_project_id
        repo_id = self._api.local_config.active_repo_id
        self._project_id = project_id
        self._repo_id = repo_id
        self.list_widget.clear()

        if not project_id or not repo_id:
            self.hint_label.setText("Select a repo to see this information.")
            self.list_widget.setEnabled(False)
            self.clear_button.setEnabled(False)
            return

        self._custom_paths = video_path_store.get_custom_paths(self._api, project_id, repo_id)

        if not self._custom_paths:
            self.hint_label.setText(
                "This repo has no Custom Paths declared yet — UkoreShot has nowhere to look for videos. "
                "Add one under Repository Setting > Custom Paths > Create Input Path first."
            )
            self.list_widget.setEnabled(False)
            self.clear_button.setEnabled(False)
            return

        self.list_widget.setEnabled(True)
        self.clear_button.setEnabled(True)
        chosen_id = video_path_store.get_selected_custom_path_id(self._api, project_id, repo_id)
        for index, custom_path in enumerate(self._custom_paths):
            self.list_widget.addItem(QListWidgetItem(f"{custom_path['label']}  ({custom_path['path']})"))
            if custom_path.get("id") == chosen_id:
                self.list_widget.setCurrentRow(index)

        if len(self._custom_paths) == 1:
            self.hint_label.setText(
                "Only one Custom Path declared — UkoreShot uses it automatically, no choice needed."
            )
        else:
            self.hint_label.setText(
                "This repo has multiple Custom Paths declared — pick which one is the playblast video library."
            )

    def _on_selection_changed(self) -> None:
        if self._project_id is None or self._repo_id is None:
            return
        row = self.list_widget.currentRow()
        if not (0 <= row < len(self._custom_paths)):
            return
        video_path_store.set_selected_custom_path_id(
            self._api, self._project_id, self._repo_id, self._custom_paths[row]["id"]
        )

    def _on_clear(self) -> None:
        if self._project_id is None or self._repo_id is None:
            return
        video_path_store.set_selected_custom_path_id(self._api, self._project_id, self._repo_id, None)
        self.list_widget.clearSelection()
