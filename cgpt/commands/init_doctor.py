import argparse
import importlib.util
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from cgpt.core.layout import die, home_dir, init_layout


def cmd_init(args: argparse.Namespace) -> None:
    home = home_dir(args.home)
    created, existing = init_layout(home)

    quiet = bool(getattr(args, "quiet", False))
    if quiet:
        return

    print(f"Home: {home}")
    for d in created:
        print(f"created: {d.name}/")
    for d in existing:
        print(f"exists: {d.name}/")
    if not created:
        print("All required folders already exist.")

@dataclass
class DoctorCheckResult:
    status: str
    name: str
    detail: str

def _doctor_add(
    checks: List[DoctorCheckResult], status: str, name: str, detail: str
) -> None:
    checks.append(DoctorCheckResult(status=status, name=name, detail=detail))

def _doctor_version(cmd: List[str]) -> Tuple[bool, str]:
    try:
        proc = subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        return False, "not found"
    except Exception as e:
        return False, str(e)

    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or f"exit {proc.returncode}").strip()
        first_line = err.splitlines()[0] if err else f"exit {proc.returncode}"
        return False, first_line

    out = (proc.stdout or proc.stderr or "").strip()
    first_line = out.splitlines()[0] if out else "ok"
    return True, first_line

def _doctor_parse_major_version(text: str) -> Optional[int]:
    match = re.search(r"(\d+)", text or "")
    if not match:
        return None
    try:
        return int(match.group(1))
    except Exception:
        return None

def _doctor_validate_layout(home: Path, fix: bool) -> Tuple[str, str]:
    required = [home / "zips", home / "extracted", home / "dossiers"]

    if home.exists() and not home.is_dir():
        return "FAIL", f"home path is not a directory: {home}"

    created: List[str] = []
    if fix:
        try:
            home.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return "FAIL", f"failed to create home directory {home}: {e}"
        for d in required:
            if d.exists():
                continue
            try:
                d.mkdir(parents=True, exist_ok=True)
                created.append(d.name)
            except Exception as e:
                return "FAIL", f"failed to create {d}: {e}"

    missing = [d.name for d in required if not d.exists()]
    not_dirs = [d.name for d in required if d.exists() and not d.is_dir()]
    if missing or not_dirs:
        bits: List[str] = []
        if missing:
            bits.append("missing: " + ", ".join(missing))
        if not_dirs:
            bits.append("not-directories: " + ", ".join(not_dirs))
        bits.append("run `cgpt init` or `cgpt doctor --fix`")
        return "FAIL", "; ".join(bits)

    perms = []
    for d in required:
        can_read = os.access(d, os.R_OK)
        can_write = os.access(d, os.W_OK)
        if not (can_read and can_write):
            perms.append(d.name)
    if perms:
        return "FAIL", "missing read/write permission for: " + ", ".join(perms)

    if created:
        return "PASS", f"home={home}; created: {', '.join(created)}"
    return "PASS", f"home={home}; zips/extracted/dossiers are ready"

def cmd_doctor(args: argparse.Namespace) -> None:
    """
    Validate local runtime (and optional dev) prerequisites without requiring
    contributors-only tooling for normal end users.
    """
    checks: List[DoctorCheckResult] = []
    strict = bool(getattr(args, "strict", False))
    include_dev = bool(getattr(args, "dev", False))
    fix = bool(getattr(args, "fix", False))

    py_detail = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    _doctor_add(checks, "PASS", "python", f"{py_detail} (runtime supported)")

    home = home_dir(args.home)
    layout_status, layout_detail = _doctor_validate_layout(home, fix=fix)
    _doctor_add(checks, layout_status, "layout", layout_detail)

    if importlib.util.find_spec("docx") is not None:
        _doctor_add(checks, "PASS", "docx", "python-docx installed; DOCX export available")
    else:
        _doctor_add(
            checks,
            "WARN",
            "docx",
            "python-docx not installed; TXT/MD work, DOCX export disabled",
        )

    if include_dev:
        ruff_ok, ruff_detail = _doctor_version([sys.executable, "-m", "ruff", "--version"])
        if ruff_ok:
            _doctor_add(checks, "PASS", "dev:ruff", ruff_detail)
        else:
            _doctor_add(
                checks,
                "WARN",
                "dev:ruff",
                f"{ruff_detail}; install with `python -m pip install -e \".[dev]\"`",
            )

        node_ok, node_detail = _doctor_version(["node", "--version"])
        if node_ok:
            node_major = _doctor_parse_major_version(node_detail)
            if node_major is None:
                _doctor_add(
                    checks,
                    "WARN",
                    "dev:node",
                    f"{node_detail}; could not parse version, requires Node.js 20+",
                )
            elif node_major >= 20:
                _doctor_add(checks, "PASS", "dev:node", node_detail)
            else:
                _doctor_add(
                    checks,
                    "WARN",
                    "dev:node",
                    f"{node_detail}; requires Node.js 20+",
                )
        else:
            _doctor_add(checks, "WARN", "dev:node", f"{node_detail}; requires Node.js 20+")

        npx_ok, npx_detail = _doctor_version(["npx", "--version"])
        if npx_ok:
            _doctor_add(checks, "PASS", "dev:npx", npx_detail)
            _doctor_add(
                checks,
                "PASS",
                "dev:markdownlint",
                "use `npx --yes markdownlint-cli2@0.16.0` (no global install required)",
            )
        else:
            _doctor_add(checks, "WARN", "dev:npx", f"{npx_detail}; required for markdown lint")

        tox_ok, tox_detail = _doctor_version(["tox", "--version"])
        if tox_ok:
            _doctor_add(checks, "PASS", "dev:tox", tox_detail)
        else:
            _doctor_add(
                checks,
                "WARN",
                "dev:tox",
                f"{tox_detail}; install with `python -m pip install -e \".[dev]\"`",
            )

        matrix_bins = [
            "python3.8",
            "python3.9",
            "python3.10",
            "python3.11",
            "python3.12",
            "python3.13",
        ]
        missing = [b for b in matrix_bins if shutil.which(b) is None]
        if missing:
            _doctor_add(
                checks,
                "WARN",
                "dev:python-matrix",
                "missing interpreters: "
                + ", ".join(missing)
                + " (CI still validates full matrix)",
            )
        else:
            _doctor_add(checks, "PASS", "dev:python-matrix", "python3.8-3.13 detected")

    passes = sum(1 for c in checks if c.status == "PASS")
    warns = sum(1 for c in checks if c.status == "WARN")
    fails = sum(1 for c in checks if c.status == "FAIL")

    for c in checks:
        print(f"[{c.status}] {c.name}: {c.detail}")
    print(f"Summary: {passes} passed, {warns} warnings, {fails} failed")

    if fails > 0 or (strict and warns > 0):
        die("doctor checks failed", code=2)
