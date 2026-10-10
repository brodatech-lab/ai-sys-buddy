"""PyInstaller / plain-python launcher for ai-sys-buddy.

Kept at the repository root so PyInstaller can use it as an entry script with
absolute imports (the package ``__main__`` relies on relative imports).
"""

from __future__ import annotations

import sys

from ai_sys_buddy.cli import run


def main() -> int:
    try:
        return run(sys.argv[1:])
    except KeyboardInterrupt:
        print()
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
