"""User configuration handling.

The config lives next to the user's other dotfiles and is never uploaded
anywhere. Writes are atomic to avoid corrupting the file on interruption.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from . import APP_NAME, DEFAULT_PERSONA

DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_HISTORY_SIZE = 4
UI_BACKENDS = ("rich", "standard")


def config_dir() -> Path:
    """Return the per-user config directory for the current platform."""
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / APP_NAME
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / APP_NAME


def config_path() -> Path:
    return config_dir() / "config.json"


@dataclass
class Config:
    """Persisted user settings with sensible defaults."""

    ollama_url: str = DEFAULT_OLLAMA_URL
    model: str = ""
    persona_name: str = DEFAULT_PERSONA
    ui_backend: str = "rich"
    history_size: int = DEFAULT_HISTORY_SIZE
    verbose_default: bool = False
    telemetry_enabled: bool = False
    no_color: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        known = {field.name for field in fields(cls)}
        filtered = {key: value for key, value in (data or {}).items() if key in known}
        return cls(**filtered)

    def validate(self) -> list[str]:
        """Return a list of human readable validation problems (empty is ok)."""
        problems: list[str] = []
        if not self.ollama_url.startswith(("http://", "https://")):
            problems.append("ollama_url must start with http:// or https://")
        if self.ui_backend not in UI_BACKENDS:
            problems.append(f"ui_backend must be one of {', '.join(UI_BACKENDS)}")
        if not 1 <= self.history_size <= 20:
            problems.append("history_size must be between 1 and 20")
        if not self.persona_name.strip():
            problems.append("persona_name must not be empty")
        return problems


def load_config(path: Path | None = None) -> Config:
    """Load the config, falling back to defaults when missing or invalid."""
    target = path or config_path()
    try:
        raw = target.read_text(encoding="utf-8")
    except FileNotFoundError:
        return Config()
    except OSError:
        return Config()
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return Config()
    if not isinstance(data, dict):
        return Config()
    return Config.from_dict(data)


def save_config(config: Config, path: Path | None = None) -> Path:
    """Atomically persist the config and return the written path."""
    target = path or config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(config.to_dict(), indent=2, ensure_ascii=False) + "\n"
    # Atomic write: write to a temp file in the same directory, then replace.
    fd, tmp_name = tempfile.mkstemp(dir=str(target.parent), prefix=".config-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
        os.replace(tmp_name, target)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    return target
