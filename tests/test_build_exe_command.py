from __future__ import annotations

import platform
from pathlib import Path

from scripts.build_exe import BuildPaths, ExeBuilder, NuitkaCommand, PythonInterpreter


class TestBuildPaths:
    def test_default_locates_repo_root(self) -> None:
        paths = BuildPaths.default()
        assert paths.repo_root.is_dir()
        assert (paths.repo_root / "pyproject.toml").exists()
        assert paths.entry_script.name == "__main__.py"


class TestNuitkaCommand:
    def _paths(self, tmp: Path) -> BuildPaths:
        return BuildPaths(
            repo_root=tmp,
            entry_script=tmp / "src" / "chapter_extractor" / "__main__.py",
            output_dir=tmp / "dist",
            icon_path=tmp / "assets" / "app.ico",
        )

    def test_argv_includes_required_flags(self, tmp_path: Path) -> None:
        cmd = NuitkaCommand(paths=self._paths(tmp_path))
        argv = cmd.build_argv()
        # First entries are the resolved Python interpreter (may be `py -3.13`
        # or the current sys.executable depending on what's installed).
        assert len(argv) > 1
        assert "--onefile" in argv
        assert "--standalone" in argv
        assert "--enable-plugin=pyside6" in argv
        assert "--include-package=chapter_extractor" in argv
        assert "--assume-yes-for-downloads" in argv
        assert any(a.startswith("--output-dir=") for a in argv)
        assert any(a.startswith("--output-filename=") for a in argv)

    def test_entry_script_is_last(self, tmp_path: Path) -> None:
        cmd = NuitkaCommand(paths=self._paths(tmp_path))
        argv = cmd.build_argv()
        assert argv[-1].endswith("__main__.py")

    def test_windows_console_disabled_on_windows(self, tmp_path: Path) -> None:
        if platform.system() != "Windows":
            return
        argv = NuitkaCommand(paths=self._paths(tmp_path)).build_argv()
        assert "--windows-console-mode=disable" in argv


class TestPythonInterpreter:
    def test_resolve_returns_at_least_one_element(self) -> None:
        argv = PythonInterpreter.resolve()
        assert len(argv) >= 1
        assert all(isinstance(a, str) for a in argv)


class TestExeBuilderValidation:
    def test_missing_entry_raises(self, tmp_path: Path) -> None:
        paths = BuildPaths(
            repo_root=tmp_path,
            entry_script=tmp_path / "missing.py",
            output_dir=tmp_path / "dist",
            icon_path=tmp_path / "icon.ico",
        )
        builder = ExeBuilder(paths=paths)
        try:
            builder._validate()
        except FileNotFoundError as exc:
            assert "Entry script not found" in str(exc)
            return
        raise AssertionError("expected FileNotFoundError")
