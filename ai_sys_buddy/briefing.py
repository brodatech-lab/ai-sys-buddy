"""Local system-status snapshot for the ``ai status`` briefing.

Everything here is read from the OS (``/proc``, ``os``, ``ctypes``) and the
Ollama API; no shell commands are ever executed. The snapshot is turned into a
text block that is handed to the model to produce a friendly briefing.
"""

from __future__ import annotations

import os
import shutil
import sys
from datetime import datetime

from . import telemetry

_GIB = 1024**3


def _uptime_seconds() -> float | None:
    if sys.platform.startswith("linux"):
        try:
            with open("/proc/uptime", "r", encoding="utf-8", errors="replace") as handle:
                return float(handle.readline().split()[0])
        except (OSError, ValueError, IndexError):
            return None
    if sys.platform.startswith("win"):
        try:
            import ctypes

            return ctypes.windll.kernel32.GetTickCount64() / 1000.0
        except Exception:  # pragma: no cover - Windows only
            return None
    return None


def _humanize_uptime(seconds: float | None) -> str:
    if seconds is None:
        return "?"
    minutes, _ = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)


def _memory() -> dict[str, object]:
    if sys.platform.startswith("linux"):
        values: dict[str, int] = {}
        try:
            with open("/proc/meminfo", "r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    key, _, rest = line.partition(":")
                    values[key.strip()] = int(rest.strip().split()[0])
        except (OSError, ValueError, IndexError):
            return {}
        total = values.get("MemTotal")
        available = values.get("MemAvailable")
        swap_total = values.get("SwapTotal")
        swap_free = values.get("SwapFree")
        result: dict[str, object] = {}
        if total:
            result["ram_total_gb"] = round(total / 1024 / 1024, 1)
        if available:
            result["ram_available_gb"] = round(available / 1024 / 1024, 1)
        if total and available:
            result["ram_used_percent"] = round((total - available) / total * 100, 1)
        if swap_total:
            result["swap_total_gb"] = round(swap_total / 1024 / 1024, 1)
            if swap_free is not None:
                result["swap_used_percent"] = round(
                    (swap_total - swap_free) / swap_total * 100, 1
                )
        return result
    # Windows: only total RAM is available from ctypes here.
    total_gb = telemetry._ram_total_gb()
    return {"ram_total_gb": total_gb} if total_gb is not None else {}


def _disk(path: str) -> dict[str, object] | None:
    try:
        usage = shutil.disk_usage(path)
    except OSError:
        return None
    percent = round(usage.used / usage.total * 100, 1) if usage.total else None
    return {
        "path": path,
        "total_gb": round(usage.total / _GIB, 1),
        "used_gb": round(usage.used / _GIB, 1),
        "free_gb": round(usage.free / _GIB, 1),
        "used_percent": percent,
    }


def _load_average() -> list[float] | None:
    try:
        return list(os.getloadavg())
    except (OSError, AttributeError):
        return None


def gather_briefing() -> dict[str, object]:
    """Collect a full, read-only snapshot of the machine."""
    hardware = telemetry.gather_hardware()
    disks = [d for d in (_disk(os.path.abspath(os.sep)), _disk(str(_home()))) if d]
    data: dict[str, object] = {
        "time": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z"),
        "uptime": _humanize_uptime(_uptime_seconds()),
        "load_average": _load_average(),
        "memory": _memory(),
        "disks": disks,
        "hardware": hardware,
    }
    return data


def _home() -> str:
    try:
        from pathlib import Path

        return str(Path.home())
    except Exception:  # pragma: no cover
        return "~"


def render_snapshot(data: dict[str, object]) -> str:
    """Turn the snapshot into a compact text block for the model prompt."""
    hardware = data.get("hardware", {}) or {}
    memory = data.get("memory", {}) or {}
    lines = [
        f"Time: {data.get('time')}",
        f"OS: {hardware.get('os', '?')} ({hardware.get('machine', '?')})",
        f"CPU: {hardware.get('cpu', '?')} ({hardware.get('cores', '?')} cores)",
        f"GPU: {hardware.get('gpu', '?')}",
        f"App: {hardware.get('app', '?')}",
        f"Uptime: {data.get('uptime')}",
    ]
    load = data.get("load_average")
    if load:
        lines.append("Load average (1/5/15m): " + ", ".join(f"{value:.2f}" for value in load))
    if memory.get("ram_total_gb") is not None:
        used = memory.get("ram_used_percent")
        avail = memory.get("ram_available_gb")
        summary = f"RAM: {memory['ram_total_gb']} GiB total"
        if used is not None:
            summary += f", {used}% used"
        if avail is not None:
            summary += f", {avail} GiB available"
        lines.append(summary)
    if memory.get("swap_total_gb") is not None:
        lines.append(
            f"Swap: {memory['swap_total_gb']} GiB total, "
            f"{memory.get('swap_used_percent', '?')}% used"
        )
    for disk in data.get("disks", []):
        lines.append(
            f"Disk {disk['path']}: {disk['used_percent']}% used "
            f"({disk['used_gb']}/{disk['total_gb']} GiB, {disk['free_gb']} GiB free)"
        )
    return "\n".join(lines)


STATUS_INSTRUCTION = (
    "You are given a system snapshot. Reply with at most 2 short sentences "
    "total: first a one-line health verdict, then (only if something looks off) "
    "the single most important concern and one safe next step. Never repeat the "
    "numbers from the snapshot. Read-only: never claim to run commands, and put "
    "any command in a code block for the user to run manually."
)


def render_markdown(data: dict[str, object]) -> str:
    """Render the snapshot as a compact Markdown table for display."""
    hardware = data.get("hardware", {}) or {}
    memory = data.get("memory", {}) or {}
    rows: list[tuple[str, str]] = [
        ("OS", str(hardware.get("os", "?"))),
        ("CPU", f"{hardware.get('cpu', '?')} \u00b7 {hardware.get('cores', '?')} cores"),
        ("GPU", str(hardware.get("gpu", "?"))),
        ("Uptime", str(data.get("uptime", "?"))),
    ]
    load = data.get("load_average")
    if load:
        rows.append(("Load (1/5/15)", " / ".join(f"{value:.2f}" for value in load)))
    if memory.get("ram_total_gb") is not None:
        value = f"{memory.get('ram_used_percent', '?')}% used"
        if memory.get("ram_available_gb") is not None:
            value += f" \u00b7 {memory['ram_available_gb']} GiB free of {memory['ram_total_gb']} GiB"
        rows.append(("RAM", value))
    if memory.get("swap_total_gb") is not None:
        rows.append(
            ("Swap", f"{memory.get('swap_used_percent', '?')}% used of {memory['swap_total_gb']} GiB")
        )
    for disk in data.get("disks", []):
        rows.append(
            (
                f"Disk `{disk['path']}`",
                f"{disk['used_percent']}% used \u00b7 {disk['free_gb']} GiB free of {disk['total_gb']} GiB",
            )
        )
    lines = ["| Metric | Value |", "| --- | --- |"]
    lines += [f"| **{name}** | {value} |" for name, value in rows]
    return "\n".join(lines)

