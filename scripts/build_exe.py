"""Build a single-file ChapterExtractor.exe via Nuitka.

Run from the repo root:

    python scripts/build_exe.py

Per the Qt for Python deployment guide
(https://doc.qt.io/qtforpython-6/deployment/deployment-nuitka.html),
Nuitka is the recommended packager for PySide6 single-file builds —
PyInstaller's ``--onefile`` mode is officially flagged as unable to
properly deploy Qt plugins. Nuitka's ``--enable-plugin=pyside6`` handles
that automatically.

Why Python 3.13: Nuitka 4.x only experimentally supports Python 3.14.
On 3.14 the compiled binary fails to register SQLAlchemy ORM loader
strategies (``LoaderStrategyException`` at first query). On 3.13 it
works. We resolve to ``py -3.13`` automatically; install via
``winget install Python.Python.3.13`` if missing.
"""
from __future__ import annotations

import platform
import shutil
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


class PythonInterpreter:
    """Resolves the Python interpreter to use as Nuitka's host.

    On Windows we strongly prefer Python 3.13 because Nuitka 4.x's
    experimental Python 3.14 support breaks decorator-based registration
    inside SQLAlchemy. We try ``py -3.13`` first, then any 3.13 on PATH,
    then fall back to the current interpreter with a warning.
    """

    PREFERRED_VERSION = "3.13"

    @classmethod
    def resolve(cls) -> list[str]:
        # 1) Windows py launcher with explicit version.
        py_launcher = shutil.which("py")
        if py_launcher:
            try:
                subprocess.check_call(
                    [py_launcher, f"-{cls.PREFERRED_VERSION}", "-c", "import sys"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return [py_launcher, f"-{cls.PREFERRED_VERSION}"]
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
        # 2) python3.13 on PATH (POSIX convention).
        for candidate in (f"python{cls.PREFERRED_VERSION}", f"python{cls.PREFERRED_VERSION}.exe"):
            found = shutil.which(candidate)
            if found:
                return [found]
        # 3) Fallback to whatever invoked us.
        major_minor = f"{sys.version_info.major}.{sys.version_info.minor}"
        if major_minor != cls.PREFERRED_VERSION:
            sys.stderr.write(
                f"[build_exe] WARNING: Python {cls.PREFERRED_VERSION} not found; "
                f"falling back to {major_minor}. Nuitka onefile may fail at runtime "
                "with SQLAlchemy LoaderStrategyException.\n"
                f"  Install with: winget install Python.Python.{cls.PREFERRED_VERSION}\n"
            )
        return [sys.executable]


@dataclass
class NuitkaCommand:
    """Composes the Nuitka command-line for our specific app.

    All flags chosen per the official sources cited in the docstring
    of this module — no ad-hoc additions.
    """

    paths: BuildPaths
    output_filename: str = "ChapterExtractor.exe"
    extra_packages: list[str] = field(
        default_factory=lambda: [
            "chapter_extractor",
            # SQLAlchemy uses dynamic discovery for ORM loader strategies and
            # dialect drivers (e.g. orm.strategies, dialects.sqlite). Without
            # forcing the whole package, Nuitka's static import scan misses
            # them and the EXE crashes with LoaderStrategyException at runtime.
            "sqlalchemy",
        ]
    )

    def build_argv(self) -> list[str]:
        argv: list[str] = [
            *PythonInterpreter.resolve(),
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
        # Verify Nuitka is importable from the *target* interpreter, which
        # may be different from the one running this script.
        host = PythonInterpreter.resolve()
        try:
            subprocess.check_call(
                [*host, "-c", "import nuitka"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(
                f"Nuitka is not installed in {' '.join(host)}.\n"
                f"  Install with:  {' '.join(host)} -m pip install -e .[dev]"
            ) from exc


def main() -> int:
    return ExeBuilder().run()


if __name__ == "__main__":
    raise SystemExit(main())
