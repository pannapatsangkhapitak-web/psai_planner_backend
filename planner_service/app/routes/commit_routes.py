# =========================================================
# PSAI ENGINE
# File: commit_route.py
# Version: v1.0.0-d1/22.4.26
# Layer: API
# Role: Enforce commit + role-based override (AUTH FROM TOKEN)
# Status: ACTIVE
# Debug:
# - d1: REMOVE TRUST FROM PAYLOAD actor
# - d1: ADD get_current_uid() from Authorization header
# - d1: DEBUG compare AUTH UID vs PAYLOAD actor
# =========================================================

from datetime import datetime, date
from fastapi import APIRouter, HTTPException, Request

from planner_service.app.schemas import CommitRequest, CommitResponse
from planner_service.app.mapper import payload_to_task, payload_to_subtasks

from planner_v2.core.commit_engine import CommitEngine
from planner_v2.core.calendar_adapter import CalendarAdapter
from planner_v2.db.firestore_db import FirestoreDB

from planner_v2.extensions.multi_skill.worktype_mapping import (
    build_subtasks_from_worktype
)
from planner_v2.core.enums import WorkType

router = APIRouter(prefix="/commit", tags=["Commit"])

# ==================================================
# 🔐 AUTH HELPER
# ==================================================
def get_current_uid(request: Request):
    """
    🔥 SOURCE OF TRUTH FOR USER ID
    - Read from Authorization header ONLY
    - DO NOT TRUST req.actor
    """

    auth = request.headers.get("Authorization")

    if not auth:
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        token = auth.split(" ")[1]
    except:
        raise HTTPException(status_code=401, detail="Invalid token format")

    # ⚠️ DEV MODE (ยังไม่ verify Firebase จริง)
    # TODO: replace with firebase_admin.verify_id_token(token)

    print(f"🔥 RAW TOKEN (partial) = {token[:20]}...")

    # 🔥 TEMP: ใช้ fallback UID ชั่วคราว
    # 👉 ใน production ต้อง decode token จริง
    return "DEV_FAKE_UID"


# ==================================================
# 🔧 helpers
# ==================================================

def normalize_skill(skill: str) -> str:
    return skill.upper()


def apply_timeline_to_subtasks(subtasks, timeline):
    by_skill = {st.skill.name.upper(): st for st in subtasks}

    for item in timeline:
        skill_code = normalize_skill(item.skill)
        st = by_skill.get(skill_code)

        if not st:
            continue

        st.start_date = date.fromisoformat(item.start)
        st.end_date = date.fromisoformat(item.end)


def build_committed_timeline(timeline):
    """
    Format response timeline
    """
    return [
        {
            "skill": normalize_skill(item.skill),
            "start": date.fromisoformat(item.start),
            "end": date.fromisoformat(item.end),
        }
        for item in timeline
    ]


# ==================================================
# 🚀 COMMIT ROUTE
# ==================================================

@router.post("", response_model=CommitResponse)
def commit_task(req: CommitRequest, request: Request):
    try:
        # --------------------------------------------------
        # 🔐 AUTH (d1)
        # --------------------------------------------------
        uid = get_current_uid(request)

        print(f"🔥 AUTH UID = {uid}")
        print(f"🔥 PAYLOAD ACTOR = {req.actor}")  # debug only (DO NOT TRUST)

        # --------------------------------------------------
        # 1) payload → Task
        # --------------------------------------------------
        task = payload_to_task(req.task)

        # ❌ OLD (unsafe)
        # task.created_by = req.actor

        # ✅ NEW (trusted)
        task.created_by = uid

        # --------------------------------------------------
        # 2) Build Subtasks
        # --------------------------------------------------
        if task.work_type == WorkType.INV:
            subtasks = payload_to_subtasks(
                task,
                req.task.durations_by_skill
            )
        else:
            subtasks = build_subtasks_from_worktype(
                task_id=task.task_id,
                work_type=task.work_type.name,
            )

        # --------------------------------------------------
        # 3) Apply timeline (🔥 USER CHOICE, NOT AI)
        # --------------------------------------------------
        if not req.timeline:
            raise HTTPException(
                status_code=400,
                detail="Timeline is required for commit"
            )

        apply_timeline_to_subtasks(subtasks, req.timeline)

        # sanity check
        for st in subtasks:
            if st.start_date is None or st.end_date is None:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid timeline mapping"
                )

        # --------------------------------------------------
        # 4) Commit to Firestore
        # --------------------------------------------------
        db = FirestoreDB()

        committed = db.list_committed(req.hotel_id)

        calendar = CalendarAdapter(committed)

        engine = CommitEngine(
            ai=None,
            firestore=db
        )

        result = engine.apply_commit(
            task=task,
            subtasks=subtasks,
            actor_uid=uid,  # ✅ ใช้ uid จริง
            decision_policy=req.decision_policy,
            use_ai=req.use_ai_helper,
            hotel_id=req.hotel_id,
        )

        if not result.get("success", False):
            raise HTTPException(
                status_code=409,
                detail=result.get("reason", "Commit failed")
            )

        # --------------------------------------------------
        # 5) Response
        # --------------------------------------------------
        committed_timeline = build_committed_timeline(req.timeline)

        return CommitResponse(
            task_id=result["task_id"],
            final_state="SCHEDULED",
            committed_start_date=result["committed_start"],
            committed_timeline=result["timeline"],
            actor=uid,  # ✅ reflect real user
            created_at=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )