from __future__ import annotations

from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from interface.shared.widget_helpers import wrap_scrollable


class ConflictResolutionDialog(QDialog):
    """Per-file (not per-line) merge conflict resolution — appropriate for a
    mostly-binary animation production pipeline where line-level diffing
    doesn't make sense."""

    def __init__(self, parent=None, *, conflicted_files: list[str]):
        super().__init__(parent)
        self.setWindowTitle("Resolve Merge Conflicts")
        self.resize(500, 400)

        self._groups: dict[str, QButtonGroup] = {}

        intro = QLabel(
            "These files changed both locally and on the remote. Pick which "
            "version to keep for each file (whole file, not a line merge)."
        )
        intro.setWordWrap(True)

        rows_container = QWidget()
        rows_layout = QVBoxLayout(rows_container)
        for file_path in conflicted_files:
            row = QHBoxLayout()
            row.addWidget(QLabel(file_path), stretch=1)
            mine_radio = QRadioButton("Keep Mine")
            theirs_radio = QRadioButton("Keep Theirs")
            group = QButtonGroup(self)
            group.addButton(mine_radio)
            group.addButton(theirs_radio)
            group.buttonToggled.connect(self._update_continue_enabled)
            row.addWidget(mine_radio)
            row.addWidget(theirs_radio)
            rows_layout.addLayout(row)
            self._groups[file_path] = group
        rows_layout.addStretch()

        # frameless=False: keeps the default QScrollArea border, since this
        # sits directly inside a QDialog rather than a tab's content area.
        scroll = wrap_scrollable(rows_container, frameless=False)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Cancel)
        self.continue_button = self.buttons.addButton("Resolve && Continue", QDialogButtonBox.AcceptRole)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(intro)
        layout.addWidget(scroll)
        layout.addWidget(self.buttons)

        self._update_continue_enabled()

    def _update_continue_enabled(self, *_args) -> None:
        all_resolved = all(group.checkedButton() is not None for group in self._groups.values())
        self.continue_button.setEnabled(all_resolved)

    def resolutions(self) -> dict[str, str]:
        result = {}
        for file_path, group in self._groups.items():
            checked = group.checkedButton()
            result[file_path] = "ours" if checked is not None and checked.text() == "Keep Mine" else "theirs"
        return result
