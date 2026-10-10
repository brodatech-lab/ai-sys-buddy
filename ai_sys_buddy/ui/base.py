"""Common UI interface.

Two backends implement this interface: a ``rich`` based one and a pure
standard-library one. Keeping the surface small lets the rest of the code stay
backend agnostic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence


class UI(ABC):
    """Abstract presentation layer used by the CLI."""

    def __init__(self, color: bool = True) -> None:
        self.color = color

    def clear(self) -> None:
        """Clear the screen. A no-op by default (e.g. when output is piped)."""
        return None

    # --- Plain output -------------------------------------------------
    @abstractmethod
    def print(self, text: str = "", style: str | None = None) -> None:
        """Print a line of text."""

    def echo(self, text: str = "") -> None:
        self.print(text)

    @abstractmethod
    def banner(self, title: str, subtitle: str = "") -> None:
        """Render a prominent title block."""

    @abstractmethod
    def frame(self, title: str, body: str) -> None:
        """Render content inside a bordered frame."""

    # --- Severity helpers --------------------------------------------
    @abstractmethod
    def info(self, text: str) -> None: ...

    @abstractmethod
    def success(self, text: str) -> None: ...

    @abstractmethod
    def warning(self, text: str) -> None: ...

    @abstractmethod
    def error(self, text: str) -> None: ...

    # --- Interaction --------------------------------------------------
    @abstractmethod
    def select(self, message: str, choices: Sequence[str]) -> str | None:
        """Let the user pick one option. Returns None when cancelled."""

    @abstractmethod
    def confirm(self, message: str, default: bool = True) -> bool: ...

    @abstractmethod
    def text(self, message: str, default: str = "") -> str: ...

    # --- Streaming output --------------------------------------------
    @abstractmethod
    def stream_start(self) -> None: ...

    @abstractmethod
    def stream_write(self, text: str) -> None: ...

    @abstractmethod
    def stream_end(self) -> None: ...
