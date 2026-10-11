"""Common UI interface.

Two backends implement this interface: a ``rich`` based one and a pure
standard-library one. Keeping the surface small lets the rest of the code stay
backend agnostic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Iterator, Sequence


class Status:
    """Handle for updating a transient status message while work runs."""

    def update(self, message: str) -> None:
        return None


class UI(ABC):
    """Abstract presentation layer used by the CLI."""

    def __init__(self, color: bool = True) -> None:
        self.color = color

    def clear(self) -> None:
        """Clear the screen. A no-op by default (e.g. when output is piped)."""
        return None

    @contextmanager
    def status(self, message: str) -> Iterator[Status]:
        """Show a transient status. Default prints the message once."""
        self.print(message, "dim")
        yield Status()

    def render_markdown(self, text: str, title: str | None = None) -> None:
        """Render text as Markdown. Default fallback is plain text."""
        if title:
            self.frame(title, text)
        else:
            self.print(text)

    def pause(self, message: str = "Press Enter to continue") -> None:
        """Wait for the user to acknowledge a message (before a redraw)."""
        self.print(message, "dim")
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            print()

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
    def stream_write(self, text: str, style: str | None = None) -> None: ...

    @abstractmethod
    def stream_end(self) -> None: ...
