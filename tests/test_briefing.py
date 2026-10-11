"""Tests for ai_sys_buddy.briefing and the `ai status` command."""

from __future__ import annotations

import unittest

from ai_sys_buddy import briefing
from ai_sys_buddy.cli import run_status
from ai_sys_buddy.config import Config
from ai_sys_buddy.ui.base import UI


class _FakeUI(UI):
    def __init__(self) -> None:
        super().__init__(color=False)
        self.rendered: list[tuple[str | None, str]] = []

    def print(self, text="", style=None): pass
    def banner(self, title, subtitle=""): pass
    def frame(self, title, body): pass
    def info(self, text): pass
    def success(self, text): pass
    def warning(self, text): pass
    def error(self, text): pass
    def select(self, message, choices): return None
    def confirm(self, message, default=True): return True
    def text(self, message, default=""): return default
    def stream_start(self): pass
    def stream_write(self, text, style=None): pass
    def stream_end(self): pass
    def render_markdown(self, text, title=None): self.rendered.append((title, text))


class BriefingTests(unittest.TestCase):
    def test_gather_briefing_keys(self) -> None:
        data = briefing.gather_briefing()
        for key in ("time", "uptime", "memory", "disks", "hardware"):
            self.assertIn(key, data)

    def test_render_snapshot_has_sections(self) -> None:
        snapshot = briefing.render_snapshot(briefing.gather_briefing())
        self.assertIn("Time:", snapshot)
        self.assertIn("CPU:", snapshot)
        self.assertIn("Uptime:", snapshot)

    def test_render_markdown_is_a_table(self) -> None:
        table = briefing.render_markdown(briefing.gather_briefing())
        self.assertIn("| Metric | Value |", table)
        self.assertIn("Uptime", table)
        self.assertIn("RAM", table)

    def test_run_status_without_model_shows_snapshot(self) -> None:
        ui = _FakeUI()
        run_status(Config(model=""), ui)
        self.assertTrue(ui.rendered)
        title, body = ui.rendered[0]
        self.assertEqual(title, "status")
        self.assertIn("Uptime", body)
        self.assertIn("| Metric | Value |", body)


if __name__ == "__main__":
    unittest.main()
