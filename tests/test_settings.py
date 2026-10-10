"""Tests for the interactive settings panel."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ai_sys_buddy import config as config_mod
from ai_sys_buddy import settings
from ai_sys_buddy.ui.base import UI


class FakeUI(UI):
    """A scripted UI that returns preprogrammed answers."""

    def __init__(self, selections=None, texts=None, confirm=True):
        super().__init__(color=False)
        self._selections = list(selections or [])
        self._texts = list(texts or [])
        self._confirm = confirm
        self.messages: list[tuple[str, str]] = []

    def print(self, text="", style=None):
        self.messages.append(("print", text))

    def banner(self, title, subtitle=""):
        pass

    def frame(self, title, body):
        self.messages.append(("frame", title))

    def info(self, text):
        self.messages.append(("info", text))

    def success(self, text):
        self.messages.append(("success", text))

    def warning(self, text):
        self.messages.append(("warning", text))

    def error(self, text):
        self.messages.append(("error", text))

    def select(self, message, choices):
        if not self._selections:
            return None
        token = self._selections.pop(0)
        for choice in choices:
            if token in choice:
                return choice
        return None

    def confirm(self, message, default=True):
        return self._confirm

    def text(self, message, default=""):
        if self._texts:
            return self._texts.pop(0)
        return default

    def stream_start(self):
        pass

    def stream_write(self, text, style=None):
        pass

    def stream_end(self):
        pass

    def kinds(self):
        return [kind for kind, _ in self.messages]


class SettingsTests(unittest.TestCase):
    def test_save_and_exit_persists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            cfg = config_mod.Config()
            ui = FakeUI(selections=["Save and exit"])
            saved = settings.run_settings(cfg, ui, path=path)
            self.assertTrue(saved)
            self.assertTrue(path.exists())
            self.assertEqual(config_mod.load_config(path), cfg)

    def test_toggle_verbose_then_save(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            cfg = config_mod.Config(verbose_default=False)
            ui = FakeUI(selections=["Verbose default", "Save and exit"])
            settings.run_settings(cfg, ui, path=path)
            self.assertTrue(cfg.verbose_default)
            self.assertTrue(config_mod.load_config(path).verbose_default)

    def test_toggle_think_then_save(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            cfg = config_mod.Config(think=False)
            ui = FakeUI(selections=["Reasoning", "Save and exit"])
            settings.run_settings(cfg, ui, path=path)
            self.assertTrue(cfg.think)
            self.assertTrue(config_mod.load_config(path).think)

    def test_cancel_does_not_save(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            ui = FakeUI(selections=["Exit without saving"])
            saved = settings.run_settings(config_mod.Config(), ui, path=path)
            self.assertFalse(saved)
            self.assertFalse(path.exists())

    def test_invalid_url_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            cfg = config_mod.Config()
            ui = FakeUI(selections=["Ollama URL", "Save and exit"], texts=["ftp://nope"])
            settings.run_settings(cfg, ui, path=path)
            self.assertEqual(cfg.ollama_url, config_mod.DEFAULT_OLLAMA_URL)
            self.assertIn("warning", ui.kinds())

    def test_persona_edit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            cfg = config_mod.Config()
            ui = FakeUI(selections=["Persona name", "Save and exit"], texts=["buddy"])
            settings.run_settings(cfg, ui, path=path)
            self.assertEqual(cfg.persona_name, "buddy")

    def test_pick_model_without_server_warns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            cfg = config_mod.Config()
            ui = FakeUI(selections=["Model", "Exit without saving"])
            from unittest import mock

            with mock.patch.object(settings.ollama, "list_models", side_effect=settings.ollama.OllamaError("down")):
                settings.run_settings(cfg, ui, path=path)
            self.assertIn("error", ui.kinds())

    def test_switch_model_unloads_others(self) -> None:
        from unittest import mock

        cfg = config_mod.Config()
        ui = FakeUI(confirm=True)
        with mock.patch.object(settings.ollama, "list_running", return_value=["old:7b"]), \
                mock.patch.object(settings.ollama, "unload_model", return_value=True) as unload:
            settings.switch_model(cfg, ui, "new:8b")
        self.assertEqual(cfg.model, "new:8b")
        unload.assert_called_once_with(cfg.ollama_url, "old:7b")
        self.assertIn("success", ui.kinds())

    def test_switch_model_declined_keeps_others(self) -> None:
        from unittest import mock

        cfg = config_mod.Config()
        ui = FakeUI(confirm=False)
        with mock.patch.object(settings.ollama, "list_running", return_value=["old:7b"]), \
                mock.patch.object(settings.ollama, "unload_model", return_value=True) as unload:
            settings.switch_model(cfg, ui, "new:8b")
        self.assertEqual(cfg.model, "new:8b")
        unload.assert_not_called()

    def test_switch_model_no_others(self) -> None:
        from unittest import mock

        cfg = config_mod.Config()
        ui = FakeUI(confirm=True)
        with mock.patch.object(settings.ollama, "list_running", return_value=["new:8b"]), \
                mock.patch.object(settings.ollama, "unload_model", return_value=True) as unload:
            settings.switch_model(cfg, ui, "new:8b")
        self.assertEqual(cfg.model, "new:8b")
        unload.assert_not_called()


if __name__ == "__main__":
    unittest.main()
