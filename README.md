# ai-sys-buddy

**English** | [Polski](README.pl.md)

A lightweight, privacy-first terminal assistant with a friendly **sysadmin
buddy** personality. It talks to a local or remote [Ollama](https://ollama.com)
instance, helps you diagnose problems, teaches commands, and shows you
performance metrics for your models.

> **Read-only by design.** `ai-sys-buddy` never runs commands for you. The
> model only produces text and formats commands in frames; you review and run
> them yourself. Nothing is ever sent anywhere except your own Ollama server.

## Features

- **OS aware** — detects Linux and Windows and adapts its guidance.
- **Diagnostic mode** — `ai "why is my disk full?"`.
- **Encyclopedia mode** — `ai ?chmod` for a short, practical command guide.
- **Pipes & sudo** — `sudo journalctl -u pveproxy -n 50 | ai "what is going on?"`.
- **Interactive mode** — a small REPL with short-term conversation memory.
- **Verbose profiler** — `-v` shows load time, eval tokens and tokens/second.
- **Settings menu** — pick the model, URL, persona and UI backend with arrows.
- **Zero-dependency fallback** — a `standard` UI backend works without `rich`.

## Installation

### Prebuilt binaries

Download the latest `ai-linux` or `ai-windows.exe` from the
[Releases](https://github.com/brodatech-lab/ai-sys-buddy/releases) page, make it
executable (Linux) and put it on your `PATH`.

```bash
chmod +x ai-linux
mv ai-linux ~/.local/bin/ai
```

### From source (Python 3.10+)

```bash
git clone https://github.com/brodatech-lab/ai-sys-buddy.git
cd ai-sys-buddy
./install.sh
```

`install.sh` creates a virtual environment, installs the package in editable
mode and links the `ai` command into `~/.local/bin` so it works from anywhere.
If that directory is not on your `PATH`, the script prints the one line to add.

Prefer to do it manually? The package also exposes a console script:

```bash
python -m venv .venv && source .venv/bin/activate
pip install .
```

## Requirements

- A running Ollama server (`ollama serve`), by default at `http://127.0.0.1:11434`.
- At least one model pulled, e.g. `ollama pull llama3.2`. On first run the tool
  asks you to pick one from the installed list.

## Usage

```bash
ai                          # interactive mode
ai "how do I check disk usage on Linux?"
ai ?chmod                   # encyclopedia entry for chmod
ai s                        # settings menu (alias: ai settings)
ai help                     # help
sudo journalctl -u pveproxy -n 50 | ai "what is going on?"
ai -v "list open ports"     # verbose mode with performance metrics
```

### Options

| Option | Description |
| --- | --- |
| `-v`, `--verbose` | Show model performance metrics. |
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
| `telemetry_enabled` | `false` | Reserved for future opt-in hardware telemetry. |
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

### Building a standalone binary

```bash
pyinstaller --onefile --name ai --clean main.py
```

### Releases

Releases are fully automated. Push a tag and GitHub Actions builds the Windows
and Linux binaries and creates the release, using the notes from
[`CHANGELOG.md`](CHANGELOG.md):

```bash
git tag v0.1.0
git push origin v0.1.0
```

Local helper scripts live in the untracked `scripts/` directory.

## License

See the `LICENSE` file included in the repository.
