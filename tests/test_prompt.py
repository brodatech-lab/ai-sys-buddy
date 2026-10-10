"""Tests for ai_sys_buddy.prompt."""

from __future__ import annotations

import unittest

from ai_sys_buddy import prompt
from ai_sys_buddy.osenv import EnvContext


def _ctx() -> EnvContext:
    return EnvContext(os_name="linux", os_release="6.x", shell="bash", cwd="/tmp", user="tester")


class PromptTests(unittest.TestCase):
    def test_system_prompt_has_persona_and_context(self) -> None:
        text = prompt.build_system_prompt(_ctx(), persona_name="buddy")
        self.assertIn("buddy", text)
        self.assertIn("Environment context:", text)
        self.assertIn("read-only", text)

    def test_history_fifo_keeps_last_exchanges(self) -> None:
        history = prompt.History(size=2)
        for index in range(3):
            history.add("user", f"u{index}")
            history.add("assistant", f"a{index}")
        messages = history.messages()
        self.assertEqual(len(messages), 4)
        self.assertEqual(messages[0]["content"], "u1")
        self.assertEqual(messages[-1]["content"], "a2")

    def test_build_messages_order(self) -> None:
        history = prompt.History(size=2)
        history.add("user", "earlier")
        history.add("assistant", "reply")
        messages = prompt.build_messages("SYS", history, "now")
        self.assertEqual(messages[0], {"role": "system", "content": "SYS"})
        self.assertEqual(messages[1]["content"], "earlier")
        self.assertEqual(messages[-1], {"role": "user", "content": "now"})

    def test_wrap_stdin_embeds_content(self) -> None:
        wrapped = prompt.wrap_stdin("what is this?", "line1\nline2")
        self.assertIn("what is this?", wrapped)
        self.assertIn("line1", wrapped)

    def test_wrap_stdin_empty(self) -> None:
        self.assertEqual(prompt.wrap_stdin("q", "   "), "q")


if __name__ == "__main__":
    unittest.main()
