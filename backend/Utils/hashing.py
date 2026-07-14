import hashlib
import hmac
import json
from typing import Optional

from Config.database import PII_TOKEN_KEY


def tokenise_identifier(value: str) -> str:
    """
    Deterministically tokenise a citizen identifier (e.g. phone number).

    Same input always produces the same token, so a CitizenContact can be
    looked up by token without ever storing the raw value (DR-003, DR-007).
    Keyed on PII_TOKEN_KEY, not the JWT signing key — see Config/database.py.
    """
    return hmac.new(
        PII_TOKEN_KEY.encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def hash_snapshot(data: Optional[dict]) -> Optional[str]:
    """
    SHA-256 of a canonical JSON snapshot, for AuditEvent before_hash/after_hash.
    Returns None for an empty/absent snapshot rather than hashing "null".
    """
    if not data:
        return None
    canonical = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
