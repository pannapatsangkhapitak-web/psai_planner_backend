# =========================================================
# PSAI ENGINE
# File: worktype_mapping.py
# Version: v1.0.0-d1
# Layer: SUPPORT
# Role: WorkType → Skill Chain + SubTask Builder
# Status: ACTIVE (LEGACY COMPATIBLE)
# =========================================================

from planner_v2.core.models import SubTask, Skill
from planner_v2.core.enums import WorkType

WORKTYPE_SKILL_CHAIN: dict[WorkType, list[tuple[Skill, int]]] = {
    WorkType.CNP: [  # Carpenter → Painter
        (Skill.CARPENTER, 1),
        (Skill.PAINTER, 1),
    ],
    WorkType.PNP: [  # TECH → Painter
        (Skill.TECH, 1),
        (Skill.PAINTER, 1),
    ],
    WorkType.PCP: [  # TECH → Carpenter → Painter
        (Skill.TECH, 1),
        (Skill.CARPENTER, 1),
        (Skill.PAINTER, 1),
    ],
}

print("🔗 [PSAI v1.0.0-d1][worktype_mapping] LOADED")


# =========================================================
# HELPER: GET SKILL SEQUENCE
# =========================================================

def get_skill_sequence(work_type: WorkType) -> list[Skill]:
    chain = WORKTYPE_SKILL_CHAIN.get(work_type)

    if not chain:
        raise ValueError(f"Unsupported work type: {work_type}")

    return [skill for skill, _ in chain]


# =========================================================
# HELPER: TOTAL DEFAULT DURATION
# =========================================================

def get_total_duration(work_type: WorkType) -> int:
    chain = WORKTYPE_SKILL_CHAIN.get(work_type)

    if not chain:
        raise ValueError(f"Unsupported work type: {work_type}")

    return sum(duration for _, duration in chain)


# =========================================================
# FACTORY: BUILD SUBTASKS FROM WORKTYPE
# =========================================================

def build_subtasks_from_worktype(
    *,
    task_id: str,
    work_type: str | WorkType,
    durations_override: dict[str | Skill, int] | None = None,
) -> list[SubTask]:

    print(f"🧠 [PSAI v1.0.0-d1][worktype_mapping] BUILD → {work_type}")

    # -----------------------------------------
    # normalize work_type → WorkType
    # -----------------------------------------
    if isinstance(work_type, str):
        try:
            work_type = WorkType[work_type]
        except KeyError:
            raise ValueError(f"Unknown WorkType: {work_type}")

    chain = WORKTYPE_SKILL_CHAIN.get(work_type)

    if not chain:
        raise ValueError(f"Unsupported work type: {work_type}")

    # -----------------------------------------
    # normalize durations_override
    # -----------------------------------------
    normalized_durations: dict[Skill, int] = {}

    if durations_override:
        for k, v in durations_override.items():

            if isinstance(k, Skill):
                normalized_durations[k] = v
            else:
                try:
                    normalized_durations[Skill[k]] = v
                except KeyError:
                    raise ValueError(f"Unknown Skill in duration: {k}")

    # -----------------------------------------
    # build subtasks
    # -----------------------------------------
    subtasks: list[SubTask] = []

    for idx, (skill, default_days) in enumerate(chain):

        # 🔥 legacy-compatible fallback
        duration = normalized_durations.get(skill, default_days)

        subtasks.append(
            SubTask(
                task_id=task_id,
                skill=skill,
                sequence=idx,
                duration_days=duration,
                start_date=None,
                end_date=None,
            )
        )

    print(f"✅ [PSAI v1.0.0-d1][worktype_mapping] BUILT {len(subtasks)} subtasks")

    return subtasks