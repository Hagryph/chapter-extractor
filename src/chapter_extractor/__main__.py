"""Entry point. The Qt application is wired up in a later PR; for now this is a stub."""
from __future__ import annotations

import sys


class StubEntryPoint:
    """Placeholder until the GUI layer lands (PR 5)."""

    @staticmethod
    def run(argv: list[str]) -> int:
        del argv
        sys.stdout.write(
            "chapter-extractor: domain + parser layer installed.\n"
            "GUI is wired up in a later PR.\n"
        )
        return 0


def main() -> int:
    return StubEntryPoint.run(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
