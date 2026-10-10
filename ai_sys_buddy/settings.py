"""Interactive settings panel (Phase 3 TUI).

Navigated with arrow keys on the ``rich`` backend (via questionary) and with a
numbered menu on the ``standard`` backend. Every change is validated before it
is saved.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from . import ollama
from .config import Config, UI_BACKENDS, config_path, save_config
from .ui import UI


@dataclass
class _Item:
    key: str
    label: str
    handler: Callable[[], None] | None = None


def _status_body(config: Config, path: Path | None = None) -> str:
    lines = [
        f"Ollama URL      : {config.ollama_url}",
        f"Model           : {config.model or '(not set)'}",
        f"Persona name    : {config.persona_name}",
        f"UI backend      : {config.ui_backend}",
        f"History size    : {config.history_size}",
        f"Verbose default : {config.verbose_default}",
        f"Telemetry       : {config.telemetry_enabled}",
        f"No color        : {config.no_color}",
        f"Config file     : {path or config_path()}",
    ]
    return "\n".join(lines)


def _edit_url(config: Config, ui: UI) -> None:
    value = ui.text("Ollama URL", config.ollama_url).strip() or config.ollama_url
    if not value.startswith(("http://", "https://")):
        ui.warning("URL must start with http:// or https://")
        return
    config.ollama_url = value
    ui.success("Updated Ollama URL.")


def _edit_persona(config: Config, ui: UI) -> None:
    value = ui.text("Persona name (e.g. ai or buddy)", config.persona_name).strip()
    if value:
        config.persona_name = value


def _edit_backend(config: Config, ui: UI) -> None:
    picked = ui.select("UI backend", list(UI_BACKENDS))
    if picked:
        config.ui_backend = picked


def _edit_history(config: Config, ui: UI) -> None:
    raw = ui.text("History size (1-20)", str(config.history_size)).strip()
    if raw.isdigit():
        config.history_size = max(1, min(20, int(raw)))
    else:
        ui.warning("Please enter a number between 1 and 20.")


def _toggle_verbose(config: Config, ui: UI) -> None:
    config.verbose_default = not config.verbose_default


def _toggle_color(config: Config, ui: UI) -> None:
    config.no_color = not config.no_color


def _toggle_telemetry(config: Config, ui: UI) -> None:
    config.telemetry_enabled = not config.telemetry_enabled
    if config.telemetry_enabled:
        ui.warning("Opt-in hardware telemetry is reserved and not active yet.")


def _pick_model(config: Config, ui: UI) -> None:
    try:
        models = ollama.list_models(config.ollama_url)
    except ollama.OllamaError as exc:
        ui.error(str(exc))
        return
    if not models:
        ui.warning("No models installed. Try: ollama pull llama3.2")
        return
    picked = ui.select("Installed models", models)
    if picked:
        config.model = picked
        ui.success(f"Model set to {picked}.")


def _test_connection(config: Config, ui: UI) -> None:
    if ollama.ping(config.ollama_url):
        ui.success(f"Ollama is reachable at {config.ollama_url}.")
    else:
        ui.error(f"Cannot reach Ollama at {config.ollama_url}.")


def run_settings(config: Config, ui: UI, path: Path | None = None) -> bool:
    """Show the interactive settings panel. Returns True when changes were saved."""
    while True:
        ui.clear()
        ui.frame("Settings", _status_body(config, path))

        items = [
            _Item("url", f"Ollama URL       : {config.ollama_url}",
                  lambda: _edit_url(config, ui)),
            _Item("model", f"Model            : {config.model or '(not set)'}",
                  lambda: _pick_model(config, ui)),
            _Item("persona", f"Persona name     : {config.persona_name}",
                  lambda: _edit_persona(config, ui)),
            _Item("backend", f"UI backend       : {config.ui_backend}",
                  lambda: _edit_backend(config, ui)),
            _Item("history", f"History size     : {config.history_size}",
                  lambda: _edit_history(config, ui)),
            _Item("verbose", f"Verbose default  : {config.verbose_default}",
                  lambda: _toggle_verbose(config, ui)),
            _Item("telemetry", f"Telemetry (opt-in): {config.telemetry_enabled}",
                  lambda: _toggle_telemetry(config, ui)),
            _Item("color", f"No color         : {config.no_color}",
                  lambda: _toggle_color(config, ui)),
            _Item("test", "Test Ollama connection", lambda: _test_connection(config, ui)),
            _Item("save", "Save and exit"),
            _Item("cancel", "Exit without saving"),
        ]

        choice = ui.select("What do you want to change?", [item.label for item in items])
        if choice is None:
            return False
        selected = next((item for item in items if item.label == choice), None)
        if selected is None:
            continue
        if selected.key == "cancel":
            return False
        if selected.key == "save":
            problems = config.validate()
            if problems:
                for problem in problems:
                    ui.error(problem)
                ui.text("Press Enter to continue")
                continue
            saved_path = save_config(config, path)
            ui.success(f"Saved to {saved_path}")
            return True
        if selected.handler is not None:
            selected.handler()
