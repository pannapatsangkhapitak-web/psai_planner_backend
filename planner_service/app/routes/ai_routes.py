from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, List
from datetime import date

from planner_v2.core.ai_engine import AIEngine
from planner_v2.core.models import Task, SubTask
from planner_v2.core.enums import WorkType, Skill

router = APIRouter(tags=["AI"])


# =========================
# REQUEST MODEL
# =========================
class SimulateRequest(BaseModel):
    work_type: str
    duration: Dict[str, int]  # {"CARPENTER": 2, "PAINTER": 1}


# =========================
# HELPER: convert string → Enum
# =========================
def to_work_type(w: str) -> WorkType:
    return WorkType[w]


def to_skill(s: str) -> Skill:
    return Skill[s]


# =========================
# ROUTE: SIMULATE
# =========================
@router.post("/simulate")
def simulate(req: SimulateRequest):
    try:
        work_type = to_work_type(req.work_type)

        # 🔹 create Task
        task = Task(
            task_id="SIM-1",
            name="Simulated Task",
            category="SIM",
            work_type=work_type,
            leader=to_skill(list(req.duration.keys())[0]),
            start_date=None,
        )

        # 🔹 create SubTasks
        subtasks: List[SubTask] = []
        for i, (skill_name, days) in enumerate(req.duration.items()):
            subtasks.append(
                SubTask(
                    task_id=task.task_id,
                    skill=to_skill(skill_name),
                    sequence=i + 1,
                    duration_days=days,
                )
            )

        # 🔹 run AI
        engine = AIEngine(
            calendar={},              # mock ก่อน
            base_date=date.today()    # ใช้วันนี้เป็น default
            )

        result = engine.simulate(
            task=task,
            subtasks=subtasks,
            existing_tasks=[]  # 🔥 ยังไม่ต่อ DB
        )

        return {
            "status": "ok",
            "result": result
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


# =========================
# ROUTE: HEALTH CHECK
# =========================
@router.get("/check")
def check_ai():
    return {"status": "AI route ready"}