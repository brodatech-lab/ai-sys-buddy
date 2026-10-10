"""Formatting of Ollama performance metrics for verbose mode."""

from __future__ import annotations

_NS_PER_S = 1_000_000_000


def _seconds(value_ns: int | None) -> float | None:
    if value_ns is None:
        return None
    return value_ns / _NS_PER_S


def tokens_per_second(metrics: dict | None) -> float | None:
    """Compute the generation speed (tokens/s) from raw metrics."""
    if not metrics:
        return None
    eval_count = metrics.get("eval_count")
    eval_duration = metrics.get("eval_duration")
    if not eval_count or not eval_duration:
        return None
    return eval_count / (eval_duration / _NS_PER_S)


def format_metrics(metrics: dict | None) -> str:
    """Render a compact, human readable performance report."""
    if not metrics:
        return "Performance: no metrics returned by the server."

    load = _seconds(metrics.get("load_duration"))
    eval_dur = _seconds(metrics.get("eval_duration"))
    prompt_dur = _seconds(metrics.get("prompt_eval_duration"))
    total = _seconds(metrics.get("total_duration"))
    eval_count = metrics.get("eval_count")
    prompt_count = metrics.get("prompt_eval_count")
    speed = tokens_per_second(metrics)

    lines = ["Performance:"]
    if load is not None:
        lines.append(f"  Load duration : {load:.3f} s")
    if eval_count is not None:
        lines.append(f"  Eval tokens   : {eval_count}")
    if eval_dur is not None:
        lines.append(f"  Eval duration : {eval_dur:.3f} s")
    if speed is not None:
        lines.append(f"  Speed         : {speed:.2f} tok/s")
    if prompt_count is not None:
        lines.append(f"  Prompt tokens : {prompt_count}")
    if prompt_dur is not None:
        lines.append(f"  Prompt eval   : {prompt_dur:.3f} s")
    if total is not None:
        lines.append(f"  Total duration: {total:.3f} s")
    return "\n".join(lines)
