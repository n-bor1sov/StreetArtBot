from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.db.models import Excursion, Quiz


def admin_panel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Вопросы для презентации", callback_data="quizes")],
            [InlineKeyboardButton("Добавить вопрос на презентацию", callback_data="addQuiz")],
            [InlineKeyboardButton("Открыть доступ к презентации", callback_data="addAcess")],
        ]
    )


def quiz_excursion_list_kb(excursions: list[Excursion]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                f"Маршрут №{e.id} : {e.name}",
                callback_data=f"quizQuest_{e.id}_0",
            )
        ]
        for e in excursions
        if e.id > 3
    ]
    rows.append([InlineKeyboardButton("Назад", callback_data="admin")])
    return InlineKeyboardMarkup(rows)


def quiz_object_kb(
    exc_id: int,
    num: int,
    total: int,
    quiz: Quiz | None,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    is_first = num == 0
    is_last = num == total - 1

    if not is_first:
        rows.append(
            [InlineKeyboardButton("Разослать путь до объекта", callback_data=f"postWayToObj_{exc_id}_{num}")]
        )
    rows.append(
        [InlineKeyboardButton("Разослать описание", callback_data=f"postObject_{exc_id}_{num}")]
    )

    if quiz:
        rows.append(
            [InlineKeyboardButton("Запустить квиз", callback_data=f"startQuiz_{quiz.id}_{num}")]
        )

    nav = []
    if not is_first:
        nav.append(
            InlineKeyboardButton("◀️ Предыдущий", callback_data=f"quizQuest_{exc_id}_{num - 1}")
        )
    if not is_last:
        nav.append(
            InlineKeyboardButton("Следующий ▶️", callback_data=f"quizQuest_{exc_id}_{num + 1}")
        )
    if nav:
        rows.append(nav)

    if is_last:
        rows.append(
            [InlineKeyboardButton("🏆 Подвести итоги", callback_data=f"results_{exc_id}")]
        )

    rows.append([InlineKeyboardButton("Маршруты", callback_data="quizes")])
    return InlineKeyboardMarkup(rows)


def quiz_answer_kb(quiz: Quiz) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(a.text, callback_data=f"ans_{quiz.id}_{a.id}")]
        for a in quiz.answers
    ]
    return InlineKeyboardMarkup(rows)
