"""Entry point: ``python -m chapter_extractor`` launches the GUI."""
from __future__ import annotations

from chapter_extractor.views.application import main

if __name__ == "__main__":
    raise SystemExit(main())
