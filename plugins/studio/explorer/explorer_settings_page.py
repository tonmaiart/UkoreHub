from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QInputDialog, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from core.exceptions import NotFoundError
from core.extensibility.config_store import PluginConfigStore
from core.models import ExplorerPin, Project, Repo
from core.store import LocalConfigStore, MetadataStore
from interface.login.repo_picker import RepoPickerDialog
from interface.shared.widget_helpers import show_exclusive, wrap_scrollable


class ExplorerSettingsPage(QWidget):
    """Per-repo list of other repos pinned as extra Explorer-style sidebar
    tabs while this repo is active (Repo.explorer_pins, rendered by
    plugins/studio/explorer/pinned_repo_browser_page.py's PinnedRepoBrowserPage,
    rebuilt by interface/main_window.py's _rebuild_pinned_explorer_tabs).
    Scoped to a single repo, so like BrowserLinksSettingsPage it resolves
    the active project/repo itself from local_config_store on refresh()
    rather than waiting for a set_repo() call MainWindow never makes for
    Settings pages.

    "Add Pinned Repo..." only offers repos declared as this repo's pipeline
    inputs/outputs in Project Data Editor (plugins/studio/pipeline_architect) —
    read via pipeline_config_store, a PluginConfigStore constructed with
    that plugin's own id string (see its README's "Reading pipeline data
    from another plugin" section) rather than an import, per this app's
    "convention, not import" cross-plugin data-sharing pattern."""

    pins_changed = Signal()

    def __init__(
        self,
        parent=None,
        *,
        store: MetadataStore,
        local_config_store: LocalConfigStore,
        pipeline_config_store: PluginConfigStore,
    ):
        super().__init__(parent)
        self.store = store
        self.local_config_store = local_config_store
        self.pipeline_config_store = pipeline_config_store
        self._project: Project | None = None
        self._repo: Repo | None = None

        self.empty_label = QLabel("Select a repo to see this information.")

        self._rows_container = QWidget()
        self._rows_layout = QVBoxLayout(self._rows_container)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)

        add_button = QPushButton("Add Pinned Repo...")
        add_button.clicked.connect(self._on_add_pin)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.addWidget(self._rows_container)
        content_layout.addWidget(add_button)
        content_layout.addStretch()

        scroll = wrap_scrollable(content)

        self.content_widget = QWidget()
        content_wrap_layout = QVBoxLayout(self.content_widget)
        content_wrap_layout.setContentsMargins(0, 0, 0, 0)
        content_wrap_layout.addWidget(scroll)

        layout = QVBoxLayout(self)
        layout.addWidget(self.empty_label)
        layout.addWidget(self.content_widget)

        self.refresh()

    def refresh(self) -> None:
        """Re-resolves the active project/repo from local_config_store and
        rebuilds the pin rows — called on construction and every time this
        tab becomes active (SettingsTabSpec.on_activated), the same
        lazy-refresh pattern BrowserLinksSettingsPage uses."""
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
        self._rebuild_rows()

    def _resolve_target_name(self, pin: ExplorerPin) -> str:
        try:
            project = self.store.get_project(pin.target_project_id)
            repo = self.store.get_repo(pin.target_project_id, pin.target_repo_id)
        except NotFoundError:
            return "(deleted repo)"
        return f"{project.name} / {repo.name}"

    def _rebuild_rows(self) -> None:
        while self._rows_layout.count():
            item = self._rows_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        if self._repo is None:
            return
        for index, pin in enumerate(self._repo.explorer_pins):
            row_widget = QWidget()
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(0, 0, 0, 0)
            row.addWidget(QLabel(f"<b>{pin.label}</b>"))
            target_label = QLabel(self._resolve_target_name(pin))
            target_label.setWordWrap(True)
            row.addWidget(target_label, stretch=1)
            rename_button = QPushButton("Rename")
            rename_button.clicked.connect(lambda _checked, i=index: self._on_rename_pin(i))
            row.addWidget(rename_button)
            remove_button = QPushButton("Remove")
            remove_button.clicked.connect(lambda _checked, i=index: self._on_remove_pin(i))
            row.addWidget(remove_button)
            self._rows_layout.addWidget(row_widget)

    def _pipeline_repo_pairs(self) -> set[tuple[str, str]]:
        """Every (project_id, repo_id) declared as a pipeline input or
        output of the active repo — see pipeline_architect's README for the
        exact JSON shape this navigates ("projects" -> project_id ->
        "repos" -> repo_id -> pipeline_inputs/pipeline_outputs, each entry
        a {"project_id", "repo_id"} pair)."""
        if self._project is None or self._repo is None:
            return set()
        # Re-read from disk — this PluginConfigStore instance is a separate
        # object from pipeline_architect's own (each plugin constructs its
        # own via api.plugin_config_store(), per the "convention, not
        # import" pattern), so its in-memory cache from app startup would
        # otherwise miss edits pipeline_architect's own page made later in
        # the same session.
        self.pipeline_config_store.load()
        tree = self.pipeline_config_store.get("projects", {})
        entry = tree.get(self._project.id, {}).get("repos", {}).get(self._repo.id, {})
        pairs = set()
        for ref in entry.get("pipeline_inputs", []) + entry.get("pipeline_outputs", []):
            pairs.add((ref["project_id"], ref["repo_id"]))
        return pairs

    def _on_add_pin(self) -> None:
        if self._project is None or self._repo is None:
            return
        allowed_pairs = self._pipeline_repo_pairs()
        if not allowed_pairs:
            QMessageBox.information(
                self,
                "Add Pinned Repo",
                "This repo has no pipeline inputs/outputs declared yet. "
                "Set them in Settings > Developer > Project Data Editor first.",
            )
            return
        dialog = RepoPickerDialog(self, store=self.store, allowed_pairs=allowed_pairs)
        if not dialog.exec():
            return
        target_project_id = dialog.selected_project_id()
        target_repo_id = dialog.selected_repo_id()
        if not target_project_id or not target_repo_id:
            return
        if target_project_id == self._project.id and target_repo_id == self._repo.id:
            return  # pinning the active repo onto itself is meaningless
        try:
            target_repo = self.store.get_repo(target_project_id, target_repo_id)
        except NotFoundError:
            return
        pins = list(self._repo.explorer_pins) + [
            ExplorerPin(target_project_id=target_project_id, target_repo_id=target_repo_id, label=target_repo.name)
        ]
        self._save_pins(pins)

    def _on_rename_pin(self, index: int) -> None:
        if self._repo is None:
            return
        pins = list(self._repo.explorer_pins)
        if not (0 <= index < len(pins)):
            return
        new_label, ok = QInputDialog.getText(self, "Rename Pinned Repo", "New name:", text=pins[index].label)
        if not ok or not new_label.strip():
            return
        pins[index] = ExplorerPin(
            target_project_id=pins[index].target_project_id,
            target_repo_id=pins[index].target_repo_id,
            label=new_label.strip(),
        )
        self._save_pins(pins)

    def _on_remove_pin(self, index: int) -> None:
        if self._repo is None:
            return
        pins = list(self._repo.explorer_pins)
        if 0 <= index < len(pins):
            del pins[index]
        self._save_pins(pins)

    def _save_pins(self, pins: list[ExplorerPin]) -> None:
        self.store.set_repo_explorer_pins(self._project.id, self._repo.id, pins)
        self._repo.explorer_pins = pins
        self._rebuild_rows()
        self.pins_changed.emit()
