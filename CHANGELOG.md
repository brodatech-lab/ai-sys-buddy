# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Releases are cut automatically: pushing a tag like `v0.1.0` triggers the
release workflow, which publishes the "What's New", "Fixed" and "Changed"
sections below as the GitHub release notes.

## [Unreleased]

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

[Unreleased]: https://github.com/brodatech-lab/ai-sys-buddy/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/brodatech-lab/ai-sys-buddy/releases/tag/v0.1.1
[0.1.0]: https://github.com/brodatech-lab/ai-sys-buddy/releases/tag/v0.1.0
