from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QGroupBox, QLabel, QVBoxLayout, QWidget

from core.exceptions import NotFoundError
from plugins.studio.maya_launcher.repo_tools_store import RepoToolsStore
from plugins.studio.maya_launcher.tools import TOOL_IDS, TOOL_LABELS

SOFTWARE_LINKER_PLUGIN_ID = "software_linker"


class MayaLauncherSettingsPage(QWidget):
    """Settings > Maya Launcher — per-repo enable/disable for this plugin's
    7 nested tools (whichever repo is active when this tab is shown; see
    on_activated wiring in plugin.py's register(), which calls refresh()
    every time this tab becomes visible — interface/settings_tab_registry.py's
    SettingsTabSpec.on_activated), plus the Software Linker status readout
    that used to be a separate Repo Add-on panel (see this plugin's own
    README.md for why that moved here)."""

    def __init__(self, parent=None, *, api, tools_store: RepoToolsStore):
        super().__init__(parent)
        self._api = api
        self._tools_store = tools_store
        self._checkboxes: dict[str, QCheckBox] = {}

        self._active_repo_label = QLabel("")
        self._active_repo_label.setWordWrap(True)

        tools_group = QGroupBox("Enabled Tools for Active Repo")
        tools_layout = QVBoxLayout(tools_group)
        for tool_id in TOOL_IDS:
            checkbox = QCheckBox(TOOL_LABELS[tool_id])
            checkbox.toggled.connect(lambda _checked, tid=tool_id: self._on_tool_toggled(tid))
            tools_layout.addWidget(checkbox)
            self._checkboxes[tool_id] = checkbox

        self._link_status_label = QLabel("")
        self._link_status_label.setWordWrap(True)
        link_group = QGroupBox("Software Linker Status")
        link_layout = QVBoxLayout(link_group)
        link_layout.addWidget(self._link_status_label)

        layout = QVBoxLayout(self)
        layout.addWidget(self._active_repo_label)
        layout.addWidget(tools_group)
        layout.addWidget(link_group)
        layout.addStretch()

        self.refresh()

    def refresh(self) -> None:
        project_id = self._api.local_config.active_project_id
        repo_id = self._api.local_config.active_repo_id
        if not project_id or not repo_id:
            self._active_repo_label.setText("No repo selected.")
            for checkbox in self._checkboxes.values():
                checkbox.setEnabled(False)
            self._link_status_label.setText("")
            return

        try:
            project = self._api.metadata.get_project(project_id)
            repo = self._api.metadata.get_repo(project_id, repo_id)
        except NotFoundError:
            self._active_repo_label.setText("No repo selected.")
            for checkbox in self._checkboxes.values():
                checkbox.setEnabled(False)
            self._link_status_label.setText("")
            return

        self._active_repo_label.setText(f"Active repo: {project.name} / {repo.name}")
        enabled_tool_ids = set(self._tools_store.enabled_tool_ids_for(project_id, repo_id))
        for tool_id, checkbox in self._checkboxes.items():
            checkbox.setEnabled(True)
            blocked = checkbox.blockSignals(True)
            checkbox.setChecked(tool_id in enabled_tool_ids)
            checkbox.blockSignals(blocked)

        self._refresh_link_status(repo)

    def _refresh_link_status(self, repo) -> None:
        maya_programs = []
        for program_id in repo.required_program_ids:
            try:
                program = self._api.programs.get_program(program_id)
            except NotFoundError:
                continue
            if "maya" in program.name.lower():
                maya_programs.append(program)

        if not maya_programs:
            self._link_status_label.setText("This repo doesn't require Maya.")
            return

        linked = self._api.plugin_config_store(SOFTWARE_LINKER_PLUGIN_ID, shared=False)
        lines = []
        for program in maya_programs:
            path = linked.get(program.id)
            if path:
                lines.append(f"✅ {program.name} v{program.version} — linked: {path}")
            else:
                lines.append(
                    f"⚠️ {program.name} v{program.version} — not linked. "
                    "Configure it in Settings > Software Linker."
                )
        self._link_status_label.setText("\n".join(lines))

    def _on_tool_toggled(self, _tool_id: str) -> None:
        project_id = self._api.local_config.active_project_id
        repo_id = self._api.local_config.active_repo_id
        if not project_id or not repo_id:
            return
        enabled_tool_ids = sorted(tid for tid, checkbox in self._checkboxes.items() if checkbox.isChecked())
        self._tools_store.set_enabled_tool_ids(project_id, repo_id, enabled_tool_ids)
