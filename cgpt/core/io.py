import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional

from cgpt.core.constants import MAX_CONTEXT, MIN_CONTEXT, SAO_PAULO_TZ
from cgpt.core.layout import die

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

def safe_slug(s: str, max_len: int = 80) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^\w\-\.\s]", "", s, flags=re.UNICODE)
    s = s.strip().replace(" ", "_")
    return s[:max_len] if len(s) > max_len else s

def ts_to_local_str(ts: float) -> str:
    if not ts:
        return ""
    dt_utc = datetime.fromtimestamp(ts, tz=timezone.utc)
    if ZoneInfo:
        try:
            dt_loc = dt_utc.astimezone(ZoneInfo(SAO_PAULO_TZ))
            return dt_loc.isoformat()
        except Exception:
            return dt_utc.isoformat()
    return dt_utc.isoformat()

def normalize_text(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s

def read_text_utf8(path: Path, *, label: str) -> str:
    """Read text inputs with UTF-8/UTF-8-BOM support and clear decode failures."""
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as e:
        die(f"Failed to read {label} file as UTF-8 text: {path}\n{e}")
    except Exception as e:
        die(f"Failed to read {label} file: {path}\n{e}")

def read_nonempty_lines_utf8(path: Path, *, label: str) -> List[str]:
    return [ln.strip() for ln in read_text_utf8(path, label=label).splitlines() if ln.strip()]

def require_existing_file(path_value: str, *, label: str) -> Path:
    path = Path(path_value).expanduser().resolve()
    if not path.exists():
        die(f"{label} file not found: {path}")
    if not path.is_file():
        die(f"{label} path is not a file: {path}")
    return path

def parse_context(value: Any) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError) as err:
        raise argparse.ArgumentTypeError("--context must be an integer") from err
    if n < MIN_CONTEXT or n > MAX_CONTEXT:
        raise argparse.ArgumentTypeError(
            f"--context must be between {MIN_CONTEXT} and {MAX_CONTEXT}"
        )
    return n

def coerce_create_time(value: Any, invalid_counter: Optional[List[int]] = None) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        if invalid_counter is not None:
            invalid_counter[0] += 1
        return 0.0

def warn_invalid_create_time(invalid_count: int, command_name: str) -> None:
    if invalid_count > 0:
        print(
            f"WARNING: Encountered {invalid_count} invalid create_time value(s) in {command_name}; coerced to 0.0.",
            file=sys.stderr,
        )
