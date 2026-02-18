from cgpt.cli import main as main
from cgpt.commands.init_doctor import (
    _doctor_parse_major_version as _doctor_parse_major_version,
)
from cgpt.core.constants import __version__ as __version__
from cgpt.domain import conversations as _conversations

JSON_DISCOVERY_BUCKET_LIMIT = _conversations.JSON_DISCOVERY_BUCKET_LIMIT
load_json_loose = _conversations.load_json_loose

__all__ = [
    "__version__",
    "main",
    "_doctor_parse_major_version",
    "JSON_DISCOVERY_BUCKET_LIMIT",
    "load_json_loose",
    "find_conversations_json",
]

def find_conversations_json(root):
    _conversations.JSON_DISCOVERY_BUCKET_LIMIT = JSON_DISCOVERY_BUCKET_LIMIT
    _conversations.load_json_loose = load_json_loose
    return _conversations.find_conversations_json(root)
