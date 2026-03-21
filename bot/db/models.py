from typing import Any

from pydantic import BaseModel, Field


class User(BaseModel):
    id: int
    state: str = "main"
    name: str = ""
    username: str = ""


class Performance(BaseModel):
    id: int
    name: str = ""
    text: str = ""
    painter: str = ""
    photo_id: str = Field(default="", alias="photoId")
    address: str = Field(default="", alias="adress")
    way_to: str = Field(default="", alias="wayTo")

    model_config = {"populate_by_name": True}


class SpeakerSlot(BaseModel):
    id: int
    speaker: int = 0


class Excursion(BaseModel):
    id: int
    name: str = ""
    text: str = ""
    time: str = ""
    start_point: str = Field(default="", alias="startPoint")
    end_point: str = Field(default="", alias="endPoint")
    objects: list[int] = Field(default_factory=list)
    speakers: list[SpeakerSlot] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class QuizAnswer(BaseModel):
    quest_id: int = Field(default=0, alias="questID")
    id: int = 0
    text: str = ""
    right: str = "false"

    model_config = {"populate_by_name": True}

    @property
    def is_correct(self) -> bool:
        return self.right.lower() == "true"


class QuizUserResult(BaseModel):
    id: int
    answer: str


class Quiz(BaseModel):
    id: int
    obj_id: Any = Field(default=0, alias="objID")
    question: str = ""
    answers: list[QuizAnswer] = Field(default_factory=list)
    users: list[QuizUserResult] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class Painter(BaseModel):
    id: int
    name: str = ""
    text: str = ""
    country: str = ""
    photo_id: str = Field(default="", alias="photoId")

    model_config = {"populate_by_name": True}


class BotSettings(BaseModel):
    live_access_open: bool = False
