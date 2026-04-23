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
        role: str,   # 🔥 เพิ่ม
        decision_policy: str,
        use_ai: bool,
        hotel_id: str,
    ):
        # --------------------------------------------
        # 1) Validate timeline
        # --------------------------------------------
        for st in subtasks:
            if not st.start_date or not st.end_date:
                return {
                    "success": False,
                    "reason": "INVALID_TIMELINE"
                }

        # --------------------------------------------
        # 2) Sort execution order
        # --------------------------------------------
        subtasks_sorted = sorted(subtasks, key=lambda st: st.sequence)

        # --------------------------------------------
        # 3) Build timeline
        # --------------------------------------------
        timeline = []

        for st in subtasks_sorted:
            timeline.append({
                "skill": st.skill.name,
                "start": st.start_date.isoformat(),
                "end": st.end_date.isoformat(),
            })

        committed_start = timeline[0]["start"]

        # --------------------------------------------
        # 🔥 4) CONFLICT CHECK (หัวใจของระบบ)
        # --------------------------------------------
        conflict_tasks = self.db.check_conflict(
            subtasks=subtasks_sorted,
            hotel_id=hotel_id
        )

        if conflict_tasks:

            # ❌ USER → BLOCK
            if role == "USER":
                return {
                    "success": False,
                    "reason": "CONFLICT_NOT_ALLOWED"
                }

            # 🔴 MASTER → ALLOW WITH CONSEQUENCE
            if role == "MASTER":

                # 1) archive task เดิม
                self.db.move_to_archive(conflict_tasks, hotel_id)

                # 3) audit log
                self.db.log_audit({
                    "action": "OVERRIDE",
                    "actor": actor_uid,
                    "affected_tasks": [t["task_id"] for t in conflict_tasks],
                    "new_task": task.task_id,
                })

        # --------------------------------------------
        # 5) Persist new task
        # --------------------------------------------
        task_id = self.db.commit_chain(
            task=task,
            subtasks=subtasks_sorted,
            actor=actor_uid,
            hotel_id=hotel_id,
        )

        # --------------------------------------------
        # 6) Return result
        # --------------------------------------------
        return {
            "success": True,
            "task_id": task_id,
            "committed_start": committed_start,
            "timeline": timeline,
        }