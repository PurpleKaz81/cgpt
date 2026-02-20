import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from cgpt.commands.dossier_options import collect_build_options, collect_wanted_ids
from cgpt.commands.dossier_roots import (
    ensure_root_with_latest,
    load_conversations,
    resolve_root,
)
from cgpt.commands.dossier_selection import collect_selection_indices, write_ids_tsv
from cgpt.core.color import _colorize_title_with_topics
from cgpt.core.io import (
    coerce_create_time,
    safe_slug,
    ts_to_local_str,
    warn_invalid_create_time,
)
from cgpt.core.layout import die, ensure_layout, home_dir
from cgpt.core.project import project_output_dir
from cgpt.domain.config_schema import load_column_config
from cgpt.domain.conversations import (
    build_conversation_map_by_id,
    conv_id_and_title,
    conversation_messages_blob,
    extract_messages_best_effort,
)
from cgpt.domain.dossier_builder import build_combined_dossier, markdown_to_plain_text
from cgpt.domain.dossier_cleaning import _extract_sources


def cmd_make_dossiers(args: argparse.Namespace) -> None:
    home = home_dir(args.home)
    _, _, dossiers_dir = ensure_layout(home)
    project_name = getattr(args, "name", None)
    root, _, _ = resolve_root(home, getattr(args, "root", None), project_name)
    out_dir = project_output_dir(dossiers_dir, project_name)
    convs = load_conversations(root)
    wanted = collect_wanted_ids(args)

    by_id = build_conversation_map_by_id(convs)

    missing = [i for i in wanted if i not in by_id]
    if missing:
        die("Some IDs not found in export:\n" + "\n".join(missing))

    for cid in wanted:
        c = by_id[cid]
        _, title = conv_id_and_title(c)
        base = out_dir / f"{cid}__{safe_slug(title or 'untitled')}"
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
    options = collect_build_options(args)

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
    if not topics and options.mode == "excerpts":
        die("Provide --topic and/or --topics when using --mode excerpts")
    if not topics:
        # In full mode, allow dossiers without topic filtering.
        topics = ["selected-conversations"]

    home = home_dir(args.home)
    _, _, dossiers_dir = ensure_layout(home)
    root, _, _ = resolve_root(home, getattr(args, "root", None), options.name)

    convs = load_conversations(root)
    wanted = collect_wanted_ids(args)

    out_path = build_combined_dossier(
        topics=topics,
        mode=options.mode,
        context=options.context,
        root=root,
        dossiers_dir=dossiers_dir,
        wanted_ids=wanted,
        convs=convs,
        formats=options.formats,
        split=options.split,
        patterns=options.patterns,
        dedup=options.dedup,
        used_links_file=options.used_links_file,
        config_file=options.config_file,
        name=options.name,
    )
    print(out_path)


def cmd_recent(args: argparse.Namespace) -> None:
    """
    Show the N most recent conversations and let you select interactively.
    Like 'quick' but without keyword filtering - just by recency.
    """
    count = int(args.count)
    if count < 1:
        die("Count must be at least 1.")

    home = home_dir(args.home)
    project_name = getattr(args, "name", None)
    root, dossiers_dir = ensure_root_with_latest(
        home, getattr(args, "root", None), project_name
    )
    selected_output_dir = project_output_dir(dossiers_dir, project_name)
    convs = load_conversations(root)

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
    all_ids_path, selected_ids_path = write_ids_tsv(selected_output_dir, slug, matches)

    # Print numbered list
    print(f"\n=== {count} Most Recent Conversations ===\n")
    for i, (cid, title, ctime) in enumerate(matches, start=1):
        print(f"{i:>3}. {cid}\t{title}\t{ts_to_local_str(ctime)}")

    print(f"\nSaved full list to: {all_ids_path}")

    picked = collect_selection_indices(
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

    options = collect_build_options(args, validate_config=True)

    out_path = build_combined_dossier(
        topics=[f"recent-{count}"],
        mode=options.mode,
        context=options.context,
        root=root,
        dossiers_dir=dossiers_dir,
        wanted_ids=wanted_ids,
        convs=convs,
        formats=options.formats,
        split=options.split,
        patterns=options.patterns,
        dedup=options.dedup,
        used_links_file=options.used_links_file,
        config_file=options.config_file,
        name=options.name,
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

    recent_count = getattr(args, "recent_count", None)
    days_count = getattr(args, "days_count", None)
    if recent_count is not None and recent_count < 1:
        die("--recent must be >= 1")
    if days_count is not None and days_count < 1:
        die("--days must be >= 1")

    home = home_dir(args.home)
    project_name = getattr(args, "name", None)
    root, dossiers_dir = ensure_root_with_latest(
        home, getattr(args, "root", None), project_name
    )
    selected_output_dir = project_output_dir(dossiers_dir, project_name)
    convs = load_conversations(root)
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
        messages_lower = ""
        if where in ("messages", "all"):
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
    all_ids_path, selected_ids_path = write_ids_tsv(selected_output_dir, slug, matches)

    # Print numbered list
    for i, (cid, title, ctime) in enumerate(matches, start=1):
        colored_title = _colorize_title_with_topics(title or "", topics)
        print(f"{i:>3}. {cid}\t{colored_title}\t{ts_to_local_str(ctime)}")

    print(f"\nSaved full match list to: {all_ids_path}")

    picked = collect_selection_indices(
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

    options = collect_build_options(args)

    out_path = build_combined_dossier(
        topics=topics,
        mode=options.mode,
        context=options.context,
        root=root,
        dossiers_dir=dossiers_dir,
        wanted_ids=wanted_ids,
        convs=convs,
        formats=options.formats,
        split=options.split,
        patterns=options.patterns,
        dedup=options.dedup,
        used_links_file=options.used_links_file,
        config_file=options.config_file,
        name=options.name,
    )
    print(f"\nWrote dossier: {out_path}")
