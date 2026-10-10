"""Minimal Ollama HTTP client built on httpx.

Read-only guarantee: this module only ever talks HTTP to the configured Ollama
instance. It never executes shell commands and never sends data anywhere else.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Iterator, Sequence

import httpx

# Long default because local models can take a while to load into memory.
DEFAULT_TIMEOUT = 120.0
TAGS_TIMEOUT = 10.0

# Keys returned by Ollama's final streamed chunk that we care about.
_METRIC_KEYS = (
    "total_duration",
    "load_duration",
    "prompt_eval_count",
    "prompt_eval_duration",
    "eval_count",
    "eval_duration",
)


class OllamaError(RuntimeError):
    """Raised for any recoverable connection or protocol problem."""


@dataclass
class StreamEvent:
    """A single streamed chunk plus (on completion) the metrics."""

    text: str = ""
    metrics: dict[str, int] | None = None
    done: bool = False


def _endpoint(base_url: str, path: str) -> str:
    return base_url.rstrip("/") + path


def list_models(base_url: str, timeout: float = TAGS_TIMEOUT) -> list[str]:
    """Return the names of all locally installed models."""
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(_endpoint(base_url, "/api/tags"))
            response.raise_for_status()
            data = response.json()
    except httpx.ConnectError as exc:
        raise OllamaError(f"Cannot reach Ollama at {base_url}") from exc
    except httpx.HTTPStatusError as exc:
        raise OllamaError(f"Ollama returned HTTP {exc.response.status_code}") from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise OllamaError(f"Failed to read model list: {exc}") from exc

    models = data.get("models") or []
    names: list[str] = []
    for entry in models:
        name = entry.get("name") or entry.get("model")
        if name:
            names.append(name)
    return names


def ping(base_url: str, timeout: float = TAGS_TIMEOUT) -> bool:
    """Return True when the Ollama server answers."""
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(_endpoint(base_url, "/api/tags"))
            return response.status_code == 200
    except httpx.HTTPError:
        return False


def _extract_metrics(data: dict) -> dict[str, int]:
    metrics: dict[str, int] = {}
    for key in _METRIC_KEYS:
        value = data.get(key)
        if isinstance(value, (int, float)):
            metrics[key] = int(value)
    return metrics


def stream_chat(
    base_url: str,
    model: str,
    messages: Sequence[dict],
    *,
    timeout: float = DEFAULT_TIMEOUT,
) -> Iterator[StreamEvent]:
    """Stream a chat completion, yielding text chunks and final metrics.

    Yields :class:`StreamEvent` objects. The last event has ``done=True`` and
    carries the performance metrics (when the server provides them).
    """
    payload = {"model": model, "messages": list(messages), "stream": True}
    try:
        with httpx.Client(timeout=timeout) as client:
            with client.stream("POST", _endpoint(base_url, "/api/chat"), json=payload) as response:
                if response.status_code >= 400:
                    response.read()
                    raise OllamaError(
                        f"Ollama returned HTTP {response.status_code}: {response.text[:200]}"
                    )
                for line in response.iter_lines():
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    chunk = (data.get("message") or {}).get("content", "")
                    done = bool(data.get("done"))
                    metrics = _extract_metrics(data) if done else None
                    if chunk or done:
                        yield StreamEvent(text=chunk, metrics=metrics, done=done)
    except httpx.ConnectError as exc:
        raise OllamaError(f"Cannot reach Ollama at {base_url}") from exc
    except httpx.HTTPError as exc:
        raise OllamaError(f"Connection error: {exc}") from exc


def chat(
    base_url: str,
    model: str,
    messages: Sequence[dict],
    *,
    timeout: float = DEFAULT_TIMEOUT,
) -> str:
    """Convenience helper that collects a full streamed reply into a string."""
    parts: list[str] = []
    for event in stream_chat(base_url, model, messages, timeout=timeout):
        parts.append(event.text)
    return "".join(parts)
