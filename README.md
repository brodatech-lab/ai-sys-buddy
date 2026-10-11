# ai-sys-buddy

**English** | [Polski](README.pl.md)

A lightweight, privacy-first terminal assistant with a friendly **sysadmin
buddy** personality. Purpose-built to run on older hardware with small, fast AI
models, it talks to a local or remote [Ollama](https://ollama.com) instance,
helps you diagnose problems, teaches commands, and shows you performance metrics
for your models.

> **Built for modest hardware.** Older machines with small, fast AI models are
> the sweet spot; with integrated graphics (or no GPU) the computation is simply
> done by the CPU.

> **Read-only by design.** `ai-sys-buddy` never runs commands for you. The
> model only produces text and formats commands in frames; you review and run
> them yourself. Nothing is ever sent anywhere except your own Ollama server.

## Features

- **OS aware** — detects Linux and Windows and adapts its guidance.
- **Diagnostic mode** — `ai why is my disk full?`
- **Encyclopedia mode** — `ai ?chmod` for a short, practical command guide.
- **Pipes & sudo** — `sudo journalctl -n 50 | ai what is going on?`
- **Interactive chat** — just run `ai` and press Enter; a small REPL with
  short-term conversation memory.
- **Metrics** — `-v` shows load time, eval tokens and tokens/second.
- **Telemetry & benchmark** — `ai perf` compares models; an optional local
  hardware + performance panel is shown when enabled.
- **Settings menu** — pick the model, URL, persona, theme and backend with arrows.
- **Runs on modest hardware** — purpose-built for older machines and small, fast
  AI models. With integrated graphics (or no GPU) the computation is simply done
  by the CPU.
- **Zero-dependency fallback** — a `standard` UI backend works without `rich`.

## Requirements

- A running Ollama server (`ollama serve`), by default at `http://127.0.0.1:11434`.
- At least one model pulled, e.g. `ollama pull llama3.2`. On first run the tool
  asks you to pick one from the installed list.

## Installation

### Linux

Download the latest `ai-sys-buddy` binary from the
[Releases](https://github.com/brodatech-lab/ai-sys-buddy/releases) page, then make
it executable and put it on your `PATH`:

```bash
chmod +x ai-sys-buddy
mv ai-sys-buddy ~/.local/bin/ai
```

Or install from source (Python 3.10+):

```bash
git clone https://github.com/brodatech-lab/ai-sys-buddy.git
cd ai-sys-buddy
./install.sh
```

`install.sh` creates a virtual environment, installs the package in editable
mode and links the `ai` command into `~/.local/bin`. If that directory is not on
your `PATH`, the script prints the one line to add.

Prefer to do it manually?

```bash
python -m venv .venv && source .venv/bin/activate
pip install .
```

### Windows

Install with a single PowerShell command:

```powershell
irm https://raw.githubusercontent.com/brodatech-lab/ai-sys-buddy/main/install.ps1 | iex
```

Or download `install.ps1` and run it (optionally place `ai-sys-buddy.exe` next
to it to install offline):

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

The installer copies `ai-sys-buddy.exe` to
`%LOCALAPPDATA%\Programs\ai-sys-buddy`, creates an `ai` command, adds it to your
user `PATH`, and asks for your Ollama URL and model. Open a new terminal
afterwards, then use `ai` exactly like on Linux.

To remove it again:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Uninstall
```

## Usage

### Ask a question

```bash
ai how do I check disk usage on Linux?
ai why is my service not starting?
```

### Look up a command

```bash
ai ?chmod
ai ?systemctl
```

### Analyse piped output (Linux)

```bash
sudo journalctl -u pveproxy -n 50 | ai what is going on?
cat error.log | ai why does this fail?
```

### Interactive mode

Type `ai` and press Enter to enter chat mode:

```bash
ai
```

Then type your questions. Inside the prompt you can use `?cmd` for command
lookups, `perf` to benchmark, `s` for settings, and `exit` to quit.

### Settings, benchmark and help

```bash
ai s            # settings menu (alias: ai settings)
ai perf         # benchmark the current model
ai perf all     # benchmark every installed model
ai help         # help
```

### Options

| Option | Description |
| --- | --- |
| `-v`, `--verbose` | Show model performance metrics. |
| `--think` | Enable model reasoning (thinking models only). |
| `--no-markdown` | Print plain text instead of rendered Markdown. |
| `--theme NAME` | Syntax highlighting theme (rich backend). |
| `--model NAME` | Override the model for this run. |
| `--url URL` | Override the Ollama URL for this run. |
| `--backend rich\|standard` | Choose the UI backend. |
| `--no-color` | Disable colors. |
| `--config PATH` | Use an alternative config file. |
| `--version` | Show the version and exit. |

## Configuration

Stored per user:

- Linux: `~/.config/ai-sys-buddy/config.json`
- Windows: `%APPDATA%\ai-sys-buddy\config.json`

| Key | Default | Meaning |
| --- | --- | --- |
| `ollama_url` | `http://127.0.0.1:11434` | Ollama base URL. |
| `model` | _(empty)_ | Selected model; chosen on first run. |
| `persona_name` | `ai` | Buddy name shown in prompts (can be `buddy`). |
| `ui_backend` | `rich` | `rich` or `standard`. |
| `history_size` | `4` | Conversation exchanges kept in memory (FIFO). |
| `verbose_default` | `false` | Always show metrics. |
| `think` | `false` | Enable model reasoning (thinking models only). |
| `markdown` | `true` | Render answers as Markdown in a panel. |
| `code_theme` | `monokai` | Syntax highlighting theme for code blocks. |
| `telemetry_enabled` | `false` | Show the local hardware + performance telemetry panel after each answer. |
| `no_color` | `false` | Disable colors. |

## Privacy & security

- No telemetry, no analytics, no external calls other than your Ollama URL.
- The tool cannot and will not execute commands. Everything is advisory.
- Suggested commands are shown for manual review; never pipe them to a shell.

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install . pyinstaller
python -m unittest discover -s tests
```

Building a standalone binary:

```bash
pyinstaller --onefile --name ai-sys-buddy --clean main.py
```

## License

See the `LICENSE` file included in the repository.
