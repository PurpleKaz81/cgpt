import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from cgpt.core.io import read_nonempty_lines_utf8, require_existing_file
from cgpt.core.layout import die
from cgpt.domain.config_schema import load_column_config


@dataclass
class BuildOptions:
    formats: List[str]
    patterns: Optional[List[str]]
    split: bool
    dedup: bool
    used_links_file: Optional[str]
    config_file: Optional[str]
    mode: str
    context: int
    name: Optional[str]


def collect_wanted_ids(args: argparse.Namespace) -> List[str]:
    wanted: List[str] = []
    wanted.extend(getattr(args, "ids", None) or [])

    ids_file = getattr(args, "ids_file", None)
    if ids_file:
        p = Path(ids_file).expanduser().resolve()
        if not p.exists():
            die(f"IDs file not found: {p}")
        wanted.extend(read_nonempty_lines_utf8(p, label="IDs"))

    wanted = [w.strip() for w in wanted if w.strip()]
    if not wanted:
        die("Provide --ids and/or --ids-file")
    return wanted


def collect_build_options(
    args: argparse.Namespace, *, validate_config: bool = False
) -> BuildOptions:
    formats = [f.lower() for f in (getattr(args, "format", None) or [])]

    patterns = None
    patterns_file = getattr(args, "patterns_file", None)
    if patterns_file:
        pf = require_existing_file(patterns_file, label="patterns")
        patterns = read_nonempty_lines_utf8(pf, label="patterns")

    split = bool(getattr(args, "split", False))
    dedup = bool(getattr(args, "dedup", True))
    used_links_file = getattr(args, "used_links_file", None)
    if used_links_file:
        used_links_file = str(
            require_existing_file(used_links_file, label="used-links")
        )

    config_file = getattr(args, "config", None)
    if validate_config and config_file:
        load_column_config(config_file)

    return BuildOptions(
        formats=formats,
        patterns=patterns,
        split=split,
        dedup=dedup,
        used_links_file=used_links_file,
        config_file=config_file,
        mode=getattr(args, "mode", None) or "full",
        context=int(getattr(args, "context", 2)),
        name=getattr(args, "name", None),
    )
