from __future__ import annotations

import shutil

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.addon_store import AddonMetadataStore
from core.extensibility.loader import DiscoveredPlugin, PluginLoadFailure, plugin_source
from core.program_store import ProgramStore
from interface.dialogs import AddonSettingsDialog


class AddonSettingsPage(QWidget):
    """Editable counterpart to the read-only PluginCatalogPage, scoped to
    add-ons only (plugins stay read-only — they aren't per-repo/program
    scoped). Catalog membership itself is fixed by add-on/ discovery (no
    add/delete here), but each add-on's icon, description override, and
    required Program(s) can be edited and persist immediately, same as
    every other settings page in this app."""

    def __init__(
        self,
        parent=None,
        *,
        description: str,
        addon_catalog: list[DiscoveredPlugin],
        addon_load_failures: list[PluginLoadFailure],
        addon_store: AddonMetadataStore,
        program_store: ProgramStore,
    ):
        super().__init__(parent)
        self.addon_catalog = addon_catalog
        self.addon_store = addon_store
        self.program_store = program_store
        self._by_id = {discovered.manifest.id: discovered for discovered in addon_catalog}

        description_label = QLabel(description)
        description_label.setWordWrap(True)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)

        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self._on_edit)
        button_row = QHBoxLayout()
        button_row.addWidget(edit_btn)
        button_row.addStretch()

        catalog_group = QGroupBox("Discovered Add-ons")
        catalog_layout = QVBoxLayout(catalog_group)
        catalog_layout.addLayout(button_row)
        catalog_layout.addWidget(self.list_widget)

        failed_group = QGroupBox("Failed to Load")
        failed_list = QListWidget()
        for failure in addon_load_failures:
            failed_list.addItem(QListWidgetItem(f"{failure.dir_path}\n{failure.reason}"))
        if not addon_load_failures:
            failed_list.addItem(QListWidgetItem("No load failures."))
        failed_layout = QVBoxLayout(failed_group)
        failed_layout.addWidget(failed_list)

        layout = QVBoxLayout(self)
        layout.addWidget(description_label)
        layout.addWidget(catalog_group)
        layout.addWidget(failed_group)

        self.refresh_list()

    def refresh_list(self) -> None:
        self.list_widget.clear()
        for discovered in self.addon_catalog:
            manifest = discovered.manifest
            metadata = self.addon_store.get(manifest.id)
            label = f"{manifest.name}  (v{manifest.version} · {plugin_source(discovered)})"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, manifest.id)
            icon_path = self.addon_store.resolve_icon_path(metadata)
            if icon_path and icon_path.exists():
                item.setIcon(QIcon(str(icon_path)))
            self.list_widget.addItem(item)

    def _selected_addon_id(self) -> str | None:
        items = self.list_widget.selectedItems()
        if not items:
            return None
        return items[0].data(Qt.UserRole)

    def _on_edit(self) -> None:
        addon_id = self._selected_addon_id()
        if not addon_id:
            QMessageBox.information(self, "Edit", "Select an add-on first.")
            return
        discovered = self._by_id[addon_id]
        manifest = discovered.manifest
        metadata = self.addon_store.get(addon_id)
        dialog = AddonSettingsDialog(
            self,
            manifest_name=manifest.name,
            manifest_description=manifest.description,
            description_override=metadata.description,
            icon_path=self.addon_store.resolve_icon_path(metadata),
            program_store=self.program_store,
            selected_program_ids=metadata.required_program_ids,
        )
        if dialog.exec():
            self.addon_store.set_description(addon_id, dialog.description())
            self.addon_store.set_required_program_ids(addon_id, dialog.selected_program_ids())
            if dialog.chosen_icon_path():
                self._save_icon(addon_id, dialog.chosen_icon_path())
            self.refresh_list()

    def _save_icon(self, addon_id: str, source_path) -> None:
        icons_dir = self.addon_store.icons_dir
        icons_dir.mkdir(parents=True, exist_ok=True)
        ext = source_path.suffix or ".png"
        dest_path = icons_dir / f"{addon_id}{ext}"
        try:
            shutil.copyfile(source_path, dest_path)
        except OSError as exc:
            QMessageBox.warning(self, "Icon", f"Could not save icon: {exc}")
            return
        self.addon_store.set_icon(addon_id, dest_path.name)
