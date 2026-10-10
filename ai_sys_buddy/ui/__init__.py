"""UI backend selection.

Prefers ``rich`` when configured and available, otherwise silently falls back
to the standard-library backend so the tool keeps working with zero deps.
"""

from __future__ import annotations

import sys

from ..config import Config
from .base import UI


def _should_color(config: Config) -> bool:
    if config.no_color:
        return False
    if not sys.stdout.isatty():
        return False
    return True


def get_ui(config: Config) -> UI:
    """Return a UI instance for the given config."""
    color = _should_color(config)
    if config.ui_backend == "rich":
        try:
            from .rich_ui import RichUI

            return RichUI(color=color)
        except ImportError:
            pass
    from .standard_ui import StandardUI

    return StandardUI(color=color)


__all__ = ["UI", "get_ui"]
