import re
from typing import Dict, List, Optional, Tuple

from cgpt.core.io import normalize_text


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
    pattern = r"\{\s*['\"]?(?:" + "|".join(tool_keys) + r")[\'\"]?.*?\}"
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


def extract_research_artifacts(text: str) -> Tuple[str, List[str]]:
    """
    Extract tool-call artifacts (JSON, search fragments, etc.) into separate appendix.
    Returns (cleaned_text, artifacts_list) where artifacts_list is list of artifact strings.
    Also filters out any stray appendix headers that may have been included in text.
    """
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
    for _i, line in enumerate(lines):
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
