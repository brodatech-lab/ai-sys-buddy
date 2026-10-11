"""Tests for the UI backends."""

from __future__ import annotations

import contextlib
import io
import unittest

from ai_sys_buddy.ui.rich_ui import RichUI
from ai_sys_buddy.ui.standard_ui import StandardUI


class RichUITests(unittest.TestCase):
    def test_soft_wrap_is_disabled_so_text_wraps(self) -> None:
        ui = RichUI(color=False)
        # soft_wrap=True would crop long lines instead of wrapping them.
        self.assertFalse(ui.console.soft_wrap)


class StandardUITests(unittest.TestCase):
    def test_render_markdown_with_title_uses_frame(self) -> None:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            StandardUI(color=False).render_markdown("# hello", title="demo")
        output = buffer.getvalue()
        self.assertIn("demo", output)
        self.assertIn("hello", output)

    def test_render_markdown_without_title_prints_text(self) -> None:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            StandardUI(color=False).render_markdown("plain body")
        self.assertIn("plain body", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
