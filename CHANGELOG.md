# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Releases are cut automatically: pushing a tag like `v0.1.0` triggers the
release workflow, which publishes the "What's New", "Fixed" and "Changed"
sections below as the GitHub release notes.

## [Unreleased]

## [0.1.3] - 2026-10-10

### What's New
- Answers and command lookups are rendered as Markdown in a framed panel:
  headings, lists, emphasis and syntax-highlighted code blocks.
- A spinner is shown while the model generates ("Thinking..." then
  "Answering...").
- The code theme is selectable via `--theme NAME` or in settings; a
  `--no-markdown` flag (and `markdown = false`) keeps the previous plain-text
  streaming output.
- Local hardware telemetry: enable it in settings and a `telemetry` panel
  (CPU, cores, RAM, GPU, and full metrics - load/eval durations, tokens and
  tokens/second) is shown after each answer. It stays on the machine, no upload.
- `ai perf` benchmarks the selected model, and `ai perf all` every installed
  model, printing a comparison table (load time, tokens, tokens/second).

### Fixed
- Markdown answers are now word-wrapped to the terminal width instead of being
  cropped at the right edge.
- Piped input is now read fully (blocking) so pipelines like
  `sudo journalctl -n 50 | ai "what is going on?"` include the upstream output
  instead of being sent empty. The number of included lines is shown, and very
  large inputs are truncated from the front.
- Settings actions that print a result (such as "Test Ollama connection") now
  pause so the message is visible before the panel redraws.

### Changed
- Diagnostic answers are now formatted with Markdown inside a panel by default
  instead of being streamed as plain text.
- Settings menu reordered: "Test Ollama connection" under the Ollama URL,
  "Manage loaded models" under Model, and "Code theme" under the UI backend.
- Documentation reworked (install split per OS, expanded usage) and the Windows
  installer no longer needs a GitHub token.

## [0.1.2] - 2026-10-10

### What's New
- Windows installer `install.ps1`: installs `ai-sys-buddy.exe`, creates an `ai`
  command, adds it to the user PATH and configures your Ollama URL and model.
  The installer is also attached to every release.

### Fixed
- The config file is now read tolerantly of a UTF-8 BOM, so configs written or
  edited by Windows tools are accepted.

### Changed
- Nothing yet.

## [0.1.1] - 2026-10-10

### What's New
- The settings panel can now view and unload currently loaded models, and
  switching models offers to free the previous one so two models never stay
  loaded at once.
- Reasoning can be toggled: `--think` on the command line, or the
  "Reasoning (think)" switch in settings.

### Fixed
- Thinking models (e.g. Qwen3) now answer directly: reasoning is disabled by
  default via the Ollama `think` flag, so the model no longer appears to hang
  before its answer.
- Thinking models (e.g. Qwen3) no longer appear to hang: reasoning tokens sent
  in `message.thinking` are now streamed (dimmed) instead of being ignored.

### Changed
- `--config` is now honored when saving, and opening the settings panel no
  longer consumes piped stdin.
- Release binaries are now named `ai-sys-buddy` (Linux) and `ai-sys-buddy.exe`
  (Windows).

## [0.1.0] - 2026-10-10

### What's New
- First public release of `ai-sys-buddy`, a read-only terminal sysadmin buddy.
- Operating system detection for Linux and Windows with platform-aware hints.
- Diagnostic question mode: `ai "<question>"`.
- Encyclopedia mode for commands: `ai ?chmod`.
- Pipe and sudo support, e.g. `sudo journalctl -u pveproxy -n 50 | ai "what is going on?"`.
- Interactive mode with short-term FIFO conversation memory.
- Verbose profiler (`-v`) showing load time, eval tokens and tokens/second.
- Arrow-key settings menu built on questionary, with a zero-dependency
  `standard` UI backend as a fallback.

### Fixed
- Non-blocking stdin detection so the tool never hangs on an open-but-empty pipe.

### Changed
- Nothing yet.

[Unreleased]: https://github.com/brodatech-lab/ai-sys-buddy/compare/v0.1.3...HEAD
[0.1.3]: https://github.com/brodatech-lab/ai-sys-buddy/releases/tag/v0.1.3
[0.1.2]: https://github.com/brodatech-lab/ai-sys-buddy/releases/tag/v0.1.2
[0.1.1]: https://github.com/brodatech-lab/ai-sys-buddy/releases/tag/v0.1.1
[0.1.0]: https://github.com/brodatech-lab/ai-sys-buddy/releases/tag/v0.1.0
