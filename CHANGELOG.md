# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Releases are cut automatically: pushing a tag like `v0.1.0` triggers the
release workflow, which publishes the "What's New", "Fixed" and "Changed"
sections below as the GitHub release notes.

## [Unreleased]

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

[Unreleased]: https://github.com/brodatech-lab/ai-sys-buddy/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/brodatech-lab/ai-sys-buddy/releases/tag/v0.1.0
