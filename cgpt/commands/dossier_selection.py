import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from cgpt.core.io import read_nonempty_lines_utf8, read_text_utf8
from cgpt.core.layout import die


def _parse_selection_text(
    raw_text: str,
    matches: List[Tuple[str, str, float]],
    *,
    allow_ids_file_include: bool,
) -> Tuple[List[int], List[str]]:
    tokens = [t for t in re.split(r"[,\s]+", raw_text) if t]
    picked_local: List[int] = []
    warnings: List[str] = []
    id_to_index = {cid: idx for idx, (cid, _, _) in enumerate(matches, start=1)}

    for tok in tokens:
        if allow_ids_file_include and tok.startswith("@"):
            path = Path(tok[1:]).expanduser()
            if not path.exists():
                warnings.append(f"IDs file not found: {path}")
                continue
            for ln in read_text_utf8(path, label="IDs").splitlines():
                ln = ln.strip()
                if not ln:
                    continue
                if ln in id_to_index:
                    picked_local.append(id_to_index[ln])
                    continue
                if ln.isdigit():
                    n = int(ln)
                    if 1 <= n <= len(matches):
                        picked_local.append(n)
                    else:
                        warnings.append(f"Selection number out of range in file: {n}")
                    continue
                warnings.append(f"Unknown ID in file: {ln}")
            continue

        if re.match(r"^\d+-\d+$", tok):
            a, b = tok.split("-", 1)
            a_i, b_i = int(a), int(b)
            if a_i > b_i:
                a_i, b_i = b_i, a_i
            a_i = max(1, a_i)
            b_i = min(len(matches), b_i)
            if a_i > len(matches) or b_i < 1:
                warnings.append(f"Range out of bounds: {tok}")
                continue
            for n in range(a_i, b_i + 1):
                picked_local.append(n)
            continue

        if tok.isdigit():
            n = int(tok)
            if 1 <= n <= len(matches):
                picked_local.append(n)
            else:
                warnings.append(f"Selection number out of range: {n}")
            continue

        if tok in id_to_index:
            picked_local.append(id_to_index[tok])
        else:
            warnings.append(f"Unknown ID in selection: {tok}")

    return picked_local, warnings


def _print_selection_warnings(warnings: List[str]) -> None:
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)


def collect_selection_indices(
    *,
    matches: List[Tuple[str, str, float]],
    select_all: bool,
    ids_file: Optional[str],
    allow_ids_file_include: bool,
    pick_prompt: str,
    correction_prompt: str,
    no_valid_warning: str,
    no_valid_error: str,
) -> Optional[List[int]]:
    if ids_file:
        p = Path(ids_file).expanduser().resolve()
        if not p.exists():
            die(f"IDs file not found: {p}")
        raw = "\n".join(read_nonempty_lines_utf8(p, label="IDs"))
        picked, warnings = _parse_selection_text(
            raw, matches, allow_ids_file_include=allow_ids_file_include
        )
        if warnings:
            _print_selection_warnings(warnings)
    elif select_all:
        picked = list(range(1, len(matches) + 1))
    else:
        stdin_is_tty = sys.stdin.isatty()
        if not stdin_is_tty:
            try:
                raw = sys.stdin.read()
            except Exception:
                die("Failed to read stdin for selection.")
            if not raw or not raw.strip():
                die("No selection provided on stdin.")
            picked, warnings = _parse_selection_text(
                raw, matches, allow_ids_file_include=allow_ids_file_include
            )
            if warnings:
                _print_selection_warnings(warnings)
        else:
            picked = []
            while True:
                try:
                    raw = input(pick_prompt).strip()
                except (KeyboardInterrupt, EOFError):
                    print("\nSelection cancelled.")
                    return None
                if not raw:
                    die("No selection provided.")
                if raw.lower() == "all":
                    picked = list(range(1, len(matches) + 1))
                    break

                picked, warnings = _parse_selection_text(
                    raw, matches, allow_ids_file_include=allow_ids_file_include
                )
                if not warnings:
                    break
                _print_selection_warnings(warnings)
                try:
                    correction = input(correction_prompt)
                except (KeyboardInterrupt, EOFError):
                    print("\nSelection cancelled.")
                    return None
                if correction is None:
                    print("\nSelection cancelled.")
                    return None
                correction = correction.strip()
                if correction == "":
                    if not picked:
                        print(no_valid_warning, file=sys.stderr)
                        continue
                    break
                raw = correction
                if raw.lower() == "all":
                    picked = list(range(1, len(matches) + 1))
                    break
                picked, warnings = _parse_selection_text(
                    raw, matches, allow_ids_file_include=allow_ids_file_include
                )
                if not warnings:
                    break

    picked = sorted(set(picked))
    if not picked:
        die(no_valid_error)
    return picked


def write_ids_tsv(
    output_dir: Path, slug: str, matches: List[Tuple[str, str, float]]
) -> Tuple[Path, Path]:
    all_ids_path = output_dir / f"ids__{slug}.tsv"
    selected_ids_path = output_dir / f"selected_ids__{slug}.txt"
    all_lines = [f"{cid}\t{title}\n" for (cid, title, _) in matches]
    all_ids_path.write_text("".join(all_lines), encoding="utf-8")
    return all_ids_path, selected_ids_path
