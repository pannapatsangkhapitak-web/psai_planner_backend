# =========================================================
# PSAI ENGINE
# File: commit_engine.py
# Version: v1.0.0-d0/21.1.26
# Layer: engine
# Role: 
# Status: ACTIVE
# Debug: 
# =========================================================

from planner_v2.core.models import Task, SubTask


class CommitEngine:

    def __init__(self, ai, firestore):
        self.ai = ai
        self.db = firestore

    def apply_commit(
        self,
        task: Task,
        subtasks: list[SubTask],
        actor_uid: str,
        decision_policy: str,
        use_ai: bool,
        hotel_id: str,   # ✅ เพิ่มตรงนี้
    ):
        # --------------------------------------------
        # 1) Validate timeline (must be provided)
        # --------------------------------------------
        for st in subtasks:
            if not st.start_date or not st.end_date:
                return {
                    "success": False,
                    "reason": "INVALID_TIMELINE"
                }

        # --------------------------------------------
        # 2) Ensure execution order (multi-skill chain)
        # --------------------------------------------
        subtasks_sorted = sorted(subtasks, key=lambda st: st.sequence)

        # --------------------------------------------
        # 3) Build timeline (from USER, not AI)
        # --------------------------------------------
        timeline = []

        for st in subtasks_sorted:
            timeline.append({
                "skill": st.skill.name,
                "start": st.start_date.isoformat(),
                "end": st.end_date.isoformat(),
            })

        # --------------------------------------------
        # 4) Determine committed start date
        # --------------------------------------------
        committed_start = timeline[0]["start"]  # ต้องมาจาก timeline เท่านั้น
        
        # --------------------------------------------
        # 5) Persist to Firestore
        # --------------------------------------------
        task_id = self.db.commit_chain(
            task=task,
            subtasks=subtasks_sorted,
            actor=actor_uid,
            hotel_id=hotel_id,   # ✅ เพิ่มบรรทัดนี้
        )

        # --------------------------------------------
        # 6) Return result
        # --------------------------------------------
        return {
                "success": True,
                "task_id": task_id,
                "committed_start": committed_start,  # 🔥 ตรงนี้
                "timeline": timeline,
        }