"""Operating system detection and lightweight environment context.

Only Linux and Windows are supported targets. All gathering here is read-only
and intentionally cheap so that startup stays fast.
"""

from __future__ import annotations

import os
import platform
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

LINUX = "linux"
WINDOWS = "windows"


def detect_os() -> str:
    """Return the supported platform name based on ``sys.platform``."""
    if sys.platform.startswith("win"):
        return WINDOWS
    if sys.platform.startswith("linux"):
        return LINUX
    # Any other POSIX system is treated as Linux-like for guidance purposes.
    return LINUX


def is_windows() -> bool:
    return detect_os() == WINDOWS


def detect_shell(os_name: str | None = None) -> str:
    """Best-effort detection of the user's shell."""
    os_name = os_name or detect_os()
    if os_name == WINDOWS:
        if os.environ.get("PSModulePath"):
            return "powershell"
        return "cmd"
    shell = os.environ.get("SHELL", "")
    return Path(shell).name if shell else "sh"


# Short, practical hints the model can lean on per platform.
_GUIDANCE: dict[str, dict[str, object]] = {
    LINUX: {
        "shell": "bash/sh",
        "service_manager": "systemd (systemctl)",
        "logs": "journalctl",
        "packages": "apt/dnf/pacman (distro dependent)",
        "paths": "POSIX paths, forward slashes",
    },
    WINDOWS: {
        "shell": "PowerShell",
        "service_manager": "Windows Services (Get-Service / Set-Service)",
        "logs": "Event Viewer (Get-WinEvent)",
        "packages": "winget/scoop/choco",
        "paths": "Windows paths, backslashes, drive letters",
    },
}


@dataclass
class EnvContext:
    """A tiny snapshot of the environment injected into the system prompt."""

    os_name: str
    os_release: str
    shell: str
    cwd: str
    user: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    def to_prompt_block(self) -> str:
        """Render the context as a compact block for the system prompt."""
        guidance = _GUIDANCE.get(self.os_name, {})
        lines = [
            "Environment context:",
            f"- OS: {self.os_name} ({self.os_release})",
            f"- Shell: {self.shell}",
            f"- CWD: {self.cwd}",
            f"- User: {self.user}",
        ]
        if guidance:
            hints = "; ".join(f"{key}={value}" for key, value in guidance.items())
            lines.append(f"- Platform hints: {hints}")
        return "\n".join(lines)


def get_context() -> EnvContext:
    """Collect the environment context used by the model (read-only, fast)."""
    os_name = detect_os()
    try:
        user = os.getlogin()
    except OSError:
        user = os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"
    return EnvContext(
        os_name=os_name,
        os_release=platform.release(),
        shell=detect_shell(os_name),
        cwd=str(Path.cwd()),
        user=user,
    )
