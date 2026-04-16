"""
Workflow Builder (TWI)

Responsibility:
- Convert Task + WorkType into ordered SubTasks
- Enforce workflow dependency rules
- Do NOT perform scheduling
"""

from typing import Dict, List
from .models import Task, SubTask
from .enums import Skill, WorkType


# ==================================================
# Workflow definition (FREEZE)
# ==================================================

WORKFLOW_MAP = {
    WorkType.INV: [],  # Independent work
    WorkType.CNP: [Skill.CARPENTER, Skill.PAINTER],
    WorkType.PNP: [Skill.TECH, Skill.PAINTER],
    WorkType.PCP: [Skill.TECH, Skill.CARPENTER, Skill.PAINTER],
}


# ==================================================
# Validation
# ==================================================

def validate_workflow(task: Task, durations: Dict[Skill, int]) -> None:
    """
    Validate that duration definitions are compatible with workflow.
    Raise ValueError if invalid.
    """

    if task.work_type not in WORKFLOW_MAP:
        raise ValueError(f"Unknown WorkType: {task.work_type}")

    workflow_skills = WORKFLOW_MAP[task.work_type]

    # INV: allow any skill, all independent
    if task.work_type == WorkType.INV:
        if not durations:
            raise ValueError("INV workflow requires at least one skill duration")
        return

    # Non-INV: strict dependency
    for skill in workflow_skills:
        if skill not in durations:
            raise ValueError(
                f"Missing duration for skill {skill.value} "
                f"in workflow {task.work_type.value}"
            )

    # Extra duration provided (warn-level behavior)
    for skill in durations:
        if skill not in workflow_skills:
            raise ValueError(
                f"Skill {skill.value} not allowed in workflow {task.work_type.value}"
            )


# ==================================================
# Builder
# ==================================================

def build_subtasks(
    task: Task,
    durations: Dict[Skill, int]
) -> List[SubTask]:
    """
    Build ordered SubTasks according to workflow definition.

    durations: {Skill: duration_in_days}
    """

    validate_workflow(task, durations)

    subtasks: List[SubTask] = []

    # --------------------------------------------------
    # Independent workflow (parallel)
    # --------------------------------------------------
    if task.work_type == WorkType.INV:
        for skill, days in durations.items():
            subtasks.append(
                SubTask(
                    task_id=task.task_id,
                    skill=skill,
                    sequence=0,
                    duration_days=days,
                )
            )
        return subtasks

    # --------------------------------------------------
    # Sequential workflow
    # --------------------------------------------------
    sequence = 1
    for skill in WORKFLOW_MAP[task.work_type]:
        subtasks.append(
            SubTask(
                task_id=task.task_id,
                skill=skill,
                sequence=sequence,
                duration_days=durations[skill],
            )
        )
        sequence += 1

    return subtasks
