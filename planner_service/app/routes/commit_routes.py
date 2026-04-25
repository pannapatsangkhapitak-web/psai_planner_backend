# =========================================================
# PSAI ENGINE
# File: commit_route.py
# Version: v1.1.0-d2/23.04.26
# Layer: API
# Role:
# - Enforce trusted commit (UID from Firebase token)
# - Enforce role-based override (MASTER only)
# Status: ACTIVE (AUTH + RBAC LOCKED)
#
# Debug:
# - d1: REMOVE TRUST FROM PAYLOAD actor
# - d1: ADD get_current_user() from Authorization header
# - d1: MIGRATE actor → backend UID (token-based)
#
# - d2: REMOVE actor from CommitRequest schema (no client authority)
# - d2: FRONTEND remove actor from request body
# - d2: ADD override guard (decision_policy == "OVERRIDE")
# - d2: ENFORCE require_master(uid) at API layer
# - d2: NORMALIZE decision_policy (upper-case safety)
# - d2: FIX exception handling (preserve HTTPException, avoid masking 403)
#
# System Behavior:
# - USER → allowed to commit under constraints (STRICT/SAFE)
# - USER → blocked on OVERRIDE (403 Forbidden)
# - MASTER → allowed to override constraints
#
# Security Model:
# - Client cannot define actor
# - Backend = source of truth (UID from token)
# - Role enforcement at API boundary (not frontend)
#
# Notes:
# - Override defined as decision_policy == "OVERRIDE"
# - Future: extend override detection from engine constraint violation
# - Next step: wire override → archive + audit trail
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
from ..core.auth import get_current_user
from ..services.role_service import get_user_role
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/commit", tags=["Commit"])

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
from planner_service.app.services.role_service import require_master

@router.post("", response_model=CommitResponse)
def commit_task(req: CommitRequest, request: Request):
    try:
        # --------------------------------------------------
        # 🔐 AUTH (source of truth)
        # --------------------------------------------------
        user = get_current_user(request)
        uid = user["uid"]
        
        role = get_user_role(uid, req.hotel_id)

        print(f"🔥 UID = {uid}")
        print(f"🔥 HOTEL = {req.hotel_id}")
        print(f"🔥 ROLE = {role}")

        # --------------------------------------------------
        # 🔒 OVERRIDE GUARD (MASTER only)
        # --------------------------------------------------
        policy = (req.decision_policy or "STRICT").upper()

        if policy == "OVERRIDE":
            require_master(uid, req.hotel_id)

        # --------------------------------------------------
        # 1) payload → Task
        # --------------------------------------------------
        task = payload_to_task(req.task)

        # ✅ trusted actor
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
        # 🔥 4) CHECK CONFLICT
        # --------------------------------------------------
        from planner_service.app.services.conflict_service import has_conflict
        
        conflict = has_conflict(subtasks, req.hotel_id)

        print(f"🔥 POLICY={policy} CONFLICT={conflict}")
        
        if policy == "STRICT" and conflict:
            return JSONResponse(
                status_code=200,
            content={
                "conflict": True,
                "message": "Task overlaps existing schedule"
            }
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
            actor_uid=uid,  # ✅ real UID
            role=role,   # 🔥 เพิ่มบรรทัดนี้
            decision_policy=policy,  # 🔥 ใช้ค่าที่ normalize แล้ว
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

    except HTTPException:
        # pass through (อย่าห่อ 403/400 ให้กลายเป็น 500)
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )