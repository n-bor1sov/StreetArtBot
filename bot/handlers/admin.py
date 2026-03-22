import asyncio
import logging

from telegram import Bot, Update
from telegram.ext import ContextTypes

from bot.config import settings
from bot.db.connection import get_db
from bot.db.models import Quiz
from bot.db.queries import (
    count_quizzes,
    get_all_excursions,
    get_excursion,
    get_performance,
    get_quiz_by_id,
    get_quiz_for_object,
    get_users_on_presentation,
    save_quiz,
    set_live_access,
    set_user_state,
)
from bot.keyboards.admin_kb import admin_panel_kb, quiz_excursion_list_kb, quiz_object_kb
from bot.middlewares.user import USER_KEY
from bot.services.broadcast import run_broadcast_in_background
from bot.services.quiz import compute_leaderboard, format_leaderboard
from bot.utils.callback_data import (
    parse_post_object,
    parse_post_way_to,
    parse_quiz_quest,
    parse_results,
    parse_start_quiz,
)
from bot.utils.errors import AccessDenied, safe_handler
from bot.utils.media import load_photo, object_photo_paths, way_to_path

logger = logging.getLogger(__name__)


def _require_admin(uid: int) -> None:
    if uid not in settings.admin_ids:
        raise AccessDenied(f"User {uid} is not an admin")


@safe_handler
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _require_admin(update.effective_user.id)
    await update.message.reply_html(
        "Приветствуем в администраторском интерфейсе!",
        reply_markup=admin_panel_kb(),
    )


@safe_handler
async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _require_admin(update.effective_user.id)
    await update.callback_query.answer()
    await update.callback_query.message.reply_html(
        "Приветствуем в администраторском интерфейсе!",
        reply_markup=admin_panel_kb(),
    )


@safe_handler
async def add_access_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _require_admin(update.effective_user.id)
    db = get_db()
    await set_live_access(db, open=True)
    await update.callback_query.answer("Доступ открыт")
    await update.callback_query.message.reply_html("Доступ к экскурсиям открыт ✅")
    logger.info("Admin %s opened live tour access", update.effective_user.id)


@safe_handler
async def quizes_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _require_admin(update.effective_user.id)
    db = get_db()
    excursions = await get_all_excursions(db)
    await update.callback_query.answer()
    await update.callback_query.message.reply_html(
        "Выберите маршрут:",
        reply_markup=quiz_excursion_list_kb(excursions),
    )


@safe_handler
async def quiz_quest_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _require_admin(update.effective_user.id)
    db = get_db()
    exc_id, num = parse_quiz_quest(update.callback_query.data)

    exc = await get_excursion(db, exc_id)
    obj_id = exc.objects[num]
    obj, quiz = await asyncio.gather(
        get_performance(db, obj_id),
        get_quiz_for_object(db, obj_id),
    )

    total = len(exc.objects)
    kb = quiz_object_kb(exc_id, num, total, quiz)

    if quiz:
        text = (
            f"Объект: {obj.name}\n"
            f"Автор: {obj.painter}\n"
            f"Адрес: {obj.address}\n\n"
            f"Вопрос: {quiz.question}"
        )
    else:
        text = (
            f"Объект: {obj.name}\n"
            f"Автор: {obj.painter}\n"
            f"Адрес: {obj.address}\n\n"
            "Вопрос: Отсутствует"
        )

    await update.callback_query.answer()
    await update.callback_query.message.reply_html(text, reply_markup=kb)


@safe_handler
async def add_quiz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _require_admin(update.effective_user.id)
    db = get_db()
    uid = update.effective_user.id

    await update.callback_query.answer()
    await update.callback_query.message.reply_html(
        "Введите вопрос в формате:\n"
        "<code>objId*текст вопроса*Вариант 1*Вариант 2 (правильный)*...</code>"
    )
    await set_user_state(db, uid, "addquiz")


@safe_handler
async def handle_add_quiz_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles raw text input when admin is in 'addquiz' state."""
    user = context.user_data.get(USER_KEY)
    if not user or user.state != "addquiz":
        return

    _require_admin(update.effective_user.id)
    db = get_db()
    text = update.message.text.strip()

    parts = text.split("*")
    if len(parts) < 3:
        await update.message.reply_html(
            "Неверный формат. Используйте:\n"
            "<code>objId*вопрос*ответ1*ответ2(правильный)*...</code>"
        )
        return

    try:
        obj_id = int(parts[0].strip())
    except ValueError:
        await update.message.reply_html("Первым элементом должен быть числовой ID объекта.")
        return

    question = parts[1].strip()
    answer_texts = [p.strip() for p in parts[2:] if p.strip()]

    if not answer_texts:
        await update.message.reply_html("Укажите хотя бы один вариант ответа.")
        return

    num = await count_quizzes(db)
    answers = []
    for i, ans_text in enumerate(answer_texts):
        is_last = i == len(answer_texts) - 1
        answers.append({
            "questID": num + 1,
            "id": i + 1,
            "text": ans_text,
            "right": "true" if is_last else "false",
        })

    quiz = Quiz(
        id=num + 1,
        objID=obj_id,
        question=question,
        answers=answers,
    )
    await save_quiz(db, quiz)
    await set_user_state(db, update.effective_user.id, "main")
    await update.message.reply_html(f"Вопрос добавлен (id: {quiz.id}) ✅")
    logger.info("Admin %s added quiz %s for obj %s", update.effective_user.id, quiz.id, obj_id)


@safe_handler
async def post_object_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _require_admin(update.effective_user.id)
    db = get_db()
    exc_id, num = parse_post_object(update.callback_query.data)

    exc = await get_excursion(db, exc_id)
    obj = await get_performance(db, exc.objects[num])

    users = await get_users_on_presentation(db, exc_id)
    user_ids = [u.id for u in users]

    txt = (
        f"{num + 1}-ым объектом экскурсии является {obj.name}\n\n"
        f"Адрес: {obj.address}\n\n"
        f"Автор: {obj.painter}\n\n"
        f"{obj.text}"
    )
    photo_paths = object_photo_paths(
        settings.photos_dir, obj.photo_id, object_id=obj.id
    )

    async def send_description(bot: Bot, uid: int) -> None:
        if photo_paths:
            inp = load_photo(photo_paths[0])
            if inp:
                await bot.send_photo(uid, inp)
        await bot.send_message(uid, txt, parse_mode="HTML")

    await update.callback_query.answer()
    await run_broadcast_in_background(context.bot, user_ids, send_description)
    await update.callback_query.message.reply_html(
        f"Описание объекта разослано {len(user_ids)} участникам."
    )


@safe_handler
async def post_way_to_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _require_admin(update.effective_user.id)
    db = get_db()
    exc_id, num = parse_post_way_to(update.callback_query.data)

    exc = await get_excursion(db, exc_id)
    obj, prev_obj = await asyncio.gather(
        get_performance(db, exc.objects[num]),
        get_performance(db, exc.objects[num - 1]),
    )

    users = await get_users_on_presentation(db, exc_id)
    user_ids = [u.id for u in users]

    txt = (
        f"Следующий объект нашей экскурсии расположен по адресу {obj.address}\n\n"
        f"{obj.way_to}\n\n"
        "Нажмите на кнопку «Я на месте», когда найдете объект."
    )
    nav_path = way_to_path(settings.scrins_dir, obj.id, prev_obj.id)

    async def send_way(bot: Bot, uid: int) -> None:
        inp = load_photo(nav_path)
        if inp:
            await bot.send_photo(uid, inp, caption=txt, parse_mode="HTML")
        else:
            await bot.send_message(uid, txt, parse_mode="HTML")

    await update.callback_query.answer()
    await run_broadcast_in_background(context.bot, user_ids, send_way)
    await update.callback_query.message.reply_html(
        f"Маршрут до объекта разослан {len(user_ids)} участникам."
    )


@safe_handler
async def start_quiz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _require_admin(update.effective_user.id)
    db = get_db()
    quiz_id, num = parse_start_quiz(update.callback_query.data)

    user = context.user_data.get(USER_KEY)
    if not user:
        await update.callback_query.answer("Нет данных пользователя.")
        return

    state_parts = user.state.split("_")
    if len(state_parts) < 2 or state_parts[0] != "onPresentation":
        await update.callback_query.answer("Вы не на презентации.")
        return

    exc_id = int(state_parts[1])
    quiz, exc = await asyncio.gather(
        get_quiz_by_id(db, quiz_id),
        get_excursion(db, exc_id),
    )

    users = await get_users_on_presentation(db, exc_id)
    user_ids = [u.id for u in users]

    txt = f"{quiz.question}\n\n"
    txt += "\n".join(f"{i + 1}) {a.text}" for i, a in enumerate(quiz.answers))

    from bot.keyboards.admin_kb import quiz_answer_kb
    kb = quiz_answer_kb(quiz)

    async def send_quiz(bot: Bot, uid: int) -> None:
        await bot.send_message(uid, txt, parse_mode="HTML", reply_markup=kb)

    await update.callback_query.answer()
    await run_broadcast_in_background(context.bot, user_ids, send_quiz)
    await update.callback_query.message.reply_html(
        f"Квиз запущен, вопрос разослан {len(user_ids)} участникам."
    )


@safe_handler
async def results_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _require_admin(update.effective_user.id)
    db = get_db()
    exc_id = parse_results(update.callback_query.data)

    exc = await get_excursion(db, exc_id)
    users = await get_users_on_presentation(db, exc_id)
    user_ids = [u.id for u in users]

    participants = await compute_leaderboard(db, exc.objects)
    result_text = format_leaderboard(participants)

    async def send_results(bot: Bot, uid: int) -> None:
        await bot.send_message(uid, result_text, parse_mode="HTML")

    await update.callback_query.answer()
    await run_broadcast_in_background(context.bot, user_ids, send_results)
    await update.callback_query.message.reply_html(
        f"Итоги разосланы {len(user_ids)} участникам.\n\n{result_text}"
    )
