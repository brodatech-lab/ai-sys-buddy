"""Command line interface: argument parsing and mode dispatch."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import __version__
from .config import Config, UI_BACKENDS, config_path, load_config, save_config
from . import ollama, profiler, prompt
from .osenv import get_context
from .settings import run_settings, switch_model
from .ui import UI, get_ui

PROG = "ai"

_HELP = """\
{prog} - your terminal sysadmin buddy (read-only, private)

Usage:
  {prog}                       interactive mode
  {prog} <question>            ask a diagnostic question
  {prog} ?<command>            encyclopedia entry for a command (e.g. ?chmod)
  {prog} s | settings          open the settings menu
  {prog} help                  show this help

Options:
  -v, --verbose    show model performance metrics
      --think      enable model reasoning (thinking models only)
      --model NAME override the model for this run
      --url URL    override the Ollama URL for this run
      --backend B  UI backend: rich | standard
      --no-color   disable colors
      --config P   use an alternative config file
      --version    show version and exit

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
    parser.add_argument("--no-color", action="store_true")
    parser.add_argument("--model")
    parser.add_argument("--url")
    parser.add_argument("--backend", choices=UI_BACKENDS)
    parser.add_argument("--config", metavar="PATH")
    parser.add_argument("--version", action="store_true")
    parser.add_argument("prompt", nargs=argparse.REMAINDER)
    return parser


def read_piped_stdin() -> str:
    """Return piped stdin content, or an empty string when interactive.

    Uses a non-blocking readiness check on POSIX so an open-but-empty stdin
    never makes the process hang waiting for input that will not arrive.
    """
    if sys.stdin.isatty():
        return ""
    try:
        if os.name == "posix":
            import select

            ready, _, _ = select.select([sys.stdin], [], [], 0.0)
            if not ready:
                return ""
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


def collect_reply(config: Config, ui: UI, messages: list[dict]) -> tuple[str, dict | None]:
    """Collect the reply without printing (used for framed output)."""
    parts: list[str] = []
    metrics: dict | None = None
    for event in ollama.stream_chat(
        config.ollama_url, config.model, messages, think=config.think
    ):
        parts.append(event.text)
        if event.done:
            metrics = event.metrics
    return "".join(parts), metrics


def run_query(config: Config, ui: UI, history: prompt.History, question: str,
              verbose: bool, piped: str = "") -> None:
    user_content = prompt.wrap_stdin(question, piped) if piped else question
    messages = _messages(config, history, user_content)
    try:
        reply, metrics = stream_reply(config, ui, messages)
    except ollama.OllamaError as exc:
        ui.error(str(exc))
        return
    history.add("user", user_content)
    history.add("assistant", reply)
    if verbose:
        ui.print(profiler.format_metrics(metrics), "dim")


def run_encyclopedia(config: Config, ui: UI, command: str, verbose: bool) -> None:
    if not command.strip():
        ui.warning("Usage: ?<command>  (for example: ?chmod)")
        return
    context = get_context()
    system_prompt = prompt.build_system_prompt(context, config.persona_name)
    user_content = f"{prompt.ENCYCLOPEDIA_INSTRUCTION}\n\nCommand: {command.strip()}"
    messages = prompt.build_messages(system_prompt, [], user_content)
    ui.info(f"Looking up: {command.strip()}")
    try:
        reply, metrics = collect_reply(config, ui, messages)
    except ollama.OllamaError as exc:
        ui.error(str(exc))
        return
    ui.frame(f"?{command.strip()}", reply.strip())
    if verbose:
        ui.print(profiler.format_metrics(metrics), "dim")


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
