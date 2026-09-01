from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QEventLoop, QFile, QSize, Qt, QTimer
from PySide6.QtGui import QIcon, QImage, QPixmap
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QApplication,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from plugin_api import (
    ConflictError,
    GitService,
    LocalConfigStore,
    MetadataStore,
    NotFoundError,
    Program,
    Project,
    Repo,
    UkoreHubError,
    confirm_action,
    open_in_file_explorer,
    pick_image_file,
    save_image_asset,
)
from plugins.core.project_editor.dialogs import EditInfoDialog, RepoDialog
from plugins.core.project_editor.pipeline_store import PipelineStore
from plugins.core.project_editor.repo_status_scan_worker import RepoStatusScanWorker
from plugins.core.project_editor.required_repo_clone_worker import RequiredRepoCloneWorker

_UI_FILE = Path(__file__).parent / "ProjectEditorTabWindows.ui"
_STATUS_ICON_SIZE = QSize(18, 18)
_PREVIEW_MAX_SIZE = QSize(320, 180)
_REQUIREMENT_ICON_SIZE = QSize(32, 32)

_COL_NAME, _COL_STATUS, _COL_CONNECTION = range(3)
_COLUMN_LABELS = ("Name", "Status", "Connection")

# tableWidget_Repo's Status column — same three live-status icons
# submit/repo_git_status_page.py's sidebar status dot uses
# (QStyle.SP_MessageBoxWarning/SP_DialogApplyButton), plus a not-cloned and
# a check-failed state that page doesn't need (Submit only ever shows the
# already-active repo, which is always cloned by definition).
_STATUS_ICONS = {
    "not_cloned": (QStyle.SP_DialogNoButton, "Not cloned"),
    "syncing": (QStyle.SP_BrowserReload, "Syncing..."),
    "modified": (QStyle.SP_MessageBoxWarning, "Modified"),
    "up_to_date": (QStyle.SP_DialogApplyButton, "Up to date"),
    "unknown": (QStyle.SP_MessageBoxCritical, "Status check failed"),
}


def _grayscale(pixmap: QPixmap) -> QPixmap:
    """A not-yet-cloned repo's thumbnail (detail-panel preview) desaturates
    as the visual "not on disk yet" cue — Clone/Unclone are the only things
    that actually change it."""
    image = pixmap.toImage().convertToFormat(QImage.Format_Grayscale8)
    return QPixmap.fromImage(image)


class ProjectEditorPage(QWidget):
    """Top-level section page (see plugin.py's register(api)). UI authored
    in Qt Designer (ProjectEditorTabWindows.ui) and loaded at runtime via
    QUiLoader, same pattern custom_paths_settings_page.py uses for
    CustomPathWindow.ui — replaced the old QGraphicsView node graph
    (project_graph_view.py, removed 2026-08-19) with a plain repo table
    plus a detail panel, per the user's own request to go back to "a dumb
    list with thumbnails" instead of a pipeline diagram.

    tableWidget_Repo is the whole project's repos, one row each: name
    (bold for the active repo), a live Status icon (Not
    cloned / Syncing / Up to date / Modified — background-scanned, see
    RepoStatusScanWorker), and a Connection icon that only lights up for a
    row the currently ACTIVE repo has a Custom Paths connection to
    (SP_MediaSkipBackward for an Input connection, SP_MediaSkipForward for
    Output — see _refresh_connection_column). Selecting a row only updates
    the detail panel on the right — it never clones anything and never
    changes the active repo unless the selected repo is already cloned;
    Clone/Unclone are the only things that change what's on disk, kept
    deliberately separate from selection.

    Any plugin's own CATEGORY_REPO tab still renders generically in the
    main Settings dialog's Plugins category (Settings > Project > Repository
    Settings covers per-repo Program/Plugin requirements instead — see
    repo_settings_page.py). There is no "Repository Setting..." row
    context-menu entry anymore — it used to jump straight to the builtin
    "Local Repository" tab (Remove Local Repositories), which was removed
    2026-09-01 as redundant with this table's own Unclone button (same
    operation, just scoped to whichever repo is selected here instead of
    only the active one); Open Local Directory (added the same day) covers
    the other thing that tab was for, glancing at where a repo actually
    lives on disk.

    current_project_id()/add_repo() are this page's own single source of
    truth/entry points, same contract project_database_page.py's callbacks
    (bound in plugin.py) rely on. set_current_project() is the one place
    that actually (re)loads a project's repos into the table — as of the
    single-project-per-session change nothing calls it with a project id
    other than the one launcher.py's Project Selector gate already fixed,
    except set_repo() defensively re-checking in case that ever changes.
    """

    def __init__(
        self,
        parent=None,
        *,
        store: MetadataStore,
        local_config_store: LocalConfigStore,
        pipeline_store: PipelineStore,
        git_service: GitService,
    ):
        super().__init__(parent)
        self.store = store
        self.local_config_store = local_config_store
        self.pipeline_store = pipeline_store
        self.git_service = git_service

        self._project_id: str | None = None
        self._selected_repo_id: str | None = None
        self._active_repo_id: str | None = None
        self._repo_rows: dict[str, int] = {}
        self._status_scan_token = 0
        self._status_workers: list[RepoStatusScanWorker] = []
        self._set_active_repo_callback: Callable[[str, str], None] | None = None

        loader = QUiLoader()
        ui_file = QFile(str(_UI_FILE))
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, self)
        ui_file.close()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ui)

        self.repo_table: QTableWidget = self.ui.findChild(QTableWidget, "tableWidget_Repo")
        self.image_label: QLabel = self.ui.findChild(QLabel, "label_images")
        self.software_requirements_list: QListWidget = self.ui.findChild(
            QListWidget, "listWidget_software_requirements"
        )
        self.info_browser: QTextBrowser = self.ui.findChild(QTextBrowser, "textBrowser_info")
        self.edit_info_button: QPushButton = self.ui.findChild(QPushButton, "pushButton_edit_info")
        # Object name is a typo in the .ui itself ("thubmnail") — matched
        # verbatim here since findChild looks up by the real object name.
        self.set_thumbnail_button: QPushButton = self.ui.findChild(QPushButton, "pushButton_set_thubmnail")
        self.clone_button: QPushButton = self.ui.findChild(QPushButton, "pushButton_clone")
        self.unclone_button: QPushButton = self.ui.findChild(QPushButton, "pushButton_unclone")
        self.open_local_directory_button: QPushButton = self.ui.findChild(
            QPushButton, "pushButton_open_local_directory"
        )

        self.repo_table.setColumnCount(len(_COLUMN_LABELS))
        self.repo_table.setHorizontalHeaderLabels(list(_COLUMN_LABELS))
        self.repo_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.repo_table.setSelectionMode(QTableWidget.SingleSelection)
        self.repo_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.repo_table.verticalHeader().setVisible(False)
        self.repo_table.setIconSize(_STATUS_ICON_SIZE)
        self.repo_table.setContextMenuPolicy(Qt.CustomContextMenu)
        header = self.repo_table.horizontalHeader()
        header.setSectionResizeMode(_COL_NAME, QHeaderView.Stretch)
        header.setSectionResizeMode(_COL_STATUS, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(_COL_CONNECTION, QHeaderView.ResizeToContents)

        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(_PREVIEW_MAX_SIZE.height())

        self.software_requirements_list.setIconSize(_REQUIREMENT_ICON_SIZE)
        self.software_requirements_list.setViewMode(QListWidget.IconMode)
        self.software_requirements_list.setMovement(QListWidget.Static)
        self.software_requirements_list.setResizeMode(QListWidget.Adjust)
        self.software_requirements_list.setSelectionMode(QListWidget.NoSelection)
        self.software_requirements_list.setFlow(QListWidget.LeftToRight)
        self.software_requirements_list.setWrapping(True)

        self.repo_table.itemSelectionChanged.connect(self._on_repo_selection_changed)
        self.repo_table.customContextMenuRequested.connect(self._on_repo_context_menu)
        self.clone_button.clicked.connect(self._on_clone_clicked)
        self.unclone_button.clicked.connect(self._on_unclone_clicked)
        self.edit_info_button.clicked.connect(self._on_edit_info_clicked)
        self.set_thumbnail_button.clicked.connect(self._on_set_thumbnail_clicked)
        self.open_local_directory_button.clicked.connect(self._on_open_local_directory_clicked)

        # Fixed to whichever project launcher.py's mandatory Project
        # Selector gate locked in for this run — see the class docstring.
        self.set_current_project(local_config_store.active_project_id)

    # -- UICommandService wiring (see plugin.py's _wire) ----------------------

    def bind_set_active_repo(self, callback: Callable[[str, str], None]) -> None:
        self._set_active_repo_callback = callback

    # -- page protocol (see plugin_api/registries/section_registry.py) ----------------

    def set_repo(self, project: Project | None, repo: Repo | None, workspace_root: str | None) -> None:
        self._active_repo_id = repo.id if repo is not None else None
        if project is not None and project.id != self._project_id:
            self.set_current_project(project.id)
        else:
            # A pure active-repo switch (no project change) only needs the
            # bold-name highlight and the Connection column refreshed —
            # not a full rebuild/re-scan of every row's Status icon.
            self._update_active_repo_highlight()
            self._refresh_connection_column()

    # -- current project (see project_database_page.py's callbacks) -------

    def current_project_id(self) -> str | None:
        return self._project_id

    def set_current_project(self, project_id: str | None) -> None:
        self._project_id = project_id
        # Default the selection to whichever repo is already active (the one
        # local_config_store itself points at), per the user's own request,
        # rather than opening with nothing selected.
        self._selected_repo_id = self.local_config_store.active_repo_id
        self._reload_repo_table()
        self._refresh_detail_panel()

    # -- Add Repo (called by Setting > Project's "Add Repo" button) -------

    def add_repo(self) -> None:
        if self._project_id is None:
            QMessageBox.information(self, "Add Repo", "Select or create a project first.")
            return
        workspace_root = self.local_config_store.workspace_root
        if not workspace_root:
            QMessageBox.information(self, "Add Repo", "Set and save a workspace folder in Setting > Common first.")
            return
        dialog = RepoDialog(self, store=self.store, project_id=self._project_id)
        if not dialog.exec():
            return
        try:
            repo = self.store.add_repo(self._project_id, dialog.name(), dialog.git_url(), workspace_root)
        except ConflictError as exc:
            self.store.load()
            QMessageBox.warning(self, "Add Repo", str(exc))
            self._reload_repo_table()
            return
        except UkoreHubError as exc:
            QMessageBox.warning(self, "Add Repo", str(exc))
            return
        if dialog.chosen_thumbnail_path():
            filename = save_image_asset(
                self, source_path=dialog.chosen_thumbnail_path(), dest_dir=self.store.thumbnails_dir, asset_id=repo.id
            )
            if filename is not None:
                self.store.set_repo_thumbnail(self._project_id, repo.id, filename)
        self.store.set_repo_requirements(self._project_id, repo.id, dialog.selected_program_ids())
        self.store.set_repo_program_version_pins(self._project_id, repo.id, dialog.selected_program_version_pins())
        self._reload_repo_table()

    # -- repo table --------------------------------------------------------

    def _is_repo_cloned(self, project_id: str, repo_id: str) -> bool:
        workspace_root = self.local_config_store.workspace_root
        if not workspace_root:
            return False
        try:
            repo = self.store.get_repo(project_id, repo_id)
        except NotFoundError:
            return False
        return self.git_service.is_cloned(Path(workspace_root) / repo.local_path)

    def _reload_repo_table(self) -> None:
        self._status_scan_token += 1
        self._repo_rows = {}
        table = self.repo_table

        repos: list[Repo] = []
        if self._project_id is not None:
            try:
                project = self.store.get_project(self._project_id)
            except NotFoundError:
                project = None
            if project is not None:
                repos = project.repos

        table.blockSignals(True)
        table.setRowCount(len(repos))
        scan_targets: list[tuple[str, Path]] = []
        found_selected = False
        workspace_root = self.local_config_store.workspace_root
        for row, repo in enumerate(repos):
            self._repo_rows[repo.id] = row
            self._populate_repo_row(row, repo)

            cloned = self._is_repo_cloned(self._project_id, repo.id)
            if cloned:
                self._set_status_cell(row, "syncing")
                if workspace_root:
                    scan_targets.append((repo.id, Path(workspace_root) / repo.local_path))
            else:
                self._set_status_cell(row, "not_cloned")

            if repo.id == self._selected_repo_id:
                table.setCurrentCell(row, _COL_NAME)
                found_selected = True
        if not found_selected:
            self._selected_repo_id = None
        table.blockSignals(False)

        # Belt-and-suspenders alongside the ResizeToContents modes set in
        # __init__: that automatic mode can compute a stale/too-small width
        # (e.g. before this widget has ever had a real layout pass), so
        # force an immediate recompute against the rows just populated.
        table.resizeColumnsToContents()

        self._refresh_connection_column()
        if scan_targets:
            self._start_status_scan(scan_targets)

    def _populate_repo_row(self, row: int, repo: Repo) -> None:
        table = self.repo_table

        name_item = QTableWidgetItem(repo.name)
        name_item.setData(Qt.UserRole, repo.id)
        font = name_item.font()
        font.setBold(repo.id == self._active_repo_id)
        name_item.setFont(font)
        table.setItem(row, _COL_NAME, name_item)

        table.setItem(row, _COL_STATUS, QTableWidgetItem())
        table.setItem(row, _COL_CONNECTION, QTableWidgetItem())

    def _update_active_repo_highlight(self) -> None:
        for repo_id, row in self._repo_rows.items():
            item = self.repo_table.item(row, _COL_NAME)
            if item is None:
                continue
            font = item.font()
            font.setBold(repo_id == self._active_repo_id)
            item.setFont(font)

    def _set_status_cell(self, row: int, status_key: str) -> None:
        item = self.repo_table.item(row, _COL_STATUS)
        if item is None:
            return
        standard_icon, label = _STATUS_ICONS[status_key]
        item.setIcon(QApplication.style().standardIcon(standard_icon))
        item.setToolTip(label)

    def _refresh_connection_column(self) -> None:
        """The Connection column only lights up for a row the currently
        ACTIVE repo has a Custom Paths connection to (not the selected
        row) — a quick-glance replacement for the old graph's directed
        edges, per the user's own request."""
        style = QApplication.style()
        input_icon = style.standardIcon(QStyle.SP_MediaSkipBackward)
        output_icon = style.standardIcon(QStyle.SP_MediaSkipForward)

        for row in range(self.repo_table.rowCount()):
            item = self.repo_table.item(row, _COL_CONNECTION)
            if item is not None:
                item.setIcon(QIcon())
                item.setToolTip("")

        project_id, active_repo_id = self._project_id, self._active_repo_id
        if project_id is None or active_repo_id is None:
            return
        for ref in self.pipeline_store.get_inputs(project_id, active_repo_id):
            if ref.project_id != project_id or ref.repo_id == active_repo_id:
                continue
            row = self._repo_rows.get(ref.repo_id)
            if row is None:
                continue
            item = self.repo_table.item(row, _COL_CONNECTION)
            if item is None:
                continue
            if ref.direction == "output":
                item.setIcon(output_icon)
                item.setToolTip("Output Custom Path")
            else:
                item.setIcon(input_icon)
                item.setToolTip("Input Custom Path")

    def _on_repo_selection_changed(self) -> None:
        row = self.repo_table.currentRow()
        item = self.repo_table.item(row, _COL_NAME) if row >= 0 else None
        self._selected_repo_id = item.data(Qt.UserRole) if item is not None else None
        self._refresh_detail_panel()

        project_id, repo_id = self._project_id, self._selected_repo_id
        if (
            project_id is not None
            and repo_id is not None
            and repo_id != self._active_repo_id
            and self._is_repo_cloned(project_id, repo_id)
            and self._set_active_repo_callback is not None
        ):
            # Deferred: the active-repo switch can end up round-tripping
            # back into set_repo() on this very page (updating this very
            # table) while the selection-changed signal that triggered it
            # is still on the call stack.
            callback = self._set_active_repo_callback
            QTimer.singleShot(0, lambda: callback(project_id, repo_id))

    # -- background status scan --------------------------------------------

    def _start_status_scan(self, targets: list[tuple[str, Path]]) -> None:
        token = self._status_scan_token
        worker = RepoStatusScanWorker(git_service=self.git_service, targets=targets)
        worker.status_ready.connect(lambda repo_id, is_dirty, t=token: self._on_status_ready(t, repo_id, is_dirty))
        worker.status_failed.connect(lambda repo_id, t=token: self._on_status_failed(t, repo_id))
        worker.scan_finished.connect(lambda w=worker: self._on_scan_finished(w))
        self._status_workers.append(worker)
        worker.start()

    def _on_scan_finished(self, worker: RepoStatusScanWorker) -> None:
        if worker in self._status_workers:
            self._status_workers.remove(worker)
        worker.deleteLater()

    def _on_status_ready(self, token: int, repo_id: str, is_dirty: bool) -> None:
        if token != self._status_scan_token:
            return  # a superseded scan (table reloaded again since) — drop it
        row = self._repo_rows.get(repo_id)
        if row is not None:
            self._set_status_cell(row, "modified" if is_dirty else "up_to_date")

    def _on_status_failed(self, token: int, repo_id: str) -> None:
        if token != self._status_scan_token:
            return
        row = self._repo_rows.get(repo_id)
        if row is not None:
            self._set_status_cell(row, "unknown")

    # -- detail panel ------------------------------------------------------

    def _update_detail_controls(self) -> None:
        project_id, repo_id = self._project_id, self._selected_repo_id
        cloned = project_id is not None and repo_id is not None and self._is_repo_cloned(project_id, repo_id)
        has_selection = repo_id is not None
        self.clone_button.setEnabled(has_selection and not cloned)
        self.unclone_button.setEnabled(has_selection and cloned)
        self.edit_info_button.setEnabled(has_selection)
        self.set_thumbnail_button.setEnabled(has_selection)
        self.open_local_directory_button.setEnabled(has_selection and cloned)

    def _refresh_detail_panel(self) -> None:
        project_id, repo_id = self._project_id, self._selected_repo_id
        if project_id is None or repo_id is None:
            self.image_label.setPixmap(QPixmap())
            self.software_requirements_list.clear()
            self.info_browser.clear()
            self._update_detail_controls()
            return
        try:
            repo = self.store.get_repo(project_id, repo_id)
        except NotFoundError:
            self._selected_repo_id = None
            self._refresh_detail_panel()
            return

        cloned = self._is_repo_cloned(project_id, repo_id)
        thumbnail_path = self.store.resolve_thumbnail_path(repo)
        pixmap = QPixmap(str(thumbnail_path)) if thumbnail_path and thumbnail_path.exists() else None
        if pixmap is not None and not pixmap.isNull():
            pixmap = pixmap.scaled(_PREVIEW_MAX_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            if not cloned:
                pixmap = _grayscale(pixmap)
            self.image_label.setPixmap(pixmap)
        else:
            self.image_label.setPixmap(QPixmap())

        self._reload_software_requirements(project_id, repo)
        self.info_browser.setPlainText(self.pipeline_store.get_repo_info(project_id, repo_id))
        self._update_detail_controls()

    def _program_icon(self, program: Program) -> QIcon:
        icon_path = self.store.resolve_program_icon_path(program)
        pixmap = QPixmap(str(icon_path)) if icon_path and icon_path.exists() else None
        if pixmap is None or pixmap.isNull():
            return QApplication.style().standardIcon(QStyle.SP_ComputerIcon)
        return QIcon(pixmap.scaled(_REQUIREMENT_ICON_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def _reload_software_requirements(self, project_id: str, repo: Repo) -> None:
        self.software_requirements_list.clear()
        for program_id in repo.required_program_ids:
            try:
                program = self.store.get_program(project_id, program_id)
            except NotFoundError:
                continue
            item = QListWidgetItem(self._program_icon(program), "")
            item.setToolTip(program.name)
            self.software_requirements_list.addItem(item)

    # -- Edit Info -----------------------------------------------------------

    def _on_edit_info_clicked(self) -> None:
        project_id, repo_id = self._project_id, self._selected_repo_id
        if project_id is None or repo_id is None:
            return
        current_text = self.pipeline_store.get_repo_info(project_id, repo_id)
        dialog = EditInfoDialog(self, text=current_text)
        if not dialog.exec():
            return
        new_text = dialog.text()
        self.pipeline_store.set_repo_info(project_id, repo_id, new_text)
        self.info_browser.setPlainText(new_text)

    # -- Set Thumbnail -------------------------------------------------------

    def _on_set_thumbnail_clicked(self) -> None:
        project_id, repo_id = self._project_id, self._selected_repo_id
        if project_id is None or repo_id is None:
            return
        self._change_repo_thumbnail(project_id, repo_id)

    # -- Open Local Directory -------------------------------------------------

    def _on_open_local_directory_clicked(self) -> None:
        project_id, repo_id = self._project_id, self._selected_repo_id
        if project_id is None or repo_id is None or not self._is_repo_cloned(project_id, repo_id):
            return
        repo = self.store.get_repo(project_id, repo_id)
        local_path = Path(self.local_config_store.workspace_root) / repo.local_path
        open_in_file_explorer(local_path)

    # -- Clone / Unclone ---------------------------------------------------

    def _run_clone_worker(self, targets: list[tuple[str, Repo]]) -> bool:
        workspace_root = self.local_config_store.workspace_root
        progress = QProgressDialog("Preparing...", None, 0, len(targets), self)
        progress.setWindowTitle("Cloning")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        worker = RequiredRepoCloneWorker(git_service=self.git_service, workspace_root=workspace_root, targets=targets)
        loop = QEventLoop()
        outcome: dict[str, object] = {"ok": False, "repo_name": None, "error": None}
        step = {"n": 0}

        def on_progress(repo_name: str) -> None:
            progress.setLabelText(f"Cloning '{repo_name}'...")
            progress.setValue(step["n"])
            step["n"] += 1

        def on_finished_ok() -> None:
            outcome["ok"] = True
            loop.quit()

        def on_failed(repo_name: str, error: str) -> None:
            outcome["repo_name"] = repo_name
            outcome["error"] = error
            loop.quit()

        worker.repo_progress.connect(on_progress)
        worker.finished_ok.connect(on_finished_ok)
        worker.failed.connect(on_failed)
        worker.start()
        loop.exec()
        progress.close()
        worker.wait()

        if not outcome["ok"]:
            QMessageBox.warning(
                self, "Clone Failed", f"Cloning '{outcome['repo_name']}' failed:\n\n{outcome['error']}"
            )
            return False
        return True

    def _on_clone_clicked(self) -> None:
        project_id, repo_id = self._project_id, self._selected_repo_id
        if project_id is None or repo_id is None:
            return
        try:
            repo = self.store.get_repo(project_id, repo_id)
        except NotFoundError:
            return
        if self._is_repo_cloned(project_id, repo_id):
            return
        if not self.local_config_store.workspace_root:
            QMessageBox.information(self, "Clone Repo", "Set and save a workspace folder in Setting > Common first.")
            return
        if not confirm_action(self, "Clone Repo", f"Clone '{repo.name}' now?"):
            return
        if not self._run_clone_worker([(project_id, repo)]):
            return
        self._reload_repo_table()
        self._refresh_detail_panel()
        if self._set_active_repo_callback is not None:
            callback = self._set_active_repo_callback
            QTimer.singleShot(0, lambda: callback(project_id, repo_id))

    def _on_unclone_clicked(self) -> None:
        project_id, repo_id = self._project_id, self._selected_repo_id
        if project_id is None or repo_id is None:
            return
        try:
            repo = self.store.get_repo(project_id, repo_id)
        except NotFoundError:
            return
        if not self._is_repo_cloned(project_id, repo_id):
            return
        if not confirm_action(
            self,
            "Unclone Repo",
            f"Remove '{repo.name}'s local clone from disk?\n\n"
            "This only deletes the local folder — the repo stays in the registry and can be cloned again later.",
        ):
            return
        dest_path = Path(self.local_config_store.workspace_root) / repo.local_path
        try:
            shutil.rmtree(dest_path)
        except OSError as exc:
            QMessageBox.warning(self, "Unclone Repo", f"Couldn't remove the local folder:\n\n{exc}")
            return
        self.store.mark_status(project_id, repo_id, "not_cloned")
        self._reload_repo_table()
        self._refresh_detail_panel()

    # -- repo table context menu --------------------------------------------

    def _on_repo_context_menu(self, pos) -> None:
        item = self.repo_table.itemAt(pos)
        project_id = self._project_id
        if item is None or project_id is None:
            return
        row = item.row()
        repo_id = self.repo_table.item(row, _COL_NAME).data(Qt.UserRole)

        menu = QMenu(self)
        rename_action = menu.addAction("Rename Repo...")
        thumbnail_action = menu.addAction("Change Thumbnail...")
        menu.addSeparator()
        delete_action = menu.addAction("Delete Repo")
        chosen = menu.exec(self.repo_table.viewport().mapToGlobal(pos))

        if chosen is rename_action:
            self._rename_repo(project_id, repo_id)
        elif chosen is thumbnail_action:
            self._change_repo_thumbnail(project_id, repo_id)
        elif chosen is delete_action:
            self._delete_repo(project_id, repo_id)

    def _rename_repo(self, project_id: str, repo_id: str) -> None:
        repo = self.store.get_repo(project_id, repo_id)
        dialog = RepoDialog(self, name=repo.name, git_url=repo.git_url, show_thumbnail=False)
        if not dialog.exec():
            return
        try:
            self.store.edit_repo(project_id, repo_id, name=dialog.name(), git_url=dialog.git_url())
        except ConflictError as exc:
            self.store.load()
            QMessageBox.warning(self, "Rename Repo", str(exc))
            self._reload_repo_table()
            return
        except UkoreHubError as exc:
            QMessageBox.warning(self, "Rename Repo", str(exc))
            return
        self._reload_repo_table()
        self._refresh_detail_panel()

    def _change_repo_thumbnail(self, project_id: str, repo_id: str) -> None:
        source_path = pick_image_file(self, "Choose Thumbnail Image")
        if source_path is None:
            return
        filename = save_image_asset(self, source_path=source_path, dest_dir=self.store.thumbnails_dir, asset_id=repo_id)
        if filename is not None:
            self.store.set_repo_thumbnail(project_id, repo_id, filename)
            self._reload_repo_table()
            self._refresh_detail_panel()

    def _delete_repo(self, project_id: str, repo_id: str) -> None:
        repo = self.store.get_repo(project_id, repo_id)
        if not confirm_action(
            self,
            "Delete Repo",
            f"Delete repo '{repo.name}' from the registry for EVERYONE at the studio?\n\n"
            "This removes it from the shared registry immediately and cannot be undone.",
        ):
            return
        try:
            self.store.delete_repo(project_id, repo_id)
        except ConflictError as exc:
            self.store.load()
            QMessageBox.warning(self, "Delete Repo", str(exc))
        if self._selected_repo_id == repo_id:
            self._selected_repo_id = None
        self._reload_repo_table()
        self._refresh_detail_panel()

    # -- Repositories Database CRUD (called by Setting > Project's Project
    # Database tab, project_database_page.py) — thin public wrappers around
    # the same _rename_repo/_delete_repo the table's own right-click menu
    # uses, so both entry points share one refresh path. ------------------

    def rename_repo(self, repo_id: str) -> None:
        if self._project_id is None:
            return
        self._rename_repo(self._project_id, repo_id)

    def delete_repo(self, repo_id: str) -> None:
        if self._project_id is None:
            return
        self._delete_repo(self._project_id, repo_id)
