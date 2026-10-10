"""Rich + questionary UI backend."""

from __future__ import annotations

from typing import Sequence

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .base import UI


class RichUI(UI):
    """Aimed at interactive terminals; falls back gracefully when piped."""

    def __init__(self, color: bool = True) -> None:
        super().__init__(color=color)
        self.console = Console(
            no_color=not color,
            highlight=False,
            soft_wrap=True,
        )

    def print(self, text: str = "", style: str | None = None) -> None:
        self.console.print(text, style=style, highlight=False)

    def clear(self) -> None:
        if self.console.is_terminal:
            self.console.clear()

    def banner(self, title: str, subtitle: str = "") -> None:
        text = Text(title, style="bold cyan")
        if subtitle:
            text.append("\n" + subtitle, style="dim")
        self.console.print(text)

    def frame(self, title: str, body: str) -> None:
        self.console.print(
            Panel(body, title=title, title_align="left", border_style="cyan", expand=True)
        )

    def info(self, text: str) -> None:
        self.console.print(f"[bold blue]i[/] {text}")

    def success(self, text: str) -> None:
        self.console.print(f"[bold green]+[/] {text}")

    def warning(self, text: str) -> None:
        self.console.print(f"[bold yellow]![/] {text}")

    def error(self, text: str) -> None:
        self.console.print(f"[bold red]x[/] {text}")

    def select(self, message: str, choices: Sequence[str]) -> str | None:
        if not choices:
            return None
        return questionary.select(message, choices=list(choices)).ask()

    def confirm(self, message: str, default: bool = True) -> bool:
        answer = questionary.confirm(message, default=default).ask()
        return default if answer is None else bool(answer)

    def text(self, message: str, default: str = "") -> str:
        answer = questionary.text(message, default=default).ask()
        return default if answer is None else answer

    def stream_start(self) -> None:
        # Nothing to prepare; rich prints incrementally.
        return None

    def stream_write(self, text: str) -> None:
        self.console.print(text, end="", markup=False, highlight=False, soft_wrap=True)

    def stream_end(self) -> None:
        self.console.print()
