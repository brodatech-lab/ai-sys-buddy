"""Tests for ai_sys_buddy.ollama using a fake httpx client."""

from __future__ import annotations

import json
import unittest
from unittest import mock

from ai_sys_buddy import ollama


class _FakeStreamResponse:
    def __init__(self, lines, status_code=200):
        self._lines = lines
        self.status_code = status_code
        self.text = ""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def iter_lines(self):
        yield from self._lines

    def read(self):
        return self.text


class _FakeClient:
    lines: list = []
    status_code: int = 200

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def stream(self, method, url, json=None):
        return _FakeStreamResponse(self.lines, self.status_code)

    def get(self, url):
        response = mock.Mock()
        response.status_code = self.status_code
        response.json.return_value = {"models": [{"name": "llama3.2:latest"}, {"model": "phi3"}]}
        response.raise_for_status.return_value = None
        return response


class OllamaTests(unittest.TestCase):
    def test_extract_metrics_filters_and_casts(self) -> None:
        data = {"eval_count": 10.0, "load_duration": 3, "ignored": 1, "text": "x"}
        metrics = ollama._extract_metrics(data)
        self.assertEqual(metrics, {"eval_count": 10, "load_duration": 3})

    def test_stream_chat_parses_chunks_and_metrics(self) -> None:
        chunks = [
            json.dumps({"message": {"content": "hel"}, "done": False}),
            json.dumps({"message": {"content": "lo"}, "done": False}),
            json.dumps({"message": {"content": ""}, "done": True,
                        "eval_count": 2, "eval_duration": 1_000_000_000}),
        ]
        fake = type("C", (_FakeClient,), {"lines": chunks})
        with mock.patch.object(ollama.httpx, "Client", fake):
            events = list(ollama.stream_chat("http://x", "m", [{"role": "user", "content": "q"}]))
        self.assertEqual("".join(e.text for e in events), "hello")
        self.assertTrue(events[-1].done)
        self.assertEqual(events[-1].metrics["eval_count"], 2)

    def test_list_models_reads_names(self) -> None:
        with mock.patch.object(ollama.httpx, "Client", _FakeClient):
            models = ollama.list_models("http://x")
        self.assertEqual(models, ["llama3.2:latest", "phi3"])

    def test_list_models_connection_error(self) -> None:
        def boom(*args, **kwargs):
            raise ollama.httpx.ConnectError("nope")

        with mock.patch.object(ollama.httpx, "Client", side_effect=boom):
            with self.assertRaises(ollama.OllamaError):
                ollama.list_models("http://x")


if __name__ == "__main__":
    unittest.main()
