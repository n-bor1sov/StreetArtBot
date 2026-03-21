import asyncio
import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.db.connection import get_db
from bot.db.queries import count_excursions, count_users, get_all_excursions, set_user_state
from bot.keyboards.main_kb import (
    LINKS_KB,
    MAIN_REPLY_KB,
    START_LINKS_KB,
    excursion_list_kb,
)
from bot.utils.errors import safe_handler

logger = logging.getLogger(__name__)

WELCOME_TEXT = (
    "Добро пожаловать в SpotBot проекта «Место»!\n"
    "Мы создали онлайн-гид по уличному искусству Нижнего Новгорода. "
    "Сейчас действует три маршрута по Нижегородскому району, именно тут находится основное "
    "скопление стрит-арта. Вы познакомитесь с фестивальными объектами, а также партизанскими "
    "работами локальных и приезжих уличных художников. Вы узнаете о разных авторах их стилях "
    "и техниках, посмотрите масштабные монументальные работы на фасадах и маленькие произведения, "
    "спрятанные в атмосферных дворах. Кроме подсказок с адресами мы составили подробное описание "
    "о каждом объекте. Эти экскурсии не только про уличное искусство, но и про архитектуру и "
    "историю города. Подписывайтесь на телеграм-канал проекта, мы будем информировать о "
    "формировании новых маршрутов и анонсировать наши события."
)

SELECT_ROUTE_TEXT = (
    "SpotBot разработан командой проекта «Место» в рамках специального дополнения к онлайн-карте "
    "и Энциклопедии уличного искусства Нижнего Новгорода. В издании собран большой фотоархив, "
    "биографические справки о локальных уличных художниках и подробная статья о истории и "
    "формировании нижегородского уличного искусства.\n"
    "Выберите маршрут для себя!"
)


@safe_handler
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = get_db()
    user_id = update.effective_user.id

    excursions, _ = await asyncio.gather(
        get_all_excursions(db),
        set_user_state(db, user_id, "main"),
    )

    await update.message.reply_html(WELCOME_TEXT, reply_markup=MAIN_REPLY_KB)
    await update.message.reply_html(
        SELECT_ROUTE_TEXT,
        reply_markup=excursion_list_kb(excursions),
        disable_web_page_preview=True,
    )
    logger.info("User %s sent /start", user_id)


@safe_handler
async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = get_db()
    excursions = await get_all_excursions(db)

    await update.callback_query.answer()
    await update.callback_query.message.reply_html(
        SELECT_ROUTE_TEXT,
        reply_markup=excursion_list_kb(excursions),
        disable_web_page_preview=True,
    )


@safe_handler
async def text_developers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = get_db()
    user_count, exc_count = await asyncio.gather(
        count_users(db),
        count_excursions(db),
    )
    text = (
        f"Информация о проекте\n"
        f"Статистика:\n"
        f"Пользователей проекта: {user_count}\n"
        f"Действующих экскурсий: {exc_count}\n"
        f"Разработчики: Никита Nomerz, "
        f'<a href="https://t.me/mf_pups">Никита Борисов</a>, '
        f"Влад Борисов, Даниела Мол-Оглы\n"
        f"Почта: mesto.fest@mail.ru"
    )
    await update.message.reply_html(text, disable_web_page_preview=True)


@safe_handler
async def text_links(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html("Ссылки:", reply_markup=LINKS_KB)


@safe_handler
async def text_donate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html(
        "Спасибо, что воспользовались онлайн-гидом, надеемся, что вам было интересно. "
        "Будем благодарны за донаты в поддержку проекта.\n"
        "Сбербанк: 2202 2061 7327 2795 (при переводе указать в комментарии: «SpotBot»)"
    )
