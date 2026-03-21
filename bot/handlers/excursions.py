import asyncio
import logging

from telegram import InputMediaPhoto, Update
from telegram.ext import ContextTypes

from bot.config import settings
from bot.db.connection import get_db
from bot.db.queries import (
    get_bot_settings,
    get_excursion,
    get_performance,
    get_user,
    set_user_state,
    update_excursion_speakers,
)
from bot.keyboards.excursion_kb import (
    courage_kb,
    last_obj_kb,
    next_obj_kb,
    start_excursion_kb,
    way_to_obj_kb,
)
from bot.keyboards.main_kb import TO_MAIN_KB
from bot.middlewares.user import USER_KEY
from bot.utils.callback_data import (
    parse_courage,
    parse_end_of_exc,
    parse_exc,
    parse_object_page,
    parse_way_to_obj,
)
from bot.utils.errors import safe_handler
from bot.utils.media import load_photo, object_photo_paths, route_map_path, way_to_path

logger = logging.getLogger(__name__)


@safe_handler
async def exc_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = get_db()
    exc_id = parse_exc(update.callback_query.data)
    uid = update.effective_user.id

    exc, bot_cfg = await asyncio.gather(
        get_excursion(db, exc_id),
        get_bot_settings(db),
    )

    text = (
        f"{exc.name}\n\n"
        f"Продолжительность: {exc.time}\n\n"
        f"{exc.start_point}\n\n"
        f"{exc.text}\n\n"
        "Нажмите кнопку «Начать экскурсию» как только прибудете на начальную точку."
    )

    map_photo = load_photo(route_map_path(settings.scrins_dir, exc.id))
    await update.callback_query.answer()

    if exc.id < 10:
        kb = start_excursion_kb(f"objectPage_{exc.id}_0")
        if map_photo:
            await update.callback_query.message.reply_photo(map_photo, caption=text, reply_markup=kb)
        else:
            await update.callback_query.message.reply_html(text, reply_markup=kb)

    elif uid in settings.admin_ids or bot_cfg.live_access_open:
        kb = start_excursion_kb(f"courageindicator_{exc.id}")
        if map_photo:
            await update.callback_query.message.reply_photo(map_photo, caption=text, reply_markup=kb)
        else:
            await update.callback_query.message.reply_html(text, reply_markup=kb)
    else:
        await update.callback_query.message.reply_html(
            "Экскурсия станет доступной, когда она начнётся по расписанию."
        )


@safe_handler
async def courageindicator_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = get_db()
    exc_id = parse_courage(update.callback_query.data)
    uid = update.effective_user.id

    await set_user_state(db, uid, f"onPresentation_{exc_id}")
    await update.callback_query.answer()
    await update.callback_query.message.reply_html(
        "Наша экскурсия рассчитана на интерактив с её участниками. Поэтому мы предлагаем вам "
        "принять участие в её проведении. Тем, кто нажмет кнопку ниже, будет предоставлена "
        "возможность по подготовленному нами материалу рассказать другим участникам экскурсии "
        "об одном из объектов.",
        reply_markup=courage_kb(),
    )


@safe_handler
async def iamcourage_plus_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = get_db()
    uid = update.effective_user.id
    user = context.user_data.get(USER_KEY)

    if user is None:
        user = await get_user(db, uid)

    state_parts = (user.state if user else "").split("_")
    if len(state_parts) < 2 or state_parts[0] != "onPresentation":
        await update.callback_query.answer("Нет активной экскурсии.")
        return

    exc_id = int(state_parts[1])
    exc = await get_excursion(db, exc_id)

    free_slots = [s for s in exc.speakers if s.speaker == 0]
    await update.callback_query.answer()

    if not free_slots:
        await update.callback_query.message.reply_html(
            "Похоже все места только что заняли другие участники экскурсии."
        )
        return

    import random
    chosen_slot = random.choice(free_slots)
    for slot in exc.speakers:
        if slot.id == chosen_slot.id:
            slot.speaker = uid
            break

    await update_excursion_speakers(db, exc_id, exc.speakers)
    obj = await get_performance(db, chosen_slot.id)

    await update.callback_query.message.reply_html(
        f"Вы будете рассказывать про объект {obj.name}. "
        "Когда экскурсионная группа подойдёт к вашему объекту, подойдите к экскурсоводу.",
        reply_markup=_first_obj_kb(exc_id),
    )


@safe_handler
async def iamcourage_minus_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = get_db()
    uid = update.effective_user.id
    user = context.user_data.get(USER_KEY)

    if user is None:
        user = await get_user(db, uid)

    state_parts = (user.state if user else "").split("_")
    if len(state_parts) < 2 or state_parts[0] != "onPresentation":
        await update.callback_query.answer()
        return

    exc_id = int(state_parts[1])
    exc = await get_excursion(db, exc_id)

    for slot in exc.speakers:
        if slot.speaker == uid:
            slot.speaker = 0
            break

    await update_excursion_speakers(db, exc_id, exc.speakers)
    await update.callback_query.answer()
    await update.callback_query.message.reply_html(
        "Тогда просто наслаждайтесь экскурсией.",
        reply_markup=_first_obj_kb(exc_id),
    )


def _first_obj_kb(exc_id: int):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("Перейти к первому объекту", callback_data=f"objectPage_{exc_id}_0")]]
    )


@safe_handler
async def object_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = get_db()
    exc_id, num = parse_object_page(update.callback_query.data)
    uid = update.effective_user.id

    exc, bot_cfg = await asyncio.gather(
        get_excursion(db, exc_id),
        get_bot_settings(db),
    )

    obj_id = exc.objects[num]
    obj = await get_performance(db, obj_id)

    photo_paths = object_photo_paths(settings.photos_dir, obj.photo_id)
    await update.callback_query.answer()

    if photo_paths:
        if len(photo_paths) == 1:
            inp = load_photo(photo_paths[0])
            if inp:
                await update.callback_query.message.reply_photo(inp)
        else:
            media = []
            for p in photo_paths:
                inp = load_photo(p)
                if inp:
                    media.append(InputMediaPhoto(inp))
            if media:
                await update.callback_query.message.reply_media_group(media)

    sz = len(exc.objects)
    is_last = num == sz - 1
    is_first = num == 0

    if exc.id < 10:
        txt = (
            f"{num + 1}-ым объектом экскурсии является {obj.name}\n\n"
            f"Адрес: {obj.address}\n\n"
            f"Автор: {obj.painter}\n\n"
            f"{obj.text}"
        )
        if is_last:
            kb = last_obj_kb(f"wayToObj_{exc_id}_{num}", obj.photo_id, exc_id)
        elif is_first:
            kb = next_obj_kb(f"wayToObj_{exc_id}_{num + 1}", "main", obj.photo_id, exc_id)
        else:
            kb = next_obj_kb(
                f"wayToObj_{exc_id}_{num + 1}",
                f"wayToObj_{exc_id}_{num}",
                obj.photo_id,
                exc_id,
            )
    else:
        if uid not in settings.admin_ids and not bot_cfg.live_access_open:
            await update.callback_query.message.reply_html(
                "Экскурсия ещё не началась."
            )
            return

        speaker_txt = _resolve_speaker_text(exc, obj, uid)
        txt = (
            f"{num + 1}-ым объектом экскурсии является {obj.name}\n\n"
            f"{speaker_txt}\n\n"
            f"Адрес: {obj.address}\n\n"
            f"Автор: {obj.painter}\n\n"
            f"{obj.text}"
        )
        if is_last:
            kb = last_obj_kb(f"wayToObj_{exc_id}_{num}", obj.photo_id, exc_id)
        elif is_first:
            kb = next_obj_kb(f"wayToObj_{exc_id}_{num + 1}", "main", obj.photo_id, exc_id)
        else:
            kb = next_obj_kb(
                f"wayToObj_{exc_id}_{num + 1}",
                f"wayToObj_{exc_id}_{num}",
                obj.photo_id,
                exc_id,
            )

    await update.callback_query.message.reply_html(txt, reply_markup=kb)


def _resolve_speaker_text(exc, obj, current_uid: int) -> str:
    slot = next((s for s in exc.speakers if s.id == obj.id), None)
    if slot is None:
        return "О нём расскажет экскурсовод."
    if slot.speaker == 0:
        return "Об этом объекте пока никто не вызвался рассказать."
    if slot.speaker == current_uid:
        return "Ваш звёздный час настал! Расскажите другим участникам об этом объекте."
    return f"О нём расскажет участник (id: {slot.speaker})."


@safe_handler
async def way_to_obj_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = get_db()
    exc_id, num = parse_way_to_obj(update.callback_query.data)

    exc = await get_excursion(db, exc_id)
    obj = await get_performance(db, exc.objects[num])
    prev_obj = await get_performance(db, exc.objects[num - 1])

    nav_photo = load_photo(way_to_path(settings.scrins_dir, obj.id, prev_obj.id))
    text = (
        f"Следующий объект нашей экскурсии расположен по адресу {obj.address}\n\n"
        f"{obj.way_to}\n\n"
        "Нажмите на кнопку «Я на месте», когда найдете объект."
    )
    kb = way_to_obj_kb(
        f"objectPage_{exc_id}_{num}",
        f"objectPage_{exc_id}_{num - 1}",
        exc_id,
    )

    await update.callback_query.answer()
    if nav_photo:
        await update.callback_query.message.reply_photo(nav_photo, caption=text, reply_markup=kb)
    else:
        await update.callback_query.message.reply_html(text, reply_markup=kb)


@safe_handler
async def end_of_exc_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = get_db()
    exc_id = parse_end_of_exc(update.callback_query.data)
    exc = await get_excursion(db, exc_id)

    await update.callback_query.answer()
    await update.callback_query.message.reply_html(exc.end_point, reply_markup=TO_MAIN_KB)
