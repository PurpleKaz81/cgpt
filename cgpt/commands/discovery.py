import argparse
from pathlib import Path
from typing import List

from cgpt.commands.dossier_roots import resolve_root
from cgpt.core.color import _colorize_title_with_topic, _colorize_title_with_topics
from cgpt.core.layout import die, ensure_layout, home_dir
from cgpt.core.project import get_active_project, set_project_extract_root
from cgpt.domain.conversations import (
    conv_id_and_title,
    conversation_messages_blob,
    find_conversations_json,
    load_json,
    normalize_conversations,
)
from cgpt.domain.indexing import build_fts_query, index_matches_root, query_index


def _resolve_search_root(args: argparse.Namespace) -> Path:
    home = home_dir(getattr(args, "home", None))
    _, _, dossiers_dir = ensure_layout(home)
    active_project = get_active_project(dossiers_dir)
    root, _, _ = resolve_root(home, getattr(args, "root", None), active_project)
    if active_project:
        set_project_extract_root(dossiers_dir, active_project, root)
    return root


def cmd_ids(args: argparse.Namespace) -> None:
    root = _resolve_search_root(args)
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
    root = _resolve_search_root(args)
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
    root = _resolve_search_root(args)

    # Try using SQLite FTS index only when scoped to the same export root.
    db_path = extracted_dir / "cgpt_index.db"
    if db_path.exists() and index_matches_root(db_path, root):
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

    terms_lower = [term.lower() for term in terms]

    for c in convs:
        cid, title = conv_id_and_title(c)
        if not cid:
            continue

        title_lower = (title or "").lower()
        messages_lower = ""
        if where in ("messages", "all"):
            messages_lower = conversation_messages_blob(c).lower()

        checks: List[bool]
        if where == "title":
            checks = [term in title_lower for term in terms_lower]
        elif where == "messages":
            checks = [term in messages_lower for term in terms_lower]
        elif where == "all":
            checks = [
                (term in title_lower) or (term in messages_lower)
                for term in terms_lower
            ]
        else:
            die(f"Invalid --where value: {where}")

        hit = all(checks) if and_terms else any(checks)

        if hit:
            colored_title = _colorize_title_with_topics(title or "", terms)
            print(f"{cid}\t{colored_title}")
