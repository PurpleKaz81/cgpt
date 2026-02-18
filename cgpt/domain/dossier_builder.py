import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from cgpt.core.io import (
    coerce_create_time,
    read_text_utf8,
    require_existing_file,
    safe_slug,
    ts_to_local_str,
)
from cgpt.core.layout import die
from cgpt.domain.config_schema import (
    generate_completeness_check,
    generate_control_layer,
    load_column_config,
)
from cgpt.domain.conversations import (
    base_title,
    build_conversation_map_by_id,
    compile_topic_pattern,
    conv_id_and_title,
    excerpt_messages,
    extract_messages_best_effort,
    trim_branch_new_part,
)
from cgpt.domain.dossier_cleaning import (
    _build_clean_txt,
    _dedupe_appendix_header,
    _deduplicate_blocks,
    _extract_deliverables,
    _generate_working_index,
    _generate_working_index_with_tags,
    _remove_appendix_header_lines,
    _reorganize_sources_section,
    _replace_dead_citations,
    _sanitize_openai_markup,
    _strip_citation_markers,
    _strip_existing_appendix,
    _strip_tool_noise,
    extract_research_artifacts,
)


def build_combined_dossier(
    *,
    topics: List[str],
    mode: str,
    context: int,
    root: Path,
    dossiers_dir: Path,
    wanted_ids: List[str],
    convs: List[Dict[str, Any]],
    formats: Optional[List[str]] = None,
    split: bool = False,
    patterns: Optional[List[str]] = None,
    dedup: bool = True,
    used_links_file: Optional[str] = None,
    config_file: Optional[str] = None,
    name: Optional[str] = None,
) -> Path:
    if not wanted_ids:
        die("No valid selections provided; cannot build dossier.")

    by_id = build_conversation_map_by_id(convs)

    missing = [i for i in wanted_ids if i not in by_id]
    if missing:
        die("Some IDs not found in export:\n" + "\n".join(missing))

    topic_re = compile_topic_pattern(topics)
    topic_label = ", ".join(topics)

    convo_items = []
    for cid in wanted_ids:
        c = by_id[cid]
        _, title = conv_id_and_title(c)
        ctime = coerce_create_time(c.get("create_time"))
        msgs = extract_messages_best_effort(c)
        convo_items.append(
            {
                "id": cid,
                "title": title,
                "base_title": base_title(title),
                "ctime": ctime,
                "msgs": msgs,
            }
        )

    groups: Dict[str, List[Dict[str, Any]]] = {}
    for item in convo_items:
        groups.setdefault(item["base_title"] or item["title"] or item["id"], []).append(
            item
        )

    for k in groups.keys():
        groups[k].sort(key=lambda x: x["ctime"])

    group_order = sorted(
        groups.items(), key=lambda kv: kv[1][0]["ctime"] if kv[1] else 0.0
    )

    # Determine output directory and filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    if name:
        normalized_name = safe_slug(name)
        if not normalized_name or normalized_name in {".", ".."}:
            die(
                "--name must contain at least one safe alphanumeric character after normalization."
            )
        # Create named subfolder: dossiers/{name}/
        named_dir = dossiers_dir / normalized_name
        named_dir.mkdir(parents=True, exist_ok=True)
        out_name = f"{timestamp}.md"
        out_path = named_dir / out_name
    else:
        # Flat structure (original behavior): dossiers/dossier__{topic}__{timestamp}.md
        out_name = f"dossier__{safe_slug(topic_label)}__{timestamp.replace('-', '')}.md"
        out_path = dossiers_dir / out_name

    doc: List[str] = []
    doc.append(f"# Dossier: {topic_label}\n\n")
    doc.append(
        f"- generated_at: {ts_to_local_str(datetime.now(tz=timezone.utc).timestamp())}\n"
    )
    doc.append(f"- export_root: {root}\n")
    doc.append(f"- mode: {mode}\n\n")
    doc.append("---\n\n")

    for _, items in group_order:
        root_item = items[0]
        root_id = root_item["id"]
        root_title = root_item["title"] or "Untitled"
        doc.append(f"## Thread: {root_title}\n\n")
        doc.append(f"- root_id: {root_id}\n")
        doc.append(
            f"- conversation_create_time: {ts_to_local_str(root_item['ctime'])}\n\n"
        )

        root_msgs = root_item["msgs"]
        if mode == "excerpts":
            root_msgs = excerpt_messages(root_msgs, topic_re, context)

        if root_msgs:
            doc.append("### Root conversation\n\n")
            for m in root_msgs:
                doc.append(f"**{m.role}** ({ts_to_local_str(m.t)})\n\n{m.text}\n\n")
        else:
            doc.append(
                "_No matching excerpts in root conversation._\n\n"
                if mode == "excerpts"
                else "_No messages found._\n\n"
            )

        for b in items[1:]:
            b_id = b["id"]
            b_title = b["title"] or "Untitled"
            b_msgs_new = trim_branch_new_part(root_item["msgs"], b["msgs"])

            if mode == "excerpts":
                b_msgs_new = excerpt_messages(b_msgs_new, topic_re, context)

            doc.append(f"### Branch: {b_title}\n\n")
            doc.append(f"- branch_id: {b_id}\n")
            doc.append(
                f"- branch_conversation_create_time: {ts_to_local_str(b['ctime'])}\n\n"
            )

            if b_msgs_new:
                for m in b_msgs_new:
                    doc.append(f"**{m.role}** ({ts_to_local_str(m.t)})\n\n{m.text}\n\n")
            else:
                doc.append(
                    "_No matching excerpts in this branch._\n\n"
                    if mode == "excerpts"
                    else "_No new messages after trimming._\n\n"
                )

        doc.append("---\n\n")

    md_content = "".join(doc)
    # Normalize requested formats: default to ['txt'] when not provided
    req_formats = [f.lower() for f in (formats or [])]
    if not req_formats:
        req_formats = ["txt"]

    # Utility to convert markdown -> plain text
    def _markdown_to_plain(md: str) -> str:
        s = re.sub(r"\r\n?", "\n", md)
        s = re.sub(r"(?m)^#{1,6}\s*", "", s)
        s = re.sub(r"\*\*(.*?)\*\*", r"\1", s)
        s = re.sub(r"\*(.*?)\*", r"\1", s)
        s = re.sub(r"```.*?```", "", s, flags=re.S)
        s = re.sub(r"`([^`]+)`", r"\1", s)
        s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
        s = re.sub(r"\n{3,}", "\n\n", s)
        return s.strip() + "\n"

    md_path = out_path
    created_primary: Optional[Path] = None

    # Build raw TXT (clean format, minimal processing)
    raw_txt = None
    if "txt" in req_formats:
        try:
            raw_txt = _build_clean_txt(group_order, topics, root)
        except Exception as e:
            print(f"WARNING: Raw TXT generation failed: {e}", file=sys.stderr)

    # Build working TXT if split mode enabled (apply all filters)
    working_txt = None
    append_expected = False
    if split and raw_txt:
        try:
            # Load config if provided
            config = None
            if config_file:
                config = load_column_config(config_file)

            # Load used links if file provided
            used_links: Optional[Set[str]] = None
            if used_links_file:
                used_links_path = require_existing_file(
                    used_links_file, label="used-links"
                )
                used_links_text = read_text_utf8(used_links_path, label="used-links")
                used_links = {
                    line.strip()
                    for line in used_links_text.splitlines()
                    if line.strip() and not line.startswith("#")
                }

            working_txt = raw_txt
            # Apply all processing filters (in order)
            working_txt = _strip_tool_noise(working_txt)
            working_txt = _strip_citation_markers(working_txt)
            working_txt = _sanitize_openai_markup(working_txt)
            working_txt = _strip_existing_appendix(working_txt)
            working_txt = _remove_appendix_header_lines(working_txt)
            working_txt = _replace_dead_citations(working_txt, {})
            if dedup:
                working_txt = _deduplicate_blocks(working_txt, min_block_size=200)
            if patterns is not None:
                working_txt = _extract_deliverables(working_txt, patterns)

            # Reorganize sources section with categorization
            working_txt = _reorganize_sources_section(working_txt, used_links)

            # Extract and quarantine research artifacts to list (not to string yet)
            working_txt, artifacts_list = extract_research_artifacts(working_txt)
            if artifacts_list:
                artifacts_list = [
                    a
                    for a in artifacts_list
                    if "APPENDIX: RESEARCH LOG" not in a
                    and "RESEARCH LOG & TOOL ARTIFACTS" not in a
                    and "JSON/Tool Call" not in a
                ]
            append_expected = bool(artifacts_list)

            # Add control layer front-matter if config provided
            if config:
                control_layer = generate_control_layer(config)
                completeness = generate_completeness_check(convs, config)
                front_matter = (
                    control_layer
                    + "COMPLETENESS CHECK\n"
                    + "=" * 70
                    + "\n"
                    + completeness
                    + "\n"
                    + "=" * 70
                    + "\n\n"
                )
                working_txt = front_matter + working_txt

            if not working_txt.strip():
                die("NO INCLUDED THREADS/SEGMENTS — CHECK FILTERS/KEYWORDS/PATTERNS")

            # Add working index at top (with timeline, priority threads, and tags if config)
            selected_convs = [by_id[cid] for cid in wanted_ids if cid in by_id]
            coverage_report = []
            if config:
                # Use tagged index if config provided
                working_idx, coverage_report = _generate_working_index_with_tags(
                    working_txt,
                    conversations=selected_convs,
                    topics=topics,
                    config=config,
                )
            else:
                # Fall back to standard index
                working_idx = _generate_working_index(
                    working_txt, conversations=selected_convs, topics=topics
                )

            # Build final output: index + coverage + content + appendix (once, at end)
            final_txt = "".join(working_idx)
            if coverage_report:
                final_txt += "\n" + "\n".join(coverage_report)
            final_txt += "\n" + working_txt

            # Emit appendix ONCE at the very end if artifacts exist
            if artifacts_list:
                final_txt += (
                    "\n\n" + "=" * 70 + "\n"
                    "APPENDIX: RESEARCH LOG & TOOL ARTIFACTS\n"
                    "=" * 70 + "\n\n"
                    "This section contains metadata, tool-call fragments, and provenance\n"
                    "information from the research extraction process.\n\n"
                    + "\n\n".join(artifacts_list)
                )

            # Final safety: ensure appendix header appears only once
            final_txt = _dedupe_appendix_header(final_txt)

            working_txt = final_txt
        except Exception as e:
            print(f"WARNING: Working TXT processing failed: {e}", file=sys.stderr)
            working_txt = None

    # Write MD if requested
    if "md" in req_formats:
        try:
            md_path.write_text(md_content, encoding="utf-8")
            created_primary = md_path
        except Exception as e:
            print(f"WARNING: MD generation failed: {e}", file=sys.stderr)

    # Write TXT files
    if "txt" in req_formats:
        try:
            txt_path = out_path.with_suffix(".txt")
            if raw_txt:
                txt_path.write_text(raw_txt, encoding="utf-8")
                if created_primary is None:
                    created_primary = txt_path

            # Write working variant if split enabled
            if split and working_txt:
                working_path = txt_path.parent / (
                    txt_path.stem + "__working" + txt_path.suffix
                )

                # HARD GUARDS: Verify appendix header appears exactly once (only if appended)
                if append_expected:
                    appendix_header_count = working_txt.count(
                        "APPENDIX: RESEARCH LOG & TOOL ARTIFACTS"
                    )
                    if appendix_header_count != 1:
                        print(
                            f"WARNING: Appendix header appears {appendix_header_count} times (expected 1)",
                            file=sys.stderr,
                        )

                    research_log_count = working_txt.count(
                        "RESEARCH LOG & TOOL ARTIFACTS"
                    )
                    if research_log_count != 1:
                        print(
                            f"WARNING: 'RESEARCH LOG & TOOL ARTIFACTS' appears {research_log_count} times (expected 1)",
                            file=sys.stderr,
                        )

                working_path.write_text(working_txt, encoding="utf-8")
        except Exception as e:
            print(f"WARNING: TXT generation failed: {e}", file=sys.stderr)

    # Write DOCX (use MD as source if available, fallback to plain conversion)
    if "docx" in req_formats:
        try:
            from docx import Document  # type: ignore

            docx_path = out_path.with_suffix(".docx")
            docx_doc = Document()
            plain = _markdown_to_plain(md_content)
            for para in [p for p in plain.split("\n\n") if p.strip()]:
                docx_doc.add_paragraph(para)
            docx_doc.save(str(docx_path))
            if created_primary is None:
                created_primary = docx_path
        except Exception as e:
            print(f"WARNING: DOCX generation failed: {e}", file=sys.stderr)

    if created_primary is None:
        die(
            "No dossier output files were created. "
            "Check requested formats and dependencies (for DOCX, install python-docx)."
        )
    return created_primary
