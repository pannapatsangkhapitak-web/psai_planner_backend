from datetime import date
from planner_v2.core import Task, Skill, WorkType
from planner_v2.core.workflow import build_subtasks
from planner_v2.core.scheduler import schedule_task

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

ok, scheduled = schedule_task(task, subs, policy="STRICT")

print("OK:", ok)
print("STATE:", task.state)

for s in scheduled:
    print(s.skill, s.start_date, s.end_date)

from planner_v2.core.scheduler import trace_log

for e in trace_log.all_events():
    print(e)

