import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from cgpt.core.io import safe_slug
from cgpt.core.layout import die

_PROJECT_STATE_DIR = ".project"
_ACTIVE_PROJECT_FILE = "active.json"
_PROJECT_META_FILE = ".cgpt-project.json"


def _state_dir(dossiers_dir: Path) -> Path:
    return dossiers_dir / _PROJECT_STATE_DIR


def _active_state_path(dossiers_dir: Path) -> Path:
    return _state_dir(dossiers_dir) / _ACTIVE_PROJECT_FILE


def _project_meta_path(project_dir: Path) -> Path:
    return project_dir / _PROJECT_META_FILE


def normalize_project_name(name: str) -> str:
    normalized = safe_slug(name or "")
    if (
        not normalized
        or normalized in {".", ".."}
        or normalized.startswith(".")
        or normalized.endswith(".")
    ):
        die(
            "--name (project name) must contain at least one safe alphanumeric "
            "character after normalization and cannot start/end with '.'."
        )
    return normalized


def ensure_project_dir(dossiers_dir: Path, name: str) -> Path:
    normalized = normalize_project_name(name)
    project_dir = dossiers_dir / normalized
    if project_dir.exists() and not project_dir.is_dir():
        die(
            f"Project path exists but is not a directory: {project_dir}\n"
            "Rename or remove that file, then try again."
        )
    project_dir.mkdir(parents=True, exist_ok=True)
    _ensure_project_metadata(project_dir, normalized)
    return project_dir


def _ensure_project_metadata(project_dir: Path, normalized_name: str) -> None:
    meta_path = _project_meta_path(project_dir)
    now = datetime.now(tz=timezone.utc).isoformat()
    if meta_path.exists():
        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                data = {}
        except Exception:
            data = {}
        data["name"] = normalized_name
        data["updated_at"] = now
    else:
        data = {
            "name": normalized_name,
            "created_at": now,
            "updated_at": now,
            "extract_root": None,
        }
    meta_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def set_active_project(dossiers_dir: Path, name: str) -> str:
    normalized = normalize_project_name(name)
    ensure_project_dir(dossiers_dir, normalized)
    state_dir = _state_dir(dossiers_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "name": normalized,
        "updated_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    _active_state_path(dossiers_dir).write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    return normalized


def clear_active_project(dossiers_dir: Path) -> None:
    active_path = _active_state_path(dossiers_dir)
    if active_path.exists():
        active_path.unlink()


def get_active_project(dossiers_dir: Path) -> Optional[str]:
    active_path = _active_state_path(dossiers_dir)
    if not active_path.exists():
        return None
    try:
        data = json.loads(active_path.read_text(encoding="utf-8"))
    except Exception as e:
        die(
            f"Invalid project state file: {active_path}\n{e}\n"
            "Run `cgpt project clear` and set a project again."
        )
    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        die(
            f"Invalid project state file: {active_path}\n"
            "Missing or invalid 'name'. Run `cgpt project clear`."
        )
    return normalize_project_name(name)


def resolve_project_name(
    dossiers_dir: Path, explicit_name: Optional[str]
) -> Optional[str]:
    if explicit_name:
        return normalize_project_name(explicit_name)
    return get_active_project(dossiers_dir)


def project_output_dir(dossiers_dir: Path, project_name: Optional[str]) -> Path:
    if not project_name:
        return dossiers_dir
    return ensure_project_dir(dossiers_dir, project_name)


def _read_project_meta(project_dir: Path) -> Dict[str, Any]:
    meta_path = _project_meta_path(project_dir)
    if not meta_path.exists():
        return {}
    try:
        data = json.loads(meta_path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def set_project_extract_root(dossiers_dir: Path, name: str, root: Path) -> None:
    project_dir = ensure_project_dir(dossiers_dir, name)
    data = _read_project_meta(project_dir)
    if not data:
        data = {"name": normalize_project_name(name)}
    data["name"] = normalize_project_name(name)
    data["extract_root"] = str(root.resolve())
    data["updated_at"] = datetime.now(tz=timezone.utc).isoformat()
    if "created_at" not in data:
        data["created_at"] = data["updated_at"]
    _project_meta_path(project_dir).write_text(
        json.dumps(data, indent=2) + "\n", encoding="utf-8"
    )


def get_project_extract_root(dossiers_dir: Path, name: str) -> Optional[Path]:
    project_dir = dossiers_dir / normalize_project_name(name)
    if not project_dir.exists():
        return None
    data = _read_project_meta(project_dir)
    value = data.get("extract_root")
    if not isinstance(value, str) or not value.strip():
        return None
    p = Path(value).expanduser()
    if not p.exists() or not p.is_dir():
        return None
    return p.resolve()
