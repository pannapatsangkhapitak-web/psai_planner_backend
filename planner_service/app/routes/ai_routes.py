from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, List
from datetime import date
from google.cloud import firestore

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

        # create Task
        task = Task(
            task_id="SIM-1",
            name="Simulated Task",
            category="SIM",
            work_type=work_type,
            leader=to_skill(list(req.duration.keys())[0]),
            start_date=None,
        )

        # create SubTasks
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

        # =========================
        # 🔥 ดึงข้อมูลจาก Firestore
        # =========================
        from google.cloud import firestore

        db = firestore.Client(project="aras-connect-planner-v2")

        docs = db.collection("properties") \
            .document(req.property_id) \
            .collection("tasks_committed") \
            .stream()

        committed_docs = [d.to_dict() for d in docs]

        # =========================
        # 🔥 ใช้ CalendarAdapter
        # =========================
        from planner_v2.core.calendar_adapter import CalendarAdapter

        calendar = CalendarAdapter(committed_docs)
        print("REQ:", req)
        print("HAS PROPERTY:", hasattr(req, "property_id"))
        # =========================
        # run AI
        # =========================
        engine = AIEngine(
            calendar=calendar,
            base_date=date.today()
        )

        result = engine.suggest(
            task=task,
            subtasks=subtasks
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