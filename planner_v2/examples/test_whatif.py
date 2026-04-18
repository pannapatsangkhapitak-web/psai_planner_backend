from datetime import date
from planner_v2.core import Task, Skill, WorkType
from core.workflow import build_subtasks
from core.whatif import WhatIfEngine

task = Task(
    task_id="TASK-002",
    name="VIP Room Upgrade",
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

engine = WhatIfEngine()

outcome = engine.simulate(task, subs, policy="STRICT")

print("FEASIBLE:", outcome.feasible)
print("STATE:", outcome.final_state)
print("REASON:", outcome.reason)

print("\nDETAIL:")
print(engine.summary(outcome))

print("\nTRACE:")
for e in engine.trace.all_events():
    print(e)
