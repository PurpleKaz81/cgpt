import argparse
import re
from pathlib import Path
from typing import List

from cgpt.core.color import _colorize_title_with_topic, _colorize_title_with_topics
from cgpt.core.layout import default_root, die, ensure_layout, home_dir
from cgpt.domain.conversations import (
    compile_topic_pattern,
    conv_id_and_title,
    conversation_matches_text,
    find_conversations_json,
    load_json,
    normalize_conversations,
)
from cgpt.domain.indexing import build_fts_query, query_index


def cmd_ids(args: argparse.Namespace) -> None:
    home = home_dir(args.home)
    _, extracted_dir, _ = ensure_layout(home)
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
    for c in convs:
        cid, title = conv_id_and_title(c)
        if cid:
            print(f"{cid}\t{title}")

def cmd_find(args: argparse.Namespace) -> None:
    query_raw = args.query.strip()
    q = query_raw.lower()
    if not query_raw:
        die("Query cannot be empty.")
    home = home_dir(args.home)
    _, extracted_dir, _ = ensure_layout(home)
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
    for c in convs:
        cid, title = conv_id_and_title(c)
        if cid and q in (title or "").lower():
            colored = _colorize_title_with_topic(title or "", query_raw)
            print(f"{cid}\t{colored}")

def cmd_search(args: argparse.Namespace) -> None:
    # Support both legacy single positional `query` and new multi-term `--terms`.
    query_raw = getattr(args, "query", None) or ""
    terms: List[str] = []
    if getattr(args, "terms", None):
        terms = [t for t in args.terms if t]
    elif query_raw:
        terms = [query_raw]
    if not terms:
        die("Query cannot be empty.")
    and_terms = bool(getattr(args, "and_terms", False))

    # Resolve where: prefer explicit --where (`where_opt`), then positional `where`, then default 'title'
    where = getattr(args, "where_opt", None) or getattr(args, "where", None) or "title"

    home = home_dir(getattr(args, "home", None))
    _, extracted_dir, _ = ensure_layout(home)
    root = (
        Path(args.root).expanduser().resolve()
        if getattr(args, "root", None)
        else default_root(extracted_dir)
    )

    # Try using SQLite FTS index if present for faster searches
    db_path = extracted_dir / "cgpt_index.db"
    if db_path.exists():
        fts_q = build_fts_query(terms, and_terms)
        if fts_q:
            rows = query_index(db_path, fts_q, where=where)
            if rows:
                for cid, title in rows:
                    colored_title = _colorize_title_with_topics(title or "", terms)
                    print(f"{cid}\t{colored_title}")
                return

    data_file = find_conversations_json(root)
    if not data_file:
        die(f"No conversations JSON found under {root}")
    data = load_json(data_file)
    convs = normalize_conversations(data)

    # For fallback scanning: compile an OR regex for quick checks; use per-term checks for AND.
    topic_re = compile_topic_pattern(terms)

    for c in convs:
        cid, title = conv_id_and_title(c)
        if not cid:
            continue

        hit = False
        # Title checks
        if where in ("title", "all"):
            t = title or ""
            if and_terms:
                ok_title = all((term.lower() in t.lower()) for term in terms)
            else:
                ok_title = bool(topic_re.search(t))
            if ok_title:
                hit = True

        # Message checks (AND/OR semantics)
        if not hit and where in ("messages", "all"):
            if and_terms:
                ok_msgs = True
                for term in terms:
                    p = re.compile(re.escape(term), re.IGNORECASE)
                    if not conversation_matches_text(c, p):
                        ok_msgs = False
                        break
            else:
                ok_msgs = conversation_matches_text(c, topic_re)
            if ok_msgs:
                hit = True

        if hit:
            colored_title = _colorize_title_with_topics(title or "", terms)
            print(f"{cid}\t{colored_title}")

