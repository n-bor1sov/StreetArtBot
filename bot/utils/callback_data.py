import re

from .errors import InvalidCallbackData

EXC_RE = re.compile(r"^exc_(\d+)$")
OBJECT_PAGE_RE = re.compile(r"^objectPage_(\d+)_(\d+)$")
WAY_TO_OBJ_RE = re.compile(r"^wayToObj_(\d+)_(\d+)$")
END_OF_EXC_RE = re.compile(r"^endOfExc_(\d+)$")
COURAGE_RE = re.compile(r"^courageindicator_(\d+)$")
ANS_RE = re.compile(r"^ans_(\d+)_(\d+)$")
START_QUIZ_RE = re.compile(r"^startQuiz_(\d+)_(\d+)$")
RESULTS_RE = re.compile(r"^results_(\d+)$")
QUIZ_QUEST_RE = re.compile(r"^quizQuest_(\d+)_(\d+)$")
POST_OBJECT_RE = re.compile(r"^postObject_(\d+)_(\d+)$")
POST_WAY_TO_RE = re.compile(r"^postWayToObj_(\d+)_(\d+)$")
ADD_QUIZ_RE = re.compile(r"^addQuiz$")


def parse_exc(data: str) -> int:
    m = EXC_RE.match(data)
    if not m:
        raise InvalidCallbackData(f"Expected exc_<id>, got: {data!r}")
    return int(m.group(1))


def parse_object_page(data: str) -> tuple[int, int]:
    m = OBJECT_PAGE_RE.match(data)
    if not m:
        raise InvalidCallbackData(f"Expected objectPage_<exc>_<num>, got: {data!r}")
    return int(m.group(1)), int(m.group(2))


def parse_way_to_obj(data: str) -> tuple[int, int]:
    m = WAY_TO_OBJ_RE.match(data)
    if not m:
        raise InvalidCallbackData(f"Expected wayToObj_<exc>_<num>, got: {data!r}")
    return int(m.group(1)), int(m.group(2))


def parse_end_of_exc(data: str) -> int:
    m = END_OF_EXC_RE.match(data)
    if not m:
        raise InvalidCallbackData(f"Expected endOfExc_<id>, got: {data!r}")
    return int(m.group(1))


def parse_courage(data: str) -> int:
    m = COURAGE_RE.match(data)
    if not m:
        raise InvalidCallbackData(f"Expected courageindicator_<id>, got: {data!r}")
    return int(m.group(1))


def parse_ans(data: str) -> tuple[int, int]:
    m = ANS_RE.match(data)
    if not m:
        raise InvalidCallbackData(f"Expected ans_<quiz_id>_<ans_num>, got: {data!r}")
    return int(m.group(1)), int(m.group(2))


def parse_start_quiz(data: str) -> tuple[int, int]:
    m = START_QUIZ_RE.match(data)
    if not m:
        raise InvalidCallbackData(f"Expected startQuiz_<quiz_id>_<num>, got: {data!r}")
    return int(m.group(1)), int(m.group(2))


def parse_results(data: str) -> int:
    m = RESULTS_RE.match(data)
    if not m:
        raise InvalidCallbackData(f"Expected results_<exc_id>, got: {data!r}")
    return int(m.group(1))


def parse_quiz_quest(data: str) -> tuple[int, int]:
    m = QUIZ_QUEST_RE.match(data)
    if not m:
        raise InvalidCallbackData(f"Expected quizQuest_<exc_id>_<num>, got: {data!r}")
    return int(m.group(1)), int(m.group(2))


def parse_post_object(data: str) -> tuple[int, int]:
    m = POST_OBJECT_RE.match(data)
    if not m:
        raise InvalidCallbackData(f"Expected postObject_<exc_id>_<num>, got: {data!r}")
    return int(m.group(1)), int(m.group(2))


def parse_post_way_to(data: str) -> tuple[int, int]:
    m = POST_WAY_TO_RE.match(data)
    if not m:
        raise InvalidCallbackData(f"Expected postWayToObj_<exc_id>_<num>, got: {data!r}")
    return int(m.group(1)), int(m.group(2))
