"""Helpers for MongoDB connection strings (including mongodb+srv Atlas URIs)."""

from __future__ import annotations

import re
from urllib.parse import unquote, urlparse


def parse_database_name_from_uri(uri: str) -> str | None:
    """
    Extract the database name from a MongoDB URI path, e.g.:
    mongodb+srv://user:pass@host/TarifAuction?retryWrites=true -> TarifAuction
    mongodb://localhost:27017/mydb -> mydb
    """
    parsed = urlparse(uri)
    path = (parsed.path or "").lstrip("/")
    if not path:
        return None
    # First segment only (MongoDB default DB in URI)
    segment = path.split("/")[0]
    return unquote(segment) if segment else None


def redact_mongo_uri_for_log(uri: str) -> str:
    """Hide user credentials in logs (user:password@ -> ***@)."""
    return re.sub(r"//[^:]+:[^@]+@", "//***@", uri, count=1)
