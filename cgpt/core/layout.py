import os
import shutil
import sys
from contextlib import suppress
from pathlib import Path
from typing import List, Optional, Tuple


def die(msg: str, code: int = 1) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)

def looks_like_home(p: Path) -> bool:
    return (
        (p / "zips").is_dir()
        and (p / "extracted").is_dir()
        and (p / "dossiers").is_dir()
    )

def discover_home() -> Path:
    """
    If user runs cgpt.py from a random folder, try to find the chatgpt_chat_exports
    home by walking up from:
        - current working directory
        - the directory containing cgpt.py
    """
    candidates = []
    with suppress(Exception):
        candidates.append(Path.cwd().resolve())
    with suppress(Exception):
        candidates.append(Path(__file__).resolve().parent)

    seen = set()
    for base in candidates:
        for p in [base, *list(base.parents)[:8]]:
            if p in seen:
                continue
            seen.add(p)
            if looks_like_home(p):
                return p

    # Fallback: cwd (will error later if layout missing)
    return Path.cwd().resolve()

def home_dir(cli_home: Optional[str]) -> Path:
    if cli_home:
        return Path(cli_home).expanduser().resolve()
    env = os.environ.get("CGPT_HOME")
    if env:
        return Path(env).expanduser().resolve()
    return discover_home()

def ensure_layout(home: Path) -> Tuple[Path, Path, Path]:
    zips_dir = home / "zips"
    extracted_dir = home / "extracted"
    dossiers_dir = home / "dossiers"
    for d in (zips_dir, extracted_dir, dossiers_dir):
        if not d.exists():
            die(
                f"Missing folder: {d}\nExpected: zips/, extracted/, dossiers/ under {home}"
            )
        if not d.is_dir():
            die(f"Not a directory: {d}")
    return zips_dir, extracted_dir, dossiers_dir

def init_layout(home: Path) -> Tuple[List[Path], List[Path]]:
    """Create required folders under home when missing; verify existing layout."""
    required = [home / "zips", home / "extracted", home / "dossiers"]
    created: List[Path] = []
    existing: List[Path] = []

    if home.exists() and not home.is_dir():
        die(f"Home path is not a directory: {home}")
    home.mkdir(parents=True, exist_ok=True)

    for d in required:
        if d.exists():
            if not d.is_dir():
                die(f"Expected directory but found file: {d}")
            existing.append(d)
            continue
        d.mkdir(parents=True, exist_ok=True)
        created.append(d)

    return created, existing

def newest_zip(zips_dir: Path) -> Path:
    zips = sorted(zips_dir.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not zips:
        die(f"No ZIPs found in {zips_dir}")
    return zips[0]

def newest_extracted(extracted_dir: Path) -> Path:
    dirs = [p for p in extracted_dir.iterdir() if p.is_dir() and p.name != "latest"]
    if not dirs:
        die(f"No extracted folders found in {extracted_dir}. Run: cgpt.py extract")
    dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return dirs[0]

def refresh_latest_symlink(extracted_dir: Path, target: Path) -> None:
    """Point extracted/latest to target. Fall back to extracted/LATEST.txt if symlink fails."""
    latest = extracted_dir / "latest"
    try:
        if latest.is_symlink() or latest.is_file():
            latest.unlink()
        elif latest.is_dir():
            shutil.rmtree(latest)
        latest.symlink_to(target, target_is_directory=True)
        # also keep pointer file as a backup
        (extracted_dir / "LATEST.txt").write_text(str(target) + "\n", encoding="utf-8")
    except OSError:
        (extracted_dir / "LATEST.txt").write_text(str(target) + "\n", encoding="utf-8")

def default_root(extracted_dir: Path) -> Path:
    """
    Prefer extracted/latest if present. Otherwise use extracted/LATEST.txt. Otherwise newest extracted dir.
    """
    latest = extracted_dir / "latest"
    if latest.exists():
        try:
            return latest.resolve()
        except Exception:
            return latest

    ptr = extracted_dir / "LATEST.txt"
    if ptr.exists():
        t = ptr.read_text(encoding="utf-8").strip()
        if t:
            p = Path(t).expanduser()
            if p.exists():
                return p.resolve()

    return newest_extracted(extracted_dir)
