from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.exceptions import NotFoundError
from core.models import BrowserLink, Project, Repo
from core.store import LocalConfigStore, MetadataStore
from interface.shared.image_asset import pick_image_file, save_image_asset
from interface.shared.widget_helpers import show_exclusive, wrap_scrollable


class BrowserLinksSettingsPage(QWidget):
    """Add/rename/remove the active repo's Browser Links — each shown as
    its own top-level tab elsewhere (see interface/main_window.py's dynamic
    tab rebuild). Moved here from About > Browser since it's a repo
    *setting*, not repo info — unlike the other Repo-category tabs it's
    scoped to a single repo, so it resolves the active project/repo itself
    from local_config_store on refresh() rather than waiting for a
    set_repo() call MainWindow never makes for Settings pages."""

    browser_links_changed = Signal()

    def __init__(self, parent=None, *, store: MetadataStore, local_config_store: LocalConfigStore):
        super().__init__(parent)
        self.store = store
        self.local_config_store = local_config_store
        self._project: Project | None = None
        self._repo: Repo | None = None

        self.empty_label = QLabel("Select a repo to see this information.")

        self._rows_container = QWidget()
        self._rows_layout = QVBoxLayout(self._rows_container)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)

        self.new_link_name_edit = QLineEdit()
        self.new_link_name_edit.setPlaceholderText("Name (e.g. Google Sheet)")
        self.new_link_url_edit = QLineEdit()
        self.new_link_url_edit.setPlaceholderText("https://...")
        add_link_button = QPushButton("Add Link")
        add_link_button.clicked.connect(self._on_add_browser_link)
        add_link_row = QHBoxLayout()
        add_link_row.addWidget(self.new_link_name_edit)
        add_link_row.addWidget(self.new_link_url_edit, stretch=1)
        add_link_row.addWidget(add_link_button)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.addWidget(self._rows_container)
        content_layout.addLayout(add_link_row)
        content_layout.addStretch()

        scroll = wrap_scrollable(content)

        self.content_widget = QWidget()
        content_wrap_layout = QVBoxLayout(self.content_widget)
        content_wrap_layout.setContentsMargins(0, 0, 0, 0)
        content_wrap_layout.addWidget(scroll)

        layout = QVBoxLayout(self)
        layout.addWidget(self.empty_label)
        layout.addWidget(self.content_widget)

        self.refresh()

    def refresh(self) -> None:
        """Re-resolves the active project/repo from local_config_store and
        rebuilds the link rows — called on construction and every time this
        tab becomes active (SettingsTabSpec.on_activated), the same
        lazy-refresh pattern ProjectStatusPage uses."""
        project_id = self.local_config_store.active_project_id
        repo_id = self.local_config_store.active_repo_id
        if not project_id or not repo_id:
            self._project = None
            self._repo = None
            show_exclusive(self.empty_label, self.content_widget)
            return
        try:
            self._project = self.store.get_project(project_id)
            self._repo = self.store.get_repo(project_id, repo_id)
        except NotFoundError:
            self._project = None
            self._repo = None
            show_exclusive(self.empty_label, self.content_widget)
            return
        show_exclusive(self.content_widget, self.empty_label)
        self._rebuild_rows()

    def _rebuild_rows(self) -> None:
        while self._rows_layout.count():
            item = self._rows_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        if self._repo is None:
            return
        for index, link in enumerate(self._repo.browser_links):
            row_widget = QWidget()
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(0, 0, 0, 0)
            icon_label = QLabel()
            icon_label.setFixedSize(24, 24)
            icon_path = self.store.resolve_browser_link_icon_path(link)
            if icon_path and icon_path.exists():
                icon_label.setPixmap(
                    QPixmap(str(icon_path)).scaled(24, 24, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                )
            row.addWidget(icon_label)
            row.addWidget(QLabel(f"<b>{link.name}</b>"))
            url_label = QLabel(link.url)
            url_label.setWordWrap(True)
            row.addWidget(url_label, stretch=1)
            change_icon_button = QPushButton("Change Icon...")
            change_icon_button.clicked.connect(lambda _checked, i=index: self._on_change_browser_link_icon(i))
            row.addWidget(change_icon_button)
            rename_button = QPushButton("Rename")
            rename_button.clicked.connect(lambda _checked, i=index: self._on_rename_browser_link(i))
            row.addWidget(rename_button)
            remove_button = QPushButton("Remove")
            remove_button.clicked.connect(lambda _checked, i=index: self._on_remove_browser_link(i))
            row.addWidget(remove_button)
            self._rows_layout.addWidget(row_widget)

    def _on_add_browser_link(self) -> None:
        if self._repo is None or self._project is None:
            return
        name = self.new_link_name_edit.text().strip()
        url = self.new_link_url_edit.text().strip()
        if not name or not url:
            QMessageBox.information(self, "Add Link", "Enter both a name and a URL.")
            return
        links = list(self._repo.browser_links) + [BrowserLink(name=name, url=url)]
        self._save_browser_links(links)
        self.new_link_name_edit.clear()
        self.new_link_url_edit.clear()

    def _on_rename_browser_link(self, index: int) -> None:
        if self._repo is None or self._project is None:
            return
        links = list(self._repo.browser_links)
        if not (0 <= index < len(links)):
            return
        new_name, ok = QInputDialog.getText(self, "Rename Link", "New name:", text=links[index].name)
        if not ok or not new_name.strip():
            return
        links[index] = BrowserLink(
            name=new_name.strip(), url=links[index].url, icon_filename=links[index].icon_filename
        )
        self._save_browser_links(links)

    def _on_remove_browser_link(self, index: int) -> None:
        if self._repo is None or self._project is None:
            return
        links = list(self._repo.browser_links)
        if 0 <= index < len(links):
            del links[index]
        self._save_browser_links(links)

    def _on_change_browser_link_icon(self, index: int) -> None:
        if self._repo is None or self._project is None:
            return
        links = self._repo.browser_links
        if not (0 <= index < len(links)):
            return
        source_path = pick_image_file(self, "Choose Browser Link Icon")
        if source_path is None:
            return
        filename = save_image_asset(
            self,
            source_path=source_path,
            dest_dir=self.store.browser_link_icons_dir,
            asset_id=f"{self._repo.id}_{index}",
        )
        if filename is None:
            return
        self.store.set_browser_link_icon(self._project.id, self._repo.id, index, filename)
        links[index].icon_filename = filename
        self._rebuild_rows()
        self.browser_links_changed.emit()

    def _save_browser_links(self, links: list[BrowserLink]) -> None:
        self.store.set_repo_browser_links(self._project.id, self._repo.id, links)
        self._repo.browser_links = links
        self._rebuild_rows()
        self.browser_links_changed.emit()
