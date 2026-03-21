import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from .models import BotSettings, Excursion, Performance, Quiz, User

logger = logging.getLogger(__name__)


class DocumentNotFound(Exception):
    pass


async def get_user(db: AsyncIOMotorDatabase, user_id: int) -> Optional[User]:
    doc = await db.users.find_one({"id": user_id})
    return User(**doc) if doc else None


async def upsert_user(db: AsyncIOMotorDatabase, user: User) -> None:
    await db.users.update_one(
        {"id": user.id},
        {"$set": user.model_dump()},
        upsert=True,
    )


async def set_user_state(db: AsyncIOMotorDatabase, user_id: int, state: str) -> None:
    await db.users.update_one({"id": user_id}, {"$set": {"state": state}})


async def count_users(db: AsyncIOMotorDatabase) -> int:
    return await db.users.count_documents({})


async def get_users_on_presentation(db: AsyncIOMotorDatabase, exc_id: int) -> list[User]:
    cursor = db.users.find({"state": f"onPresentation_{exc_id}"})
    return [User(**doc) async for doc in cursor]


async def get_excursion(db: AsyncIOMotorDatabase, exc_id: int) -> Excursion:
    doc = await db.excursions.find_one({"id": exc_id})
    if doc is None:
        raise DocumentNotFound(f"Excursion {exc_id} not found")
    return Excursion(**doc)


async def get_all_excursions(db: AsyncIOMotorDatabase) -> list[Excursion]:
    cursor = db.excursions.find({})
    excursions = [Excursion(**doc) async for doc in cursor]
    return sorted(excursions, key=lambda e: e.id)


async def count_excursions(db: AsyncIOMotorDatabase) -> int:
    return await db.excursions.count_documents({})


async def get_performance(db: AsyncIOMotorDatabase, perf_id: int) -> Performance:
    doc = await db.performances.find_one({"id": perf_id})
    if doc is None:
        raise DocumentNotFound(f"Performance {perf_id} not found")
    return Performance(**doc)


async def get_quiz_for_object(db: AsyncIOMotorDatabase, obj_id: int) -> Optional[Quiz]:
    doc = await db.quizes.find_one({"objID": obj_id})
    return Quiz(**doc) if doc else None


async def get_quiz_by_id(db: AsyncIOMotorDatabase, quiz_id: int) -> Quiz:
    doc = await db.quizes.find_one({"id": quiz_id})
    if doc is None:
        raise DocumentNotFound(f"Quiz {quiz_id} not found")
    return Quiz(**doc)


async def count_quizzes(db: AsyncIOMotorDatabase) -> int:
    return await db.quizes.count_documents({})


async def save_quiz(db: AsyncIOMotorDatabase, quiz: Quiz) -> None:
    await db.quizes.update_one(
        {"id": quiz.id},
        {"$set": quiz.model_dump(by_alias=True)},
        upsert=True,
    )


async def record_quiz_answer(
    db: AsyncIOMotorDatabase,
    quiz_id: int,
    user_id: int,
    answer_value: str,
) -> bool:
    """Record a user's answer. Returns True if accepted, False if already answered."""
    quiz = await get_quiz_by_id(db, quiz_id)
    already_answered = any(r.id == user_id for r in quiz.users)
    if already_answered:
        return False
    await db.quizes.update_one(
        {"id": quiz_id},
        {"$push": {"users": {"id": user_id, "answer": answer_value}}},
    )
    return True


async def update_excursion_speakers(
    db: AsyncIOMotorDatabase, exc_id: int, speakers: list
) -> None:
    await db.excursions.update_one(
        {"id": exc_id},
        {"$set": {"speakers": [s.model_dump() for s in speakers]}},
    )


async def get_bot_settings(db: AsyncIOMotorDatabase) -> BotSettings:
    doc = await db.settings.find_one({})
    return BotSettings(**doc) if doc else BotSettings()


async def set_live_access(db: AsyncIOMotorDatabase, open: bool) -> None:
    await db.settings.update_one(
        {},
        {"$set": {"live_access_open": open}},
        upsert=True,
    )
