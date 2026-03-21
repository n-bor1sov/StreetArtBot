import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.db.connection import get_db
from bot.db.models import User
from bot.db.queries import get_user, upsert_user

logger = logging.getLogger(__name__)

USER_KEY = "db_user"
BOT_USERNAME = "StreetartSpotBot"


async def user_registration_hook(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Runs first (group=-1 TypeHandler) on every update.
    - Looks up the Telegram user in MongoDB
    - Registers them if new (skips the bot's own service account)
    - Attaches the User object to context.user_data[USER_KEY]
    """
    effective_user = update.effective_user
    if effective_user is None or effective_user.username == BOT_USERNAME:
        return

    try:
        db = get_db()
        user = await get_user(db, effective_user.id)

        if user is None:
            user = User(
                id=effective_user.id,
                state="main",
                name=effective_user.first_name or "",
                username=effective_user.username or "",
            )
            await upsert_user(db, user)
            logger.info("New user registered: id=%s username=%s", user.id, user.username)

        context.user_data[USER_KEY] = user

    except Exception:
        logger.exception(
            "Error in user_registration_hook for user_id=%s", effective_user.id
        )
