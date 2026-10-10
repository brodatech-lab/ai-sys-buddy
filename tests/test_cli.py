"""Tests for ai_sys_buddy.cli argument handling."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from unittest import mock

from ai_sys_buddy import cli, __version__


class CliTests(unittest.TestCase):
    def test_parser_captures_remainder_verbatim(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["how", "to", "use", "--force"])
        self.assertEqual(args.prompt, ["how", "to", "use", "--force"])

    def test_parser_flags_before_prompt(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["-v", "--model", "llama3.2", "?chmod"])
        self.assertTrue(args.verbose)
        self.assertEqual(args.model, "llama3.2")
        self.assertEqual(args.prompt, ["?chmod"])

    def test_read_piped_stdin_when_tty(self) -> None:
        fake = mock.Mock()
        fake.isatty.return_value = True
        with mock.patch.object(cli.sys, "stdin", fake):
            self.assertEqual(cli.read_piped_stdin(), "")

    def test_version_flag(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = cli.run(["--version"])
        self.assertEqual(code, 0)
        self.assertIn(__version__, buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
