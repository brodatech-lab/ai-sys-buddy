#!/usr/bin/env bash
# Installer for ai-sys-buddy (Linux/macOS).
#
# Creates a virtual environment, installs the package in editable mode and
# links the `ai` command into ~/.local/bin so it works from anywhere.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$REPO_DIR/.venv"
BIN_DIR="${HOME}/.local/bin"
LINK="$BIN_DIR/ai"
PYTHON="${PYTHON:-python3}"

echo "Installing ai-sys-buddy from $REPO_DIR"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "error: python3 not found. Install Python 3.10+ first." >&2
  exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment in $VENV_DIR ..."
  "$PYTHON" -m venv "$VENV_DIR"
fi

echo "Installing package (editable) ..."
"$VENV_DIR/bin/python" -m pip install --upgrade pip >/dev/null
"$VENV_DIR/bin/python" -m pip install --editable "$REPO_DIR"

mkdir -p "$BIN_DIR"
ln -sfn "$VENV_DIR/bin/ai" "$LINK"
echo "Linked $LINK -> $VENV_DIR/bin/ai"

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *)
    echo
    echo "NOTE: $BIN_DIR is not on your PATH."
    echo "Add this line to ~/.profile (or ~/.bashrc) and reopen your shell:"
    echo "  export PATH=\"$BIN_DIR:\$PATH\""
    ;;
esac

echo
echo "Done. Try: ai \"hello\""
