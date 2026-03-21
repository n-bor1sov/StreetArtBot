import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.db.connection import get_db
from bot.db.queries import get_excursion, get_performance, get_quiz_by_id, record_quiz_answer
from bot.keyboards.admin_kb import quiz_answer_kb
from bot.utils.callback_data import parse_ans
from bot.utils.errors import safe_handler

logger = logging.getLogger(__name__)


@safe_handler
async def ans_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = get_db()
    quiz_id, ans_num = parse_ans(update.callback_query.data)
    uid = update.effective_user.id

    quiz = await get_quiz_by_id(db, quiz_id)

    answer_index = ans_num - 1
    if answer_index < 0 or answer_index >= len(quiz.answers):
        await update.callback_query.answer("Неверный номер ответа.")
        return

    answer_value = str(quiz.answers[answer_index].is_correct).lower()
    accepted = await record_quiz_answer(db, quiz_id, uid, answer_value)

    if accepted:
        await update.callback_query.answer("Ответ принят!")
        logger.info("User %s answered quiz %s: ans %s (%s)", uid, quiz_id, ans_num, answer_value)
    else:
        await update.callback_query.answer("Вы уже ответили на этот вопрос.")
