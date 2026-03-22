from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def start_excursion_kb(start_callback: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("♥️ Начать экскурсию", callback_data=start_callback)],
            [InlineKeyboardButton("◀️ Назад", callback_data="main")],
        ]
    )


def way_to_obj_kb(arrived_callback: str, back_callback: str, exc_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⬆️ Я на месте", callback_data=arrived_callback)],
            [InlineKeyboardButton("◀️ Назад", callback_data=back_callback)],
            [InlineKeyboardButton("✅ Завершить досрочно", callback_data=f"endOfExc_{exc_id}")],
        ]
    )


def next_obj_kb(
    next_callback: str,
    back_callback: str,
    painter_instagram: str,
    exc_id: int,
) -> InlineKeyboardMarkup:
    rows = []
    if painter_instagram:
        rows.append(
            [
                InlineKeyboardButton(
                    "👨‍🎨 Instagram художника",
                    url=f"https://www.instagram.com/{painter_instagram}/",
                )
            ]
        )
    rows += [
        [InlineKeyboardButton("⬆️ Перейти к следующему объекту", callback_data=next_callback)],
        [InlineKeyboardButton("🔙 Назад", callback_data=back_callback)],
        [InlineKeyboardButton("✅ Завершить досрочно", callback_data=f"endOfExc_{exc_id}")],
    ]
    return InlineKeyboardMarkup(rows)


def last_obj_kb(
    back_callback: str,
    painter_instagram: str,
    exc_id: int,
) -> InlineKeyboardMarkup:
    rows = []
    if painter_instagram:
        rows.append(
            [
                InlineKeyboardButton(
                    "👨‍🎨 Instagram художника",
                    url=f"https://www.instagram.com/{painter_instagram}/",
                )
            ]
        )
    rows += [
        [InlineKeyboardButton("🔙 Назад", callback_data=back_callback)],
        [InlineKeyboardButton("✅ Завершить экскурсию", callback_data=f"endOfExc_{exc_id}")],
    ]
    return InlineKeyboardMarkup(rows)


def courage_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Я готов", callback_data="iamcourage_+")],
            [InlineKeyboardButton("Я пас", callback_data="iamcourage_-")],
        ]
    )
