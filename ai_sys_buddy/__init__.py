"""ai-sys-buddy - a friendly, privacy-first system buddy for the terminal.

The package only ever produces text: it never executes commands suggested by
the model. Any command shown to the user is meant to be reviewed and run
manually.
"""

__all__ = ["__version__", "APP_NAME", "DEFAULT_PERSONA"]

# Single source of truth for the version. It must match the git tag and the
# matching entry in CHANGELOG.md.
__version__ = "0.1.0"

APP_NAME = "ai-sys-buddy"

# Default buddy persona name. Users may switch it to "buddy" in settings.
DEFAULT_PERSONA = "ai"
