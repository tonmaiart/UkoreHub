"""interface_api: the only import surface for app/interface/'s internals.

app/interface/ is closed — nothing outside app/interface/ and
app/interface_api/ may import interface.* directly (see
developer/app/check_import_boundaries.py). `launcher.py` and
`plugin_api/__init__.py` import UI pieces from here instead.

Flat re-export module, not a composition class — unlike core_api/plugin_api,
interface/ already has its own composition object (MainWindow), so there's
nothing to wrap. Bundling apply_theme/register_builtin_settings_tabs/
MainWindow into a single facade class was considered and rejected: real
launcher.py calls apply_theme() before the ProjectSelectorDialog gate, and
calls register_builtin_settings_tabs() before the plugin-apply loop (so a
plugin can't silently win a SettingsTabRegistry key collision against a
builtin tab) — both orderings a single bundled __init__ would have to
either hard-code or break. A flat facade lets launcher.py keep calling
each piece exactly where it already does, unchanged.

Re-exports MainWindow/ProjectSelectorDialog/theme helpers/
register_builtin_settings_tabs (launcher.py's needs) plus the
interface/shared/* widgets and interface/theme.py helpers that
app/plugins/core/**'s pages use (plugin_api/__init__.py re-exports these
on from here, so a plugin file never has to write `from interface.xxx
import yyy`). Add a new re-export here whenever launcher.py or a plugin
needs another interface/ symbol — see developer/app/docs/interface-api.md.

Import order below is load-bearing, not stylistic: interface.main_window
and interface.builtin_settings_tabs both transitively import plugin_api
(MainWindow needs UIRegistryManager; register_builtin_settings_tabs needs
SettingsTabSpec/CATEGORY_*), and plugin_api/__init__.py imports back from
this module — a straight circular import. Every symbol plugin_api actually
re-exports from here (everything except MainWindow/ProjectSelectorDialog/
apply_theme/register_builtin_settings_tabs, which plugin_api never needs)
must already be bound on this partially-initialized module *before* the
main_window/builtin_settings_tabs imports run, so plugin_api's `from
interface_api import ...` finds them already set. Add a new plugin-facing
re-export above the main_window/builtin_settings_tabs imports, not below.
"""
from __future__ import annotations

from interface.project_selector_dialog import ProjectSelectorDialog
from interface.qt_log_handler import QtLogHandler, configure_app_logging
from interface.shared.commit_history import (
    CommitCard,
    CommitFilesDialog,
    CommitHistoryEntry,
    fetch_entries_via_github,
    format_commit_date,
    format_relative_time,
)
from interface.settings.program_dialog import ProgramDialog
from interface.shared.image_asset import pick_image_file, save_image_asset
from interface.shared.requirements_tree_widget import RequirementsTreeWidget
from interface.shared.widget_helpers import confirm_action, set_bold, set_secondary_text, show_exclusive, wrap_scrollable
from interface.theme import DEFAULT_THEME_NAME, get_theme
from interface.theme_apply import apply_theme

# These two transitively import plugin_api (see the load-bearing-order note
# above) — must come after every plugin-facing re-export above.
from interface.builtin_settings_tabs import register_builtin_settings_tabs
from interface.main_window import MainWindow

__all__ = [
    "CommitCard",
    "CommitFilesDialog",
    "CommitHistoryEntry",
    "DEFAULT_THEME_NAME",
    "MainWindow",
    "ProgramDialog",
    "ProjectSelectorDialog",
    "QtLogHandler",
    "RequirementsTreeWidget",
    "apply_theme",
    "confirm_action",
    "configure_app_logging",
    "fetch_entries_via_github",
    "format_commit_date",
    "format_relative_time",
    "get_theme",
    "pick_image_file",
    "register_builtin_settings_tabs",
    "save_image_asset",
    "set_bold",
    "set_secondary_text",
    "show_exclusive",
    "wrap_scrollable",
]
