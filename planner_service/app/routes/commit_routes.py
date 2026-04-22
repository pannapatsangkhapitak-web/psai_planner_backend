# =========================================================
# PSAI ENGINE
# File: commit_route.py
# Version: v1.0.0-d0/21.1.26
# Layer: API
# Role: 
# Status: ACTIVE
# Debug: 
# =========================================================

from datetime import datetime, date
from fastapi import APIRouter, HTTPException

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

#==================================================
# 🔧 helpers
#==================================================

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
def commit_task(req: CommitRequest):
    try:
        # --------------------------------------------------
        # 1) payload → Task
        # --------------------------------------------------
        task = payload_to_task(req.task)
        task.created_by = req.actor
        
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
            actor_uid=req.actor,
            decision_policy=req.decision_policy,
            use_ai=req.use_ai_helper,
            hotel_id=req.hotel_id,   # ✅ เพิ่ม
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
            task_id=result["task_id"],  # ✅ ดึงจาก result
            final_state="SCHEDULED",
            committed_start_date=result["committed_start"],  # ✅ ดึงจาก result
            committed_timeline=result["timeline"],
            actor=req.actor,
            created_at=datetime.utcnow().isoformat(),
            )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )