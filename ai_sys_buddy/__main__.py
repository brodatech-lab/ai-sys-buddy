"""Executable entry point (``python -m ai_sys_buddy`` and PyInstaller)."""

from __future__ import annotations

import sys

from .cli import run


def main() -> int:
    try:
        return run(sys.argv[1:])
    except KeyboardInterrupt:
        print()
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
