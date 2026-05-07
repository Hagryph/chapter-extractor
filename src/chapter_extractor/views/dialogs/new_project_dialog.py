from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from chapter_extractor.infrastructure.paths import AppPaths
from chapter_extractor.views.style import ViewStyle


class NewProjectDialog(QDialog):
    """Themed replacement for ``QInputDialog.getText`` + ``QFileDialog`` combo.

    Single dialog: project name on top, folder picker below, primary
    "Create" / secondary "Cancel" buttons. Inherits the global QSS so it
    looks like the rest of the app instead of the Win32 native popup.

    The folder picker forces ``DontUseNativeDialog`` so the file dialog
    also picks up our QSS — Qt for Python docs note that native dialogs
    bypass the stylesheet entirely.
    """

    def __init__(self, paths: AppPaths, parent=None) -> None:
        super().__init__(parent)
        self._paths = paths
        self._chosen_folder: Path | None = None

        self.setWindowTitle("New Project")
        self.setModal(True)
        self.resize(560, 280)

        self._build_ui()

    # ─── UI ─────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(
            ViewStyle.PANE_PADDING,
            ViewStyle.PANE_PADDING,
            ViewStyle.PANE_PADDING,
            ViewStyle.PANE_PADDING,
        )
        outer.setSpacing(ViewStyle.GRID + 4)

        heading = QLabel("Create a new project")
        heading.setProperty("role", "heading")
        outer.addWidget(heading)

        sub = QLabel(
            "Pick a name and where to keep its files. We'll create a folder "
            "with a project database and a chapters/ directory inside."
        )
        sub.setWordWrap(True)
        sub.setProperty("role", "dim")
        outer.addWidget(sub)

        outer.addSpacing(ViewStyle.GRID)

        # Name
        name_label = QLabel("Project name")
        name_label.setProperty("role", "title")
        outer.addWidget(name_label)
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("My Story")
        self._name_input.textChanged.connect(self._on_name_changed)
        outer.addWidget(self._name_input)

        # Folder
        folder_label = QLabel("Folder")
        folder_label.setProperty("role", "title")
        outer.addWidget(folder_label)

        folder_row = QHBoxLayout()
        folder_row.setSpacing(ViewStyle.GRID)

        self._folder_path = QLineEdit()
        self._folder_path.setReadOnly(True)
        self._folder_path.setPlaceholderText("(default location)")
        folder_row.addWidget(self._folder_path, stretch=1)

        self._browse_btn = QPushButton("Browse…")
        self._browse_btn.clicked.connect(self._on_browse)
        folder_row.addWidget(self._browse_btn)

        outer.addLayout(folder_row)

        outer.addStretch()

        # Buttons
        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
        )
        ok_btn = self._buttons.button(QDialogButtonBox.StandardButton.Ok)
        ok_btn.setText("Create Project")
        ok_btn.setProperty("primary", True)
        ok_btn.setEnabled(False)
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)
        outer.addWidget(self._buttons, alignment=Qt.AlignmentFlag.AlignRight)

        self._update_default_folder("")

    # ─── Slots ──────────────────────────────────────────────────

    def _on_name_changed(self, text: str) -> None:
        cleaned = text.strip()
        ok_btn = self._buttons.button(QDialogButtonBox.StandardButton.Ok)
        ok_btn.setEnabled(bool(cleaned))
        if self._chosen_folder is None:
            self._update_default_folder(cleaned)

    def _on_browse(self) -> None:
        # DontUseNativeDialog forces the Qt-styled file picker so it picks
        # up our QSS instead of the unstyled OS chooser.
        start = self._chosen_folder or self._paths.default_projects_dir
        chosen = QFileDialog.getExistingDirectory(
            self,
            "Choose folder for project",
            str(start),
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontUseNativeDialog,
        )
        if not chosen:
            return
        self._chosen_folder = Path(chosen)
        name = self._name_input.text().strip()
        target = (self._chosen_folder / name) if name else self._chosen_folder
        self._folder_path.setText(str(target))

    def _update_default_folder(self, name: str) -> None:
        if self._chosen_folder is not None:
            return
        if name:
            self._folder_path.setText(str(self._paths.project_root(name)))
        else:
            self._folder_path.setText(str(self._paths.default_projects_dir / "<name>"))

    # ─── Public API ─────────────────────────────────────────────

    @property
    def project_name(self) -> str:
        return self._name_input.text().strip()

    @property
    def project_root(self) -> Path:
        name = self.project_name
        if self._chosen_folder is not None:
            return self._chosen_folder / name if name else self._chosen_folder
        return self._paths.project_root(name)
