"""
Scheduler Core (Day-based)

Responsibilities:
- Assign start/end dates to SubTasks
- Enforce daily capacity (no overload)
- Detect conflicts
- Support STRICT vs ADD_ANYWAY decision policy
- Record state transitions via TraceLog
"""

from datetime import timedelta
from typing import Dict, List
from collections import defaultdict

from .models import Task, SubTask
from .enums import Skill, TaskState
from .trace import TraceLog


# ==================================================
# In-memory calendar (can be replaced by storage)
# ==================================================

# daily_load[skill][date] = used capacity
daily_load: Dict[Skill, Dict] = defaultdict(lambda: defaultdict(int))

# daily_capacity[skill][date] = max capacity
daily_capacity: Dict[Skill, Dict] = defaultdict(lambda: defaultdict(lambda: 1))


# ==================================================
# Trace log (in-memory)
# ==================================================

trace_log = TraceLog()


# ==================================================
# Utilities
# ==================================================

def daterange(start, end):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def capacity_available(subtask: SubTask) -> bool:
    """
    Check if capacity allows this subtask to be scheduled.
    """
    for d in daterange(subtask.start_date, subtask.end_date):
        if daily_load[subtask.skill][d] + 1 > daily_capacity[subtask.skill][d]:
            return False
    return True


# ==================================================
# Core placement logic
# ==================================================

def try_place_workflow(
    subtasks: List[SubTask],
    start_date
):
    """
    Attempt to place workflow starting from start_date.
    Does NOT commit load.
    """

    scheduled: List[SubTask] = []
    current_date = start_date

    for st in sorted(subtasks, key=lambda x: x.sequence):

        # clone subtask to avoid mutation
        st = SubTask(**vars(st))

        st.start_date = current_date
        st.end_date = current_date + timedelta(days=st.duration_days - 1)

        if not capacity_available(st):
            return False, None

        scheduled.append(st)
        current_date = st.end_date + timedelta(days=1)

    return True, scheduled


def find_next_available_start(
    subtasks: List[SubTask],
    preferred_start
):
    """
    Find the next date where workflow can be placed.
    """
    probe = preferred_start

    while True:
        ok, scheduled = try_place_workflow(subtasks, probe)
        if ok:
            return probe, scheduled
        probe += timedelta(days=1)


def commit_workflow(subtasks: List[SubTask]) -> None:
    """
    Commit workflow into daily load calendar.
    """
    for st in subtasks:
        for d in daterange(st.start_date, st.end_date):
            daily_load[st.skill][d] += 1


# ==================================================
# Public API
# ==================================================

def schedule_task(
    task: Task,
    subtasks: List[SubTask],
    policy: str = "STRICT"  # STRICT | ADD_ANYWAY
):
    """
    Schedule a task according to policy.

    Returns:
        success (bool), scheduled_subtasks (List[SubTask] | None)
    """

    # --------------------------------------------------
    # Try preferred start
    # --------------------------------------------------
    ok, scheduled = try_place_workflow(subtasks, task.start_date)

    if ok:
        commit_workflow(scheduled)

        trace_log.record(
            task_id=task.task_id,
            from_state=task.state,
            to_state=TaskState.SCHEDULED,
            reason="scheduled_successfully",
        )

        task.state = TaskState.SCHEDULED
        return True, scheduled

    # --------------------------------------------------
    # Conflict
    # --------------------------------------------------
    trace_log.record(
        task_id=task.task_id,
        from_state=task.state,
        to_state=TaskState.CONFLICT,
        reason="capacity_conflict",
    )

    task.state = TaskState.CONFLICT

    if policy == "STRICT":
        return False, None

    # --------------------------------------------------
    # ADD_ANYWAY → delay
    # --------------------------------------------------
    new_start, scheduled = find_next_available_start(
        subtasks,
        task.start_date
    )

    commit_workflow(scheduled)

    trace_log.record(
        task_id=task.task_id,
        from_state=TaskState.CONFLICT,
        to_state=TaskState.DELAYED,
        reason="user_add_it_anyway",
    )

    task.start_date = new_start
    task.state = TaskState.DELAYED

    return True, scheduled
