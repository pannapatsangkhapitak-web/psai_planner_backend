# planner_service/app/mapper.py
from planner_v2.core.models import SubTask

def payload_to_task(req):
    return req  # placeholder

def payload_to_subtasks(task, durations_by_skill):
    subtasks = []

    for skill, days in durations_by_skill.items():
        subtasks.append(
            SubTask(
                task_id=task.task_id,
                skill=Skill[skill],
                duration=days
            )
        )

    return subtasks

from planner_v2.core.models import Task
from planner_v2.core.enums import WorkType, Skill

def payload_to_task(payload):
    return Task(
        task_id=payload.task_id,
        name=payload.name,
        category=payload.category,
        work_type=WorkType[payload.work_type],
        leader=Skill.CARPENTER,  # หรือ derive จาก logic
        start_date=None,
        created_by=None
    )