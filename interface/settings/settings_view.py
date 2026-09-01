from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QFile, QSize, Qt
from PySide6.QtGui import QColor
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from interface.theme import DEFAULT_THEME_NAME, get_theme
from plugin_api import (
    CATEGORY_DEVELOPER,
    CATEGORY_GENERAL,
    CATEGORY_LABELS,
    CATEGORY_PROJECT,
    CATEGORY_REPO,
    SettingsTabRegistry,
    SettingsTabSpec,
)

_HEADER_TEXT_COLOR = QColor(get_theme(DEFAULT_THEME_NAME).text_secondary)
# Extra vertical gap between groups in the flat settings list — a
# blank non-selectable row, on top of each header row's own padding, so the
# groups read as visually distinct sections.
_CATEGORY_GAP_HEIGHT = 10

_UI_FILE = Path(__file__).parent.parent / "SettingsWindow.ui"

_ACCOUNT_GROUP_LABEL = "Account"

# There used to be a separate hardcoded "Repository" group here, splitting
# CATEGORY_REPO specs between a handful of builtin tabs and everything else
# (plugin-contributed, e.g. Maya Launcher, MayaPublisher, UkoreBrowser).
# That builtin set shrank to zero over time — Requirements & Plugins moved
# to plugins/core/project_editor/'s CATEGORY_PROJECT "Repository Settings"
# tab, Custom Paths moved to that plugin's own CATEGORY_PROJECT group
# directly, and Local Repository was removed outright (2026-09-01, redundant
# with project_editor_page.py's own per-repo Unclone button) — so every
# CATEGORY_REPO spec is plugin-contributed now and the split was retired;
# they all render under "Plugins" (see `groups` below).


class SettingsView(QWidget):
    """Settings UI content, shown inside SettingsDialog (below), opened
    from Sidebar's footer Setting icon button (see
    MainWindow._on_settings_requested). Every settings page persists its
    own changes immediately, so there's no Save/Cancel here.

    UI authored in Qt Designer (SettingsWindow.ui, interface/ root) and
    loaded at runtime via QUiLoader, same pattern
    plugins/core/project_editor/custom_paths_settings_page.py uses for
    CustomPathWindow.ui. Every registered SettingsTabSpec (built-in or
    plugin-provided, via plugin_api.SettingsTabRegistry) renders as one row
    in a single flat listWidget_settings, grouped under a header per
    category — Account, Project, Developer, Plugins — instead
    of the old nested QTabWidget-of-QTabWidgets (2026-08-25 consolidation,
    per user request). widget_setting_info hosts a QStackedWidget switched
    by the list's current row.

    checkBox_admin_mode (unchecked by default) hides every group except
    Account — everything else here is Project/Developer/Repo-level
    plumbing most artists never need to see. select_tab() force-enables it
    when jumping straight to an admin-only tab, since a caller asking for
    that tab by key means it needs to be reachable regardless of the
    checkbox state."""

    def __init__(self, parent=None, *, settings_tab_registry: SettingsTabRegistry):
        super().__init__(parent)

        specs = settings_tab_registry.ordered()

        def specs_for(category: str) -> list[SettingsTabSpec]:
            return [spec for spec in specs if spec.category == category]

        # (header label, specs, requires admin mode to be visible)
        groups: list[tuple[str, list[SettingsTabSpec], bool]] = [
            (_ACCOUNT_GROUP_LABEL, specs_for(CATEGORY_GENERAL), False),
            (CATEGORY_LABELS[CATEGORY_PROJECT], specs_for(CATEGORY_PROJECT), True),
            (CATEGORY_LABELS[CATEGORY_DEVELOPER], specs_for(CATEGORY_DEVELOPER), True),
            ("Plugins", specs_for(CATEGORY_REPO), True),
        ]

        loader = QUiLoader()
        ui_file = QFile(str(_UI_FILE))
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, self)
        ui_file.close()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ui)

        self.list_widget: QListWidget = self.ui.findChild(QListWidget, "listWidget_settings")
        self.admin_checkbox: QCheckBox = self.ui.findChild(QCheckBox, "checkBox_admin_mode")
        self.close_button: QPushButton = self.ui.findChild(QPushButton, "pushButton_close")

        info_widget: QWidget = self.ui.findChild(QWidget, "widget_setting_info")
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        info_layout.addWidget(self.stack)

        self._tab_widgets: dict[str, QWidget] = {}
        self._stack_index_by_key: dict[str, int] = {}
        self._row_specs: list[SettingsTabSpec | None] = []
        self._row_requires_admin: list[bool] = []

        for label, group_specs, requires_admin in groups:
            if not group_specs:
                continue
            self._add_header_row(label, requires_admin)
            for spec in group_specs:
                widget = spec.page_factory()
                self._tab_widgets[spec.key] = widget
                self._stack_index_by_key[spec.key] = self.stack.addWidget(widget)
                self.list_widget.addItem(spec.label)
                self._row_specs.append(spec)
                self._row_requires_admin.append(requires_admin)
            self._add_gap_row(requires_admin)

        self.list_widget.currentRowChanged.connect(self._on_row_changed)
        self.admin_checkbox.toggled.connect(self._apply_admin_filter)
        self._apply_admin_filter(self.admin_checkbox.isChecked())

    def _add_header_row(self, label: str, requires_admin: bool) -> None:
        item = QListWidgetItem(label.upper())
        item.setFlags(Qt.NoItemFlags)
        item.setForeground(_HEADER_TEXT_COLOR)
        font = item.font()
        font.setBold(True)
        font.setPointSize(max(font.pointSize() - 1, 1))
        item.setFont(font)
        self.list_widget.addItem(item)
        self._row_specs.append(None)
        self._row_requires_admin.append(requires_admin)

    def _add_gap_row(self, requires_admin: bool) -> None:
        item = QListWidgetItem("")
        item.setFlags(Qt.NoItemFlags)
        item.setSizeHint(QSize(0, _CATEGORY_GAP_HEIGHT))
        self.list_widget.addItem(item)
        self._row_specs.append(None)
        self._row_requires_admin.append(requires_admin)

    def _apply_admin_filter(self, admin_mode: bool) -> None:
        for row in range(self.list_widget.count()):
            self.list_widget.item(row).setHidden(self._row_requires_admin[row] and not admin_mode)
        current = self.list_widget.currentRow()
        if current < 0 or self._row_specs[current] is None or self.list_widget.item(current).isHidden():
            self._select_first_visible_row()

    def _select_first_visible_row(self) -> None:
        for row, spec in enumerate(self._row_specs):
            if spec is not None and not self.list_widget.item(row).isHidden():
                self.list_widget.setCurrentRow(row)
                return

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
        """Looks up a constructed settings page by its SettingsTabSpec key —
        e.g. so MainWindow can connect to a signal a specific built-in page
        exposes (CommonSettingsPage.logout_requested) without SettingsView
        needing to know about that page's internals itself."""
        return self._tab_widgets.get(key)

    def select_tab(self, key: str) -> None:
        """Jumps straight to one row by its SettingsTabSpec key — e.g.
        project_graph_view.py's "Repository Setting..." landing on
        Repository > Local Repository. Force-enables admin mode first if
        the target row is admin-only, since a caller asking for it by key
        means it must be reachable. A key with no matching row is a
        no-op — the dialog just stays on its current row."""
        for row, spec in enumerate(self._row_specs):
            if spec is not None and spec.key == key:
                if self._row_requires_admin[row] and not self.admin_checkbox.isChecked():
                    self.admin_checkbox.setChecked(True)
                self.list_widget.setCurrentRow(row)
                return

    def refresh_current_tab(self) -> None:
        """Re-runs the current row's on_activated — not called anywhere
        right now (a fresh SettingsDialog/SettingsView already fires this
        once on construction), kept for a future caller that needs to
        force a redraw without changing rows."""
        self._on_row_changed(self.list_widget.currentRow())


class SettingsDialog(QDialog):
    """Popup wrapper around SettingsView — opened from Sidebar's footer
    Setting icon button (MainWindow._on_settings_requested). Constructs a
    fresh SettingsView on every open (no state carried between opens, same
    "reopening gets clean state" convention register_builtin_settings_tabs'
    own docstring documents for every settings page's page_factory). The
    Close button lives inside SettingsWindow.ui (pushButton_close) rather
    than a separate QDialogButtonBox."""

    def __init__(self, parent=None, *, settings_tab_registry: SettingsTabRegistry):
        super().__init__(parent)
        self.setWindowTitle("Setting")
        self.resize(1000, 700)

        self.view = SettingsView(settings_tab_registry=settings_tab_registry)
        self.view.close_button.clicked.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)

    def get_tab_widget(self, key: str) -> QWidget | None:
        """Looks up a constructed settings page by its SettingsTabSpec key —
        e.g. so MainWindow can connect to a signal a specific built-in page
        exposes (CommonSettingsPage.logout_requested) without SettingsView
        needing to know about that page's internals itself."""
        return self.view.get_tab_widget(key)

    def select_tab(self, key: str) -> None:
        self.view.select_tab(key)
