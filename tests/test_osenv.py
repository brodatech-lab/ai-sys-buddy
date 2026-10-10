"""Tests for ai_sys_buddy.osenv."""

from __future__ import annotations

import unittest
from unittest import mock

from ai_sys_buddy import osenv


class OSEnvTests(unittest.TestCase):
    def test_detect_linux(self) -> None:
        with mock.patch.object(osenv.sys, "platform", "linux"):
            self.assertEqual(osenv.detect_os(), osenv.LINUX)
            self.assertFalse(osenv.is_windows())

    def test_detect_windows(self) -> None:
        with mock.patch.object(osenv.sys, "platform", "win32"):
            self.assertEqual(osenv.detect_os(), osenv.WINDOWS)
            self.assertTrue(osenv.is_windows())

    def test_unknown_posix_treated_as_linux(self) -> None:
        with mock.patch.object(osenv.sys, "platform", "freebsd"):
            self.assertEqual(osenv.detect_os(), osenv.LINUX)

    def test_detect_shell_windows_powershell(self) -> None:
        with mock.patch.dict(osenv.os.environ, {"PSModulePath": "x"}, clear=True):
            self.assertEqual(osenv.detect_shell(osenv.WINDOWS), "powershell")

    def test_context_prompt_block_contains_os(self) -> None:
        ctx = osenv.get_context()
        block = ctx.to_prompt_block()
        self.assertIn("Environment context:", block)
        self.assertIn(ctx.os_name, block)
        self.assertIn(ctx.cwd, block)


if __name__ == "__main__":
    unittest.main()
