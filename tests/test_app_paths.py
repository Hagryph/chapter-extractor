from __future__ import annotations

from pathlib import Path

from chapter_extractor.infrastructure.paths import AppPaths


class TestAppPaths:
    def test_for_testing_isolates_paths(self, tmp_path: Path) -> None:
        paths = AppPaths.for_testing(tmp_path)
        assert paths.user_data_dir == tmp_path / "data"
        assert paths.user_documents_dir == tmp_path / "documents"

    def test_registry_db_path_under_data(self, tmp_path: Path) -> None:
        paths = AppPaths.for_testing(tmp_path)
        assert paths.registry_db_path == tmp_path / "data" / "registry.db"

    def test_default_projects_dir_under_documents(self, tmp_path: Path) -> None:
        paths = AppPaths.for_testing(tmp_path)
        assert paths.default_projects_dir == tmp_path / "documents" / "ChapterExtractor"

    def test_project_root_uses_safe_name(self, tmp_path: Path) -> None:
        paths = AppPaths.for_testing(tmp_path)
        out = paths.project_root('My/Novel: "Volume 1"')
        assert out.name == "My_Novel_ _Volume 1_"

    def test_project_root_falls_back_to_untitled(self, tmp_path: Path) -> None:
        paths = AppPaths.for_testing(tmp_path)
        assert paths.project_root("///").name == "Untitled"

    def test_ensure_dirs_creates(self, tmp_path: Path) -> None:
        paths = AppPaths.for_testing(tmp_path)
        paths.ensure_dirs()
        assert paths.user_data_dir.is_dir()
        assert paths.default_projects_dir.is_dir()

    def test_default_returns_real_paths(self) -> None:
        # Smoke test — just verify the constructor returns something sensible.
        paths = AppPaths.default()
        assert isinstance(paths.user_data_dir, Path)
        assert isinstance(paths.user_documents_dir, Path)
        assert "ChapterExtractor" in str(paths.user_data_dir)
