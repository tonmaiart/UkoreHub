from __future__ import annotations

from PySide6.QtWidgets import QGroupBox, QLabel, QVBoxLayout, QWidget

from core.extensibility.loader import DiscoveredPlugin
from core.models import Project, Repo
from interface.repo_addon_panel_registry import RepoAddonPanelRegistry


class RepoAddonTab(QWidget):
    """Project Information sub-tab where each add-on the active repo has
    enabled (Repo.enabled_addon_ids) can render its own per-repo preference
    panel, via whatever it registered through
    PluginAPI.register_repo_addon_panel(...)."""

    def __init__(
        self,
        parent=None,
        *,
        repo_addon_panel_registry: RepoAddonPanelRegistry,
        addon_catalog: list[DiscoveredPlugin],
    ):
        super().__init__(parent)
        self._registry = repo_addon_panel_registry
        self._addon_by_id = {discovered.manifest.id: discovered for discovered in addon_catalog}

        self.empty_label = QLabel("This repo has no enabled add-ons with a configuration panel.")

        self.panels_layout = QVBoxLayout()
        self.panels_layout.addStretch()

        layout = QVBoxLayout(self)
        layout.addWidget(self.empty_label)
        layout.addLayout(self.panels_layout)

    def set_repo(self, project: Project | None, repo: Repo | None, workspace_root: str | None) -> None:
        groups = []
        if repo is not None:
            for addon_id in repo.enabled_addon_ids:
                spec = self._registry.get(addon_id)
                if spec is None:
                    continue  # enabled but no registered panel — silently skip
                discovered = self._addon_by_id.get(addon_id)
                title = discovered.manifest.name if discovered else addon_id
                group = QGroupBox(title)
                group_layout = QVBoxLayout(group)
                group_layout.addWidget(spec.panel_factory(repo))
                groups.append(group)
        self.empty_label.setVisible(not groups)
        self._replace_cards(self.panels_layout, groups)

    @staticmethod
    def _replace_cards(layout: QVBoxLayout, widgets: list[QWidget]) -> None:
        while layout.count() > 1:  # keep the trailing stretch
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for widget in widgets:
            layout.insertWidget(layout.count() - 1, widget)
