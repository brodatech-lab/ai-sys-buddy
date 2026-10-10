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
    last_payload: dict | None = None

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def stream(self, method, url, json=None):
        type(self).last_payload = json
        return _FakeStreamResponse(self.lines, self.status_code)

    def get(self, url):
        response = mock.Mock()
        response.status_code = self.status_code
        if url.endswith("/api/ps"):
            response.json.return_value = {"models": [{"name": "llama3.2:latest"}]}
        else:
            response.json.return_value = {
                "models": [{"name": "llama3.2:latest"}, {"model": "phi3"}]
            }
        response.raise_for_status.return_value = None
        return response

    def post(self, url, json=None):
        response = mock.Mock()
        response.status_code = self.status_code
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

    def test_stream_chat_parses_thinking(self) -> None:
        chunks = [
            json.dumps({"message": {"content": "", "thinking": "hmm"}, "done": False}),
            json.dumps({"message": {"content": "answer"}, "done": False}),
            json.dumps({"message": {"content": ""}, "done": True}),
        ]
        fake = type("C", (_FakeClient,), {"lines": chunks})
        with mock.patch.object(ollama.httpx, "Client", fake):
            events = list(ollama.stream_chat("http://x", "m", []))
        self.assertEqual("".join(e.thinking for e in events), "hmm")
        self.assertEqual("".join(e.text for e in events), "answer")

    def test_stream_chat_defaults_think_false(self) -> None:
        fake = type("C", (_FakeClient,), {"lines": []})
        with mock.patch.object(ollama.httpx, "Client", fake):
            list(ollama.stream_chat("http://x", "m", []))
        self.assertFalse(fake.last_payload["think"])

    def test_stream_chat_passes_think(self) -> None:
        fake = type("C", (_FakeClient,), {"lines": []})
        with mock.patch.object(ollama.httpx, "Client", fake):
            list(ollama.stream_chat("http://x", "m", [], think=True))
        self.assertTrue(fake.last_payload["think"])

    def test_stream_chat_raises_on_error_line(self) -> None:
        chunks = [json.dumps({"error": "model does not support thinking"})]
        fake = type("C", (_FakeClient,), {"lines": chunks})
        with mock.patch.object(ollama.httpx, "Client", fake):
            with self.assertRaises(ollama.OllamaError):
                list(ollama.stream_chat("http://x", "m", [], think=True))

    def test_list_models_reads_names(self) -> None:
        with mock.patch.object(ollama.httpx, "Client", _FakeClient):
            models = ollama.list_models("http://x")
        self.assertEqual(models, ["llama3.2:latest", "phi3"])

    def test_list_running_reads_names(self) -> None:
        with mock.patch.object(ollama.httpx, "Client", _FakeClient):
            running = ollama.list_running("http://x")
        self.assertEqual(running, ["llama3.2:latest"])

    def test_unload_model_returns_true(self) -> None:
        with mock.patch.object(ollama.httpx, "Client", _FakeClient):
            self.assertTrue(ollama.unload_model("http://x", "llama3.2:latest"))

    def test_list_models_connection_error(self) -> None:
        def boom(*args, **kwargs):
            raise ollama.httpx.ConnectError("nope")

        with mock.patch.object(ollama.httpx, "Client", side_effect=boom):
            with self.assertRaises(ollama.OllamaError):
                ollama.list_models("http://x")


if __name__ == "__main__":
    unittest.main()
