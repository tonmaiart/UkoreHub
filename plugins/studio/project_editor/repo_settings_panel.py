from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.theme import DEFAULT_THEME_NAME, get_theme
from interface.builtin_settings_tabs import BROWSER_LINKS, ENABLE_PLUGIN, LOCAL_REPOSITORY
from interface.settings_tab_registry import CATEGORY_REPO, SettingsTabRegistry, SettingsTabSpec

_TAB_LIST_WIDTH = 150
_HEADER_TEXT_COLOR = QColor(get_theme(DEFAULT_THEME_NAME).text_secondary)
# Extra vertical gap between the Repository/Plugins category groups in
# tab_list — a blank non-selectable row, on top of each header row's own
# padding, same convention interface/settings/settings_view.py uses.
_CATEGORY_GAP_HEIGHT = 10

# Duplicated from plugin.py's own CUSTOM_PATHS_SETTINGS_KEY rather than
# imported — plugin.py imports project_editor_page.py, which imports
# project_graph_view.py, which imports this file, so importing plugin.py
# from here closes a circular-import loop (plugin.py ends up "partially
# initialized" and the whole project_editor plugin fails to load, taking
# the Viewgraph panel down with it — hit exactly this 2026-07-20). Keep
# this string in sync with plugin.py's CUSTOM_PATHS_SETTINGS_KEY by hand.
_CUSTOM_PATHS_SETTINGS_KEY = "project_editor_custom_paths"

# The built-in CATEGORY_REPO tabs that make up "Repository" — everything
# else registered under CATEGORY_REPO (every plugin's own settings tab,
# e.g. Maya Launcher, UkoreShot, ModelPublisher, ...) falls under
# "Plugins" instead. Hardcoded rather than a new SettingsTabSpec field
# since there are only ever these four built-ins to name.
_REPOSITORY_KEYS = {LOCAL_REPOSITORY, _CUSTOM_PATHS_SETTINGS_KEY, ENABLE_PLUGIN, BROWSER_LINKS}
_CATEGORY_REPOSITORY = "repository"
_CATEGORY_PLUGINS = "plugins"
_CATEGORY_LABELS = {_CATEGORY_REPOSITORY: "Repository", _CATEGORY_PLUGINS: "Plugins"}


def _category_for(spec: SettingsTabSpec) -> str:
    return _CATEGORY_REPOSITORY if spec.key in _REPOSITORY_KEYS else _CATEGORY_PLUGINS


class RepoSettingsPanel(QWidget):
    """The content of Project Editor's "Repository Setting" popup (see
    RepoSettingsDialog below) — every CATEGORY_REPO SettingsTabSpec (Browser,
    Local Repository, Custom Paths, Enable Plugin, and any plugin's own
    CATEGORY_REPO tab) rendered generically, read straight off
    SettingsTabRegistry.ordered(). Zero coupling to any specific plugin —
    a plugin registering its own CATEGORY_REPO tab shows up here with no
    edits to this file, always under "Plugins". Replaces Settings > Repo,
    which no longer renders these (see settings_view.py).

    Uses the exact same tab-list + QStackedWidget template as
    interface/settings/settings_view.py's SettingsView, including its
    category-header-row grouping (changed 2026-07-20 from a single flat
    list to two groups — "Repository" for the built-in repo-level tabs and
    "Plugins" for every plugin-contributed one — matching how the
    program's own Setting view already groups General/Developer)."""

    def __init__(self, parent=None, *, settings_tab_registry: SettingsTabRegistry):
        super().__init__(parent)
        all_specs = [spec for spec in settings_tab_registry.ordered() if spec.category == CATEGORY_REPO]
        self._tab_widgets: dict[str, QWidget] = {}
        self._stack_index_by_key: dict[str, int] = {}
        # Parallel to tab_list's rows — None for a non-selectable category
        # header/gap row, so row->spec lookups (_on_row_changed) can skip
        # them, same convention interface/settings/settings_view.py uses.
        self._row_specs: list[SettingsTabSpec | None] = []

        self.tab_list = QListWidget()
        self.tab_list.setFixedWidth(_TAB_LIST_WIDTH)
        self.stack = QStackedWidget()

        first_selectable_row: int | None = None
        is_first_category = True
        for category in (_CATEGORY_REPOSITORY, _CATEGORY_PLUGINS):
            category_specs = [spec for spec in all_specs if _category_for(spec) == category]
            if not category_specs:
                continue
            if not is_first_category:
                self._add_gap_row()
            is_first_category = False
            self._add_header_row(_CATEGORY_LABELS[category])
            for spec in category_specs:
                widget = spec.page_factory()
                self._tab_widgets[spec.key] = widget
                self._stack_index_by_key[spec.key] = self.stack.addWidget(widget)
                self.tab_list.addItem(spec.label)
                self._row_specs.append(spec)
                if first_selectable_row is None:
                    first_selectable_row = len(self._row_specs) - 1

        self.tab_list.currentRowChanged.connect(self._on_row_changed)
        self.tab_list.setCurrentRow(first_selectable_row if first_selectable_row is not None else 0)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tab_list)
        layout.addWidget(self.stack, stretch=1)

    def _add_gap_row(self) -> None:
        item = QListWidgetItem("")
        item.setFlags(Qt.NoItemFlags)
        item.setSizeHint(QSize(0, _CATEGORY_GAP_HEIGHT))
        self.tab_list.addItem(item)
        self._row_specs.append(None)

    def _add_header_row(self, label: str) -> None:
        item = QListWidgetItem(label.upper())
        item.setFlags(Qt.NoItemFlags)
        item.setForeground(_HEADER_TEXT_COLOR)
        font = item.font()
        font.setBold(True)
        font.setPointSize(max(font.pointSize() - 1, 1))
        item.setFont(font)
        self.tab_list.addItem(item)
        self._row_specs.append(None)

    def _on_row_changed(self, row: int) -> None:
        if row < 0 or row >= len(self._row_specs):
            return
        spec = self._row_specs[row]
        if spec is None:
            return
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
    that was right-clicked — RepoSettingsPanel's tabs (Browser, Local
    Repository, Custom Paths, Enable Plugin, and any plugin's own
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
