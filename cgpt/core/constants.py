from cgpt.core.env import _env_positive_int

__version__ = "0.2.15"

SAO_PAULO_TZ = "America/Sao_Paulo"
MIN_CONTEXT = 0
MAX_CONTEXT = 200

MAX_ZIP_MEMBERS = _env_positive_int("CGPT_MAX_ZIP_MEMBERS", 100_000)
MAX_ZIP_UNCOMPRESSED_BYTES = _env_positive_int(
    "CGPT_MAX_ZIP_UNCOMPRESSED_BYTES", 2 * 1024 * 1024 * 1024
)
JSON_DISCOVERY_BUCKET_LIMIT = _env_positive_int(
    "CGPT_JSON_DISCOVERY_BUCKET_LIMIT", 512
)
