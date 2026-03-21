from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from bot.db.models import Excursion

MAIN_REPLY_KB = ReplyKeyboardMarkup(
    [["🧑‍💻 Разработчики", "🌐 Ссылки", "👍 Поддержать проект"]],
    resize_keyboard=True,
)

START_LINKS_KB = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                "🗺 Онлайн-карта уличного искусства Нижнего Новгорода",
                url="https://www.google.com/maps/d/u/0/viewer?hl=ru&ll=56.32368340572147%2C43.97988871408687&z=14&mid=1xZXBBihtMkmSR4lQrntNuWMXU7Q",
            )
        ],
        [
            InlineKeyboardButton(
                "📢 Телеграм канал проекта",
                url="https://t.me/mestoproject",
            )
        ],
    ]
)

LINKS_KB = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Telegram", url="https://t.me/mestoproject")],
        [InlineKeyboardButton("VK", url="https://vk.com/mestoproject")],
        [InlineKeyboardButton("Instagram", url="https://www.instagram.com/mestoproject/")],
        [InlineKeyboardButton("Facebook", url="https://www.facebook.com/mestoproject/")],
        [InlineKeyboardButton("Зерно", url="https://www.zerno-pro.com/")],
        [
            InlineKeyboardButton(
                "🗺 Онлайн-карта уличного искусства Нижнего Новгорода",
                url="https://www.google.com/maps/d/u/0/viewer?hl=ru&ll=56.32368340572147%2C43.97988871408687&z=14&mid=1xZXBBihtMkmSR4lQrntNuWMXU7Q",
            )
        ],
        [
            InlineKeyboardButton(
                "📢 Телеграм канал проекта",
                url="https://t.me/mestoproject",
            )
        ],
    ]
)

TO_MAIN_KB = InlineKeyboardMarkup(
    [[InlineKeyboardButton("🏘 В главное меню", callback_data="main")]]
)


def excursion_list_kb(excursions: list[Excursion]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(f"Маршрут №{e.id} : {e.name}", callback_data=f"exc_{e.id}")]
        for e in excursions
    ]
    return InlineKeyboardMarkup(rows)
