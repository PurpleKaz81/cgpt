import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from cgpt.core.io import coerce_create_time, normalize_text, ts_to_local_str
from cgpt.domain.config_schema import _get_short_tag, matches_thread_filter
from cgpt.domain.conversations import conv_id_and_title


def _extract_sources(text: str) -> List[Tuple[str, str]]:
    """Extract URLs from text and return list of (url, normalized_label)."""
    url_pattern = re.compile(r"https?://[^\s\)\]\}\"\']*[^\s\)\]\}\"\'\.,;:!?]")
    matches = url_pattern.findall(text)
    unique = []
    seen = set()
    for url in matches:
        if url not in seen:
            seen.add(url)
            # normalize: remove common trailing punctuation
            url = re.sub(r"[.,;:!?\'\"]$", "", url)
            # generate label from domain + path
            try:
                from urllib.parse import urlparse

                parsed = urlparse(url)
                label = parsed.netloc + (parsed.path[:50] if parsed.path else "")
            except Exception:
                label = url[:60]
            unique.append((url, label))
    return unique

def _generate_toc(groups: Dict[str, List[Dict[str, Any]]]) -> List[str]:
    """Generate a machine-readable table of contents from conversation groups.

    Returns list of lines: title, conversation count, approximate section info.
    """
    toc: List[str] = []
    toc.append("## TABLE OF CONTENTS\n")
    line_num = 10  # rough estimate (header + metadata takes ~10 lines)

    for group_name, items in groups.items():
        root = items[0]
        root_title = root["title"] or "Untitled"
        branch_count = len(items) - 1
        create_time = root["ctime"]

        section_label = f"Line ~{line_num}: {root_title}"
        if branch_count > 0:
            section_label += (
                f" (+{branch_count} branch{'es' if branch_count != 1 else ''})"
            )
        section_label += f" — {ts_to_local_str(create_time)[:10]}"
        toc.append(f"  {section_label}\n")

        # estimate lines per conversation: ~20–30 lines per branch, messages vary
        msg_count = len(root.get("msgs", []))
        est_lines = max(10, msg_count // 3)
        for _ in items[1:]:
            est_lines += max(8, len(_.get("msgs", [])) // 5)
        line_num += est_lines + 3  # 3 for separators

    toc.append("\n")
    return toc

def _build_clean_txt(
    group_order: List[Tuple[str, List[Dict[str, Any]]]],
    topics: List[str],
    root: Path,
) -> str:
    """Build a clean, AI-friendly TXT format without technical noise.

    Removes:
      - Inline timestamps and IDs (kept minimal in metadata block)
      - Branch/root technical labels (replaced with clear section headers)
      - Excessive markdown remnants

    Includes:
      - Clear conversation grouping (thread name at top, branches below)
      - Message separation (readable dashes)
      - Sources registry at end
      - Minimal metadata header
    """
    out: List[str] = []
    topic_label = ", ".join(topics) if topics else "Dossier"

    # === HEADER ===
    out.append(f"DOSSIER: {topic_label}\n")
    out.append(
        f"Generated: {ts_to_local_str(datetime.now(tz=timezone.utc).timestamp())}\n"
    )
    out.append(f"Source: {root}\n")
    out.append("\n")

    # === TOC ===
    # Convert group_order back to dict format for TOC generation
    groups_dict = dict(group_order)
    toc = _generate_toc(groups_dict)
    out.extend(toc)

    # === CONVERSATIONS ===
    conv_num = 0
    all_sources: List[Tuple[str, str]] = []

    for _, items in group_order:
        conv_num += 1
        root_item = items[0]
        root_title = root_item["title"] or "Untitled"
        root_msgs = root_item["msgs"]

        # Section header (clean, no technical IDs unless needed for reference)
        out.append(f"\n{'='*70}\n")
        out.append(f"{conv_num}. {root_title}\n")
        out.append(f"{'='*70}\n\n")

        # Root conversation messages
        if root_msgs:
            for msg in root_msgs:
                role = msg.role.capitalize()
                out.append(f"{role}:\n\n{msg.text}\n\n")
                # extract sources incrementally
                all_sources.extend(_extract_sources(msg.text))
        else:
            out.append("[No messages in root conversation.]\n\n")

        # Branches
        for branch_idx, branch_item in enumerate(items[1:], start=1):
            branch_title = branch_item["title"] or "Untitled"
            branch_msgs = branch_item["msgs"]

            out.append(f"\n--- Branch {branch_idx}: {branch_title} ---\n\n")

            if branch_msgs:
                for msg in branch_msgs:
                    role = msg.role.capitalize()
                    out.append(f"{role}:\n\n{msg.text}\n\n")
                    all_sources.extend(_extract_sources(msg.text))
            else:
                out.append("[No new messages in this branch.]\n\n")

    # === SOURCES REGISTRY ===
    if all_sources:
        # Deduplicate and sort
        sources_dict: Dict[str, str] = {}
        for url, label in all_sources:
            if url not in sources_dict:
                sources_dict[url] = label

        out.append(f"\n{'='*70}\n")
        out.append("SOURCES REGISTRY\n")
        out.append(f"{'='*70}\n\n")
        for i, (url, label) in enumerate(sorted(sources_dict.items()), start=1):
            out.append(f"[{i}] {label}\n    {url}\n\n")

    return "".join(out)

def _strip_tool_noise(text: str) -> str:
    """Remove tool-call JSON blocks and other technical noise.

    Removes patterns like:
      {"search_query": "..."}
      {"task_violates_safety_guidelines": ...}
      {"open": ...}
      Tool creation/update messages
      Meta-prompt instructions
    """
    # Extended tool-related keys (including system/safety fields)
    tool_keys = [
        "search_query",
        "tool_call",
        "function",
        "action",
        "open",
        "click",
        "find",
        "screenshot",
        "response_length",
        "file_path",
        "command",
        "terminal",
        "browser",
        "task_violates_safety_guidelines",
        "updates",
        "comments",
        "title",
        "prompt",
    ]

    # Remove complete JSON objects that contain tool-related keys
    pattern = r"\{\s*['\"]?(?:" + "|".join(tool_keys) + r")['\"]?.*?\}"
    text = re.sub(pattern, "", text, flags=re.DOTALL)

    # Remove tool call markers
    text = re.sub(r"\[tool_call:.*?\]", "", text, flags=re.DOTALL)

    # Remove lines starting with 'tool' or '**tool**'
    text = re.sub(r"^\s*(?:\*\*)?tool\s*\(.*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*(?:\*\*)?tool\s+\w+.*", "", text, flags=re.MULTILINE)

    # Remove tool creation/update messages
    text = re.sub(
        r"(?:Successfully created|Successfully updated|Failed with error).*?\n",
        "",
        text,
    )

    # Remove meta-prompt instructions like "Make sure to include...", "remember to..."
    text = re.sub(
        r"^[^\n]*(?:Make sure to|remember to|don't forget to).*?$",
        "",
        text,
        flags=re.MULTILINE | re.IGNORECASE,
    )

    # Remove tool usage boilerplate/instruction blocks that leak into transcripts
    text = re.sub(
        r"^##\s+How to invoke the file_search tool.*?(?=^##\s|\Z)",
        "",
        text,
        flags=re.DOTALL | re.MULTILINE | re.IGNORECASE,
    )
    text = re.sub(
        r"^##\s+How to handle results from file_search.*?(?=^##\s|\Z)",
        "",
        text,
        flags=re.DOTALL | re.MULTILINE | re.IGNORECASE,
    )
    text = re.sub(
        r"^##\s+Tool usage instructions.*?(?=^##\s|\Z)",
        "",
        text,
        flags=re.DOTALL | re.MULTILINE | re.IGNORECASE,
    )
    text = re.sub(
        r"^The file is too long and its contents have been truncated\..*?$",
        "",
        text,
        flags=re.MULTILINE | re.IGNORECASE,
    )

    # Remove lines that are pure JSON (start with { and contain tool keys)
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        normalized = re.sub(r"[\u200b-\u200f\u2060\ufeff]", "", stripped)
        # Skip JSON/Tool Call annotation lines outright
        if re.search(r"\[\s*JSON\s*/\s*Tool\s*Call\s*\]", normalized, re.IGNORECASE):
            continue
        # Skip JSON blocks with tool/system keys
        if normalized.startswith("{") and any(key in normalized for key in tool_keys):
            continue
        # Skip lines with embedded JSON containing safety/task fields
        if any(
            f'"{key}"' in normalized or f"'{key}'" in normalized
            for key in ["task_violates_safety_guidelines", "updates", "comments"]
        ):
            continue
        cleaned_lines.append(line)
    text = "\n".join(cleaned_lines)

    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def _strip_citation_markers(text: str) -> str:
    """Remove internal citation markers and navigation lists.

    Removes:
      - <citeturn0newsXX> tags
      - <navlist>...</navlist> blocks
      - Bare turn0newsXX tokens
      - Citation reference artifacts
      - Internal phantom citation markers: 【…†L…】
    """
    # Remove <citeturn...> tags
    text = re.sub(r"<citeturn[^>]*>", "", text, flags=re.IGNORECASE)

    # Remove <navlist>...</navlist> blocks
    text = re.sub(r"<navlist>.*?</navlist>", "", text, flags=re.DOTALL | re.IGNORECASE)

    # Remove bare turn0newsXX tokens
    text = re.sub(r"\bturn\d+news\d+\b", "", text, flags=re.IGNORECASE)

    # Remove citation brackets like [1], [2] that appear alone
    text = re.sub(r"\[\d+\](?!\S)", "", text)

    # Remove internal phantom citation markers: 【…†L…】 or similar CJK bracket patterns
    text = re.sub(r"【[^】]*†[^】]*】", "", text)
    text = re.sub(r"【[^】]*】", "", text)  # Remove other 【】 blocks

    # Remove residual ref placeholders
    text = re.sub(r"\[REF REMOVED\]", "", text, flags=re.IGNORECASE)

    # Clean up excessive whitespace from removals
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()

def _sanitize_openai_markup(text: str) -> str:
    """Remove OpenAI/ChatGPT UI markup blobs from output.

    Removes:
      - <img.../> tags (image placeholders)
      - <click.../> tags (interactive elements)
      - <link.../> tags
      - <audio.../> tags
      - Other angle-bracket UI markup (generic)
      - Stray appendix headers (to prevent duplication)
    """
    # Remove self-closing angle-bracket tags: <tag.../> or <tag>
    text = re.sub(r"</?[a-zA-Z][^>]*/?>\s*", "", text)

    # Remove any remaining OpenAI-style span markers (often empty or metadata)
    text = re.sub(r"<span[^>]*>.*?</span>", "", text, flags=re.DOTALL)

    # Remove stray "APPENDIX" headers to prevent duplication
    # (the real header will be emitted once by the pipeline)
    text = re.sub(
        r"APPENDIX:\s*RESEARCH LOG & TOOL ARTIFACTS\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # Remove private-use markers and spans bounded by them
    text = re.sub(r"[\ue000-\uf8ff].*?[\ue000-\uf8ff]", "", text, flags=re.DOTALL)
    text = re.sub(r"[\ue000-\uf8ff]", "", text)

    # Remove common non-printing artifacts (replacement/noncharacter/soft hyphen)
    text = re.sub(r"[\u00ad\ufffd\ufffe]", "", text)

    # Remove turn/citeturn tokens if any remain
    text = re.sub(
        r"(?:cite)?turn\d+(?:search|news|view|file)\w*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\bciteturn\d+\w+\b", "", text, flags=re.IGNORECASE)

    # Remove separator lines often associated with appendix (lines of = or -)
    text = re.sub(r"^={60,}.*?$", "", text, flags=re.MULTILINE)

    # Clean up whitespace damage from removals
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()

def _is_appendix_header_line(line: str) -> bool:
    """Detect appendix header lines robustly (ignores punctuation/soft hyphens)."""
    normalized = re.sub(r"[^A-Za-z]", "", line).upper()
    return "APPENDIX" in normalized and "RESEARCHLOGTOOLARTIFACTS" in normalized

def _strip_existing_appendix(text: str) -> str:
    """Remove any existing appendix block to prevent duplication."""
    lines = text.split("\n")
    for idx, line in enumerate(lines):
        if _is_appendix_header_line(line):
            return "\n".join(lines[:idx]).rstrip()
    return text

def _dedupe_appendix_header(text: str) -> str:
    """Ensure appendix header appears only once, preserving content."""
    marker = "APPENDIX: RESEARCH LOG & TOOL ARTIFACTS"
    if marker not in text:
        return text
    parts = text.split(marker)
    if len(parts) <= 2:
        return text
    # Keep first marker and remove subsequent marker occurrences
    first = parts[0] + marker + parts[1]
    rest = "".join(parts[2:]).replace(marker, "")
    return first + rest

def _remove_appendix_header_lines(text: str) -> str:
    """Remove any appendix header lines from text."""
    lines = [line for line in text.split("\n") if not _is_appendix_header_line(line)]
    return "\n".join(lines)

def _replace_dead_citations(text: str, sources_dict: Dict[str, str]) -> str:
    """Replace dead citation tokens (turn0news01, etc.) with source registry pointers.

    If a citation token matches a source, replace with [SOURCE: {index}].
    Otherwise, replace with [SOURCE: see registry] as a placeholder.

    NOTE: This is now largely handled by _strip_citation_markers().
    Kept for backward compatibility.
    """
    # Most work done by _strip_citation_markers now
    return text

def _tag_sources(
    sources: List[Tuple[str, str]], used_links: Optional[Set[str]] = None
) -> Dict[str, List[Tuple[str, str]]]:
    """Tag sources by category and usage status.

    Returns Dict[category, List[(url, label)]]:
      - used_in_drafts: Links from used_links set (highest priority)
      - candidate: Links with keywords suggesting relevance for next column
      - legal: .gov.br, .senado, .camara, legal-related domains
      - media: news, .com.br news outlets, press
      - economic: economic, financial, trade, central bank
      - internal: notes, transcripts, internal documents
      - other: everything else (lowest priority)
    """
    categories = {
        "used_in_drafts": [],
        "candidate": [],
        "legal": [],
        "media": [],
        "economic": [],
        "internal": [],
        "other": [],
    }

    # Keywords for identifying candidates (generic research-relevant terms)
    candidate_keywords = [
        "research",
        "analysis",
        "report",
        "study",
        "project",
        "draft",
        "document",
        "paper",
        "article",
        "summary",
    ]

    legal_keywords = [
        ".gov.br",
        ".senado",
        ".camara",
        "judicial",
        "legal",
        "court",
        "law",
    ]
    media_keywords = [
        "news",
        "folha",
        "globo",
        "estadao",
        "uol",
        "bbc",
        "cnn",
        "press",
        "media",
        "jornalismo",
        "nytimes",
        "wsj",
        "reuters",
    ]
    economic_keywords = [
        "economic",
        "financial",
        "trade",
        "economy",
        "banco",
        "bcb",
        "imf",
        "world bank",
        "commerce",
        "bloomberg",
        "forbes",
    ]
    internal_keywords = ["note", "transcript", "internal", "memo", "meeting", "summary"]

    for url, label in sources:
        url_lower = url.lower()
        label_lower = label.lower()

        # First priority: check if in used_links
        if used_links and url in used_links:
            categories["used_in_drafts"].append((url, label))
            continue

        # Second priority: check if candidate for next column
        if any(kw in url_lower or kw in label_lower for kw in candidate_keywords):
            categories["candidate"].append((url, label))
            continue

        # Then categorize by domain
        categorized = False
        if any(kw in url_lower or kw in label_lower for kw in legal_keywords):
            categories["legal"].append((url, label))
            categorized = True
        elif any(kw in url_lower or kw in label_lower for kw in media_keywords):
            categories["media"].append((url, label))
            categorized = True
        elif any(kw in url_lower or kw in label_lower for kw in economic_keywords):
            categories["economic"].append((url, label))
            categorized = True
        elif any(kw in url_lower or kw in label_lower for kw in internal_keywords):
            categories["internal"].append((url, label))
            categorized = True

        # Default to other
        if not categorized:
            categories["other"].append((url, label))

    return categories

def _deduplicate_blocks(text: str, min_block_size: int = 200) -> str:
    """Remove duplicate blocks of text (e.g., repeated transcripts).

    Uses hash-based deduplication. Splits text by paragraphs and removes
    consecutive blocks that are similar (hash match).
    """
    paragraphs = text.split("\n\n")
    seen_hashes = {}
    deduplicated = []

    for para in paragraphs:
        if len(para) < min_block_size:
            # Keep small blocks (headers, short messages)
            deduplicated.append(para)
        else:
            # Hash larger blocks for deduplication
            para_hash = hash(normalize_text(para))
            if para_hash not in seen_hashes:
                seen_hashes[para_hash] = True
                deduplicated.append(para)
            # else: skip duplicate

    return "\n\n".join(deduplicated)

def _extract_deliverables(text: str, patterns: Optional[List[str]] = None) -> str:
    """Extract deliverables only (headings, constraints, drafts).

    If patterns provided, match against section headers.
    Default patterns: "##", "Constraint", "Draft", "Decision", "Output", "Result"
    """
    if patterns is None:
        patterns = [
            "##",
            "constraint",
            "draft",
            "decision",
            "output",
            "result",
            "deliverable",
        ]

    lines = text.split("\n")
    deliverables = []
    in_section = False
    current_section = []

    for line in lines:
        line_lower = line.lower()

        # Check if line matches any pattern (start of a deliverable)
        matches_pattern = any(p.lower() in line_lower for p in patterns)

        if matches_pattern:
            # Save previous section if any
            if current_section:
                deliverables.extend(current_section)
            # Start new section
            in_section = True
            current_section = [line]
        elif in_section:
            # Continue collecting section content
            if line.strip():  # Include non-empty lines
                current_section.append(line)
            elif current_section and len(current_section) > 1:
                # Stop section on blank line (after content)
                deliverables.extend(current_section)
                current_section = []
                in_section = False

    # Include final section
    if current_section:
        deliverables.extend(current_section)

    return "\n".join(deliverables)

def _generate_working_index(
    text: str,
    conversations: Optional[List[Dict[str, Any]]] = None,
    topics: Optional[List[str]] = None,
) -> List[str]:
    """Auto-generate navigational index with timeline and priority threads.

    Includes:
      - Global timeline (conversations by date)
      - Priority threads (top 5 by recency + keywords)
      - Section headers for navigation
    """
    index_lines = ["## WORKING INDEX\n\n"]
    invalid_create_time = [0]

    def _conv_ctime(conv: Dict[str, Any]) -> float:
        return coerce_create_time(conv.get("create_time"), invalid_create_time)

    # Add global timeline if conversations provided
    if conversations:
        index_lines.append("### Timeline\n\n")
        # Sort conversations by create_time
        sorted_convs = sorted(conversations, key=_conv_ctime, reverse=True)
        for conv in sorted_convs[:10]:  # Show latest 10
            cid, title = conv_id_and_title(conv)
            ctime = _conv_ctime(conv)
            date_str = ts_to_local_str(ctime).split()[0] if ctime else "Unknown"
            cid_label = f"{cid[:8]}..." if cid else "unknown"
            index_lines.append(f"  - {date_str}: {title} (ID: {cid_label})\n")
        index_lines.append("\n")

    # Add priority threads (based on keywords and recency)
    if conversations and topics:
        index_lines.append("### Priority Threads (Read These First)\n\n")
        # Generic priority keywords (project/deliverable focused)
        priority_keywords = [
            "draft",
            "decision",
            "deliverable",
            "output",
            "final",
            "review",
            "summary",
            "analysis",
        ]

        scored_convs = []
        for conv in conversations:
            cid, title = conv_id_and_title(conv)
            score = 0
            title_lower = (title or "").lower()

            # Score by keyword presence
            for kw in priority_keywords:
                if kw in title_lower:
                    score += 2

            # Score by topic match
            for topic in topics:
                if topic.lower() in title_lower:
                    score += 3

            # Boost recent conversations
            ctime = _conv_ctime(conv)
            if ctime:
                # Conversations from last 30 days get boost
                import time

                days_ago = (time.time() - ctime) / 86400
                if days_ago < 30:
                    score += (30 - days_ago) / 10

            if score > 0:
                scored_convs.append((score, cid, title, ctime))

        # Sort by score and show top 5
        scored_convs.sort(reverse=True, key=lambda x: x[0])
        for i, (score, cid, title, ctime) in enumerate(scored_convs[:5], 1):
            date_str = ts_to_local_str(ctime).split()[0] if ctime else "Unknown"
            index_lines.append(f"  {i}. [{date_str}] {title}\n")
        index_lines.append("\n")

    # Add section navigation
    index_lines.append("### Sections\n\n")
    section_num = 0

    # Find all section headers (##, ===, etc.)
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("##") or line.startswith("===") or re.match(r"^\d+\.", line):
            section_num += 1
            header = line.strip().lstrip("#").strip().lstrip("=").strip()
            if header and header != "WORKING INDEX":  # Don't index ourselves
                index_lines.append(f"  {section_num:02d}. Line ~{i}: {header}\n")

    index_lines.append("\n---\n\n")
    return index_lines

def _reorganize_sources_section(
    text: str, used_links: Optional[Set[str]] = None
) -> str:
    """Extract sources from text and reorganize them by category."""
    sources_match = re.search(
        r"^={70}\nSOURCES REGISTRY\n={70}\n\n(.+)$",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if not sources_match:
        return text

    sources: List[Tuple[str, str]] = []
    source_pattern = r"\[(\d+)\]\s+(.+?)\n\s+(https?://\S+)"
    for match in re.finditer(source_pattern, sources_match.group(1)):
        label, url = match.group(2).strip(), match.group(3).strip()
        sources.append((url, label))

    if not sources:
        return text

    categorized = _tag_sources(sources, used_links)
    new_section = ["=" * 70 + "\n", "SOURCES REGISTRY\n", "=" * 70 + "\n\n"]

    display_order = [
        ("used_in_drafts", "**Used in Drafts**"),
        ("candidate", "**Candidates for Next Column**"),
        ("legal", "Legal Sources"),
        ("media", "Media Sources"),
        ("economic", "Economic Sources"),
        ("internal", "Internal Documents"),
        ("other", "Other Sources"),
    ]

    num = 1
    for key, label in display_order:
        if categorized.get(key):
            new_section.append(f"{label}:\n\n")
            for url, lbl in sorted(categorized[key], key=lambda x: x[1].lower()):
                new_section.append(f"[{num}] {lbl}\n    {url}\n\n")
                num += 1
            new_section.append("\n")

    return text[: sources_match.start()] + "".join(new_section)

def extract_research_artifacts(text: str) -> Tuple[str, List[str]]:
    """
    Extract tool-call artifacts (JSON, search fragments, etc.) into separate appendix.
    Returns (cleaned_text, artifacts_list) where artifacts_list is list of artifact strings.
    Also filters out any stray appendix headers that may have been included in text.
    """
    import re

    artifacts = []
    cleaned_lines = []

    # Patterns to detect and quarantine
    artifact_patterns = [
        (r"\[Search Query\].*?(?=\n\n|\n[A-Z]|$)", "Search Fragment"),
        (r"\[JSON/Tool Call\].*", "JSON/Tool Call"),
        (r"\{\".*?\}", "JSON/Tool Call"),
        (r"\[Image.*?\]", "Image Reference"),
        (r"\[GPT Model.*?\]", "Model Info"),
        (r"\[Citation Widget.*?\]", "Citation Widget"),
    ]

    lines = text.split("\n")
    for i, line in enumerate(lines):
        normalized_line = re.sub(r"[\u200b-\u200f\u2060\ufeff]", "", line)
        # Skip lines that are stray appendix headers
        if _is_appendix_header_line(normalized_line):
            continue

        # Always drop JSON/Tool Call lines (do not propagate to appendix)
        if re.search(
            r"\[\s*JSON\s*/\s*Tool\s*Call\s*\]", normalized_line, re.IGNORECASE
        ):
            continue

        found_artifact = False

        for pattern, label in artifact_patterns:
            match = re.search(pattern, normalized_line, re.DOTALL)
            if match:
                artifact_text = match.group(0)[:200]
                # Avoid propagating appendix header text into artifacts
                if _is_appendix_header_line(artifact_text):
                    found_artifact = True
                    break
                # Always drop JSON/Tool Call lines (do not propagate to appendix)
                if label == "JSON/Tool Call":
                    found_artifact = True
                    break
                # Only capture substantial artifacts for other labels
                if len(match.group(0)) > 20:
                    artifacts.append(f"[{label}] {artifact_text}...")
                    found_artifact = True
                    break

        if not found_artifact:
            cleaned_lines.append(line)

    cleaned_text = "\n".join(cleaned_lines)

    return cleaned_text, artifacts

def _generate_working_index_with_tags(
    txt: str,
    conversations: List[Dict[str, Any]] = None,
    topics: List[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Tuple[List[str], List[str]]:
    """
    Generate working index with thread tags derived from config buckets.
    Returns (index_lines, coverage_report_lines).
    """
    if not conversations:
        return [], []

    index_lines = ["PRIORITY THREADS (with category tags)\n", "=" * 70 + "\n"]

    priority_threads = []
    included_count = 0
    tag_counts: Dict[str, int] = {}  # Dynamic tag counting

    for c in conversations:
        cid, title = conv_id_and_title(c)
        if cid and title:
            # Get tag from config if available
            bucket_tag = None
            if config:
                included, bucket_tag = matches_thread_filter(title, config)

            # Map bucket name to short tag
            short_tag = _get_short_tag(bucket_tag)

            ctime = coerce_create_time(c.get("create_time"))
            priority_threads.append((cid, title, ctime, short_tag))
            included_count += 1
            tag_counts[short_tag] = tag_counts.get(short_tag, 0) + 1

    # Sort by creation time
    priority_threads.sort(key=lambda x: x[2])

    for cid, title, ctime, tag in priority_threads:
        # Always show tag in brackets (mandatory)
        tag_str = f"[{tag}] "
        index_lines.append(
            f"{tag_str}{title}\n" f"  ID: {cid} | Created: {ts_to_local_str(ctime)}\n\n"
        )

    # Generate coverage report with dynamic tags
    coverage_lines = [
        "\n" + "=" * 70,
        "COVERAGE AUDIT",
        "=" * 70,
        f"Included threads (total): {included_count}",
    ]
    for tag, count in sorted(tag_counts.items()):
        coverage_lines.append(f"  - [{tag}]: {count}")
    coverage_lines.append("")

    return index_lines, coverage_lines
