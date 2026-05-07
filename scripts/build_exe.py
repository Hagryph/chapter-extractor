"""Build a single-file ChapterExtractor.exe via Nuitka.

Run from the repo root:

    python scripts/build_exe.py

Per the Qt for Python deployment guide
(https://doc.qt.io/qtforpython-6/deployment/deployment-nuitka.html),
Nuitka is the recommended packager for PySide6 single-file builds —
PyInstaller's ``--onefile`` mode is officially flagged as unable to
properly deploy Qt plugins. Nuitka's ``--enable-plugin=pyside6`` handles
that automatically.
"""
from __future__ import annotations

import platform
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class BuildPaths:
    repo_root: Path
    entry_script: Path
    output_dir: Path
    icon_path: Path

    @classmethod
    def default(cls) -> BuildPaths:
        repo = Path(__file__).resolve().parent.parent
        return cls(
            repo_root=repo,
            entry_script=repo / "src" / "chapter_extractor" / "__main__.py",
            output_dir=repo / "dist",
            icon_path=repo / "assets" / "app.ico",
        )


@dataclass
class NuitkaCommand:
    """Composes the Nuitka command-line for our specific app.

    All flags chosen per the official sources cited in the docstring
    of this module — no ad-hoc additions.
    """

    paths: BuildPaths
    output_filename: str = "ChapterExtractor.exe"
    extra_packages: list[str] = field(
        default_factory=lambda: ["chapter_extractor"]
    )

    def build_argv(self) -> list[str]:
        argv: list[str] = [
            sys.executable,
            "-m",
            "nuitka",
            "--onefile",
            "--standalone",
            "--enable-plugin=pyside6",
            "--assume-yes-for-downloads",
            "--remove-output",  # delete .build/ scratch dir on success
            f"--output-dir={self.paths.output_dir}",
            f"--output-filename={self.output_filename}",
            "--company-name=Hagryph",
            "--product-name=ChapterExtractor",
            "--file-version=0.1.0",
            "--product-version=0.1.0",
        ]
        for pkg in self.extra_packages:
            argv.append(f"--include-package={pkg}")

        if platform.system() == "Windows":
            argv.append("--windows-console-mode=disable")
            if self.paths.icon_path.exists():
                argv.append(f"--windows-icon-from-ico={self.paths.icon_path}")
        elif platform.system() == "Darwin":
            argv.append("--macos-app-icon=" + str(self.paths.icon_path))
        # Linux: no icon flag; rely on .desktop file at install time.

        argv.append(str(self.paths.entry_script))
        return argv


class ExeBuilder:
    """Top-level orchestrator. Validates inputs, runs Nuitka, reports."""

    def __init__(self, paths: BuildPaths | None = None) -> None:
        self._paths = paths or BuildPaths.default()
        self._command = NuitkaCommand(paths=self._paths)

    def run(self) -> int:
        self._validate()
        self._paths.output_dir.mkdir(parents=True, exist_ok=True)
        argv = self._command.build_argv()
        print("> " + " ".join(str(a) for a in argv) + "\n")
        return subprocess.call(argv, cwd=str(self._paths.repo_root))

    def _validate(self) -> None:
        if not self._paths.entry_script.exists():
            raise FileNotFoundError(
                f"Entry script not found: {self._paths.entry_script}"
            )
        try:
            import nuitka  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "Nuitka is not installed. Install with:\n"
                "  pip install -e .[dev]"
            ) from exc


def main() -> int:
    return ExeBuilder().run()


if __name__ == "__main__":
    raise SystemExit(main())
