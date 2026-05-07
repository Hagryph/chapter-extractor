from __future__ import annotations

from html import escape

from chapter_extractor.domain.enums import ColumnWidth
from chapter_extractor.domain.models import Chapter


class ChapterHtmlRenderer:
    """Converts chapter plain text into the HTML used by the reader.

    Transformations:
      - paragraphs split on blank lines, wrapped in ``<p>``
      - ``--- Author's Note ---`` / ``--- End Author's Note ---`` markers
        become ``<div class="author-note-divider">`` blocks for distinct styling
      - all other content is HTML-escaped (no script injection from chapters)
    """

    AUTHOR_NOTE_OPEN = "--- Author's Note ---"
    AUTHOR_NOTE_CLOSE = "--- End Author's Note ---"

    def render(
        self,
        chapter: Chapter,
        *,
        font_family: str,
        font_size_px: int,
        line_height: float,
        column_width: ColumnWidth,
    ) -> str:
        body_html = self._render_body(chapter.content)
        return self._wrap_document(
            title=chapter.title,
            number=chapter.number,
            body_html=body_html,
            font_family=font_family,
            font_size_px=font_size_px,
            line_height=line_height,
            column_chars=column_width.value,
        )

    def _render_body(self, content: str) -> str:
        normalised = content.replace("\r\n", "\n").replace("\r", "\n")
        paragraphs = [p.strip() for p in normalised.split("\n\n") if p.strip()]
        rendered: list[str] = []
        for para in paragraphs:
            if para == self.AUTHOR_NOTE_OPEN:
                rendered.append('<div class="an-divider">Author\'s Note</div>')
            elif para == self.AUTHOR_NOTE_CLOSE:
                rendered.append('<div class="an-divider an-end">End</div>')
            else:
                # Convert any single-newline within a paragraph into <br/>
                lines = [escape(line) for line in para.split("\n")]
                rendered.append("<p>" + "<br/>".join(lines) + "</p>")
        return "\n".join(rendered)

    def _wrap_document(
        self,
        *,
        title: str,
        number: int,
        body_html: str,
        font_family: str,
        font_size_px: int,
        line_height: float,
        column_chars: int,
    ) -> str:
        # Approximate ch in pixels: 0.55em per char @ default font (Baymard).
        max_width_px = int(column_chars * font_size_px * 0.55)
        return f"""
<!DOCTYPE html>
<html><head><style>
  body {{
    font-family: {font_family};
    font-size: {font_size_px}px;
    line-height: {line_height};
    margin: 0 auto;
    max-width: {max_width_px}px;
    padding: 24px;
  }}
  h1 {{
    font-size: 1.6em;
    font-weight: 600;
    margin: 0 0 24px 0;
    line-height: 1.25;
  }}
  h1 .num {{
    opacity: 0.55;
    font-weight: 400;
    font-size: 0.7em;
    margin-right: 8px;
  }}
  p {{
    margin: 0 0 1em 0;
    text-align: left;
    hyphens: auto;
  }}
  .an-divider {{
    border-top: 1px solid rgba(127,127,127,0.45);
    margin: 32px 0 16px 0;
    padding-top: 6px;
    font-size: 0.78em;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    opacity: 0.6;
  }}
  .an-divider.an-end {{
    border-top: none;
    border-bottom: 1px solid rgba(127,127,127,0.45);
    margin: 16px 0 32px 0;
    padding-bottom: 6px;
  }}
</style></head>
<body>
  <h1><span class="num">Chapter {number}</span>{escape(title)}</h1>
  {body_html}
</body></html>
""".strip()

    @staticmethod
    def empty_document(font_family: str, font_size_px: int) -> str:
        """Placeholder shown when no chapter is loaded."""
        return f"""
<html><head><style>
  body {{
    font-family: {font_family};
    font-size: {font_size_px}px;
    margin: 0;
    padding: 24px;
    text-align: center;
    opacity: 0.45;
  }}
  .hint {{
    margin-top: 64px;
  }}
</style></head>
<body><div class="hint">Select a chapter to read.</div></body></html>
""".strip()
