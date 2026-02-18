from cgpt.core.constants import __version__
from cgpt.cli import main
from cgpt.commands.init_doctor import _doctor_parse_major_version
from cgpt.domain import conversations as _conversations

JSON_DISCOVERY_BUCKET_LIMIT = _conversations.JSON_DISCOVERY_BUCKET_LIMIT
load_json_loose = _conversations.load_json_loose

def find_conversations_json(root):
    _conversations.JSON_DISCOVERY_BUCKET_LIMIT = JSON_DISCOVERY_BUCKET_LIMIT
    _conversations.load_json_loose = load_json_loose
    return _conversations.find_conversations_json(root)
