"""Tests for ai_sys_buddy.config."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ai_sys_buddy import config


class ConfigTests(unittest.TestCase):
    def test_defaults(self) -> None:
        cfg = config.Config()
        self.assertEqual(cfg.ollama_url, config.DEFAULT_OLLAMA_URL)
        self.assertEqual(cfg.persona_name, "ai")
        self.assertEqual(cfg.history_size, config.DEFAULT_HISTORY_SIZE)
        self.assertEqual(cfg.validate(), [])

    def test_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            cfg = config.Config(model="llama3.2", ui_backend="standard", history_size=6)
            saved = config.save_config(cfg, path)
            self.assertEqual(saved, path)
            loaded = config.load_config(path)
            self.assertEqual(loaded.model, "llama3.2")
            self.assertEqual(loaded.ui_backend, "standard")
            self.assertEqual(loaded.history_size, 6)

    def test_missing_file_returns_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            loaded = config.load_config(Path(tmp) / "nope.json")
            self.assertEqual(loaded, config.Config())

    def test_load_config_with_bom(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_bytes(b"\xef\xbb\xbf" + b'{"model": "m"}')
            cfg = config.load_config(path)
            self.assertEqual(cfg.model, "m")

    def test_invalid_json_returns_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text("{ not json", encoding="utf-8")
            self.assertEqual(config.load_config(path), config.Config())

    def test_from_dict_ignores_unknown_keys(self) -> None:
        cfg = config.Config.from_dict({"model": "m", "bogus": 1})
        self.assertEqual(cfg.model, "m")
        self.assertFalse(hasattr(cfg, "bogus"))

    def test_validate_reports_problems(self) -> None:
        cfg = config.Config(ollama_url="ftp://x", ui_backend="nope", history_size=0,
                            persona_name="  ")
        problems = cfg.validate()
        self.assertEqual(len(problems), 4)


if __name__ == "__main__":
    unittest.main()
