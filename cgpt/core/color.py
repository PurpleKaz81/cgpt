import re
import sys
from typing import List, Optional

from cgpt.core.env import _parse_env_bool

_CLI_COLOR_OVERRIDE: Optional[bool] = None


def set_cli_color_override(value: Optional[bool]) -> None:
    global _CLI_COLOR_OVERRIDE
    _CLI_COLOR_OVERRIDE = value

def _supports_color() -> bool:
    """Return whether to use ANSI colors.

    Honor the `CGPT_FORCE_COLOR` environment variable when present:
      - true values:  '1', 'true', 'yes', 'on'  => force enable
      - false values: '0', 'false', 'no', 'off'  => force disable
    Otherwise, fall back to `sys.stdout.isatty()`.
    """
    # CLI override takes precedence
    if _CLI_COLOR_OVERRIDE is not None:
        return _CLI_COLOR_OVERRIDE

    force_color = _parse_env_bool("CGPT_FORCE_COLOR")
    if force_color is not None:
        return force_color
    try:
        return sys.stdout.isatty()
    except Exception:
        return False

def _colorize_title_with_topic(title: str, topic: str) -> str:
    """Wrap the title in white and highlight case-insensitive `topic` matches in red.

    Falls back to the plain title when coloring isn't supported.
    """
    if not topic:
        return title
    if not _supports_color():
        return title
    try:
        red = "\033[31m"
        white = "\033[97m"
        reset = "\033[0m"
        pat = re.compile(re.escape(topic), re.IGNORECASE)
        highlighted = pat.sub(lambda m: f"{red}{m.group(0)}{white}", title)
        return f"{white}{highlighted}{reset}"
    except Exception:
        return title

def _colorize_title_with_topics(title: str, topics: List[str]) -> str:
    if not topics:
        return title
    if not _supports_color():
        return title
    try:
        red = "\033[31m"
        white = "\033[97m"
        reset = "\033[0m"
        parts = [re.escape(t) for t in topics if t]
        if not parts:
            return title
        pat = re.compile("(" + "|".join(parts) + ")", re.IGNORECASE)
        highlighted = pat.sub(lambda m: f"{red}{m.group(0)}{white}", title)
        return f"{white}{highlighted}{reset}"
    except Exception:
        return title

