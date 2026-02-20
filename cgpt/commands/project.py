import argparse
from pathlib import Path
from typing import List

from cgpt.core.layout import die, ensure_layout, home_dir
from cgpt.core.project import (
    clear_active_project,
    ensure_project_dir,
    get_active_project,
    normalize_project_name,
    set_active_project,
)


def _project_dirs(dossiers_dir: Path) -> List[Path]:
    return sorted(
        [
            p
            for p in dossiers_dir.iterdir()
            if p.is_dir() and not p.name.startswith(".")
        ],
        key=lambda p: p.name.lower(),
    )


def cmd_project_init(args: argparse.Namespace) -> None:
    home = home_dir(getattr(args, "home", None))
    _, _, dossiers_dir = ensure_layout(home)
    normalized = normalize_project_name(args.name)
    project_dir = ensure_project_dir(dossiers_dir, normalized)
    set_active_project(dossiers_dir, normalized)
    print(f"Project ready: {project_dir}")
    print(f"Active project: {normalized}")


def cmd_project_use(args: argparse.Namespace) -> None:
    home = home_dir(getattr(args, "home", None))
    _, _, dossiers_dir = ensure_layout(home)
    normalized = normalize_project_name(args.name)
    project_dir = dossiers_dir / normalized
    if not project_dir.exists():
        if getattr(args, "create", False):
            ensure_project_dir(dossiers_dir, normalized)
        else:
            die(
                f"Project folder not found: {project_dir}\n"
                "Run `cgpt project init <name>` first or pass `--create`."
            )
    set_active_project(dossiers_dir, normalized)
    print(f"Active project: {normalized}")


def cmd_project_status(args: argparse.Namespace) -> None:
    home = home_dir(getattr(args, "home", None))
    _, _, dossiers_dir = ensure_layout(home)
    active = get_active_project(dossiers_dir)
    if not active:
        print("Active project: (none)")
        return
    project_dir = dossiers_dir / active
    print(f"Active project: {active}")
    print(f"Project path: {project_dir}")


def cmd_project_list(args: argparse.Namespace) -> None:
    home = home_dir(getattr(args, "home", None))
    _, _, dossiers_dir = ensure_layout(home)
    active = get_active_project(dossiers_dir)
    projects = _project_dirs(dossiers_dir)
    if not projects:
        print("No projects found under dossiers/.")
        return
    for p in projects:
        marker = "*" if active and p.name == active else " "
        print(f"{marker} {p.name}")


def cmd_project_clear(args: argparse.Namespace) -> None:
    home = home_dir(getattr(args, "home", None))
    _, _, dossiers_dir = ensure_layout(home)
    clear_active_project(dossiers_dir)
    print("Active project cleared.")
