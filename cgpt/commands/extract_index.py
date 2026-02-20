import argparse
import sys
from pathlib import Path

from cgpt.core.layout import (
    default_root,
    die,
    ensure_layout,
    home_dir,
    newest_zip,
    refresh_latest_symlink,
)
from cgpt.core.project import get_active_project, set_project_extract_root
from cgpt.core.zip_safety import extract_zip_safely
from cgpt.domain.indexing import index_export


def cmd_latest_zip(args: argparse.Namespace) -> None:
    home = home_dir(args.home)
    zips_dir, _, _ = ensure_layout(home)
    print(newest_zip(zips_dir))

def cmd_extract(args: argparse.Namespace) -> None:
    home = home_dir(args.home)
    zips_dir, extracted_dir, dossiers_dir = ensure_layout(home)
    zpath = Path(args.zip).expanduser().resolve() if args.zip else newest_zip(zips_dir)
    if not zpath.exists():
        die(f"ZIP not found: {zpath}")
    out_dir = extracted_dir / zpath.stem
    extract_zip_safely(zpath, out_dir)
    refresh_latest_symlink(extracted_dir, out_dir)

    active_project = get_active_project(dossiers_dir)
    if active_project:
        set_project_extract_root(dossiers_dir, active_project, out_dir)

    # Print output unless quiet requested (top-level or subcommand)
    quiet = bool(getattr(args, "quiet", False))
    if not quiet:
        print(out_dir)

    # Indexing: by default update the global index at extracted/cgpt_index.db (Option A)
    no_index = bool(getattr(args, "no_index", False))
    reindex = bool(getattr(args, "reindex", False))
    if not no_index:
        try:
            db_path = extracted_dir / "cgpt_index.db"
            # If reindex, perform a full rebuild; otherwise perform incremental upsert
            index_export(out_dir, db_path, reindex=reindex, show_progress=not quiet)
        except Exception as e:
            print(f"WARNING: indexing failed: {e}", file=sys.stderr)

def cmd_index(args: argparse.Namespace) -> None:
    """(Re)build the search index from an extracted export."""
    home = home_dir(getattr(args, "home", None))
    _, extracted_dir, _ = ensure_layout(home)
    root = (
        Path(args.root).expanduser().resolve()
        if getattr(args, "root", None)
        else default_root(extracted_dir)
    )
    db_path = (
        Path(args.db).expanduser().resolve()
        if getattr(args, "db", None)
        else extracted_dir / "cgpt_index.db"
    )
    try:
        index_export(
            root,
            db_path,
            reindex=bool(getattr(args, "reindex", False)),
            show_progress=not getattr(args, "quiet", False),
        )
        print(f"Index built at: {db_path}")
    except Exception as e:
        die(f"Indexing failed: {e}")
