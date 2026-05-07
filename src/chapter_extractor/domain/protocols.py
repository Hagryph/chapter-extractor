from __future__ import annotations

from typing import Protocol, runtime_checkable

from chapter_extractor.domain.models import ParseResult


@runtime_checkable
class IParser(Protocol):
    """Anything that turns raw batch text into a ParseResult."""

    def parse(self, raw: str) -> ParseResult: ...


@runtime_checkable
class ISlugifier(Protocol):
    """Filesystem-safe slug generator for titles."""

    def slugify(self, text: str) -> str: ...
