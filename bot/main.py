import logging

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    TypeHandler,
    filters,
)

from bot.config import settings
from bot.db import connection as db_connection
from bot.handlers.admin import (
    add_access_callback,
    add_quiz_callback,
    admin_callback,
    admin_command,
    handle_add_quiz_text,
    post_object_callback,
    post_way_to_callback,
    quiz_quest_callback,
    quizes_callback,
    results_callback,
    start_quiz_callback,
)
from bot.handlers.excursions import (
    courageindicator_callback,
    end_of_exc_callback,
    exc_callback,
    iamcourage_minus_callback,
    iamcourage_plus_callback,
    object_page_callback,
    way_to_obj_callback,
)
from bot.handlers.quiz import ans_callback
from bot.handlers.start import (
    main_menu_callback,
    start_command,
    text_developers,
    text_donate,
    text_links,
)
from bot.middlewares.user import user_registration_hook
from bot.utils.callback_data import (
    ANS_RE,
    COURAGE_RE,
    END_OF_EXC_RE,
    EXC_RE,
    OBJECT_PAGE_RE,
    POST_OBJECT_RE,
    POST_WAY_TO_RE,
    QUIZ_QUEST_RE,
    RESULTS_RE,
    START_QUIZ_RE,
    WAY_TO_OBJ_RE,
)
from bot.utils.errors import global_error_handler


def setup_logging() -> None:
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)


async def on_startup(application: Application) -> None:
    await db_connection.connect(settings.mongo_url, db_name=settings.mongo_db_name)
    logging.getLogger(__name__).info("Bot started")


async def on_shutdown(application: Application) -> None:
    await db_connection.disconnect()
    logging.getLogger(__name__).info("Bot stopped")


def build_application() -> Application:
    app = (
        Application.builder()
        .token(settings.bot_token)
        .post_init(on_startup)
        .post_shutdown(on_shutdown)
        .build()
    )

    # Runs before all handlers in group 0 (PTB 21 has no BaseMiddleware)
    app.add_handler(TypeHandler(Update, user_registration_hook), group=-1)

    app.add_error_handler(global_error_handler)

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("admin", admin_command))

    app.add_handler(MessageHandler(filters.Regex(r"^🧑‍💻 Разработчики$"), text_developers))
    app.add_handler(MessageHandler(filters.Regex(r"^🌐 Ссылки$"), text_links))
    app.add_handler(MessageHandler(filters.Regex(r"^👍 Поддержать проект$"), text_donate))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_add_quiz_text)
    )

    app.add_handler(CallbackQueryHandler(main_menu_callback, pattern=r"^main$"))

    app.add_handler(CallbackQueryHandler(exc_callback, pattern=EXC_RE))
    app.add_handler(CallbackQueryHandler(object_page_callback, pattern=OBJECT_PAGE_RE))
    app.add_handler(CallbackQueryHandler(way_to_obj_callback, pattern=WAY_TO_OBJ_RE))
    app.add_handler(CallbackQueryHandler(end_of_exc_callback, pattern=END_OF_EXC_RE))
    app.add_handler(CallbackQueryHandler(courageindicator_callback, pattern=COURAGE_RE))
    app.add_handler(CallbackQueryHandler(iamcourage_plus_callback, pattern=r"^iamcourage_\+$"))
    app.add_handler(CallbackQueryHandler(iamcourage_minus_callback, pattern=r"^iamcourage_-$"))

    app.add_handler(CallbackQueryHandler(ans_callback, pattern=ANS_RE))

    app.add_handler(CallbackQueryHandler(admin_callback, pattern=r"^admin$"))
    app.add_handler(CallbackQueryHandler(add_access_callback, pattern=r"^addAcess$"))
    app.add_handler(CallbackQueryHandler(quizes_callback, pattern=r"^quizes$"))
    app.add_handler(CallbackQueryHandler(quiz_quest_callback, pattern=QUIZ_QUEST_RE))
    app.add_handler(CallbackQueryHandler(add_quiz_callback, pattern=r"^addQuiz$"))
    app.add_handler(CallbackQueryHandler(post_object_callback, pattern=POST_OBJECT_RE))
    app.add_handler(CallbackQueryHandler(post_way_to_callback, pattern=POST_WAY_TO_RE))
    app.add_handler(CallbackQueryHandler(start_quiz_callback, pattern=START_QUIZ_RE))
    app.add_handler(CallbackQueryHandler(results_callback, pattern=RESULTS_RE))

    return app


def main() -> None:
    setup_logging()
    app = build_application()
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
