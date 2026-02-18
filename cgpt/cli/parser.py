import argparse

from cgpt.commands.discovery import cmd_find, cmd_ids, cmd_search
from cgpt.commands.dossier import (
    cmd_build_dossier,
    cmd_make_dossiers,
    cmd_quick,
    cmd_recent,
)
from cgpt.commands.extract_index import cmd_extract, cmd_index, cmd_latest_zip
from cgpt.commands.init_doctor import cmd_doctor, cmd_init
from cgpt.core.constants import __version__
from cgpt.core.io import parse_context


def _add_split_flags(parser: argparse.ArgumentParser, split_help: str) -> None:
    """Add --split/--no-split flags with tri-state default for env fallback."""
    grp = parser.add_mutually_exclusive_group()
    grp.add_argument(
        "--split",
        dest="split",
        action="store_true",
        default=None,
        help=split_help,
    )
    grp.add_argument(
        "--no-split",
        dest="split",
        action="store_false",
        help="Disable split output (overrides CGPT_DEFAULT_SPLIT).",
    )

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cgpt",
        description="ChatGPT export helper (zips → extracted → dossiers).",
    )
    p.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    # CLI-level color control: --color / --no-color
    color_grp = p.add_mutually_exclusive_group()
    color_grp.add_argument(
        "--color", dest="color", action="store_true", help="Force-enable ANSI colors"
    )
    color_grp.add_argument(
        "--no-color",
        dest="no_color",
        action="store_true",
        help="Force-disable ANSI colors",
    )
    p.add_argument(
        "--home",
        help="Home folder containing zips/, extracted/, dossiers/. Default: $CGPT_HOME, auto-detected, or CWD",
    )
    p.add_argument(
        "--quiet",
        dest="quiet",
        action="store_true",
        help="Suppress non-error output (useful in scripts)",
    )
    p.add_argument(
        "--default-mode",
        dest="default_mode",
        choices=["full", "excerpts"],
        default=None,
        help="Set preferred default mode for dossier creation (overrides CGPT_DEFAULT_MODE)",
    )
    # If no subcommand is provided, we'll default to extracting the newest ZIP.
    sub = p.add_subparsers(dest="cmd", required=False)

    a = sub.add_parser(
        "init", help="Create/verify required folders: zips/, extracted/, dossiers/"
    )
    a.set_defaults(func=cmd_init)

    a = sub.add_parser(
        "doctor",
        help="Validate runtime/developer environment and folder layout",
    )
    a.add_argument(
        "--fix",
        action="store_true",
        help="Create missing home folders if possible",
    )
    a.add_argument(
        "--dev",
        action="store_true",
        help="Include contributor tooling checks (ruff/node/npx/tox/interpreters)",
    )
    a.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures (exit code 2)",
    )
    a.set_defaults(func=cmd_doctor)

    a = sub.add_parser("latest-zip", help="Print newest ZIP in zips/")
    a.set_defaults(func=cmd_latest_zip)

    a = sub.add_parser(
        "extract",
        help="Extract a ZIP into extracted/<zip_stem>/ (defaults to newest ZIP)",
    )
    a.add_argument("zip", nargs="?", help="Path to ZIP (optional)")
    a.add_argument(
        "--no-index",
        dest="no_index",
        action="store_true",
        help="Do not update the search index after extracting",
    )
    a.add_argument(
        "--reindex",
        dest="reindex",
        action="store_true",
        help="Force rebuild of the search index after extracting",
    )
    a.set_defaults(func=cmd_extract)

    a = sub.add_parser(
        "index",
        help="(Re)build the search index from an extracted export (uses FTS5 when available)",
    )
    a.add_argument(
        "--root", help="Extracted folder to scan (defaults to extracted/latest)"
    )
    a.add_argument(
        "--reindex",
        dest="reindex",
        action="store_true",
        help="Force rebuild of the search index",
    )
    a.add_argument(
        "--db",
        dest="db",
        help="Path to index DB file (defaults to extracted/cgpt_index.db)",
    )
    a.set_defaults(func=cmd_index)

    # Short alias
    a = sub.add_parser("x", help="Alias for extract")
    a.add_argument("zip", nargs="?", help="Path to ZIP (optional)")
    a.add_argument(
        "--no-index",
        dest="no_index",
        action="store_true",
        help="Do not update the search index after extracting",
    )
    a.add_argument(
        "--reindex",
        dest="reindex",
        action="store_true",
        help="Force rebuild of the search index after extracting",
    )
    a.set_defaults(func=cmd_extract)

    a = sub.add_parser("ids", help="Print id<TAB>title for all conversations")
    a.add_argument(
        "--root", help="Extracted folder to scan (defaults to extracted/latest)"
    )
    a.set_defaults(func=cmd_ids)

    # Short alias
    a = sub.add_parser("i", help="Alias for ids")
    a.add_argument(
        "--root", help="Extracted folder to scan (defaults to extracted/latest)"
    )
    a.set_defaults(func=cmd_ids)

    a = sub.add_parser(
        "find", help="Find conversations whose titles match query (case-insensitive)"
    )
    a.add_argument("query")
    a.add_argument(
        "--root", help="Extracted folder to scan (defaults to extracted/latest)"
    )
    a.set_defaults(func=cmd_find)

    # Short alias
    a = sub.add_parser("f", help="Alias for find")
    a.add_argument("query")
    a.add_argument(
        "--root", help="Extracted folder to scan (defaults to extracted/latest)"
    )
    a.set_defaults(func=cmd_find)

    a = sub.add_parser(
        "search", help="Search in titles and/or message text (case-insensitive)"
    )
    a.add_argument("query", nargs="?", default=None)
    a.add_argument(
        "where",
        nargs="?",
        choices=["title", "messages", "all"],
        help="Optional positional: where to search (title|messages|all)",
    )
    a.add_argument(
        "--terms",
        nargs="+",
        help="One or more search terms (use with --and to require all)",
    )
    a.add_argument(
        "--and",
        dest="and_terms",
        action="store_true",
        help="Require ALL terms to match (default is OR)",
    )
    a.add_argument(
        "--where",
        dest="where_opt",
        choices=["title", "messages", "all"],
        default=None,
        help="Where to search: title (default), messages, or all",
    )
    a.add_argument(
        "--root", help="Extracted folder to scan (defaults to extracted/latest)"
    )
    a.set_defaults(func=cmd_search)

    a = sub.add_parser(
        "make-dossiers", help="Write one or more formats per selected conversation ID"
    )
    a.add_argument(
        "--root", help="Extracted folder to scan (defaults to extracted/latest)"
    )
    a.add_argument("--ids-file", help="Text file with one id per line")
    a.add_argument("--ids", nargs="*", help="One or more IDs")
    a.add_argument(
        "--format",
        nargs="+",
        choices=["txt", "md", "docx"],
        default=["txt"],
        help=(
            "Output format(s) for per-conversation dossiers (default: txt). "
            "Examples: --format txt  # plain text (default); "
            "--format md docx  # produce Markdown and Word .docx; "
            "--format txt md docx  # produce all three"
        ),
    )
    a.set_defaults(func=cmd_make_dossiers)

    a = sub.add_parser(
        "build-dossier",
        help="Build a single combined dossier with time + branch nesting",
    )
    a.add_argument("--topic", help="Single topic keyword (for excerpts mode)")
    a.add_argument(
        "--topics", nargs="*", help="One or more topics (OR logic) (for excerpts mode)"
    )
    a.add_argument(
        "--mode",
        choices=["full", "excerpts"],
        default=None,
        help="full = include everything; excerpts = topic-only + context",
    )
    a.add_argument(
        "--context",
        type=parse_context,
        default=2,
        help="In excerpts mode, include +/- N messages around matches",
    )
    a.add_argument(
        "--root", help="Extracted folder to scan (defaults to extracted/latest)"
    )
    a.add_argument("--ids-file", help="Text file with one id per line")
    a.add_argument("--ids", nargs="*", help="One or more IDs")
    a.add_argument(
        "--format",
        nargs="+",
        choices=["txt", "md", "docx"],
        help=(
            "One or more output formats: txt (default), md, docx. "
            "Examples: --format txt; --format md docx; --format txt md docx"
        ),
        default=["txt"],
    )
    _add_split_flags(
        a,
        "Generate two TXT files: dossier_raw.txt (full) and dossier_raw__working.txt (cleaned, deduplicated, deliverables-only).",
    )
    a.add_argument(
        "--dedup",
        action="store_true",
        default=True,
        help="Enable deduplication in working output (default: True)",
    )
    a.add_argument(
        "--no-dedup",
        dest="dedup",
        action="store_false",
        help="Disable deduplication in working output",
    )
    a.add_argument(
        "--patterns-file",
        help="Path to file with deliverable patterns (one per line). Default patterns: ##, Constraint, Draft, Decision, Output, Result",
    )
    a.add_argument(
        "--used-links-file",
        help="Path to file with URLs already used in drafts (one per line). These will be prioritized in source lists.",
    )
    a.add_argument(
        "--config",
        help="Path to column config file (JSON) for segment filtering and control layer generation",
    )
    a.add_argument(
        "--name",
        help="Project name for organizing output. Creates dossiers/{name}/ subfolder.",
    )
    a.set_defaults(func=cmd_build_dossier)

    # Short alias
    a = sub.add_parser("d", help="Alias for build-dossier")
    a.add_argument("--topic", help="Single topic keyword (for excerpts mode)")
    a.add_argument(
        "--topics", nargs="*", help="One or more topics (OR logic) (for excerpts mode)"
    )
    a.add_argument("--mode", choices=["full", "excerpts"], default=None)
    a.add_argument("--context", type=parse_context, default=2)
    a.add_argument(
        "--root", help="Extracted folder to scan (defaults to extracted/latest)"
    )
    a.add_argument("--ids-file", help="Text file with one id per line")
    a.add_argument("--ids", nargs="*", help="One or more IDs")
    a.add_argument(
        "--format",
        nargs="+",
        choices=["txt", "md", "docx"],
        default=["txt"],
    )
    _add_split_flags(
        a,
        "Generate two TXT files: dossier_raw.txt (full) and dossier_raw__working.txt (cleaned, deduplicated, deliverables-only).",
    )
    a.add_argument(
        "--dedup",
        action="store_true",
        default=True,
        help="Enable deduplication in working output (default: True)",
    )
    a.add_argument(
        "--no-dedup",
        dest="dedup",
        action="store_false",
        help="Disable deduplication in working output",
    )
    a.add_argument(
        "--patterns-file",
        help="Path to file with deliverable patterns (one per line). Default patterns: ##, Constraint, Draft, Decision, Output, Result",
    )
    a.add_argument(
        "--used-links-file",
        help="Path to file with URLs already used in drafts (one per line). These will be prioritized in source lists.",
    )
    a.add_argument(
        "--config",
        help="Path to column config file (JSON) for segment filtering and control layer generation",
    )
    a.add_argument(
        "--name",
        help="Project name for organizing output. Creates dossiers/{name}/ subfolder.",
    )
    a.set_defaults(func=cmd_build_dossier)

    # One-shot command for minimal typing
    a = sub.add_parser(
        "quick", help="Extract (if needed) → find by title → pick IDs → build dossier"
    )
    a.add_argument(
        "topics",
        nargs="+",
        help="One or more topic terms to match in conversation titles",
    )
    a.add_argument(
        "--and",
        dest="and_terms",
        action="store_true",
        help="Require ALL terms to appear in title (default is OR)",
    )
    a.add_argument("--mode", choices=["full", "excerpts"], default=None)
    a.add_argument("--context", type=parse_context, default=2)
    a.add_argument("--all", action="store_true", help="Select all matches (no prompt)")
    a.add_argument(
        "--where",
        choices=["title", "messages", "all"],
        default="title",
        help="Where to search when matching topics: title (default), messages, or all",
    )
    quick_recency = a.add_mutually_exclusive_group()
    quick_recency.add_argument(
        "--recent",
        dest="recent_count",
        type=int,
        default=None,
        help="Limit quick matching to the N most recent conversations before applying topic filters",
    )
    quick_recency.add_argument(
        "--days",
        dest="days_count",
        type=int,
        default=None,
        help="Limit quick matching to conversations created in the last N days before applying topic filters",
    )
    a.add_argument(
        "--root", help="Extracted folder to scan (defaults to extracted/latest)"
    )
    a.add_argument("--ids-file", help="Text file with one id per line")
    a.add_argument(
        "--format",
        nargs="+",
        choices=["txt", "md", "docx"],
        default=["txt"],
        help=(
            "Output formats for dossier (default: txt). "
            "Examples: python3 cgpt.py quick --format txt 'term1' 'term2'; "
            "python3 cgpt.py quick --format md docx 'research' 'analysis'"
        ),
    )
    _add_split_flags(
        a,
        "Generate two TXT files: dossier_raw.txt (full) and dossier_raw__working.txt (cleaned, deduplicated, deliverables-only).",
    )
    a.add_argument(
        "--dedup",
        action="store_true",
        default=True,
        help="Enable deduplication in working output (default: True)",
    )
    a.add_argument(
        "--no-dedup",
        dest="dedup",
        action="store_false",
        help="Disable deduplication in working output",
    )
    a.add_argument(
        "--patterns-file",
        help="Path to file with deliverable patterns (one per line). Default patterns: ##, Constraint, Draft, Decision, Output, Result",
    )
    a.add_argument(
        "--used-links-file",
        help="Path to file with URLs already used in drafts (one per line).",
    )
    a.add_argument(
        "--config",
        help="Path to column config file (JSON) for segment filtering and control layer generation",
    )
    a.add_argument(
        "--name",
        help="Project name for organizing output. Creates dossiers/{name}/ subfolder.",
    )
    a.set_defaults(func=cmd_quick)

    # Very short alias
    a = sub.add_parser("q", help="Alias for quick")
    a.add_argument("topics", nargs="+")
    a.add_argument("--and", dest="and_terms", action="store_true")
    a.add_argument("--mode", choices=["full", "excerpts"], default=None)
    a.add_argument("--context", type=parse_context, default=2)
    a.add_argument("--all", action="store_true")
    a.add_argument(
        "--where",
        choices=["title", "messages", "all"],
        default="title",
        help="Where to search when matching topics: title (default), messages, or all",
    )
    quick_recency = a.add_mutually_exclusive_group()
    quick_recency.add_argument(
        "--recent",
        dest="recent_count",
        type=int,
        default=None,
        help="Limit quick matching to the N most recent conversations before applying topic filters",
    )
    quick_recency.add_argument(
        "--days",
        dest="days_count",
        type=int,
        default=None,
        help="Limit quick matching to conversations created in the last N days before applying topic filters",
    )
    a.add_argument(
        "--root", help="Extracted folder to scan (defaults to extracted/latest)"
    )
    a.add_argument("--ids-file", help="Text file with one id per line")
    a.add_argument(
        "--format",
        nargs="+",
        choices=["txt", "md", "docx"],
        default=["txt"],
    )
    _add_split_flags(
        a,
        "Generate two TXT files: dossier_raw.txt (full) and dossier_raw__working.txt (cleaned, deduplicated, deliverables-only).",
    )
    a.add_argument(
        "--dedup",
        action="store_true",
        default=True,
        help="Enable deduplication in working output (default: True)",
    )
    a.add_argument(
        "--no-dedup",
        dest="dedup",
        action="store_false",
        help="Disable deduplication in working output",
    )
    a.add_argument(
        "--patterns-file",
        help="Path to file with deliverable patterns (one per line). Default patterns: ##, Constraint, Draft, Decision, Output, Result",
    )
    a.add_argument(
        "--used-links-file",
        help="Path to file with URLs already used in drafts (one per line).",
    )
    a.add_argument(
        "--config",
        help="Path to column config file (JSON) for segment filtering and control layer generation",
    )
    a.add_argument(
        "--name",
        help="Project name for organizing output. Creates dossiers/{name}/ subfolder.",
    )
    a.set_defaults(func=cmd_quick)

    # Recent command: browse N most recent conversations interactively
    a = sub.add_parser(
        "recent",
        help="Show the N most recent conversations and select interactively",
    )
    a.add_argument(
        "count",
        type=int,
        nargs="?",
        default=30,
        help="Number of recent conversations to show (default: 30)",
    )
    a.add_argument("--all", action="store_true", help="Select all shown (no prompt)")
    a.add_argument(
        "--root", help="Extracted folder to scan (defaults to extracted/latest)"
    )
    a.add_argument(
        "--format",
        nargs="+",
        choices=["txt", "md", "docx"],
        default=["txt"],
        help="Output format(s) for dossier (default: txt)",
    )
    _add_split_flags(a, "Generate both raw and working TXT files.")
    a.add_argument(
        "--dedup",
        action="store_true",
        default=True,
        help="Enable deduplication in working output (default: True)",
    )
    a.add_argument(
        "--no-dedup",
        dest="dedup",
        action="store_false",
        help="Disable deduplication in working output",
    )
    a.add_argument(
        "--patterns-file",
        help="Path to file with deliverable patterns (one per line)",
    )
    a.add_argument(
        "--used-links-file",
        help="Path to file with URLs already used in drafts (one per line)",
    )
    a.add_argument(
        "--config",
        help="Path to column config file (JSON)",
    )
    a.add_argument(
        "--name",
        help="Project name for organizing output. Creates dossiers/{name}/ subfolder.",
    )
    a.add_argument("--mode", choices=["full", "excerpts"], default=None)
    a.add_argument("--context", type=parse_context, default=2)
    a.set_defaults(func=cmd_recent)

    # Short alias for recent
    a = sub.add_parser("r", help="Alias for recent")
    a.add_argument("count", type=int, nargs="?", default=30)
    a.add_argument("--all", action="store_true")
    a.add_argument("--root")
    a.add_argument(
        "--format", nargs="+", choices=["txt", "md", "docx"], default=["txt"]
    )
    _add_split_flags(a, "Generate both raw and working TXT files.")
    a.add_argument("--dedup", action="store_true", default=True)
    a.add_argument("--no-dedup", dest="dedup", action="store_false")
    a.add_argument("--patterns-file")
    a.add_argument("--used-links-file")
    a.add_argument("--config")
    a.add_argument("--name", help="Project name for organizing output.")
    a.add_argument("--mode", choices=["full", "excerpts"], default=None)
    a.add_argument("--context", type=parse_context, default=2)
    a.set_defaults(func=cmd_recent)

    return p

