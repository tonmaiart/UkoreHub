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
from interface.settings_tab_registry import (
    CATEGORY_DEVELOPER,
    CATEGORY_GENERAL,
    CATEGORY_LABELS,
    SettingsTabRegistry,
    SettingsTabSpec,
)

_HEADER_TEXT_COLOR = QColor(get_theme(DEFAULT_THEME_NAME).text_secondary)
# Extra vertical gap between category groups (General/Developer) in
# tab_list — a blank non-selectable row, on top of each header row's own
# padding, so the groups read as visually distinct sections.
_CATEGORY_GAP_HEIGHT = 10


class SettingsView(QWidget):
    """Settings UI content — a tab list + QStackedWidget, same shape
    `plugins/studio/project_editor/repo_settings_panel.py`'s
    RepoSettingsPanel uses for Repository Setting. Shown inside
    SettingsDialog (below), opened from Sidebar's footer Setting icon
    button (see MainWindow._on_settings_requested) — reverted 2026-07-19
    to a popup, matching Repository Setting's own dialog and this app's own
    pre-registry history (see register_builtin_settings_tabs' docstring:
    "matching the pre-registry behavior where SettingsDialog built new
    pages on every open" — it was briefly an embedded MainWindow.view_stack
    page instead in between). Every settings page persists its own changes
    immediately, so there's no Save/Cancel here.

    tab_list renders two sections — General (whole-app/machine settings)
    and Developer (studio-admin/internal-plumbing tabs) — each with a
    non-selectable header row, so it's visually clear which kind of setting
    a tab is before clicking into it. See SettingsTabSpec.category.

    CATEGORY_REPO tabs are still registered in the same SettingsTabRegistry
    (Explorer's own settings tab included) but are deliberately not
    rendered here as of 2026-07-15 — they render generically instead as
    collapsible sections in plugins/studio/project_editor/'s right panel
    (repo_settings_panel.py), which reads the same registry filtered to
    CATEGORY_REPO. This keeps a single place to edit repo settings rather
    than duplicating them in both Settings and Project Editor."""

    def __init__(self, parent=None, *, settings_tab_registry: SettingsTabRegistry):
        super().__init__(parent)

        self.tab_list = QListWidget()
        self.tab_list.setFixedWidth(180)

        self.stack = QStackedWidget()
        self._specs: list[SettingsTabSpec] = settings_tab_registry.ordered()
        self._tab_widgets: dict[str, QWidget] = {}
        self._stack_index_by_key: dict[str, int] = {}
        # Parallel to tab_list's rows — None for a non-selectable category
        # header row, so row->spec lookups (_on_row_changed) can skip them.
        self._row_specs: list[SettingsTabSpec | None] = []

        first_selectable_row: int | None = None
        is_first_category = True
        for category in (CATEGORY_GENERAL, CATEGORY_DEVELOPER):
            category_specs = [spec for spec in self._specs if spec.category == category]
            if not category_specs:
                continue
            if not is_first_category:
                self._add_gap_row()
            is_first_category = False
            self._add_header_row(CATEGORY_LABELS[category])
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

        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(self.tab_list)
        content_layout.addWidget(self.stack, stretch=1)

        # Big left/right spacers narrow the effective width of the page
        # (Discord/VS Code Settings style) rather than letting the tab list
        # + stack stretch edge-to-edge across a maximized window.
        layout = QHBoxLayout(self)
        layout.addStretch(1)
        layout.addWidget(content_widget, stretch=4)
        layout.addStretch(1)

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
        """Re-runs the current sub-tab's on_activated — not called anywhere
        right now (a fresh SettingsDialog/SettingsView already fires this
        once on construction, via __init__'s own setCurrentRow call), kept
        for symmetry with
        plugins/studio/project_editor/repo_settings_panel.py's
        RepoSettingsPanel.refresh_current_tab, for a future caller that
        needs to force a redraw without changing rows."""
        self._on_row_changed(self.tab_list.currentRow())

    def get_tab_widget(self, key: str) -> QWidget | None:
        """Looks up a constructed settings page by its SettingsTabSpec key —
        e.g. so MainWindow can connect to a signal a specific built-in page
        exposes (CommonSettingsPage.logout_requested) without MainWindow
        needing to know about SettingsView's internal storage. Fixed
        2026-07-20: SettingsDialog.get_tab_widget used to reference
        self._tab_widgets, which only ever existed on this class — every
        call from MainWindow._on_settings_requested raised AttributeError
        before dialog.exec() ever ran, so clicking the Setting button built
        the dialog but never actually showed it."""
        return self._tab_widgets.get(key)


class SettingsDialog(QDialog):
    """Popup wrapper around SettingsView — opened from Sidebar's footer
    Setting icon button (MainWindow._on_settings_requested), same pattern
    plugins/studio/project_editor/repo_settings_panel.py's
    RepoSettingsDialog uses for Repository Setting. Constructs a fresh
    SettingsView on every open (no state carried between opens, same
    "reopening gets clean state" convention register_builtin_settings_tabs'
    own docstring documents for every settings page's page_factory)."""

    def __init__(self, parent=None, *, settings_tab_registry: SettingsTabRegistry):
        super().__init__(parent)
        self.setWindowTitle("Setting")
        self.resize(820, 640)

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
