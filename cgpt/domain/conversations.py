import heapq
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from cgpt.core.constants import (
    JSON_DISCOVERY_BUCKET_LIMIT as _DEFAULT_JSON_DISCOVERY_BUCKET_LIMIT,
)
from cgpt.core.io import coerce_create_time, normalize_text
from cgpt.core.layout import die

JSON_DISCOVERY_BUCKET_LIMIT = _DEFAULT_JSON_DISCOVERY_BUCKET_LIMIT

def _json_candidate_priority(path: Path) -> int:
    name = path.name.lower()
    if name == "conversations.json":
        return 30
    if name.startswith("conversations") and name.endswith(".json"):
        return 25
    if "conversation" in name and name.endswith(".json"):
        return 20
    return 0

def _safe_file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return -1

def load_json_loose(path: Path) -> Optional[Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def _looks_like_conversation_record(record: Any) -> bool:
    if not isinstance(record, dict):
        return False
    has_id = any(k in record for k in ("id", "conversation_id", "uuid"))
    has_message_data = isinstance(record.get("mapping"), dict) or isinstance(
        record.get("messages"), list
    )
    has_metadata = isinstance(record.get("title"), str) or isinstance(
        record.get("name"), str
    )
    has_time = "create_time" in record
    return bool(has_id and (has_message_data or has_metadata or has_time))

def _looks_like_conversations_payload(data: Any) -> bool:
    if isinstance(data, list):
        return any(_looks_like_conversation_record(item) for item in data[:50])
    if isinstance(data, dict):
        convs = data.get("conversations")
        if isinstance(convs, list):
            return any(_looks_like_conversation_record(item) for item in convs[:50])
        values = list(data.values())[:50]
        if values and all(isinstance(v, dict) for v in values):
            return any(_looks_like_conversation_record(v) for v in values)
    return False

def _push_json_candidate(
    heap: List[Tuple[int, str, Path]], path: Path, limit: int
) -> None:
    if limit <= 0:
        return
    entry = (_safe_file_size(path), str(path), path)
    if len(heap) < limit:
        heapq.heappush(heap, entry)
        return
    if entry[:2] > heap[0][:2]:
        heapq.heapreplace(heap, entry)

def find_conversations_json(root: Path) -> Optional[Path]:
    buckets: Dict[int, List[Tuple[int, str, Path]]] = {30: [], 25: [], 20: [], 0: []}
    saw_json = False
    for path in root.rglob("*.json"):
        saw_json = True
        priority = _json_candidate_priority(path)
        bucket = priority if priority in buckets else 0
        _push_json_candidate(buckets[bucket], path, JSON_DISCOVERY_BUCKET_LIMIT)

    if not saw_json:
        return None

    ordered: List[Path] = []
    for priority in (30, 25, 20, 0):
        ranked = sorted(
            buckets[priority], key=lambda item: (item[0], item[1]), reverse=True
        )
        ordered.extend(item[2] for item in ranked)

    for candidate in ordered:
        data = load_json_loose(candidate)
        if data is None:
            continue
        if _looks_like_conversations_payload(data):
            return candidate
    return None

def load_json(p: Path) -> Any:
    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        die(f"Failed to parse JSON: {p}\n{e}")

def normalize_conversations(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, list):
        return [c for c in data if isinstance(c, dict)]
    if isinstance(data, dict):
        if isinstance(data.get("conversations"), list):
            return [c for c in data["conversations"] if isinstance(c, dict)]
        if data and all(isinstance(v, dict) for v in data.values()):
            out = []
            for k, v in data.items():
                if isinstance(v, dict):
                    merged = dict(v)
                    merged.setdefault("id", k)
                    out.append(merged)
            return out
    return []

def conv_id_and_title(c: Dict[str, Any]) -> Tuple[Optional[str], str]:
    cid = c.get("id") or c.get("conversation_id") or c.get("uuid")
    title = (
        (c.get("title") or c.get("name") or "")
        .replace("\t", " ")
        .replace("\n", " ")
        .strip()
    )
    return cid, title

def build_conversation_map_by_id(convs: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    by_id: Dict[str, Dict[str, Any]] = {}
    duplicates: Set[str] = set()
    for conv in convs:
        cid, _ = conv_id_and_title(conv)
        if not cid:
            continue
        if cid in by_id:
            duplicates.add(cid)
            continue
        by_id[cid] = conv
    if duplicates:
        die(
            "Duplicate conversation ID(s) found in export:\n"
            + "\n".join(sorted(duplicates))
        )
    return by_id

def render_content(content: Any) -> str:
    if not isinstance(content, dict):
        return ""
    ctype = content.get("content_type")
    parts = content.get("parts")
    if ctype == "text" and isinstance(parts, list):
        return "\n".join(str(p) for p in parts if p is not None).strip()
    if isinstance(parts, list) and parts:
        return "\n".join(str(p) for p in parts if p is not None).strip()
    if "text" in content and isinstance(content["text"], str):
        return content["text"].strip()
    return ""

@dataclass
class Msg:
    t: float
    role: str
    text: str

def extract_messages_best_effort(c: Dict[str, Any]) -> List[Msg]:
    msgs: List[Msg] = []

    mapping = c.get("mapping")
    if not isinstance(mapping, dict):
        flat = c.get("messages")
        if isinstance(flat, list):
            for m in flat:
                if not isinstance(m, dict):
                    continue
                t = coerce_create_time(m.get("create_time"))
                role = (m.get("author") or {}).get("role") or "unknown"
                text = render_content((m.get("content") or {})).strip()
                if text:
                    msgs.append(Msg(t=t, role=role, text=text))
        msgs.sort(key=lambda x: x.t)
        return msgs

    for node in mapping.values():
        if not isinstance(node, dict):
            continue
        m = node.get("message")
        if not isinstance(m, dict):
            continue
        t = coerce_create_time(m.get("create_time"))
        author = m.get("author") or {}
        role = author.get("role") or "unknown"
        content = m.get("content") or {}
        text = render_content(content).strip()
        if text:
            msgs.append(Msg(t=t, role=role, text=text))

    msgs.sort(key=lambda x: x.t)
    return msgs

def conversation_matches_text(c: Dict[str, Any], pat: re.Pattern) -> bool:
    """
    Return True if the compiled regex `pat` matches any message text or the conversation title.
    Uses the same message extraction logic as extract_messages_best_effort.
    """
    try:
        # Check messages
        msgs = extract_messages_best_effort(c)
        for m in msgs:
            if pat.search(m.text):
                return True
        # Fallback: check title/name fields
        title = c.get("title") or c.get("name") or ""
        if isinstance(title, str) and pat.search(title):
            return True
    except Exception:
        return False
    return False

def conversation_messages_blob(c: Dict[str, Any]) -> str:
    try:
        msgs = extract_messages_best_effort(c)
        return "\n".join(m.text for m in msgs)
    except Exception:
        return ""

def excerpt_messages(msgs: List[Msg], pattern: re.Pattern, context: int) -> List[Msg]:
    if not msgs:
        return []
    hits = [i for i, m in enumerate(msgs) if pattern.search(m.text)]
    if not hits:
        return []
    keep = set()
    for i in hits:
        for j in range(max(0, i - context), min(len(msgs), i + context + 1)):
            keep.add(j)
    return [msgs[i] for i in sorted(keep)]

def base_title(title: str) -> str:
    t = (title or "").strip()
    t = re.sub(r"^\s*Branch\s*[·\-:]\s*", "", t, flags=re.IGNORECASE)
    return t.strip()

def longest_common_prefix_len(
    a: List[Tuple[str, str]], b: List[Tuple[str, str]]
) -> int:
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i

def trim_branch_new_part(root_msgs: List[Msg], branch_msgs: List[Msg]) -> List[Msg]:
    ra = [(m.role, normalize_text(m.text)) for m in root_msgs]
    rb = [(m.role, normalize_text(m.text)) for m in branch_msgs]
    k = longest_common_prefix_len(ra, rb)
    return branch_msgs[k:]

def compile_topic_pattern(topics: List[str]) -> re.Pattern:
    parts = [re.escape(t) for t in topics if t.strip()]
    if not parts:
        # never match
        return re.compile(r"a^")
    return re.compile("|".join(parts), re.IGNORECASE)
