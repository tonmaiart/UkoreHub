from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QHBoxLayout, QListWidget, QListWidgetItem, QStackedWidget, QWidget

from core.theme import DEFAULT_THEME_NAME, get_theme
from interface.settings_tab_registry import (
    CATEGORY_DEVELOPER,
    CATEGORY_GENERAL,
    CATEGORY_LABELS,
    CATEGORY_REPO,
    SettingsTabRegistry,
    SettingsTabSpec,
)

_HEADER_TEXT_COLOR = QColor(get_theme(DEFAULT_THEME_NAME).text_secondary)
# Extra vertical gap between category groups (General/Repo/Developer) in
# tab_list — a blank non-selectable row, on top of each header row's own
# padding, so the groups read as visually distinct sections.
_CATEGORY_GAP_HEIGHT = 10


class SettingsView(QWidget):
    """Embedded (not modal) settings UI — a permanent second view inside
    MainWindow's view_stack, switched to via the trailing Setting row in
    Sidebar's SectionTabList. Every settings page persists its own changes
    immediately, so there's no Save/Cancel here.

    tab_list renders three sections — General (whole-app/machine settings),
    Repo (settings about the active repo/project data — its header row is
    relabeled to the active repo's own name, see set_active_repo_name), then
    Developer (studio-admin/internal-plumbing tabs) — each with a
    non-selectable header row, so it's visually clear which kind of setting
    a tab is before clicking into it. See SettingsTabSpec.category."""

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
        # Repo's header item gets relabeled to the active repo's name at
        # runtime — see set_active_repo_name.
        self._category_header_items: dict[str, QListWidgetItem] = {}

        first_selectable_row: int | None = None
        is_first_category = True
        for category in (CATEGORY_GENERAL, CATEGORY_REPO, CATEGORY_DEVELOPER):
            category_specs = [spec for spec in self._specs if spec.category == category]
            if not category_specs:
                continue
            if not is_first_category:
                self._add_gap_row()
            is_first_category = False
            self._add_header_row(category, CATEGORY_LABELS[category])
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

    def _add_header_row(self, category: str, label: str) -> None:
        item = QListWidgetItem(label.upper())
        item.setFlags(Qt.NoItemFlags)
        item.setForeground(_HEADER_TEXT_COLOR)
        font = item.font()
        font.setBold(True)
        font.setPointSize(max(font.pointSize() - 1, 1))
        item.setFont(font)
        self.tab_list.addItem(item)
        self._row_specs.append(None)
        self._category_header_items[category] = item

    def set_active_repo_name(self, repo_name: str | None) -> None:
        """Relabels the Repo category's header row to the active repo's own
        name (falling back to "REPO" when no repo is active) — called from
        MainWindow whenever the active repo changes/clears. A no-op if no
        tab registered under CATEGORY_REPO (so there's no header row)."""
        item = self._category_header_items.get(CATEGORY_REPO)
        if item is None:
            return
        item.setText((repo_name or CATEGORY_LABELS[CATEGORY_REPO]).upper())

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
        """Re-runs the current sub-tab's on_activated — call this whenever
        the Setting view itself is switched back into, since switching
        between Repo/Setting doesn't change tab_list's row (no
        currentRowChanged to piggyback on)."""
        self._on_row_changed(self.tab_list.currentRow())

    def get_tab_widget(self, key: str) -> QWidget | None:
        """Looks up a constructed settings page by its SettingsTabSpec key —
        e.g. so MainWindow can connect to a signal a specific built-in page
        exposes (CommonSettingsPage.logout_requested) without SettingsView
        needing to know about that page's internals itself."""
        return self._tab_widgets.get(key)
