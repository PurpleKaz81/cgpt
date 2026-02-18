import sqlite3
import sys
import time
from pathlib import Path
from typing import List, Tuple

from cgpt.core.io import coerce_create_time
from cgpt.domain.conversations import (
    conv_id_and_title,
    extract_messages_best_effort,
    find_conversations_json,
    load_json,
    normalize_conversations,
)


def _init_index(db_path: Path) -> None:
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS conv_meta (id TEXT PRIMARY KEY, title TEXT, create_time REAL)"
        )
        try:
            cur.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS conv_search USING fts5(title, content, cid UNINDEXED)"
            )
        except sqlite3.OperationalError:
            # FTS5 not available in this sqlite build
            print(
                "WARNING: SQLite FTS5 not available; full-text index disabled",
                file=sys.stderr,
            )
        conn.commit()
    finally:
        conn.close()

def index_export(
    root: Path, db_path: Path, reindex: bool = False, show_progress: bool = True
) -> None:
    """Index conversations under `root` into `db_path`.

    If `reindex` is True the existing indexed rows will be cleared first.
    This is a lightweight, best-effort implementation intended to make searches
    faster for typical-sized exports.
    """
    data_file = find_conversations_json(root)
    if not data_file:
        return
    data = load_json(data_file)
    convs = normalize_conversations(data)

    db_path.parent.mkdir(parents=True, exist_ok=True)
    _init_index(db_path)
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        if reindex:
            try:
                cur.execute("DELETE FROM conv_meta")
            except Exception:
                pass
            try:
                cur.execute("DELETE FROM conv_search")
            except Exception:
                pass

        conn.execute("BEGIN")
        total = len(convs)
        i = 0
        start = time.time()
        last_update = start
        spinner = ["|", "/", "-", "\\"]
        spin_idx = 0

        def _fmt_eta(seconds: float) -> str:
            s = int(seconds + 0.5)
            m, sec = divmod(s, 60)
            h, m = divmod(m, 60)
            if h:
                return f"{h}:{m:02d}:{sec:02d}"
            return f"{m:02d}:{sec:02d}"

        for c in convs:
            cid, title = conv_id_and_title(c)
            if not cid:
                continue
            ctime = coerce_create_time(c.get("create_time"))
            msgs = extract_messages_best_effort(c)
            content = "\n".join(m.text for m in msgs)
            try:
                cur.execute(
                    "REPLACE INTO conv_meta (id, title, create_time) VALUES (?, ?, ?)",
                    (cid, title, ctime),
                )
                # keep conv_search in sync: remove any prior entries for this cid
                try:
                    cur.execute("DELETE FROM conv_search WHERE cid = ?", (cid,))
                    cur.execute(
                        "INSERT INTO conv_search (title, content, cid) VALUES (?, ?, ?)",
                        (title, content, cid),
                    )
                except sqlite3.OperationalError:
                    # FTS table not available; ignore silently
                    pass
            except Exception:
                # best-effort: skip problematic conversations
                continue
            i += 1
            if show_progress:
                now = time.time()
                # update display at most every 0.25s, or on final item
                if i == total or (now - last_update >= 0.25):
                    elapsed = now - start if now > start else 0.0
                    rate = (i / elapsed) if elapsed > 0 else None
                    if rate and rate > 0:
                        rem = total - i
                        eta = rem / rate
                        eta_str = _fmt_eta(eta)
                    else:
                        eta_str = "--:--"
                    spin = spinner[spin_idx % len(spinner)]
                    spin_idx += 1
                    last_update = now
                    # carriage-return line to update progress in-place
                    print(
                        f"\rIndexed {i}/{total} {spin} ETA: {eta_str}",
                        end="",
                        file=sys.stderr,
                        flush=True,
                    )
        if show_progress:
            # finish line
            print("", file=sys.stderr)
        conn.commit()
    finally:
        conn.close()

def query_index(db_path: Path, q: str, where: str = "all") -> List[Tuple[str, str]]:
    """Query the index and return list of (cid, title).

    Falls back to empty list on any error.
    """
    if not db_path.exists():
        return []
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        try:
            if where == "title":
                cur.execute(
                    "SELECT cid, title FROM conv_search WHERE title MATCH ?", (q,)
                )
            elif where == "messages":
                cur.execute(
                    "SELECT cid, title FROM conv_search WHERE content MATCH ?", (q,)
                )
            else:
                cur.execute(
                    "SELECT cid, title FROM conv_search WHERE conv_search MATCH ?", (q,)
                )
            rows = cur.fetchall()
            return [(r[0], r[1]) for r in rows]
        except sqlite3.OperationalError:
            return []
    finally:
        conn.close()

def build_fts_query(terms: List[str], and_terms: bool) -> str:
    """Build a simple FTS5 MATCH query from terms.

    Wrap each term in double-quotes and join with AND/OR.
    """
    parts: List[str] = []
    for t in terms:
        if not t:
            continue
        # escape double quotes inside term
        tp = t.replace('"', '""')
        parts.append(f'"{tp}"')
    if not parts:
        return ""
    return (" AND ".join(parts)) if and_terms else (" OR ".join(parts))
