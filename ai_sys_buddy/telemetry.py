"""Local hardware telemetry and performance reporting (Phase 6).

Everything here runs locally and read-only. Hardware is read from the OS
(``/proc``, ``sysfs``); external commands are only used as a last-resort
fallback to name a GPU and never involve any user input. Nothing is uploaded.

The opt-in Supabase upload is intentionally not part of this module yet.
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from datetime import datetime, timezone

from . import __version__

_NS_PER_S = 1_000_000_000


def _cpu_model() -> str:
    """Best-effort CPU name without running external commands."""
    if sys.platform.startswith("linux"):
        try:
            with open("/proc/cpuinfo", "r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    if line.lower().startswith("model name"):
                        return line.split(":", 1)[1].strip()
        except OSError:
            pass
    name = platform.processor()
    if name and name not in ("x86_64", "AMD64", "aarch64"):
        return name.strip()
    return platform.machine() or "unknown"


def _ram_total_gb() -> float | None:
    """Total physical memory in GiB, without external commands."""
    if sys.platform.startswith("linux"):
        try:
            with open("/proc/meminfo", "r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    if line.startswith("MemTotal:"):
                        kb = int(line.split()[1])
                        return round(kb / 1024 / 1024, 1)
        except (OSError, ValueError, IndexError):
            return None
    if sys.platform.startswith("win"):
        try:
            import ctypes

            class _MemoryStatusEx(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            status = _MemoryStatusEx()
            status.dwLength = ctypes.sizeof(_MemoryStatusEx)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return round(status.ullTotalPhys / 1024**3, 1)
        except Exception:  # pragma: no cover - Windows only
            return None
    return None


def _gpus_from_proc() -> list[str]:
    """NVIDIA GPU names from /proc without running anything."""
    models: list[str] = []
    base = "/proc/driver/nvidia/gpus"
    try:
        entries = os.listdir(base)
    except OSError:
        return models
    for entry in entries:
        info_path = os.path.join(base, entry, "information")
        try:
            with open(info_path, "r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    if line.lower().startswith("model:"):
                        models.append(line.split(":", 1)[1].strip())
        except OSError:
            continue
    return models


def _gpus_from_command() -> list[str]:
    """Last-resort GPU names via fixed, local commands (no user input)."""
    commands: list[list[str]] = []
    if sys.platform.startswith("linux"):
        commands.append(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"]
        )
    elif sys.platform.startswith("win"):
        commands.append(["wmic", "path", "win32_VideoController", "get", "name"])
    for command in commands:
        try:
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=5, check=False
            )
        except (OSError, subprocess.SubprocessError):
            continue
        if result.returncode != 0:
            continue
        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        lines = [line for line in lines if line.lower() != "name"]
        if lines:
            return lines
    return []


def _gpu_info() -> str:
    models = _gpus_from_proc() or _gpus_from_command()
    if not models:
        return "?"
    unique: list[str] = []
    for model in models:
        if model not in unique:
            unique.append(model)
    label = "; ".join(unique)
    if len(models) > len(unique):
        label += f" (x{len(models)})"
    return label


def gather_hardware() -> dict[str, str]:
    """Return a small, anonymous hardware/OS summary."""
    ram = _ram_total_gb()
    return {
        "os": f"{platform.system()} {platform.release()}",
        "machine": platform.machine(),
        "cpu": _cpu_model(),
        "cores": str(os.cpu_count() or "?"),
        "ram_gb": f"{ram}" if ram is not None else "?",
        "gpu": _gpu_info(),
        "python": platform.python_version(),
        "app": __version__,
    }


def _seconds(value_ns: int | None) -> float | None:
    if value_ns is None:
        return None
    return value_ns / _NS_PER_S


def build_record(model: str, metrics: dict | None, hardware: dict | None = None) -> dict:
    """Build an anonymous telemetry record (never leaves the machine by default)."""
    hardware = hardware or gather_hardware()
    record: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": model,
        **hardware,
    }
    if metrics:
        eval_count = metrics.get("eval_count")
        eval_duration = metrics.get("eval_duration")
        record["load_duration_s"] = _fmt_seconds(_seconds(metrics.get("load_duration")))
        record["eval_count"] = eval_count
        record["eval_duration_s"] = _fmt_seconds(_seconds(eval_duration))
        record["prompt_eval_count"] = metrics.get("prompt_eval_count")
        record["prompt_eval_duration_s"] = _fmt_seconds(_seconds(metrics.get("prompt_eval_duration")))
        record["total_duration_s"] = _fmt_seconds(_seconds(metrics.get("total_duration")))
        if eval_count and eval_duration:
            record["tokens_per_second"] = round(eval_count / (eval_duration / _NS_PER_S), 2)
    return record


def _fmt_seconds(value: float | None) -> float | None:
    return round(value, 3) if value is not None else None


def render_report(model: str, hardware: dict, metrics: dict | None) -> str:
    """Render the telemetry as a Markdown report (hardware + full performance)."""
    lines = [
        "**Hardware**",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Model | `{model}` |",
        f"| OS | {hardware.get('os', '?')} |",
        f"| CPU | {hardware.get('cpu', '?')} |",
        f"| Cores | {hardware.get('cores', '?')} |",
        f"| RAM | {hardware.get('ram_gb', '?')} GiB |",
        f"| GPU | {hardware.get('gpu', '?')} |",
        f"| App | {hardware.get('app', '?')} |",
    ]
    if metrics:
        speed = None
        eval_count = metrics.get("eval_count")
        eval_duration = metrics.get("eval_duration")
        if eval_count and eval_duration:
            speed = eval_count / (eval_duration / _NS_PER_S)
        rows: list[tuple[str, str]] = [
            ("Load duration", _fmt_seconds(_seconds(metrics.get("load_duration"))), " s"),
            ("Eval tokens", eval_count, ""),
            ("Eval duration", _fmt_seconds(_seconds(eval_duration)), " s"),
            ("Speed", round(speed, 2) if speed is not None else None, " tok/s"),
            ("Prompt tokens", metrics.get("prompt_eval_count"), ""),
            ("Prompt eval", _fmt_seconds(_seconds(metrics.get("prompt_eval_duration"))), " s"),
            ("Total duration", _fmt_seconds(_seconds(metrics.get("total_duration"))), " s"),
        ]
        lines.append("")
        lines.append("**Performance**")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("| --- | --- |")
        for name, value, unit in rows:
            if value is None:
                continue
            lines.append(f"| {name} | {value}{unit} |")
    return "\n".join(lines)
