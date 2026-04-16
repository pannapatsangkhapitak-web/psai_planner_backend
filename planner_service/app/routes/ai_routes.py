from fastapi import APIRouter
from datetime import date, datetime, timedelta
from collections import defaultdict

from app.schemas import WhatIfRequest
from app.mapper import payload_to_task, payload_to_subtasks

from planner_v2.core.ai_engine import AIEngine

from firebase_admin import firestore

router = APIRouter(tags=["AI"])


def get_mtpd(hotel_id: str) -> int:
    db = firestore.client()
    doc = db.collection("properties").document(hotel_id).get()

    if not doc.exists:
        return 1

    return doc.to_dict().get("mtpd", 1)


# =========================================================
# 🔥 CALENDAR BUILDER (FROM FIRESTORE)
# =========================================================

class SimpleCalendar:
    def __init__(self):
        self.load_map = defaultdict(int)

    def add(self, day: date, skill: str):
        key = (day, skill.upper())
        self.load_map[key] += 1

    def get_skill_load(self, day: date, skill: str):
        return self.load_map.get((day, skill.upper()), 0)


def build_calendar_from_firestore(hotel_id: str) -> SimpleCalendar:

    db = firestore.client()
    cal = SimpleCalendar()

    print("🔥 BUILD CALENDAR FOR:", hotel_id)

    docs = (
    db.collection("properties")
    .document(hotel_id)
    .collection("tasks_committed")
    .stream()
)

    for doc in docs:
        data = doc.to_dict()

        timeline = data.get("committed_timeline") or []

        for t in timeline:
            skill = t.get("skill")
            start = t.get("start")
            end = t.get("end")

            if not skill or not start or not end:
                continue

            s = datetime.fromisoformat(start).date()
            e = datetime.fromisoformat(end).date()

            d = s
            while d <= e:
                cal.add(d, skill)
                print(f"📅 LOAD ADD: {skill} @ {d}")
                d += timedelta(days=1)

    return cal


# =========================================================
# AI CHECK
# =========================================================

@router.post("/{hotel_id}/check")
def ai_check(hotel_id: str, req: WhatIfRequest):

    print("🔥 HOTEL ID =", hotel_id)

    # =====================================================
    # 1. BUILD REAL WORLD
    # =====================================================

    calendar = build_calendar_from_firestore(hotel_id)

    # =====================================================
    # 2. MAP TASK
    # =====================================================

    task = payload_to_task(req.task)

    if task.start_date is None:
        task.start_date = date.today()

    durations = getattr(req.task, "durations_by_skill", {}) or {}

    print("🧪 DURATIONS =", durations)

    subtasks = payload_to_subtasks(task, durations)
    task.subtasks = subtasks

    print("🧪 SUBTASKS =", subtasks)

    # =====================================================
    # 3. RUN ENGINE
    # =====================================================

    mtpd = get_mtpd(hotel_id)

    print("🔥 MTPD =", mtpd)

    engine = AIEngine(
        calendar=calendar,
        base_date=task.start_date,
        max_per_day=mtpd
    )

    result = engine.suggest(
        task=task,
        subtasks=subtasks,
        prefer_mode="NONE"
    )

    print("🔥 AI RESULT =", result)

    if not result["feasible"]:
        return result

    timeline = result["timeline"]

    print("📥 TIMELINE =", timeline)

    # =====================================================
    # 4. RESPONSE (SINGLE RETURN ONLY)
    # =====================================================

    return {
        "feasible": True,
        "slot": {
            "date": timeline[0]["start"],
            "timeline": timeline,
        },
       "explanation": result.get("explanation") or "No explanation available",
    }