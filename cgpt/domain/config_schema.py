import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from cgpt.core.io import coerce_create_time, ts_to_local_str
from cgpt.core.layout import die


def _config_schema_error(field: str, detail: str) -> None:
    die(f"Invalid config schema for '{field}': {detail}")

def _config_require_keys(
    obj: Dict[str, Any], *, allowed: Set[str], field: str
) -> None:
    unknown = sorted(k for k in obj if k not in allowed)
    if unknown:
        _config_schema_error(field, f"unknown key(s): {', '.join(unknown)}")

def _config_require_string_list(value: Any, *, field: str) -> None:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        _config_schema_error(field, "expected a list of strings")

def validate_column_config_schema(config: Any) -> Dict[str, Any]:
    if not isinstance(config, dict):
        _config_schema_error("root", "expected a JSON object")

    allowed_top = {
        "column_name",
        "column_objective",
        "thread_filters",
        "segment_scoring",
        "op_v2_constraints",
        "dossier_contract",
        "control_layer_sections",
        "search_terms",
    }
    _config_require_keys(config, allowed=allowed_top, field="root")

    for key in ("column_name", "column_objective", "dossier_contract"):
        if key in config and not isinstance(config[key], str):
            _config_schema_error(key, "expected a string")

    if "search_terms" in config:
        _config_require_string_list(config["search_terms"], field="search_terms")

    if "thread_filters" in config:
        thread_filters = config["thread_filters"]
        if not isinstance(thread_filters, dict):
            _config_schema_error("thread_filters", "expected an object")
        _config_require_keys(
            thread_filters,
            allowed={"include", "exclude"},
            field="thread_filters",
        )
        include = thread_filters.get("include", {})
        if not isinstance(include, dict):
            _config_schema_error("thread_filters.include", "expected an object")
        for bucket, terms in include.items():
            if not isinstance(bucket, str) or not bucket.strip():
                _config_schema_error(
                    "thread_filters.include", "bucket names must be non-empty strings"
                )
            _config_require_string_list(
                terms, field=f"thread_filters.include.{bucket}"
            )
        exclude = thread_filters.get("exclude", [])
        _config_require_string_list(exclude, field="thread_filters.exclude")

    if "segment_scoring" in config:
        segment_scoring = config["segment_scoring"]
        if not isinstance(segment_scoring, dict):
            _config_schema_error("segment_scoring", "expected an object")
        _config_require_keys(
            segment_scoring,
            allowed={"mechanism_terms", "bridging_terms", "context_window", "min_score"},
            field="segment_scoring",
        )
        if "mechanism_terms" in segment_scoring:
            _config_require_string_list(
                segment_scoring["mechanism_terms"],
                field="segment_scoring.mechanism_terms",
            )
        if "bridging_terms" in segment_scoring:
            _config_require_string_list(
                segment_scoring["bridging_terms"],
                field="segment_scoring.bridging_terms",
            )
        if "context_window" in segment_scoring:
            context_window = segment_scoring["context_window"]
            if isinstance(context_window, bool) or not isinstance(context_window, int):
                _config_schema_error(
                    "segment_scoring.context_window", "expected an integer"
                )
            if context_window < 0:
                _config_schema_error(
                    "segment_scoring.context_window", "must be >= 0"
                )
        if "min_score" in segment_scoring:
            min_score = segment_scoring["min_score"]
            if isinstance(min_score, bool) or not isinstance(min_score, (int, float)):
                _config_schema_error("segment_scoring.min_score", "expected a number")
            if float(min_score) < 0.0:
                _config_schema_error("segment_scoring.min_score", "must be >= 0")

    if "op_v2_constraints" in config:
        _config_require_string_list(
            config["op_v2_constraints"], field="op_v2_constraints"
        )

    if "control_layer_sections" in config:
        control_sections = config["control_layer_sections"]
        if not isinstance(control_sections, dict):
            _config_schema_error("control_layer_sections", "expected an object")
        _config_require_keys(
            control_sections,
            allowed={
                "scope_router",
                "do_not_repeat_rules",
                "mechanism_focus",
                "evidence_vs_inference",
                "stress_tests",
            },
            field="control_layer_sections",
        )
        for key in ("scope_router", "mechanism_focus", "evidence_vs_inference"):
            if key in control_sections and not isinstance(control_sections[key], str):
                _config_schema_error(f"control_layer_sections.{key}", "expected a string")
        if "do_not_repeat_rules" in control_sections:
            _config_require_string_list(
                control_sections["do_not_repeat_rules"],
                field="control_layer_sections.do_not_repeat_rules",
            )
        if "stress_tests" in control_sections:
            _config_require_string_list(
                control_sections["stress_tests"],
                field="control_layer_sections.stress_tests",
            )

    return config

def load_column_config(config_file: str) -> Dict[str, Any]:
    """Load column-specific constraints from JSON config file."""
    config_path = Path(config_file).expanduser().resolve()
    if not config_path.exists():
        die(f"Config file not found: {config_file}")
    try:
        with open(config_path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        die(f"Error loading config: {e}")
    return validate_column_config_schema(data)

def matches_thread_filter(
    title: str, config: Dict[str, Any]
) -> Tuple[bool, Optional[str]]:
    """Check if thread title matches include/exclude filters. Returns (include, tag)."""
    if not title:
        return False, None

    title_lower = title.lower()
    filters = config.get("thread_filters", {})
    exclude_list = filters.get("exclude", [])
    include_dict = filters.get("include", {})

    # Check exclude list first
    for exclude_term in exclude_list:
        if exclude_term.lower() in title_lower:
            return False, None

    # Check include buckets
    for bucket_name, terms in include_dict.items():
        for term in terms:
            if term.lower() in title_lower:
                return True, bucket_name

    return False, None

def generate_completeness_check(
    convs: List[Dict[str, Any]], config: Dict[str, Any]
) -> str:
    """Generate completeness metadata line with basic statistics."""
    if not convs:
        return "No conversations found."

    # Find date range
    dates = []
    for conv in convs:
        ctime = coerce_create_time(conv.get("create_time"))
        if ctime:
            dates.append(ctime)

    if not dates:
        return "No date information available."

    latest_date = max(dates)
    latest_str = ts_to_local_str(latest_date).split()[0]

    # Count matches after a certain date
    now = datetime.now(tz=timezone.utc).timestamp()
    recent_matches = sum(1 for d in dates if now - d < 7 * 86400)

    metadata = (
        f"Searched conversations up to {ts_to_local_str(now).split()[0]}.\n"
        f"Last relevant match: {latest_str}.\n"
        f"Recent matches (< 7 days): {recent_matches}.\n"
        f"Total conversations in dossier: {len(convs)}."
    )

    return metadata

def generate_control_layer(config: Dict[str, Any]) -> str:
    """Generate front-matter control layer with scope router + constraints."""
    lines = [
        "=" * 70,
        "CONTROL LAYER — " + config.get("column_name", "Report"),
        "=" * 70,
        "",
    ]

    control_sections = config.get("control_layer_sections", {})

    # Scope router
    if "scope_router" in control_sections:
        lines.append("SCOPE ROUTER")
        lines.append("")
        lines.append(control_sections["scope_router"])
        lines.append("")

    # Do-not-repeat rules
    if "do_not_repeat_rules" in control_sections:
        lines.append("DO-NOT-REPEAT RULES")
        lines.append("")
        for rule in control_sections["do_not_repeat_rules"]:
            lines.append(f"• {rule}")
        lines.append("")

    # Mechanism focus
    if "mechanism_focus" in control_sections:
        lines.append("MECHANISM FOCUS (from OP v2)")
        lines.append("")
        lines.append(control_sections["mechanism_focus"])
        lines.append("")

    # Evidence vs inference
    if "evidence_vs_inference" in control_sections:
        lines.append("EVIDENCE VS INFERENCE")
        lines.append("")
        lines.append(control_sections["evidence_vs_inference"])
        lines.append("")

    # Stress tests
    if "stress_tests" in control_sections:
        lines.append("STRESS TESTS")
        lines.append("")
        for test in control_sections["stress_tests"]:
            lines.append(f"• {test}")
        lines.append("")

    lines.append("=" * 70)
    lines.append("")

    return "\n".join(lines)

def _get_short_tag(bucket_name: Optional[str]) -> str:
    """
    Map config bucket names to short machine-readable tags.
    Derives tag dynamically from bucket name (e.g., 'primary_research' -> 'PRIMARY').
    """
    if not bucket_name:
        return "OTHER"

    # Generate tag from bucket name: use first word, uppercase, max 10 chars
    tag = bucket_name.split("_")[0].upper()[:10]
    return tag if tag else "OTHER"
