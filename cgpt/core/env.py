import argparse
import heapq
import importlib.util
import json
import os
import re
import shutil
import sqlite3
import stat
import subprocess
import sys
import time
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

def _env_positive_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = int(raw.strip())
    except (TypeError, ValueError):
        return default
    if value <= 0:
        return default
    return value

def _parse_env_bool(name: str) -> Optional[bool]:
    """Parse a boolean-like env var, returning True/False/None (invalid or unset)."""
    env = os.environ.get(name)
    if env is None:
        return None
    v = env.strip().lower()
    if v in ("1", "true", "yes", "on"):
        return True
    if v in ("0", "false", "no", "off"):
        return False
    return None

