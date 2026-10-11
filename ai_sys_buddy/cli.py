"""Command line interface: argument parsing and mode dispatch."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .config import Config, UI_BACKENDS, config_path, load_config, save_config
from . import ollama, profiler, prompt, telemetry
from . import briefing
from .osenv import get_context
from .settings import run_settings, switch_model
from .ui import UI, get_ui

PROG = "ai"

_HELP = """\
{prog} - your terminal sysadmin buddy (read-only, private)

Usage:
  {prog}                       interactive chat mode
  {prog} <question>            ask a diagnostic question
  {prog} ?<command>            encyclopedia entry for a command (e.g. ?chmod)
  {prog} status                system status briefing
  {prog} perf [all]            benchmark the model (or all installed models)
  {prog} s | settings          open the settings menu
  {prog} help                  show this help

Options:
  -v, --verbose    show model performance metrics
      --think      enable model reasoning (thinking models only)
      --no-markdown  print plain text instead of rendered Markdown
      --theme NAME syntax highlighting theme (rich backend)
      --model NAME override the model for this run
      --url URL    override the Ollama URL for this run
      --backend B  UI backend: rich | standard
      --no-color   disable colors
      --config P   use an alternative config file
      --version    show version and exit

In interactive mode you can also use: status, perf, s (settings), ?<command>,
help and exit.

Pipes and sudo (Linux):
  sudo journalctl -u pveproxy -n 50 | {prog} "what is going on?"

Everything is read-only: {prog} never runs commands for you. It only shows
them so you can review and run them yourself.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=PROG, add_help=False, description=__doc__)
    parser.add_argument("-h", "--help", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--think", action="store_true", help="enable model reasoning")
    parser.add_argument("--no-markdown", action="store_true", help="print plain text, no markdown")
    parser.add_argument("--theme", help="syntax highlighting theme (rich backend)")
    parser.add_argument("--no-color", action="store_true")
    parser.add_argument("--model")
    parser.add_argument("--url")
    parser.add_argument("--backend", choices=UI_BACKENDS)
    parser.add_argument("--config", metavar="PATH")
    parser.add_argument("--version", action="store_true")
    parser.add_argument("prompt", nargs=argparse.REMAINDER)
    return parser


def read_piped_stdin() -> str:
    """Read piped stdin fully, or return "" when stdin is a terminal.

    We read to EOF (blocking) so real pipelines such as
    ``sudo journalctl -n 50 | ai "what is going on?"`` include the full upstream
    output. Even when sudo first waits for a password, the pipe stays open until
    the producer finishes, so blocking here is correct; a non-blocking peek
    would wrongly return before the data arrives.
    """
    if sys.stdin.isatty():
        return ""
    try:
        return sys.stdin.read()
    except (OSError, ValueError):
        return ""


def print_help(ui: UI, config: Config) -> None:
    ui.frame("help", _HELP.format(prog=config.persona_name or PROG))


def ensure_model(config: Config, ui: UI, config_file: Path | None = None) -> str | None:
    """Make sure a model is selected; ask the user on first run."""
    if config.model:
        return config.model
    try:
        models = ollama.list_models(config.ollama_url)
    except ollama.OllamaError as exc:
        ui.error(str(exc))
        ui.info("Start it with: ollama serve")
        return None

    if not models:
        ui.warning("No models installed.")
        ui.info("Pull one first, for example: ollama pull llama3.2")
        return None

    if len(models) == 1:
        config.model = models[0]
        save_config(config, config_file)
        ui.info(f"Using model: {models[0]}")
        return models[0]

    chosen = ui.select("Pick a model to use", models)
    if not chosen:
        return None
    switch_model(config, ui, chosen)
    save_config(config, config_file)
    ui.success(f"Saved model: {chosen}")
    return chosen


def _messages(config: Config, history: prompt.History, user_content: str) -> list[dict]:
    context = get_context()
    system_prompt = prompt.build_system_prompt(context, config.persona_name)
    return prompt.build_messages(system_prompt, history, user_content)


def stream_reply(config: Config, ui: UI, messages: list[dict]) -> tuple[str, dict | None]:
    """Stream the reply to the terminal and return (text, metrics).

    Thinking models (e.g. Qwen3) emit reasoning tokens before the answer; those
    are streamed dimmed so the tool never looks frozen, while only the actual
    answer content is collected and remembered.
    """
    parts: list[str] = []
    metrics: dict | None = None
    thinking_started = False
    answer_started = False
    ui.stream_start()
    try:
        for event in ollama.stream_chat(
            config.ollama_url, config.model, messages, think=config.think
        ):
            if event.thinking:
                ui.stream_write(event.thinking, style="dim")
                thinking_started = True
            if event.text:
                if thinking_started and not answer_started:
                    ui.stream_write("\n")
                ui.stream_write(event.text)
                answer_started = True
                parts.append(event.text)
            if event.done:
                metrics = event.metrics
    finally:
        ui.stream_end()
    return "".join(parts), metrics


def collect_reply(config: Config, ui: UI, messages: list[dict],
                  status=None) -> tuple[str, dict | None]:
    """Collect the reply while updating an optional status message.

    Used for framed Markdown output. ``status`` is the handle yielded by
    ``ui.status(...)``; when present it is updated from "Thinking..." to
    "Answering..." as the stream progresses.
    """
    parts: list[str] = []
    metrics: dict | None = None
    thinking_seen = False
    content_seen = False
    for event in ollama.stream_chat(
        config.ollama_url, config.model, messages, think=config.think
    ):
        if status is not None:
            if event.thinking and not thinking_seen:
                status.update("Thinking...")
                thinking_seen = True
            elif event.text and not content_seen:
                status.update("Answering...")
                content_seen = True
        parts.append(event.text)
        if event.done:
            metrics = event.metrics
    return "".join(parts), metrics


def show_telemetry(config: Config, ui: UI, metrics: dict | None) -> None:
    """Display the local hardware + performance telemetry in a panel."""
    hardware = telemetry.gather_hardware()
    report = telemetry.render_report(config.model, hardware, metrics)
    ui.render_markdown(report, title="telemetry")


def run_query(config: Config, ui: UI, history: prompt.History, question: str,
              verbose: bool, piped: str = "") -> None:
    if piped.strip():
        ui.info(f"Including {len(piped.splitlines())} line(s) from stdin")
    user_content = prompt.wrap_stdin(question, piped) if piped else question
    messages = _messages(config, history, user_content)
    try:
        if config.markdown:
            with ui.status("Consulting the model...") as status:
                reply, metrics = collect_reply(config, ui, messages, status=status)
            ui.render_markdown(reply.strip(), title=config.persona_name or "ai")
        else:
            reply, metrics = stream_reply(config, ui, messages)
    except ollama.OllamaError as exc:
        ui.error(str(exc))
        return
    history.add("user", user_content)
    history.add("assistant", reply)
    if config.telemetry_enabled:
        show_telemetry(config, ui, metrics)
    elif verbose:
        ui.print(profiler.format_metrics(metrics), "dim")


def run_encyclopedia(config: Config, ui: UI, command: str, verbose: bool) -> None:
    if not command.strip():
        ui.warning("Usage: ?<command>  (for example: ?chmod)")
        return
    context = get_context()
    system_prompt = prompt.build_system_prompt(context, config.persona_name)
    user_content = f"{prompt.ENCYCLOPEDIA_INSTRUCTION}\n\nCommand: {command.strip()}"
    messages = prompt.build_messages(system_prompt, [], user_content)
    try:
        with ui.status(f"Looking up {command.strip()}...") as status:
            reply, metrics = collect_reply(config, ui, messages, status=status)
    except ollama.OllamaError as exc:
        ui.error(str(exc))
        return
    ui.render_markdown(reply.strip(), title=f"?{command.strip()}")
    if config.telemetry_enabled:
        show_telemetry(config, ui, metrics)
    elif verbose:
        ui.print(profiler.format_metrics(metrics), "dim")


def run_perf(config: Config, ui: UI, all_models: bool = False) -> None:
    """Benchmark the selected model (or every installed model) with a fixed prompt."""
    if all_models:
        try:
            models = ollama.list_models(config.ollama_url)
        except ollama.OllamaError as exc:
            ui.error(str(exc))
            return
        if not models:
            ui.warning("No models installed. Try: ollama pull llama3.2")
            return
    else:
        if not config.model:
            ui.warning("No model selected. Use 'ai s' first.")
            return
        models = [config.model]

    context = get_context()
    system_prompt = prompt.build_system_prompt(context, config.persona_name)
    messages = prompt.build_messages(system_prompt, [], "Reply with exactly: ok")

    rows: list[str] = ["| Model | Load (s) | Eval tok | Speed (tok/s) |", "| --- | --- | --- | --- |"]
    for model in models:
        try:
            with ui.status(f"Benchmarking {model}...") as status:
                _, metrics = collect_reply(config, ui, messages, status=status)
            record = telemetry.build_record(model, metrics)
            load = record.get("load_duration_s")
            speed = record.get("tokens_per_second")
            rows.append(
                f"| `{model}` | {load if load is not None else '?'} "
                f"| {record.get('eval_count', '?')} | {speed if speed is not None else '?'} |"
            )
        except ollama.OllamaError as exc:
            rows.append(f"| `{model}` | error | - | {str(exc)[:40]} |")

    hardware = telemetry.gather_hardware()
    header = (
        f"**{hardware.get('cpu', '?')}** - {hardware.get('cores', '?')} cores, "
        f"{hardware.get('ram_gb', '?')} GiB RAM\n"
    )
    ui.render_markdown(header + "\n".join(rows), title="ai perf")


def run_status(config: Config, ui: UI, verbose: bool = False) -> None:
    """Show a friendly system status briefing (``ai status``)."""
    data = briefing.gather_briefing()
    snapshot = briefing.render_snapshot(data)
    table = briefing.render_markdown(data)
    if not config.model:
        # No model selected yet: show the raw snapshot instead.
        ui.render_markdown(table, title="status")
        return
    context = get_context()
    system_prompt = prompt.build_system_prompt(context, config.persona_name)
    user_content = f"{briefing.STATUS_INSTRUCTION}\n\n{snapshot}"
    messages = prompt.build_messages(system_prompt, [], user_content)
    try:
        with ui.status("Checking system status...") as status:
            reply, metrics = collect_reply(config, ui, messages, status=status)
    except ollama.OllamaError as exc:
        ui.error(str(exc))
        ui.render_markdown(table, title="status")
        return
    body = table if not reply.strip() else f"{table}\n\n{reply.strip()}"
    ui.render_markdown(body, title="status")
    if config.telemetry_enabled:
        show_telemetry(config, ui, metrics)
    elif verbose:
        ui.print(profiler.format_metrics(metrics), "dim")


def run_perf(config: Config, ui: UI, all_models: bool = False) -> None:
    """Benchmark the selected model (or every installed model) with a fixed prompt."""
    if all_models:
        try:
            models = ollama.list_models(config.ollama_url)
        except ollama.OllamaError as exc:
            ui.error(str(exc))
            return
        if not models:
            ui.warning("No models installed. Try: ollama pull llama3.2")
            return
    else:
        if not config.model:
            ui.warning("No model selected. Use 'ai s' first.")
            return
        models = [config.model]

    context = get_context()
    system_prompt = prompt.build_system_prompt(context, config.persona_name)
    messages = prompt.build_messages(system_prompt, [], "Reply with exactly: ok")

    rows: list[str] = ["| Model | Load (s) | Eval tok | Speed (tok/s) |", "| --- | --- | --- | --- |"]
    for model in models:
        try:
            with ui.status(f"Benchmarking {model}...") as status:
                _, metrics = collect_reply(config, ui, messages, status=status)
            record = telemetry.build_record(model, metrics)
            load = record.get("load_duration_s")
            speed = record.get("tokens_per_second")
            rows.append(
                f"| `{model}` | {load if load is not None else '?'} "
                f"| {record.get('eval_count', '?')} | {speed if speed is not None else '?'} |"
            )
        except ollama.OllamaError as exc:
            rows.append(f"| `{model}` | error | - | {str(exc)[:40]} |")

    hardware = telemetry.gather_hardware()
    header = (
        f"**{hardware.get('cpu', '?')}** - {hardware.get('cores', '?')} cores, "
        f"{hardware.get('ram_gb', '?')} GiB RAM\n"
    )
    ui.render_markdown(header + "\n".join(rows), title="ai perf")


def interactive_loop(config: Config, ui: UI, verbose: bool,
                     config_file: Path | None = None) -> None:
    context = get_context()
    ui.banner(
        f"{config.persona_name} - your sysadmin buddy",
        f"{context.os_name} | model: {config.model} | type 'help' or 'exit'",
    )
    history = prompt.History(size=config.history_size)
    while True:
        try:
            line = ui.text("you >")
        except (EOFError, KeyboardInterrupt):
            ui.print()
            return
        line = (line or "").strip()
        if not line:
            continue
        lowered = line.lower()
        if lowered in ("exit", "quit", ":q"):
            return
        if lowered in ("help", "?"):
            print_help(ui, config)
            continue
        if lowered in ("s", "settings", "config"):
            run_settings(config, ui, config_file)
            continue
        if lowered in ("perf", "perf all", "bench"):
            run_perf(config, ui, all_models=(lowered != "perf"))
            continue
        if lowered == "status":
            run_status(config, ui, verbose)
            continue
        if line.startswith("?"):
            run_encyclopedia(config, ui, line[1:], verbose)
            continue
        run_query(config, ui, history, line, verbose)


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(f"{PROG} (ai-sys-buddy) {__version__}")
        return 0

    config_file = Path(args.config) if args.config else None
    config = load_config(config_file)
    if args.url:
        config.ollama_url = args.url
    if args.model:
        config.model = args.model
    if args.backend:
        config.ui_backend = args.backend
    if args.no_color:
        config.no_color = True
    if args.think:
        config.think = True
    if args.no_markdown:
        config.markdown = False
    if args.theme:
        config.code_theme = args.theme

    ui = get_ui(config)
    verbose = args.verbose or config.verbose_default
    tokens = list(args.prompt)

    if args.help or (tokens and tokens[0].lower() in ("help", "-h", "--help")):
        print_help(ui, config)
        return 0

    # Settings must not consume a pipe; handle it before reading stdin.
    if tokens and tokens[0].lower() in ("s", "settings", "config"):
        run_settings(config, ui, config_file)
        return 0

    if tokens and tokens[0].lower() in ("perf", "bench"):
        all_models = any(part.lower() in ("all", "--all") for part in tokens[1:])
        run_perf(config, ui, all_models=all_models)
        return 0

    if len(tokens) == 1 and tokens[0].lower() == "status":
        ensure_model(config, ui, config_file)
        run_status(config, ui, verbose)
        return 0

    piped = read_piped_stdin()

    if not tokens and not piped:
        if ensure_model(config, ui, config_file) is None:
            return 1
        interactive_loop(config, ui, verbose, config_file)
        return 0

    # Piped input with no explicit question gets a sensible default prompt.
    if not tokens and piped:
        question = "What is going on in this output?"
    else:
        question = " ".join(tokens).strip()

    lowered = question.lower()
    if lowered in ("s", "settings", "config"):
        run_settings(config, ui, config_file)
        return 0
    if question.startswith("?") or (tokens and tokens[0] == "?"):
        if tokens and tokens[0] == "?":
            command = " ".join(tokens[1:])
        else:
            command = question[1:]
        if ensure_model(config, ui, config_file) is None:
            return 1
        run_encyclopedia(config, ui, command, verbose)
        return 0

    if ensure_model(config, ui, config_file) is None:
        return 1
    history = prompt.History(size=config.history_size)
    run_query(config, ui, history, question, verbose, piped)
    return 0
