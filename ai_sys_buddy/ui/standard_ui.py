"""Standard-library UI backend (no third-party dependencies)."""

from __future__ import annotations

import shutil
import sys
import textwrap
from typing import Sequence

from .base import UI

_RESET = "\033[0m"
_STYLES = {
    "bold": "\033[1m",
    "dim": "\033[2m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "cyan": "\033[36m",
}


class StandardUI(UI):
    """ANSI + ``input()`` implementation that always works offline."""

    def _paint(self, text: str, style: str | None) -> str:
        if not self.color or not style:
            return text
        codes = "".join(_STYLES.get(part, "") for part in style.split())
        return f"{codes}{text}{_RESET}" if codes else text

    def _width(self) -> int:
        try:
            return max(40, min(shutil.get_terminal_size().columns, 100))
        except OSError:
            return 80

    def clear(self) -> None:
        if not sys.stdout.isatty():
            return
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

    def print(self, text: str = "", style: str | None = None) -> None:
        print(self._paint(text, style))

    def banner(self, title: str, subtitle: str = "") -> None:
        self.print(title, "bold cyan")
        if subtitle:
            self.print(subtitle, "dim")

    def frame(self, title: str, body: str) -> None:
        width = self._width()
        inner = width - 4
        top = self._paint("+" + "-" * (width - 2) + "+", "cyan")
        print(top)
        header = f"| {title}".ljust(width - 2)[: width - 2] + " |"
        print(self._paint(header, "bold cyan"))
        print(self._paint("+" + "-" * (width - 2) + "+", "cyan"))
        for raw_line in body.splitlines() or [""]:
            for line in textwrap.wrap(raw_line, inner) or [""]:
                print("| " + line.ljust(inner) + " |")
        print(self._paint("+" + "-" * (width - 2) + "+", "cyan"))

    def info(self, text: str) -> None:
        self.print(f"[i] {text}", "blue")

    def success(self, text: str) -> None:
        self.print(f"[+] {text}", "green")

    def warning(self, text: str) -> None:
        self.print(f"[!] {text}", "yellow")

    def error(self, text: str) -> None:
        self.print(f"[x] {text}", "red")

    def select(self, message: str, choices: Sequence[str]) -> str | None:
        if not choices:
            return None
        self.print(message, "bold")
        for index, choice in enumerate(choices, start=1):
            self.print(f"  {index}) {choice}")
        while True:
            try:
                answer = input("Select [1-{}] (empty to cancel): ".format(len(choices))).strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return None
            if not answer:
                return None
            if answer.isdigit() and 1 <= int(answer) <= len(choices):
                return choices[int(answer) - 1]
            self.warning("Invalid selection, try again.")

    def confirm(self, message: str, default: bool = True) -> bool:
        suffix = "[Y/n]" if default else "[y/N]"
        try:
            answer = input(f"{message} {suffix} ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return default
        if not answer:
            return default
        return answer in ("y", "yes", "t", "tak")

    def text(self, message: str, default: str = "") -> str:
        prompt = f"{message} [{default}]: " if default else f"{message}: "
        try:
            answer = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return default
        return answer or default

    def stream_start(self) -> None:
        sys.stdout.flush()

    def stream_write(self, text: str, style: str | None = None) -> None:
        sys.stdout.write(self._paint(text, style))
        sys.stdout.flush()

    def stream_end(self) -> None:
        sys.stdout.write("\n")
        sys.stdout.flush()
