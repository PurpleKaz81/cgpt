import os
from contextlib import suppress

from cgpt.cli.parser import build_parser
from cgpt.commands.extract_index import cmd_extract
from cgpt.core.color import set_cli_color_override
from cgpt.core.env import _parse_env_bool

# Enable line-editing for interactive `input()` (arrow keys, history, tab completion).
# On macOS this typically wraps libedit; ignore failures if module/bindings differ.
with suppress(Exception):
    import readline  # noqa: F401

    with suppress(Exception):
        readline.parse_and_bind("tab: complete")


def main() -> None:
    args = build_parser().parse_args()

    # Honor CLI color flags (override env and auto-detect). Must set before any coloring.
    if getattr(args, "color", False):
        set_cli_color_override(True)
    elif getattr(args, "no_color", False):
        set_cli_color_override(False)

    # Default behavior: if no subcommand provided, extract newest ZIP in `zips/`.
    if not getattr(args, "cmd", None):
        # Ensure args has a `zip` attribute for cmd_extract (it expects args.zip)
        if not hasattr(args, "zip"):
            args.zip = None
        # Respect global quiet flag when default-extract
        if getattr(args, "quiet", False):
            args.quiet = True
        cmd_extract(args)
        return

    # Resolve global/default mode preference: CLI > env CGPT_DEFAULT_MODE > builtin 'full'
    effective_default_mode = None
    if getattr(args, "default_mode", None):
        effective_default_mode = args.default_mode
    else:
        env_mode = os.environ.get("CGPT_DEFAULT_MODE")
        if env_mode and env_mode.lower() in ("full", "excerpts"):
            effective_default_mode = env_mode.lower()
    if effective_default_mode is None:
        effective_default_mode = "full"

    # If the chosen subcommand has a `mode` attribute that wasn't explicitly provided
    # (we set subparser defaults to None), fill it from the effective default.
    if hasattr(args, "mode") and args.mode is None:
        args.mode = effective_default_mode

    # Resolve split default from env when subcommand supports split and CLI did not set it.
    # Priority: CLI --split/--no-split > CGPT_DEFAULT_SPLIT > builtin False.
    if hasattr(args, "split") and args.split is None:
        env_split = _parse_env_bool("CGPT_DEFAULT_SPLIT")
        args.split = env_split if env_split is not None else False

    args.func(args)
