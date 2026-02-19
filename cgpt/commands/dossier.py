import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from cgpt.core.color import _colorize_title_with_topics
from cgpt.core.io import (
    coerce_create_time,
    read_nonempty_lines_utf8,
    read_text_utf8,
    require_existing_file,
    safe_slug,
    ts_to_local_str,
    warn_invalid_create_time,
)
from cgpt.core.layout import (
    default_root,
    die,
    ensure_layout,
    home_dir,
    newest_extracted,
    newest_zip,
    refresh_latest_symlink,
)
from cgpt.core.zip_safety import extract_zip_safely
from cgpt.domain.config_schema import load_column_config
from cgpt.domain.conversations import (
    build_conversation_map_by_id,
    conv_id_and_title,
    conversation_messages_blob,
    extract_messages_best_effort,
    find_conversations_json,
    load_json,
    normalize_conversations,
)
from cgpt.domain.dossier_builder import build_combined_dossier, markdown_to_plain_text
from cgpt.domain.dossier_cleaning import _extract_sources


def _ensure_root_with_latest(home: Path, root_arg: Optional[str]) -> Tuple[Path, Path]:
    """Ensure extracted/latest points to newest extracted data and resolve root."""
    zips_dir, extracted_dir, dossiers_dir = ensure_layout(home)
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

    root = (
        Path(root_arg).expanduser().resolve()
        if root_arg
        else default_root(extracted_dir)
    )
    return root, dossiers_dir


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


def _collect_selection_indices(
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


def _write_ids_tsv(
    dossiers_dir: Path, slug: str, matches: List[Tuple[str, str, float]]
) -> Tuple[Path, Path]:
    all_ids_path = dossiers_dir / f"ids__{slug}.tsv"
    selected_ids_path = dossiers_dir / f"selected_ids__{slug}.txt"
    all_lines = [f"{cid}\t{title}\n" for (cid, title, _) in matches]
    all_ids_path.write_text("".join(all_lines), encoding="utf-8")
    return all_ids_path, selected_ids_path


def cmd_make_dossiers(args: argparse.Namespace) -> None:
    home = home_dir(args.home)
    _, extracted_dir, dossiers_dir = ensure_layout(home)
    root = (
        Path(args.root).expanduser().resolve()
        if args.root
        else default_root(extracted_dir)
    )
    data_file = find_conversations_json(root)
    if not data_file:
        die(f"No conversations JSON found under {root}")
    data = load_json(data_file)
    convs = normalize_conversations(data)

    wanted: List[str] = []
    if args.ids:
        wanted.extend(args.ids)
    if args.ids_file:
        p = Path(args.ids_file).expanduser().resolve()
        if not p.exists():
            die(f"IDs file not found: {p}")
        wanted.extend(read_nonempty_lines_utf8(p, label="IDs"))
    wanted = [w.strip() for w in wanted if w.strip()]
    if not wanted:
        die("Provide --ids and/or --ids-file")

    by_id = build_conversation_map_by_id(convs)

    missing = [i for i in wanted if i not in by_id]
    if missing:
        die("Some IDs not found in export:\n" + "\n".join(missing))

    for cid in wanted:
        c = by_id[cid]
        _, title = conv_id_and_title(c)
        base = dossiers_dir / f"{cid}__{safe_slug(title or 'untitled')}"
        md_path = base.with_suffix(".md")

        msgs = extract_messages_best_effort(c)
        header = f"# {title or 'Untitled'}\n\n- id: {cid}\n"
        ctime = c.get("create_time")
        if isinstance(ctime, (int, float)):
            header += f"- conversation_create_time: {ts_to_local_str(float(ctime))}\n"
        header += "\n---\n\n"

        parts = [header]
        for m in msgs:
            role_name = m.role.capitalize()
            parts.append(f"## {role_name} ({ts_to_local_str(m.t)})\n\n{m.text}\n\n")

        md_content = "".join(parts)

        # normalize requested formats (default to txt)
        req_formats = [f.lower() for f in (getattr(args, "format", None) or [])]
        if not req_formats:
            req_formats = ["txt"]

        created_paths: List[Path] = []

        if "md" in req_formats:
            try:
                md_path.write_text(md_content, encoding="utf-8")
                created_paths.append(md_path)
            except Exception as e:
                print(
                    f"WARNING: Failed to write Markdown file {md_path}: {e}",
                    file=sys.stderr,
                )

        if "txt" in req_formats:
            try:
                # Use clean TXT format for per-conversation dossiers as well
                clean_txt_lines: List[str] = []
                clean_txt_lines.append(f"{title or 'Untitled'}\n")
                clean_txt_lines.append(
                    f"Generated: {ts_to_local_str(datetime.now(tz=timezone.utc).timestamp())}\n"
                )
                clean_txt_lines.append(f"Source: {root}\n\n")

                # Extract sources from this conversation
                sources: List[Tuple[str, str]] = []
                for msg in msgs:
                    sources.extend(_extract_sources(msg.text))

                # Main content
                clean_txt_lines.append("=" * 70 + "\n")
                for msg in msgs:
                    role = msg.role.capitalize()
                    clean_txt_lines.append(f"{role}:\n\n{msg.text}\n\n")

                # Sources registry
                if sources:
                    sources_dict: Dict[str, str] = {}
                    for url, label in sources:
                        if url not in sources_dict:
                            sources_dict[url] = label

                    clean_txt_lines.append("\n" + "=" * 70 + "\n")
                    clean_txt_lines.append("SOURCES REGISTRY\n")
                    clean_txt_lines.append("=" * 70 + "\n\n")
                    for i, (url, label) in enumerate(
                        sorted(sources_dict.items()), start=1
                    ):
                        clean_txt_lines.append(f"[{i}] {label}\n    {url}\n\n")

                txt_path = base.with_suffix(".txt")
                txt_path.write_text("".join(clean_txt_lines), encoding="utf-8")
                created_paths.append(txt_path)
            except Exception as e:
                print(
                    f"WARNING: Failed to write TXT file for conversation {cid}: {e}",
                    file=sys.stderr,
                )

        if "docx" in req_formats:
            try:
                from docx import Document  # type: ignore

                docx_path = base.with_suffix(".docx")
                docx_doc = Document()
                plain = markdown_to_plain_text(md_content)
                for para in [p for p in plain.split("\n\n") if p.strip()]:
                    docx_doc.add_paragraph(para)
                docx_doc.save(str(docx_path))
                created_paths.append(docx_path)
            except Exception as e:
                print(
                    f"WARNING: Failed to write DOCX file for conversation {cid}: {e}",
                    file=sys.stderr,
                )

        # Print whichever primary file was created (prefer txt then md then docx)
        if created_paths:
            # choose preferred ordering
            for ext in (".txt", ".md", ".docx"):
                for p in created_paths:
                    if p.suffix == ext:
                        print(p)
                        break
                else:
                    continue
                break
        else:
            print(
                f"WARNING: No output files created for conversation {cid}",
                file=sys.stderr,
            )

def cmd_build_dossier(args: argparse.Namespace) -> None:
    mode = getattr(args, "mode", None) or "full"
    context = int(args.context)

    topics: List[str] = []
    if getattr(args, "topic", None):
        topics.append(args.topic)
    if getattr(args, "topics", None):
        topics.extend(args.topics or [])
    # Optional: extend search terms from config
    if getattr(args, "config", None):
        cfg = load_column_config(args.config)
        extra_terms = cfg.get("search_terms", [])
        if isinstance(extra_terms, list):
            topics.extend([t for t in extra_terms if isinstance(t, str)])
    topics = [t.strip() for t in topics if t and t.strip()]
    if not topics and mode == "excerpts":
        die("Provide --topic and/or --topics when using --mode excerpts")
    if not topics:
        # In full mode, allow dossiers without topic filtering.
        topics = ["selected-conversations"]

    home = home_dir(args.home)
    _, extracted_dir, dossiers_dir = ensure_layout(home)
    root = (
        Path(args.root).expanduser().resolve()
        if args.root
        else default_root(extracted_dir)
    )

    data_file = find_conversations_json(root)
    if not data_file:
        die(f"No conversations JSON found under {root}")
    data = load_json(data_file)
    convs = normalize_conversations(data)

    wanted: List[str] = []
    if args.ids:
        wanted.extend(args.ids)
    if args.ids_file:
        p = Path(args.ids_file).expanduser().resolve()
        if not p.exists():
            die(f"IDs file not found: {p}")
        wanted.extend(read_nonempty_lines_utf8(p, label="IDs"))
    wanted = [w.strip() for w in wanted if w.strip()]
    if not wanted:
        die("Provide --ids and/or --ids-file")

    # Determine output formats (default to txt)
    formats = [f.lower() for f in (getattr(args, "format", None) or [])]

    # Load patterns from file if provided
    patterns = None
    if getattr(args, "patterns_file", None):
        pf = require_existing_file(args.patterns_file, label="patterns")
        patterns = read_nonempty_lines_utf8(pf, label="patterns")

    split = bool(getattr(args, "split", False))
    dedup = bool(getattr(args, "dedup", True))
    used_links_file = getattr(args, "used_links_file", None)
    if used_links_file:
        used_links_file = str(
            require_existing_file(used_links_file, label="used-links")
        )
    config_file = getattr(args, "config", None)
    name = getattr(args, "name", None)

    out_path = build_combined_dossier(
        topics=topics,
        mode=mode,
        context=context,
        root=root,
        dossiers_dir=dossiers_dir,
        wanted_ids=wanted,
        convs=convs,
        formats=formats,
        split=split,
        patterns=patterns,
        dedup=dedup,
        used_links_file=used_links_file,
        config_file=config_file,
        name=name,
    )
    print(out_path)

def cmd_recent(args: argparse.Namespace) -> None:
    """
    Show the N most recent conversations and let you select interactively.
    Like 'quick' but without keyword filtering — just by recency.
    """
    count = int(args.count)
    if count < 1:
        die("Count must be at least 1.")

    home = home_dir(args.home)
    root, dossiers_dir = _ensure_root_with_latest(home, args.root)

    data_file = find_conversations_json(root)
    if not data_file:
        die(f"No conversations JSON found under {root}")
    data = load_json(data_file)
    convs = normalize_conversations(data)

    # Sort by create_time descending (newest first), then take top N
    invalid_create_time = [0]
    convs_with_time: List[Tuple[Any, float]] = []
    for c in convs:
        cid, title = conv_id_and_title(c)
        if cid:
            ctime = coerce_create_time(c.get("create_time"), invalid_create_time)
            convs_with_time.append((c, ctime))

    convs_with_time.sort(key=lambda x: x[1], reverse=True)
    recent_convs = convs_with_time[:count]
    warn_invalid_create_time(invalid_create_time[0], "recent")

    if not recent_convs:
        die("No conversations found.")

    # Build matches list (id, title, create_time) for selection
    matches: List[Tuple[str, str, float]] = []
    for c, ctime in recent_convs:
        cid, title = conv_id_and_title(c)
        matches.append((cid, title or "", ctime))

    # For display, reverse so oldest of the N is #1 and newest is #N (chronological within the window)
    # Actually, let's keep newest at top (#1) for intuitive "most recent first"
    # matches is already newest-first from the sort above

    slug = f"recent_{count}"
    all_ids_path, selected_ids_path = _write_ids_tsv(dossiers_dir, slug, matches)

    # Print numbered list
    print(f"\n=== {count} Most Recent Conversations ===\n")
    for i, (cid, title, ctime) in enumerate(matches, start=1):
        print(f"{i:>3}. {cid}\t{title}\t{ts_to_local_str(ctime)}")

    print(f"\nSaved full list to: {all_ids_path}")

    picked = _collect_selection_indices(
        matches=matches,
        select_all=bool(args.all),
        ids_file=None,
        allow_ids_file_include=False,
        pick_prompt="\nPick by number (e.g. 1 3 7), range (1-5), or 'all': ",
        correction_prompt="\nErrors detected. Enter corrected selection, or ENTER to accept valid picks: ",
        no_valid_warning="No valid selections; please try again.",
        no_valid_error="No valid selections were parsed.",
    )
    if picked is None:
        return
    wanted_ids = [matches[i - 1][0] for i in picked]

    selected_ids_path.write_text("\n".join(wanted_ids) + "\n", encoding="utf-8")
    print(f"\nSaved selected IDs to: {selected_ids_path}")

    # Build dossier
    formats = [f.lower() for f in (getattr(args, "format", None) or [])]
    patterns = None
    if getattr(args, "patterns_file", None):
        pf = require_existing_file(args.patterns_file, label="patterns")
        patterns = read_nonempty_lines_utf8(pf, label="patterns")

    split = bool(getattr(args, "split", False))
    dedup = bool(getattr(args, "dedup", True))
    used_links_file = getattr(args, "used_links_file", None)
    if used_links_file:
        used_links_file = str(
            require_existing_file(used_links_file, label="used-links")
        )
    config_file = getattr(args, "config", None)
    if config_file:
        # Validate upfront so explicit --config errors are not deferred/silent.
        load_column_config(config_file)
    mode = getattr(args, "mode", None) or "full"
    context = int(getattr(args, "context", 2))
    name = getattr(args, "name", None)

    out_path = build_combined_dossier(
        topics=[f"recent-{count}"],
        mode=mode,
        context=context,
        root=root,
        dossiers_dir=dossiers_dir,
        wanted_ids=wanted_ids,
        convs=convs,
        formats=formats,
        split=split,
        patterns=patterns,
        dedup=dedup,
        used_links_file=used_links_file,
        config_file=config_file,
        name=name,
    )
    print(f"\nWrote dossier: {out_path}")

def cmd_quick(args: argparse.Namespace) -> None:
    """
    One command that:
      - extracts newest zip (if nothing extracted yet)
      - searches titles by topic(s)
      - lets you select by number (or 'all')
      - builds dossier from the selected IDs
    """
    topics = [t.strip() for t in args.topics if t.strip()]
    if getattr(args, "config", None):
        cfg = load_column_config(args.config)
        extra_terms = cfg.get("search_terms", [])
        if isinstance(extra_terms, list):
            topics.extend([t for t in extra_terms if isinstance(t, str)])
    if not topics:
        die("Provide at least one topic.")

    mode = args.mode
    context = int(args.context)
    recent_count = getattr(args, "recent_count", None)
    days_count = getattr(args, "days_count", None)
    if recent_count is not None and recent_count < 1:
        die("--recent must be >= 1")
    if days_count is not None and days_count < 1:
        die("--days must be >= 1")

    home = home_dir(args.home)
    root, dossiers_dir = _ensure_root_with_latest(home, args.root)

    data_file = find_conversations_json(root)
    if not data_file:
        die(f"No conversations JSON found under {root}")
    data = load_json(data_file)
    convs = normalize_conversations(data)
    invalid_create_time = [0]

    def _ctime_for(c: Dict[str, Any]) -> float:
        return coerce_create_time(c.get("create_time"), invalid_create_time)

    if days_count is not None:
        now_ts = datetime.now(tz=timezone.utc).timestamp()
        cutoff_ts = now_ts - (days_count * 86400.0)
        filtered: List[Dict[str, Any]] = []
        for c in convs:
            cid, _ = conv_id_and_title(c)
            if not cid:
                continue
            if _ctime_for(c) >= cutoff_ts:
                filtered.append(c)
        convs = filtered
    if recent_count is not None:
        convs_with_time: List[Tuple[Any, float]] = []
        for c in convs:
            cid, _ = conv_id_and_title(c)
            if not cid:
                continue
            ctime = _ctime_for(c)
            convs_with_time.append((c, ctime))
        convs_with_time.sort(key=lambda x: x[1], reverse=True)
        convs = [c for c, _ in convs_with_time[:recent_count]]

    needles = [t.lower() for t in topics]
    and_terms = bool(args.and_terms)
    where = getattr(args, "where", "title")

    matches: List[Tuple[str, str, float]] = []  # (id, title, create_time)
    for c in convs:
        cid, title = conv_id_and_title(c)
        if not cid:
            continue
        title_lower = (title or "").lower()
        messages_lower = conversation_messages_blob(c).lower()

        checks: List[bool] = []
        if where == "title":
            checks = [n in title_lower for n in needles]
        elif where == "messages":
            checks = [n in messages_lower for n in needles]
        elif where == "all":
            checks = [(n in title_lower) or (n in messages_lower) for n in needles]
        else:
            die(f"Invalid --where value: {where}")

        matched = all(checks) if and_terms else any(checks)
        if matched:
            ctime = _ctime_for(c)
            matches.append((cid, title or "", ctime))

    warn_invalid_create_time(invalid_create_time[0], "quick")

    if not matches:
        die("No conversations matched those topic terms.")

    # Sort by conversation create_time (sane for selection)
    matches.sort(key=lambda x: x[2])

    slug = safe_slug("_".join(topics))
    all_ids_path, selected_ids_path = _write_ids_tsv(dossiers_dir, slug, matches)

    # Print numbered list
    for i, (cid, title, ctime) in enumerate(matches, start=1):
        colored_title = _colorize_title_with_topics(title or "", topics)
        print(f"{i:>3}. {cid}\t{colored_title}\t{ts_to_local_str(ctime)}")

    print(f"\nSaved full match list to: {all_ids_path}")

    picked = _collect_selection_indices(
        matches=matches,
        select_all=bool(args.all),
        ids_file=getattr(args, "ids_file", None),
        allow_ids_file_include=True,
        pick_prompt="\nPick by number (e.g. 1 3 7), or 'all', or paste IDs: ",
        correction_prompt=(
            "\nErrors detected. Enter corrected selection, or press ENTER to accept valid selections and continue: "
        ),
        no_valid_warning=(
            "No valid selections to accept; please enter a corrected selection."
        ),
        no_valid_error=(
            "No valid selections were parsed. Check your selection numbers/IDs."
        ),
    )
    if picked is None:
        return
    wanted_ids = [matches[i - 1][0] for i in picked]

    selected_ids_path.write_text("\n".join(wanted_ids) + "\n", encoding="utf-8")
    print(f"\nSaved selected IDs to: {selected_ids_path}")

    formats = [f.lower() for f in (getattr(args, "format", None) or [])]

    # Load patterns from file if provided
    patterns = None
    if getattr(args, "patterns_file", None):
        pf = require_existing_file(args.patterns_file, label="patterns")
        patterns = read_nonempty_lines_utf8(pf, label="patterns")

    split = bool(getattr(args, "split", False))
    dedup = bool(getattr(args, "dedup", True))
    used_links_file = getattr(args, "used_links_file", None)
    if used_links_file:
        used_links_file = str(
            require_existing_file(used_links_file, label="used-links")
        )
    config_file = getattr(args, "config", None)
    name = getattr(args, "name", None)

    out_path = build_combined_dossier(
        topics=topics,
        mode=mode,
        context=context,
        root=root,
        dossiers_dir=dossiers_dir,
        wanted_ids=wanted_ids,
        convs=convs,
        formats=formats,
        split=split,
        patterns=patterns,
        dedup=dedup,
        used_links_file=used_links_file,
        config_file=config_file,
        name=name,
    )
    print(f"\nWrote dossier: {out_path}")
