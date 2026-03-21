import functools
import logging
import traceback
from typing import Callable

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

MSG_GENERIC_ERROR = "Что-то пошло не так... Попробуйте ещё раз или напишите /start"


class BotError(Exception):
    """Base class for all bot-specific errors."""


class InvalidCallbackData(BotError):
    """Raised when callback data fails validation."""


class AccessDenied(BotError):
    """Raised when a non-admin tries to use an admin action."""


async def _safe_answer_callback(update: Update) -> None:
    """Answer a pending callback query so the loading spinner stops."""
    if update.callback_query:
        try:
            await update.callback_query.answer()
        except TelegramError:
            pass


async def _safe_reply(update: Update, text: str) -> None:
    try:
        if update.callback_query and update.callback_query.message:
            await update.callback_query.message.reply_text(text)
        elif update.message:
            await update.message.reply_html(text)
    except TelegramError:
        pass


async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """PTB Application-level error handler. Catches anything not handled by @safe_handler."""
    err = context.error
    tb = "".join(traceback.format_exception(type(err), err, err.__traceback__))

    user_id = None
    if isinstance(update, Update):
        user_id = update.effective_user.id if update.effective_user else None

    logger.error(
        "Unhandled exception | user_id=%s | error=%s\n%s",
        user_id,
        err,
        tb,
    )

    if isinstance(update, Update):
        await _safe_answer_callback(update)
        await _safe_reply(update, MSG_GENERIC_ERROR)


def safe_handler(func: Callable) -> Callable:
    """
    Decorator for all bot handlers.
    - Catches and logs exceptions with full context
    - Always answers pending callback queries (stops spinner)
    - Sends user-friendly error message on failure
    """
    from bot.db.queries import DocumentNotFound

    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id if update.effective_user else "unknown"
        callback_data = None
        if update.callback_query:
            callback_data = update.callback_query.data

        try:
            await func(update, context)
        except DocumentNotFound as e:
            logger.warning(
                "Document not found | user_id=%s | callback=%s | error=%s",
                user_id,
                callback_data,
                e,
            )
            await _safe_answer_callback(update)
            await _safe_reply(update, "Данные не найдены. Попробуйте /start")
        except InvalidCallbackData as e:
            logger.warning(
                "Invalid callback data | user_id=%s | callback=%s | error=%s",
                user_id,
                callback_data,
                e,
            )
            await _safe_answer_callback(update)
        except AccessDenied:
            logger.warning("Access denied | user_id=%s", user_id)
            await _safe_answer_callback(update)
            await _safe_reply(update, "Доступ запрещён.")
        except TelegramError as e:
            logger.error(
                "Telegram API error | user_id=%s | callback=%s | error=%s",
                user_id,
                callback_data,
                e,
            )
            await _safe_answer_callback(update)
        except Exception:
            logger.exception(
                "Unexpected error in handler %s | user_id=%s | callback=%s",
                func.__name__,
                user_id,
                callback_data,
            )
            await _safe_answer_callback(update)
            await _safe_reply(update, MSG_GENERIC_ERROR)

    return wrapper
