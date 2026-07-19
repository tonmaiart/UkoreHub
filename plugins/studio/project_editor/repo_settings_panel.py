from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QHBoxLayout, QListWidget, QStackedWidget, QVBoxLayout, QWidget

from interface.settings_tab_registry import CATEGORY_REPO, SettingsTabRegistry, SettingsTabSpec

_TAB_LIST_WIDTH = 150


class RepoSettingsPanel(QWidget):
    """The content of Project Editor's "Repository Setting" popup (see
    RepoSettingsDialog below) — every CATEGORY_REPO SettingsTabSpec
    (Project Status, Browser, Local Repository, Enable Plugin, and any
    plugin's own CATEGORY_REPO tab) rendered generically, read straight off
    SettingsTabRegistry.ordered(). Zero coupling to any specific plugin —
    a plugin registering its own CATEGORY_REPO tab shows up here with no
    edits to this file. Replaces Settings > Repo, which no longer renders
    these (see settings_view.py).

    Uses the exact same tab-list + QStackedWidget template as
    interface/settings/settings_view.py's SettingsView — a QListWidget of
    labels on the left switching a QStackedWidget on the right, every page
    constructed eagerly, `on_activated` re-run only for whichever tab is
    currently selected. Changed 2026-07-19 away from a column of
    collapsible accordion sections so Repository Setting reads as one
    consistent settings UI with the program's own Setting view instead of
    its own bespoke layout. No category header rows here (unlike
    SettingsView) since every spec rendered in this popup is already
    CATEGORY_REPO — there's only ever one group."""

    def __init__(self, parent=None, *, settings_tab_registry: SettingsTabRegistry):
        super().__init__(parent)
        self._specs: list[SettingsTabSpec] = [
            spec for spec in settings_tab_registry.ordered() if spec.category == CATEGORY_REPO
        ]
        self._tab_widgets: dict[str, QWidget] = {}
        self._stack_index_by_key: dict[str, int] = {}

        self.tab_list = QListWidget()
        self.tab_list.setFixedWidth(_TAB_LIST_WIDTH)
        self.stack = QStackedWidget()

        for spec in self._specs:
            widget = spec.page_factory()
            self._tab_widgets[spec.key] = widget
            self._stack_index_by_key[spec.key] = self.stack.addWidget(widget)
            self.tab_list.addItem(spec.label)

        self.tab_list.currentRowChanged.connect(self._on_row_changed)
        if self._specs:
            self.tab_list.setCurrentRow(0)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tab_list)
        layout.addWidget(self.stack, stretch=1)

    def _on_row_changed(self, row: int) -> None:
        if row < 0 or row >= len(self._specs):
            return
        spec = self._specs[row]
        self.stack.setCurrentIndex(self._stack_index_by_key[spec.key])
        if spec.on_activated is not None:
            spec.on_activated(self._tab_widgets[spec.key])

    def refresh_current_tab(self) -> None:
        """Re-runs the current tab's on_activated — same
        SettingsView.refresh_current_tab convention, for a future caller
        that needs to force a redraw without changing rows (e.g. the active
        repo changing while this popup is open)."""
        self._on_row_changed(self.tab_list.currentRow())


class RepoSettingsDialog(QDialog):
    """Popup wrapper around RepoSettingsPanel — opened from a repo node's
    right-click context menu ("Repository Setting...", see
    project_graph_view.py's RepoNodeItem.contextMenuEvent /
    ProjectGraphView.open_repo_settings) instead of the panel being a
    permanent fixture beside the graph (moved out 2026-07-15). Constructs a
    fresh RepoSettingsPanel on every open — same "reopening gets clean
    state" convention interface/builtin_settings_tabs.py's page_factory
    already documents for Settings tabs — so there's no stale
    expanded/collapsed state carried between opens.

    Reflects whichever repo is currently ACTIVE, not necessarily the node
    that was right-clicked — RepoSettingsPanel's tabs (Project Status,
    Browser, Local Repository, Enable Plugin, and any plugin's own
    CATEGORY_REPO tab) all self-resolve the active repo from
    local_config_store, the same
    established convention every one of them already uses inside Settings.
    Right-clicking a non-active node still opens this dialog, it just shows
    the active repo's settings — pair it with a left-click (now switches
    the active repo, see RepoNodeItem.mousePressEvent) first if you want
    them to match."""

    def __init__(self, parent=None, *, settings_tab_registry: SettingsTabRegistry, title: str = "Repository Setting"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(820, 640)

        self.panel = RepoSettingsPanel(settings_tab_registry=settings_tab_registry)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.Close).clicked.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(self.panel)
        layout.addWidget(buttons)
