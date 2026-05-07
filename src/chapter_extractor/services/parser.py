from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from chapter_extractor.domain.enums import ChapterStatus
from chapter_extractor.domain.models import (
    Chapter,
    ChapterHeader,
    ParseResult,
    ParseWarning,
)
from chapter_extractor.services.slugify import Slugifier


class ChapterParser:
    """Parses raw batch text into individual chapters.

    Approach (validated against real-world batch input):
      1. Find every `Chapter N: Title` header line via re.finditer + named groups.
      2. For each header, the body runs from header.span[1] to the next
         header's span[0] (or end-of-input for the last chapter).
      3. Clean body: strip surrounding `. . .` separators, collapse 3+ blank
         lines to 2.
      4. Mark inline (Author's Note ...) blocks with visible separator lines.
      5. Build a Chapter with a zero-padded, slugified filename.
    """

    _HEADER_RE = re.compile(
        r"""
        ^[ \t]*Chapter[ \t]+(?P<num>\d+)
        [ \t]*[:：][ \t]*
        (?P<title>.+?)\s*$
        """,
        re.MULTILINE | re.VERBOSE | re.IGNORECASE,
    )
    _SEPARATOR_RE = re.compile(r"^\s*\.\s*\.\s*\.\s*$", re.MULTILINE)
    _AUTHOR_NOTE_RE = re.compile(
        r"\(Author'?s\s+Note\b(?P<inner>.*?)\)(?=\s*$)",
        re.DOTALL | re.IGNORECASE,
    )
    _BLANK_LINES_RE = re.compile(r"\n{3,}")

    def __init__(self, slugifier: Slugifier | None = None) -> None:
        self._slugifier = slugifier or Slugifier()

    def parse(self, raw: str) -> ParseResult:
        text = raw.replace("\r\n", "\n").replace("\r", "\n")
        headers = self._find_headers(text)
        if not headers:
            return ParseResult(
                chapters=[],
                warnings=[ParseWarning("No chapter headers detected in input.")],
            )

        chapters: list[Chapter] = []
        warnings: list[ParseWarning] = []
        seen: dict[int, int] = {}  # chapter number -> index in chapters list

        for idx, header in enumerate(headers):
            body_start = header.span[1]
            body_end = headers[idx + 1].span[0] if idx + 1 < len(headers) else len(text)
            body = self._clean_body(text[body_start:body_end])
            chapter = self._build_chapter(header, body)

            if header.number in seen:
                warnings.append(
                    ParseWarning(
                        f"Duplicate chapter number {header.number} in input — kept last occurrence.",
                        header.number,
                    )
                )
                chapters[seen[header.number]] = chapter
            else:
                seen[header.number] = len(chapters)
                chapters.append(chapter)

        chapters.sort(key=lambda c: c.number)
        return ParseResult(chapters=chapters, warnings=warnings)

    def _find_headers(self, text: str) -> list[ChapterHeader]:
        return [
            ChapterHeader(
                number=int(mo.group("num")),
                title=mo.group("title").strip(),
                raw_match=mo.group(0),
                span=mo.span(),
            )
            for mo in self._HEADER_RE.finditer(text)
        ]

    def _clean_body(self, body: str) -> str:
        without_separators = self._SEPARATOR_RE.sub("", body)
        marked = self._mark_author_notes(without_separators)
        collapsed = self._BLANK_LINES_RE.sub("\n\n", marked)
        return collapsed.strip() + "\n"

    def _mark_author_notes(self, body: str) -> str:
        def repl(match: re.Match[str]) -> str:
            inner = match.group("inner").strip()
            return f"\n--- Author's Note ---\n{inner}\n--- End Author's Note ---\n"

        return self._AUTHOR_NOTE_RE.sub(repl, body)

    def _build_chapter(self, header: ChapterHeader, body: str) -> Chapter:
        slug = self._slugifier.slugify(header.title)
        filename = f"Chapter_{header.number:03d}_{slug}.txt"
        chapter = Chapter(
            number=header.number,
            title=header.title,
            content=body,
            filename=filename,
            file_path=Path(filename),
            status=ChapterStatus.NEW,
            created_at=datetime.now(),
        )
        chapter.recompute_word_count()
        return chapter
