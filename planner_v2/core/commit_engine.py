# planner_v2/core/commit_engine.py

from planner_v2.core.models import Task, SubTask


class CommitEngine:

    def __init__(self, ai, firestore):
        self.ai = ai
        self.db = firestore

    # ✅ ต้องอยู่ใน class
    def apply_commit(
        self,
        task: Task,
        subtasks: list[SubTask],
        actor_uid: str,
        decision_policy: str,
        use_ai: bool,
    ):
        # --------------------------------------------
        # 1) Run AI scheduling (single source of truth)
        # --------------------------------------------
        result = self.ai.suggest(task, subtasks)

        if not result.get("feasible"):
            return {
                "success": False,
                "reason": result.get("reason", "COMMIT_FAILED"),
            }

        # --------------------------------------------
        # 2) Ensure SubTasks ordered by execution
        # (important for multi-skill chain)
        # --------------------------------------------
        subtasks_sorted = sorted(subtasks, key=lambda st: st.sequence)

        # --------------------------------------------
        # 3) Normalize timeline from SubTasks
        # --------------------------------------------
        timeline = []

        for st in subtasks_sorted:

            # AI must populate these fields
            if not st.start_date or not st.end_date:
                continue

            timeline.append({
                "skill": st.skill.name,             # "PAINTER"
                "start": st.start_date.isoformat(), # "2026-03-13"
                "end": st.end_date.isoformat(),
            })

        if not timeline:
            return {
                "success": False,
                "reason": "AI_TIMELINE_EMPTY",
            }

        committed_start = timeline[0]["start"]

        # --------------------------------------------
        # 4) Persist to Firestore
        # --------------------------------------------
        task_id = self.db.commit_chain(
            task=task,
            subtasks=subtasks_sorted,
            actor=actor_uid,
        )

        return {
            "success": True,
            "task_id": task_id,
            "committed_start": committed_start,
            "timeline": timeline,
        }