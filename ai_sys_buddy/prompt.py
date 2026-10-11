"""System prompt construction and short-term conversation memory."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable, Sequence

from .osenv import EnvContext

# Upper bound on how much piped input we embed into the prompt.
MAX_STDIN_CHARS = 40000

_SAFETY_RULES = """\
Hard rules you must always follow:
- You are read-only. Never claim you ran, can run, or will run any command.
- Present every command inside a fenced code block and tell the user to review
  it before running it manually.
- Never tell the user to pipe output straight into a shell (no `| sh`, `| bash`).
- Do not invent flags, paths, or services. If unsure, say so and suggest how to
  verify safely.
- Keep answers short and practical. Prefer the platform's native tools."""


def build_system_prompt(context: EnvContext, persona_name: str = "ai") -> str:
    """Create the friendly, experienced sysadmin "buddy" system prompt."""
    return (
        f"You are {persona_name}, a friendly and experienced sysadmin buddy who "
        f"hangs out in the terminal. Talk like a knowledgeable friend: direct, "
        f"relaxed, no corporate jargon, no filler. Use plain language and short "
        f"sentences.\n\n"
        f"{context.to_prompt_block()}\n\n"
        f"{_SAFETY_RULES}"
    )


ENCYCLOPEDIA_INSTRUCTION = (
    "The user wants a short encyclopedia entry for a command. Reply with:\n"
    "1. A one-sentence summary of what it does.\n"
    "2. Two or three practical examples (in code blocks).\n"
    "3. A short list of good practices and common pitfalls.\n"
    "Keep it tight and friendly."
)


@dataclass
class History:
    """Short-term FIFO memory holding the last ``size`` exchanges."""

    size: int = 4
    _messages: deque = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        # One exchange = a user turn plus an assistant turn.
        self._messages = deque(maxlen=max(1, self.size) * 2)

    def add(self, role: str, content: str) -> None:
        self._messages.append({"role": role, "content": content})

    def messages(self) -> list[dict]:
        return list(self._messages)

    def clear(self) -> None:
        self._messages.clear()

    def __len__(self) -> int:
        return len(self._messages)


def build_messages(
    system_prompt: str,
    history: Iterable[dict] | History,
    user_content: str,
) -> list[dict]:
    """Assemble the full message list sent to Ollama."""
    history_messages = history.messages() if isinstance(history, History) else list(history)
    return [
        {"role": "system", "content": system_prompt},
        *history_messages,
        {"role": "user", "content": user_content},
    ]


def wrap_stdin(question: str, stdin_text: str) -> str:
    """Embed piped stdin content into the user turn as context.

    Very large inputs are truncated from the front so the most recent lines
    (typically the interesting ones, e.g. the tail of a log) are kept.
    """
    stripped = stdin_text.strip()
    if not stripped:
        return question
    if len(stripped) > MAX_STDIN_CHARS:
        stripped = "...(earlier output truncated)...\n" + stripped[-MAX_STDIN_CHARS:]
    return f"{question}\n\nHere is the piped input to analyse:\n```\n{stripped}\n```"
