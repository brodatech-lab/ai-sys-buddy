#!/usr/bin/env python3
"""Extract a release body from CHANGELOG.md for a given version.

Usage:
    extract_changelog.py <version> [changelog_path]

Prints the "What's New", "Fixed" and "Changed" sections of the requested
version, skipping empty sections. Exits with code 1 when the version is not
found.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Section titles we publish, in the order they should appear.
WANTED = ("What's New", "Fixed", "Changed")

_VERSION_RE = re.compile(r"^##\s+\[(?P<version>[^\]]+)\]")
_SECTION_RE = re.compile(r"^###\s+(?P<title>.+?)\s*$")
_LINK_REF_RE = re.compile(r"^\[[^\]]+\]:\s")


def parse_sections(text: str) -> dict[str, dict[str, str]]:
    """Return {version: {section_title: body}} for the whole changelog."""
    result: dict[str, dict[str, str]] = {}
    current_version: str | None = None
    current_section: str | None = None
    buffer: list[str] = []

    def flush() -> None:
        if current_version and current_section:
            result.setdefault(current_version, {})[current_section] = "\n".join(buffer).strip()

    for line in text.splitlines():
        version_match = _VERSION_RE.match(line)
        if version_match:
            flush()
            buffer = []
            current_version = version_match.group("version").strip()
            current_section = None
            continue
        section_match = _SECTION_RE.match(line)
        if section_match:
            flush()
            buffer = []
            current_section = section_match.group("title").strip()
            continue
        if _LINK_REF_RE.match(line):
            # Link references are not part of any section body.
            flush()
            buffer = []
            current_section = None
            current_version = None
            continue
        if current_version and current_section is not None:
            buffer.append(line)
    flush()
    return result


def build_body(sections: dict[str, str]) -> str:
    parts: list[str] = []
    for title in WANTED:
        body = sections.get(title)
        if body:
            parts.append(f"### {title}\n{body}")
    return "\n\n".join(parts).strip()


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: extract_changelog.py <version> [changelog_path]", file=sys.stderr)
        return 2
    version = argv[0].lstrip("v")
    path = Path(argv[1]) if len(argv) > 1 else Path("CHANGELOG.md")
    if not path.exists():
        print(f"changelog not found: {path}", file=sys.stderr)
        return 1
    sections = parse_sections(path.read_text(encoding="utf-8"))
    if version not in sections:
        print(f"version {version} not found in {path}", file=sys.stderr)
        return 1
    body = build_body(sections[version])
    if not body:
        body = f"Release {version}."
    print(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
