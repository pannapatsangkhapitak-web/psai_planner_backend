from datetime import date
from planner_v2.core import Task, Skill, WorkType
from core.workflow import build_subtasks

task = Task(
    task_id="TASK-001",
    name="Room Renovation",
    category="Room PPM",
    work_type=WorkType.CNP,
    leader=Skill.CARPENTER,
    start_date=date(2026, 1, 10),
)

subs = build_subtasks(
    task,
    {
        Skill.CARPENTER: 3,
        Skill.PAINTER: 2,
    }
)

for s in subs:
    print(s)
