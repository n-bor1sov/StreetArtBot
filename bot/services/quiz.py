import asyncio
import logging
from dataclasses import dataclass, field

from motor.motor_asyncio import AsyncIOMotorDatabase

from bot.db.queries import get_quiz_for_object, get_user

logger = logging.getLogger(__name__)


@dataclass
class ParticipantScore:
    user_id: int
    correct: int = 0
    name: str = ""
    username: str = ""


async def compute_leaderboard(
    db: AsyncIOMotorDatabase, obj_ids: list[int]
) -> list[ParticipantScore]:
    """
    Aggregate quiz scores for all objects in an excursion.
    Runs all object quiz lookups in parallel, then resolves usernames in parallel.
    """
    quizzes = await asyncio.gather(*[get_quiz_for_object(db, oid) for oid in obj_ids])

    scores: dict[int, int] = {}
    for quiz in quizzes:
        if quiz is None:
            continue
        for result in quiz.users:
            if result.answer.lower() == "true":
                scores[result.id] = scores.get(result.id, 0) + 1

    if not scores:
        return []

    async def resolve_user(uid: int, correct: int) -> ParticipantScore:
        user = await get_user(db, uid)
        if user:
            return ParticipantScore(
                user_id=uid,
                correct=correct,
                name=user.name,
                username=user.username,
            )
        return ParticipantScore(user_id=uid, correct=correct, name=f"User {uid}")

    participants = await asyncio.gather(
        *[resolve_user(uid, cnt) for uid, cnt in scores.items()]
    )
    return sorted(participants, key=lambda p: p.correct, reverse=True)


def format_leaderboard(participants: list[ParticipantScore]) -> str:
    if not participants:
        return "Результаты квиза:\nНикто не ответил на вопросы."

    lines = ["Результаты квиза:"]
    for i, p in enumerate(participants, start=1):
        username_part = f" @{p.username}" if p.username else ""
        lines.append(f"{i}. {p.name}{username_part} — {p.correct} правильных ответов")
    lines.append("\nПоздравляем!")
    return "\n".join(lines)
