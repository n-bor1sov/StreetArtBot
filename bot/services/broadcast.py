import asyncio
import logging
from typing import Awaitable, Callable

from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)

SendFn = Callable[[Bot, int], Awaitable[None]]


class BroadcastTask:
    """
    Instance-based, concurrent-safe broadcast engine.

    Each broadcast is its own object with isolated state.
    Multiple broadcasts can run simultaneously without any shared mutable globals.
    Errors for individual recipients are logged but do not abort the broadcast.
    Rate-limited via asyncio.sleep to respect Telegram API limits.
    """

    def __init__(
        self,
        bot: Bot,
        user_ids: list[int],
        send_fn: SendFn,
        rate_limit_seconds: float = 0.05,
    ) -> None:
        self._bot = bot
        self._user_ids = list(user_ids)
        self._send_fn = send_fn
        self._rate_limit = rate_limit_seconds
        self._ok = 0
        self._errors = 0

    async def run(self) -> tuple[int, int]:
        """Execute the broadcast. Returns (ok_count, error_count)."""
        for uid in self._user_ids:
            try:
                await self._send_fn(self._bot, uid)
                self._ok += 1
            except TelegramError as e:
                self._errors += 1
                logger.warning("Broadcast failed for user %s: %s", uid, e)
            except Exception:
                self._errors += 1
                logger.exception("Unexpected error broadcasting to user %s", uid)
            await asyncio.sleep(self._rate_limit)

        logger.info(
            "Broadcast finished: %d sent, %d failed (total: %d)",
            self._ok,
            self._errors,
            len(self._user_ids),
        )
        return self._ok, self._errors

    @property
    def total(self) -> int:
        return len(self._user_ids)


async def run_broadcast_in_background(
    bot: Bot,
    user_ids: list[int],
    send_fn: SendFn,
    rate_limit_seconds: float = 0.05,
) -> asyncio.Task:
    """
    Launch a broadcast as a background asyncio task.
    The caller gets an immediate return; delivery continues independently.
    """
    task = BroadcastTask(bot, user_ids, send_fn, rate_limit_seconds)
    return asyncio.create_task(task.run())
