from __future__ import annotations

import contextlib
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from sqlalchemy import Engine

from chapter_extractor.domain.models import Project
from chapter_extractor.infrastructure.app_context import AppContext
from chapter_extractor.services.db.chapter_repo import SqlAlchemyChapterRepository
from chapter_extractor.services.db.engine import SqliteEngineFactory
from chapter_extractor.services.db.migrator import project_migrator
from chapter_extractor.services.db.project_repo import SqlAlchemyProjectRepository
from chapter_extractor.services.parser import ChapterParser
from chapter_extractor.viewmodels.batch_input_vm import BatchInputViewModel
from chapter_extractor.viewmodels.chapter_list_vm import ChapterListViewModel
from chapter_extractor.viewmodels.project_list_vm import ProjectListViewModel
from chapter_extractor.viewmodels.reader_vm import ReaderViewModel
from chapter_extractor.viewmodels.trash_vm import TrashViewModel


class MainViewModel(QObject):
    """Root viewmodel. Owns child VMs and rebinds them when a project opens.

    Until a project is open, the chapter/reader/trash/batch VMs are None.
    Views observe `project_changed` and rebuild their child UIs.
    """

    project_changed = Signal(object)  # Project | None

    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self._ctx = ctx
        self._parser = ChapterParser()

        self.project_list_vm = ProjectListViewModel(ctx.registry)
        self.project_list_vm.project_opened.connect(self._on_project_opened)
        self.project_list_vm.project_created.connect(self._on_project_created)

        self._project: Project | None = None
        self._project_engine: Engine | None = None
        self.chapter_list_vm: ChapterListViewModel | None = None
        self.reader_vm: ReaderViewModel | None = None
        self.trash_vm: TrashViewModel | None = None
        self.batch_input_vm: BatchInputViewModel | None = None

    # ─── Reads ──────────────────────────────────────────────────

    @property
    def context(self) -> AppContext:
        return self._ctx

    @property
    def current_project(self) -> Project | None:
        return self._project

    # ─── Commands ───────────────────────────────────────────────

    def _on_project_created(self, project: Project) -> None:
        self._open(project, create_db=True)

    def _on_project_opened(self, project: Project) -> None:
        self._open(project, create_db=False)

    def close_project(self) -> None:
        self._teardown_project()
        self.project_changed.emit(None)

    # ─── Internals ──────────────────────────────────────────────

    def _open(self, project: Project, *, create_db: bool) -> None:
        self._teardown_project()
        project.metadata_dir.mkdir(parents=True, exist_ok=True)
        engine = SqliteEngineFactory.for_file(project.db_path)
        project_migrator().apply_all(engine)

        chapter_repo = SqlAlchemyChapterRepository(engine)
        proj_repo = SqlAlchemyProjectRepository(engine, project.root_path)

        if create_db:
            # Already-initialised DB is fine; treat as "open existing".
            with contextlib.suppress(RuntimeError):
                proj_repo.create(project)
        loaded = proj_repo.load(project.root_path)

        self._project_engine = engine
        self._project = loaded
        self.chapter_list_vm = ChapterListViewModel(chapter_repo)
        self.reader_vm = ReaderViewModel(chapter_repo, self._ctx.clipboard)
        self.trash_vm = TrashViewModel(chapter_repo)
        self.batch_input_vm = BatchInputViewModel(self._parser, chapter_repo)

        self.chapter_list_vm.selection_changed.connect(self._on_selection)
        self.batch_input_vm.commit_succeeded.connect(lambda _: self.chapter_list_vm.refresh())
        self.trash_vm.chapter_restored.connect(lambda _: self.chapter_list_vm.refresh())

        self.chapter_list_vm.refresh()
        self._ctx.settings.set_last_project_id(self._registry_id_for(loaded.root_path))
        self.project_changed.emit(loaded)

    def _on_selection(self, summary) -> None:  # ChapterSummary | None
        if self.reader_vm is None:
            return
        self.reader_vm.load_chapter(summary.id if summary else None)

    def _teardown_project(self) -> None:
        if self.chapter_list_vm:
            self.chapter_list_vm.deleteLater()
        if self.reader_vm:
            self.reader_vm.deleteLater()
        if self.trash_vm:
            self.trash_vm.deleteLater()
        if self.batch_input_vm:
            self.batch_input_vm.deleteLater()
        self.chapter_list_vm = None
        self.reader_vm = None
        self.trash_vm = None
        self.batch_input_vm = None
        if self._project_engine is not None:
            self._project_engine.dispose()
            self._project_engine = None
        self._project = None

    def _registry_id_for(self, root_path: Path) -> int | None:
        for s in self._ctx.registry.list_projects():
            if s.root_path == root_path:
                return s.id
        return None
