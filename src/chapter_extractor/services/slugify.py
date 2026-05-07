from __future__ import annotations

import re
import unicodedata


class Slugifier:
    """Filesystem-safe slug. ASCII-only, lowercase, underscore-joined.

    Hand-rolled on stdlib — adequate for chapter titles, no third-party dep.
    """

    _NON_WORD = re.compile(r"[^\w\s-]")
    _WHITESPACE = re.compile(r"[\s_-]+")

    def __init__(self, max_length: int = 60) -> None:
        if max_length < 1:
            raise ValueError("max_length must be >= 1")
        self._max_length = max_length

    def slugify(self, text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text)
        ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
        cleaned = self._NON_WORD.sub("", ascii_only).strip().lower()
        joined = self._WHITESPACE.sub("_", cleaned)
        truncated = joined[: self._max_length].rstrip("_")
        return truncated or "untitled"
