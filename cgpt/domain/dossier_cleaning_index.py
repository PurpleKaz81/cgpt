import re
from typing import Any, Dict, List, Optional, Tuple

from cgpt.core.io import coerce_create_time, ts_to_local_str
from cgpt.domain.config_schema import _get_short_tag, matches_thread_filter
from cgpt.domain.conversations import conv_id_and_title


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
        for i, (_score, _cid, title, ctime) in enumerate(scored_convs[:5], 1):
            date_str = ts_to_local_str(ctime).split()[0] if ctime else "Unknown"
            index_lines.append(f"  {i}. [{date_str}] {title}\n")
        index_lines.append("\n")

    # Add section navigation
    index_lines.append("### Sections\n\n")
    section_num = 0

    # Find all section headers (##, ===, etc.)
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.startswith(("##", "===")) or re.match(r"^\d+\.", line):
            section_num += 1
            header = line.strip().lstrip("#").strip().lstrip("=").strip()
            if header and header != "WORKING INDEX":  # Don't index ourselves
                index_lines.append(f"  {section_num:02d}. Line ~{i}: {header}\n")

    index_lines.append("\n---\n\n")
    return index_lines


def _generate_working_index_with_tags(
    txt: str,
    conversations: Optional[List[Dict[str, Any]]] = None,
    topics: Optional[List[str]] = None,
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
