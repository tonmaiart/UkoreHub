from __future__ import annotations

from PySide6.QtWidgets import QGroupBox, QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from core.extensibility.loader import DiscoveredPlugin, PluginLoadFailure, plugin_source


class PluginCatalogPage(QWidget):
    """Read-only diagnostic view of what got discovered under a plugin/add-on
    root at startup — no add/edit/save, this just reflects the real
    core/extensibility/loader.py discovery result. Shared by both the
    Plugins and Add-ons settings tabs (see core/extensibility/README.md for
    what distinguishes the two), each feeding it a different catalog and
    description."""

    def __init__(
        self,
        parent=None,
        *,
        description: str,
        loaded: list[DiscoveredPlugin],
        failures: list[PluginLoadFailure],
    ):
        super().__init__(parent)

        description_label = QLabel(description)
        description_label.setWordWrap(True)

        loaded_group = QGroupBox("Loaded")
        loaded_list = QListWidget()
        for discovered in loaded:
            manifest = discovered.manifest
            text = f"{manifest.name}  (v{manifest.version} · {plugin_source(discovered)})"
            if manifest.description:
                text += f"\n{manifest.description}"
            loaded_list.addItem(QListWidgetItem(text))
        if not loaded:
            loaded_list.addItem(QListWidgetItem("None loaded."))
        loaded_layout = QVBoxLayout(loaded_group)
        loaded_layout.addWidget(loaded_list)

        failed_group = QGroupBox("Failed to Load")
        failed_list = QListWidget()
        for failure in failures:
            failed_list.addItem(QListWidgetItem(f"{failure.dir_path}\n{failure.reason}"))
        if not failures:
            failed_list.addItem(QListWidgetItem("No load failures."))
        failed_layout = QVBoxLayout(failed_group)
        failed_layout.addWidget(failed_list)

        layout = QVBoxLayout(self)
        layout.addWidget(description_label)
        layout.addWidget(loaded_group)
        layout.addWidget(failed_group)
