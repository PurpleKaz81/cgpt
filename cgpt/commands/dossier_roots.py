from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from cgpt.core.layout import (
    default_root,
    die,
    ensure_layout,
    newest_extracted,
    newest_zip,
    refresh_latest_symlink,
)
from cgpt.core.zip_safety import extract_zip_safely
from cgpt.domain.conversations import (
    find_conversations_json,
    load_json,
    normalize_conversations,
)


def ensure_root_with_latest(home: Path, root_arg: Optional[str]) -> Tuple[Path, Path]:
    """Ensure extracted/latest points to newest extracted data and resolve root."""
    zips_dir, extracted_dir, dossiers_dir = ensure_layout(home)
    if root_arg:
        root = Path(root_arg).expanduser().resolve()
        if not root.exists():
            die(f"Root path not found: {root}")
        if not root.is_dir():
            die(f"Root path is not a directory: {root}")
        return root, dossiers_dir

    has_any_extracted = any(
        p.is_dir() and p.name != "latest" for p in extracted_dir.iterdir()
    )
    if not has_any_extracted:
        zpath = newest_zip(zips_dir)
        out_dir = extracted_dir / zpath.stem
        extract_zip_safely(zpath, out_dir)
        refresh_latest_symlink(extracted_dir, out_dir)
    else:
        refresh_latest_symlink(extracted_dir, newest_extracted(extracted_dir))

    root = default_root(extracted_dir)
    return root, dossiers_dir


def load_conversations(root: Path) -> List[Dict[str, Any]]:
    data_file = find_conversations_json(root)
    if not data_file:
        die(f"No conversations JSON found under {root}")
    data = load_json(data_file)
    return normalize_conversations(data)
