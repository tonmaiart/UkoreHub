from __future__ import annotations

from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget

from core.exceptions import NotFoundError

TOOL_ID = "rig_publisher"


class RigPublisherSettingsPage(QWidget):
    """Repo Studio Setting for RigPublisher — lets a studio admin pick
    which of the active repo's declared pipeline connections ("Connect
    Pipeline Input Path...", each a specific CustomPath within a target
    repo, see plugins/studio/project_editor/pipeline_store.py) this tool
    should actually publish into. Replaces the free-text "Custom Path"
    field artists used to type directly in Maya, removed 2026-07-19 — see
    plugins/studio/PublishApi/README.md's `get_publish_root(tool_id)` for
    how this choice is read back on the Maya side (falls back to "the
    repo's only declared connection" automatically if there's exactly
    one, so this tab only needs a real decision when a repo has more than
    one). Same self-resolving-active-repo `refresh()` pattern as
    interface/settings/browser_links_settings_page.py."""

    def __init__(self, parent=None, *, api):
        super().__init__(parent)
        self._api = api
        self._project_id: str | None = None
        self._repo_id: str | None = None
        self._outputs: list[dict] = []

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
        pipeline-connection choices — called on construction and every time
        this tab becomes active (SettingsTabSpec.on_activated)."""
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

        pipeline_store = self._api.plugin_config_store("project_editor", shared=True)
        pipeline_store.load()  # separate PluginConfigStore instance from project_editor's own — reload live
        entry = pipeline_store.get("projects", {}).get(project_id, {}).get("repos", {}).get(repo_id, {})
        self._outputs = entry.get("pipeline_inputs", [])

        if not self._outputs:
            self.hint_label.setText(
                "This repo has no pipeline connection declared in Project Editor yet — "
                "RigPublisher has nothing to publish to. Add one under Repository "
                "Setting > Custom Paths > Connect Input Path..."
            )
            self.list_widget.setEnabled(False)
            self.clear_button.setEnabled(False)
            return

        self.list_widget.setEnabled(True)
        self.clear_button.setEnabled(True)
        chosen = self._get_chosen()
        for index, ref in enumerate(self._outputs):
            self.list_widget.addItem(QListWidgetItem(self._describe_ref(pipeline_store, ref)))
            if chosen is not None and self._same_ref(ref, chosen):
                self.list_widget.setCurrentRow(index)

        if len(self._outputs) == 1:
            self.hint_label.setText(
                "Only one pipeline connection declared — RigPublisher uses it automatically, no choice needed."
            )
        else:
            self.hint_label.setText(
                "This repo has multiple pipeline connections declared — pick which one RigPublisher publishes into."
            )

    @staticmethod
    def _same_ref(a: dict, b: dict) -> bool:
        return (
            a.get("project_id") == b.get("project_id")
            and a.get("repo_id") == b.get("repo_id")
            and a.get("custom_path_id") == b.get("custom_path_id")
        )

    def _describe_ref(self, pipeline_store, ref: dict) -> str:
        try:
            target_name = self._api.metadata.get_repo(ref["project_id"], ref["repo_id"]).name
        except NotFoundError:
            target_name = "(deleted repo)"
        target_entry = (
            pipeline_store.get("projects", {}).get(ref["project_id"], {}).get("repos", {}).get(ref["repo_id"], {})
        )
        custom_path = next(
            (cp for cp in target_entry.get("custom_paths", []) if cp["id"] == ref.get("custom_path_id")), None
        )
        label = custom_path["label"] if custom_path else "(deleted custom path)"
        return f"{target_name} — {label}"

    def _get_chosen(self) -> dict | None:
        store = self._api.plugin_config_store(TOOL_ID, shared=True)
        return store.get("repo_publish_target", {}).get(f"{self._project_id}:{self._repo_id}")

    def _on_selection_changed(self) -> None:
        if self._project_id is None or self._repo_id is None:
            return
        row = self.list_widget.currentRow()
        if not (0 <= row < len(self._outputs)):
            return
        store = self._api.plugin_config_store(TOOL_ID, shared=True)
        targets = store.get("repo_publish_target", {})
        targets[f"{self._project_id}:{self._repo_id}"] = self._outputs[row]
        store.set("repo_publish_target", targets)

    def _on_clear(self) -> None:
        if self._project_id is None or self._repo_id is None:
            return
        store = self._api.plugin_config_store(TOOL_ID, shared=True)
        targets = store.get("repo_publish_target", {})
        targets.pop(f"{self._project_id}:{self._repo_id}", None)
        store.set("repo_publish_target", targets)
        self.list_widget.clearSelection()
