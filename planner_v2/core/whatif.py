"""
What-If Simulation & Scheduling Engine
"""

from copy import deepcopy
from dataclasses import dataclass
from datetime import date
from typing import List, Optional, Dict, Any

from .models import Task, SubTask
from .enums import TaskState
from .scheduler import try_place_workflow, find_next_available_start
from .trace import TraceLog


# ==================================================
# Result Model
# ==================================================
@dataclass
class WhatIfOutcome:
    feasible: bool
    initial_start: date
    resolved_start: Optional[date]
    final_state: TaskState
    reason: str
    simulated_subtasks: Optional[List[SubTask]]


# ==================================================
# Engine
# ==================================================
class WhatIfEngine:

    def __init__(self):
        self.trace = TraceLog()

    # ---------------- SIMULATE ----------------
    def simulate(self, task: Task, subtasks: List[SubTask], policy="STRICT") -> WhatIfOutcome:
        task_copy = deepcopy(task)
        subtasks_copy = deepcopy(subtasks)

        preferred_start = task_copy.start_date

        ok, scheduled = try_place_workflow(subtasks_copy, preferred_start)

        if ok:
            self.trace.record(task_copy.task_id, task_copy.state, TaskState.SCHEDULED, "simulate_success")

            return WhatIfOutcome(
                feasible=True,
                initial_start=preferred_start,
                resolved_start=preferred_start,
                final_state=TaskState.SCHEDULED,
                reason="Scheduled as requested",
                simulated_subtasks=scheduled
            )

        self.trace.record(task_copy.task_id, task_copy.state, TaskState.CONFLICT, "simulate_conflict")

        if policy == "STRICT":
            return WhatIfOutcome(
                feasible=False,
                initial_start=preferred_start,
                resolved_start=None,
                final_state=TaskState.CONFLICT,
                reason="Conflict - STRICT reject",
                simulated_subtasks=None
            )

        # ADD_ANYWAY -> find next possible
        next_start, scheduled = find_next_available_start(subtasks_copy, preferred_start)

        return WhatIfOutcome(
            feasible=True,
            initial_start=preferred_start,
            resolved_start=next_start,
            final_state=TaskState.DELAYED,
            reason="Delayed to available slot",
            simulated_subtasks=scheduled
        )

    # ---------------- COMMIT ----------------
    def schedule(self, task: Task, subtasks: List[SubTask], policy="STRICT") -> WhatIfOutcome:
        outcome = self.simulate(task, subtasks, policy)

        if not outcome.feasible:
            return outcome

        start = outcome.resolved_start or outcome.initial_start

        self.trace.record(task.task_id, task.state, TaskState.SCHEDULED, "commit_success")

        return WhatIfOutcome(
            feasible=True,
            initial_start=outcome.initial_start,
            resolved_start=start,
            final_state=TaskState.SCHEDULED,
            reason="Committed",
            simulated_subtasks=outcome.simulated_subtasks
        )

    # ---------------- SUMMARY ----------------
    def summary(self, outcome: WhatIfOutcome) -> Dict[str, Any]:
        data = {
            "feasible": outcome.feasible,
            "initial_start": outcome.initial_start,
            "resolved_start": outcome.resolved_start,
            "final_state": outcome.final_state.value,
            "reason": outcome.reason
        }

        data["subtasks"] = [{
            "skill": st.skill.value,
            "start": st.start_date,
            "end": st.end_date
        } for st in outcome.simulated_subtasks] if outcome.simulated_subtasks else []

        return data
