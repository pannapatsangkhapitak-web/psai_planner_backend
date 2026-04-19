from fastapi import APIRouter
from datetime import date

# 🔹 internal imports
from planner_v2.core.ai_engine import AIEngine
from planner_v2.core.models import Task, SubTask
from planner_v2.core.enums import WorkType, Skill

router = APIRouter(tags=["AI"])


# =========================
# TEMP: FIXED MTPD (NO DB)
# =========================
def get_mtpd(hotel_id: str) -> int:
    return 2  # 🔥 mock value


# =========================
# TEMP: FAKE CALENDAR
# =========================
class FakeCalendar:
    def get_skill_load(self, day, skill):
        return 0


# =========================
# TEST ENDPOINT
# =========================
@router.get("/ai/check")
def check_ai():
    """
    🔥 Purpose:
    - test AI engine without DB / Firebase
    - confirm Railway deploy is stable
    """

    # 🔹 mock task
    task = Task(
            task_id="T1",
            name="Test Task",
            category="Demo",
            work_type=WorkType.CNP,
            leader=Skill.CARPENTER,
            start_date=None
            )

    # 🔹 mock subtasks
    subtasks = [
        SubTask(
            task_id="T1",
            skill=Skill.CARPENTER,
            sequence=1,
            duration_days=2
        ),
        SubTask(
            task_id="T1",
            skill=Skill.PAINTER,
            sequence=2,
            duration_days=1
        ),
    ]

    # 🔹 engine
    engine = AIEngine(
        calendar=FakeCalendar(),
        base_date=date.today(),
        max_per_day=2
    )

    result = engine.suggest(task, subtasks)

    return {
        "status": "ok",
        "result": result
    }