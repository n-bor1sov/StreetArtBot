import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from bot.db.mongo_uri import parse_database_name_from_uri, redact_mongo_uri_for_log

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None

DEFAULT_DB_NAME = "street_art_bot"


def resolve_database_name(mongo_url: str, explicit_name: str | None) -> str:
    """
    Pick DB name: MONGO_DB_NAME env wins, else path in URI (e.g. /TarifAuction),
    else DEFAULT_DB_NAME.
    """
    if explicit_name and explicit_name.strip():
        return explicit_name.strip()
    from_uri = parse_database_name_from_uri(mongo_url)
    if from_uri:
        return from_uri
    return DEFAULT_DB_NAME


async def connect(
    mongo_url: str,
    db_name: str | None = None,
) -> AsyncIOMotorDatabase:
    """
    Connect to MongoDB. Supports mongodb:// and mongodb+srv:// (Atlas).

    db_name: optional override; if omitted, uses path segment in the URI or
    DEFAULT_DB_NAME when the URI has no database path.
    """
    global _client, _db
    resolved = resolve_database_name(mongo_url, db_name)
    logger.info("Connecting to MongoDB (%s)", redact_mongo_uri_for_log(mongo_url))
    _client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=15000)
    await _client.admin.command("ping")
    _db = _client[resolved]
    logger.info("MongoDB connected, database: %s", resolved)
    return _db


async def disconnect() -> None:
    global _client, _db
    if _client is not None:
        logger.info("Closing MongoDB connection")
        _client.close()
        _client = None
        _db = None


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("Database not connected. Call connect() first.")
    return _db
