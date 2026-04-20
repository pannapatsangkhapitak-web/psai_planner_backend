# planner_service/app/mapper.py

def payload_to_task(req):
    return req  # placeholder

def payload_to_subtasks(req):
    return []  # placeholder
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