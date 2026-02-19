import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from cgpt.core.io import ts_to_local_str


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

    for _group_name, items in groups.items():
        root = items[0]
        root_title = root["title"] or "Untitled"
        branch_count = len(items) - 1
        create_time = root["ctime"]

        section_label = f"Line ~{line_num}: {root_title}"
        if branch_count > 0:
            section_label += (
                f" (+{branch_count} branch{'es' if branch_count != 1 else ''})"
            )
        section_label += f" - {ts_to_local_str(create_time)[:10]}"
        toc.append(f"  {section_label}\n")

        # estimate lines per conversation: ~20-30 lines per branch, messages vary
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
    all_sources: List[Tuple[str, str]] = []

    for conv_num, (_, items) in enumerate(group_order, start=1):
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
