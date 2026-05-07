from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import platformdirs

APP_NAME = "ChapterExtractor"
APP_AUTHOR = "Hagryph"


@dataclass(frozen=True, slots=True)
class AppPaths:
    """Cross-platform filesystem locations.

    Uses `platformdirs` so we land on the OS-correct directories:
      - Windows:  %APPDATA%\\Hagryph\\ChapterExtractor
      - macOS:    ~/Library/Application Support/ChapterExtractor
      - Linux:    ~/.local/share/ChapterExtractor
    """

    user_data_dir: Path
    user_documents_dir: Path

    @property
    def registry_db_path(self) -> Path:
        return self.user_data_dir / "registry.db"

    @property
    def default_projects_dir(self) -> Path:
        return self.user_documents_dir / APP_NAME

    def project_root(self, project_name: str) -> Path:
        """Default folder for a new project given its name (user can override)."""
        return self.default_projects_dir / _safe_folder_name(project_name)

    def ensure_dirs(self) -> None:
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        self.default_projects_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def default(cls) -> AppPaths:
        return cls(
            user_data_dir=Path(platformdirs.user_data_dir(APP_NAME, APP_AUTHOR, roaming=True)),
            user_documents_dir=Path(platformdirs.user_documents_dir()),
        )

    @classmethod
    def for_testing(cls, base: Path) -> AppPaths:
        """Test-only constructor: contain everything under `base`."""
        return cls(
            user_data_dir=base / "data",
            user_documents_dir=base / "documents",
        )


def _safe_folder_name(name: str) -> str:
    """Strip filesystem-hostile characters; keep most Unicode.
    Falls back to 'Untitled' if nothing meaningful remains."""
    illegal = '<>:"/\\|?*'
    replaced = "".join("_" if c in illegal else c for c in name).strip()
    if not replaced or replaced.strip("_ ") == "":
        return "Untitled"
    return replaced
