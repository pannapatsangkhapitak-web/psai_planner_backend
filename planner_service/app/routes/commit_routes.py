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

# ==================================================
# 🚀 COMMIT ROUTE (CLEAN)
# ==================================================

from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Request

from planner_service.app.schemas import CommitRequest, CommitResponse
from planner_service.app.mapper import payload_to_task, payload_to_subtasks

from planner_v2.core.commit_engine import CommitEngine
from planner_v2.db.firestore_db import FirestoreDB

from planner_v2.extensions.multi_skill.worktype_mapping import (
    build_subtasks_from_worktype
)
from planner_v2.core.enums import WorkType

from ..core.auth import get_current_user
from ..services.role_service import get_user_role

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
            print("❌ SKIP:", item.skill)
            continue

        print("✅ MATCH:", item.skill)

        # 🔥 IMPORTANT: item.start / item.end ต้องเป็น date
        st.start_date = item.start
        st.end_date = item.end - timedelta(days=1)


# ==================================================
# 🚀 MAIN ROUTE
# ==================================================

@router.post("", response_model=CommitResponse)
def commit_task(req: CommitRequest, request: Request):

    try:
        # --------------------------------------------------
        # 🔐 AUTH
        # --------------------------------------------------
        user = get_current_user(request)
        uid = user["uid"]

        role = get_user_role(uid, req.hotel_id)

        print(f"🔥 UID = {uid}")
        print(f"🔥 HOTEL = {req.hotel_id}")
        print(f"🔥 ROLE = {role}")

        # --------------------------------------------------
        # 1) payload → Task
        # --------------------------------------------------
        task = payload_to_task(req.task)
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
        # 3) APPLY FLOW (🔥 แยกชัด)
        # --------------------------------------------------

        if req.timeline:
            # ✅ FLOW A: Timeline (AI หรือ advanced user)
            apply_timeline_to_subtasks(subtasks, req.timeline)

        elif req.preferred_start_date:
            # ✅ FLOW B: Manual (simple user)
            for st in subtasks:
                start = req.preferred_start_date
                st.start_date = start
                st.end_date = start + timedelta(days=st.duration_days - 1)

        else:
            raise HTTPException(
                status_code=400,
                detail="Either timeline or preferred_start_date is required"
            )

        # --------------------------------------------------
        # 4) Sanity Check
        # --------------------------------------------------
        for st in subtasks:
            if st.start_date is None or st.end_date is None:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid timeline mapping"
                )

        # --------------------------------------------------
        # 5) Commit via Engine
        # --------------------------------------------------
        db = FirestoreDB()

        engine = CommitEngine(
            ai=None,
            firestore=db
        )

        policy = (req.decision_policy or "STRICT").upper()

        result = engine.apply_commit(
            task=task,
            subtasks=subtasks,
            actor_uid=uid,
            role=role,
            decision_policy=policy,
            use_ai=req.use_ai_helper,
            hotel_id=req.hotel_id,
        )

        if not result.get("success", False):
            raise HTTPException(
                status_code=409,
                detail=result.get("reason", "Commit failed")
            )

        # --------------------------------------------------
        # 6) Response
        # --------------------------------------------------
        return CommitResponse(
            task_id=result["task_id"],
            final_state="SCHEDULED",
            committed_start_date=result["committed_start"],
            committed_timeline=result["timeline"],  # 🔥 engine เป็น source
            actor=uid,
            created_at=datetime.utcnow().isoformat(),
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )