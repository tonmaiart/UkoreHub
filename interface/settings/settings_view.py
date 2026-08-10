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
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from interface.theme import DEFAULT_THEME_NAME, get_theme
from interface.builtin_settings_tabs import LOCAL_REPOSITORY, REQUIREMENTS_AND_PLUGINS
from interface.settings_tab_registry import (
    CATEGORY_DEVELOPER,
    CATEGORY_GENERAL,
    CATEGORY_LABELS,
    CATEGORY_PROJECT,
    CATEGORY_REPO,
    SettingsTabRegistry,
    SettingsTabSpec,
)

_HEADER_TEXT_COLOR = QColor(get_theme(DEFAULT_THEME_NAME).text_secondary)
# Extra vertical gap between sub-groups in a _CategoryPage's tab_list — a
# blank non-selectable row, on top of each header row's own padding, so the
# groups read as visually distinct sections.
_CATEGORY_GAP_HEIGHT = 10

_TOP_TAB_ACCOUNT = "Account"
_TOP_TAB_PROJECT_DEV = "Project (Dev)"
_TOP_TAB_REPO_DEV = "Repo Setting (Dev)"

# Duplicated from plugins/core/project_editor/plugin.py's own
# CUSTOM_PATHS_SETTINGS_KEY rather than imported — importing that plugin's
# module from here would import project_editor_page.py -> project_graph_view.py,
# which itself imports interface.settings.settings_view (for
# open_settings_tab's target keys), closing a circular-import loop. Keep
# this string in sync with plugin.py's own constant by hand — same
# precaution repo_settings_panel.py used to take before it was retired.
_CUSTOM_PATHS_SETTINGS_KEY = "project_editor_custom_paths"

# The built-in CATEGORY_REPO tabs that make up "Repository" under the
# Repo Setting (Dev) top tab — everything else registered under
# CATEGORY_REPO (a plugin's own settings tab, e.g. Maya Launcher,
# MayaPublisher, UkoreBrowser, ...) falls under "Plugins" instead.
# Hardcoded rather than a new SettingsTabSpec field since there are only
# ever these three built-ins to name — same convention the now-retired
# RepoSettingsPanel used.
_REPOSITORY_KEYS = {LOCAL_REPOSITORY, _CUSTOM_PATHS_SETTINGS_KEY, REQUIREMENTS_AND_PLUGINS}


class _CategoryPage(QWidget):
    """One top-level Settings tab's content. Shows its one page directly
    with no extra chrome if there's exactly one SettingsTabSpec across all
    of its groups (auto-hiding the sub-nav); otherwise shows the familiar
    tab_list + QStackedWidget, with a header row per non-empty group only
    when there's more than one non-empty group to distinguish."""

    def __init__(self, parent=None, *, groups: list[tuple[str | None, list[SettingsTabSpec]]]):
        super().__init__(parent)
        self._tab_widgets: dict[str, QWidget] = {}
        self._stack_index_by_key: dict[str, int] = {}
        self._row_specs: list[SettingsTabSpec | None] = []
        self.tab_list: QListWidget | None = None
        self.stack: QStackedWidget | None = None
        self._single_spec: SettingsTabSpec | None = None

        non_empty_groups = [(label, specs) for label, specs in groups if specs]
        all_specs = [spec for _, specs in non_empty_groups for spec in specs]

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if len(all_specs) <= 1:
            spec = all_specs[0] if all_specs else None
            self._single_spec = spec
            if spec is not None:
                widget = spec.page_factory()
                self._tab_widgets[spec.key] = widget
                layout.addWidget(widget)
                if spec.on_activated is not None:
                    spec.on_activated(widget)
            return

        self.tab_list = QListWidget()
        self.tab_list.setFixedWidth(180)
        self.stack = QStackedWidget()

        show_headers = len(non_empty_groups) > 1
        first_selectable_row: int | None = None
        for index, (label, specs) in enumerate(non_empty_groups):
            if index > 0:
                self._add_gap_row()
            if show_headers and label is not None:
                self._add_header_row(label)
            for spec in specs:
                widget = spec.page_factory()
                self._tab_widgets[spec.key] = widget
                self._stack_index_by_key[spec.key] = self.stack.addWidget(widget)
                self.tab_list.addItem(spec.label)
                self._row_specs.append(spec)
                if first_selectable_row is None:
                    first_selectable_row = len(self._row_specs) - 1

        self.tab_list.currentRowChanged.connect(self._on_row_changed)
        self.tab_list.setCurrentRow(first_selectable_row if first_selectable_row is not None else 0)

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

    def get_tab_widget(self, key: str) -> QWidget | None:
        return self._tab_widgets.get(key)

    def select_tab(self, key: str) -> bool:
        """Selects `key` if this page has it, returning whether it did —
        SettingsView tries each top tab's page in turn."""
        if self._single_spec is not None and self._single_spec.key == key:
            return True
        if self.tab_list is None:
            return False
        for row, spec in enumerate(self._row_specs):
            if spec is not None and spec.key == key:
                self.tab_list.setCurrentRow(row)
                return True
        return False

    def refresh_current(self) -> None:
        if self.tab_list is not None:
            self._on_row_changed(self.tab_list.currentRow())
        elif self._single_spec is not None and self._single_spec.on_activated is not None:
            self._single_spec.on_activated(self._tab_widgets[self._single_spec.key])


class SettingsView(QWidget):
    """Settings UI content — a top-level QTabWidget with three categories,
    shown inside SettingsDialog (below), opened from Sidebar's footer
    Setting icon button (see MainWindow._on_settings_requested). Every
    settings page persists its own changes immediately, so there's no
    Save/Cancel here.

    - Account (CATEGORY_GENERAL) — whole-app/machine settings.
    - Project (Dev) (CATEGORY_PROJECT + CATEGORY_DEVELOPER) — the Project
      registry itself plus studio-admin/internal-plumbing tabs.
    - Repo Setting (Dev) (CATEGORY_REPO) — settings about the active repo.
      Rendered here as of this refactor; previously (2026-07-15 through
      this change) these were pulled out into
      plugins/core/project_editor/'s "Repository Setting" right-click
      popup instead, to avoid the same setting being editable from two
      different dialogs. That popup is retired now that its tabs live
      here — see project_graph_view.py's open_repo_settings(), which opens
      this same dialog via UICommandService.open_settings_tab instead.

    Each top tab auto-hides its own sub-nav chrome when it resolves to
    exactly one SettingsTabSpec (see _CategoryPage) — e.g. Account today."""

    def __init__(self, parent=None, *, settings_tab_registry: SettingsTabRegistry):
        super().__init__(parent)

        specs = settings_tab_registry.ordered()

        def specs_for(category: str) -> list[SettingsTabSpec]:
            return [spec for spec in specs if spec.category == category]

        repo_specs = specs_for(CATEGORY_REPO)
        repo_repository_specs = [spec for spec in repo_specs if spec.key in _REPOSITORY_KEYS]
        repo_plugin_specs = [spec for spec in repo_specs if spec.key not in _REPOSITORY_KEYS]

        self._account_page = _CategoryPage(groups=[(None, specs_for(CATEGORY_GENERAL))])
        self._project_dev_page = _CategoryPage(
            groups=[
                (CATEGORY_LABELS[CATEGORY_PROJECT], specs_for(CATEGORY_PROJECT)),
                (CATEGORY_LABELS[CATEGORY_DEVELOPER], specs_for(CATEGORY_DEVELOPER)),
            ]
        )
        self._repo_dev_page = _CategoryPage(
            groups=[("Repository", repo_repository_specs), ("Plugins", repo_plugin_specs)]
        )
        self._pages = [self._account_page, self._project_dev_page, self._repo_dev_page]

        self.tabs = QTabWidget()
        self.tabs.addTab(self._account_page, _TOP_TAB_ACCOUNT)
        self.tabs.addTab(self._project_dev_page, _TOP_TAB_PROJECT_DEV)
        self.tabs.addTab(self._repo_dev_page, _TOP_TAB_REPO_DEV)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tabs)

    def refresh_current_tab(self) -> None:
        """Re-runs the current top tab's current sub-tab on_activated — not
        called anywhere right now (a fresh SettingsDialog/SettingsView
        already fires this once on construction), kept for a future caller
        that needs to force a redraw without changing tabs."""
        current = self.tabs.currentWidget()
        if isinstance(current, _CategoryPage):
            current.refresh_current()

    def get_tab_widget(self, key: str) -> QWidget | None:
        """Looks up a constructed settings page by its SettingsTabSpec key —
        e.g. so MainWindow can connect to a signal a specific built-in page
        exposes (CommonSettingsPage.logout_requested) without SettingsView
        needing to know about that page's internals itself."""
        for page in self._pages:
            widget = page.get_tab_widget(key)
            if widget is not None:
                return widget
        return None

    def select_tab(self, key: str) -> None:
        """Jumps straight to one tab by its SettingsTabSpec key, switching
        the top-level QTabWidget to whichever category owns it — e.g.
        project_graph_view.py's "Repository Setting..." landing on Repo
        Setting (Dev) > Local Repository. A key with no matching tab
        anywhere is a no-op — the dialog just stays on its current tab."""
        for index, page in enumerate(self._pages):
            if page.select_tab(key):
                self.tabs.setCurrentIndex(index)
                return


class SettingsDialog(QDialog):
    """Popup wrapper around SettingsView — opened from Sidebar's footer
    Setting icon button (MainWindow._on_settings_requested). Constructs a
    fresh SettingsView on every open (no state carried between opens, same
    "reopening gets clean state" convention register_builtin_settings_tabs'
    own docstring documents for every settings page's page_factory)."""

    def __init__(self, parent=None, *, settings_tab_registry: SettingsTabRegistry):
        super().__init__(parent)
        self.setWindowTitle("Setting")
        self.resize(1000, 700)

        self.view = SettingsView(settings_tab_registry=settings_tab_registry)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.Close).clicked.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(self.view)
        layout.addWidget(buttons)

    def get_tab_widget(self, key: str) -> QWidget | None:
        """Looks up a constructed settings page by its SettingsTabSpec key —
        e.g. so MainWindow can connect to a signal a specific built-in page
        exposes (CommonSettingsPage.logout_requested) without SettingsView
        needing to know about that page's internals itself."""
        return self.view.get_tab_widget(key)

    def select_tab(self, key: str) -> None:
        self.view.select_tab(key)
