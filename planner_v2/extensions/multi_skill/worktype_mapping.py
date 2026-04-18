from core.models import SubTask, Skill
from core.enums import WorkType

# =========================================================
# WORK TYPE → SKILL CHAIN DEFINITION (MULTI-SKILL ONLY)
# =========================================================
# tuple format
# (Skill, default_duration_days)
#
# IMPORTANT:
# Order = execution sequence
# Used by AI slot finder to enforce contiguous scheduling
# =========================================================

WORKTYPE_SKILL_CHAIN: dict[WorkType, list[tuple[Skill, int]]] = {
    WorkType.CNP: [  # Carpenter → Painter
        (Skill.CARPENTER, 1),
        (Skill.PAINTER, 1),
    ],

    WorkType.PNP: [  # PM → Painter
        (Skill.TECH, 1),
        (Skill.PAINTER, 1),
    ],

    WorkType.PCP: [  # PM → Carpenter → Painter
        (Skill.TECH, 1),
        (Skill.CARPENTER, 1),
        (Skill.PAINTER, 1),
    ],
}


# =========================================================
# HELPER: GET SKILL SEQUENCE
# =========================================================
# Used by AI slot finder to build contiguous skill slots
# =========================================================

def get_skill_sequence(work_type: WorkType) -> list[Skill]:

    chain = WORKTYPE_SKILL_CHAIN.get(work_type)

    if not chain:
        raise ValueError(f"Unsupported work type: {work_type}")

    return [skill for skill, _ in chain]


# =========================================================
# HELPER: TOTAL DURATION OF CHAIN
# =========================================================
# Useful for AI calendar scanning
# =========================================================

def get_total_duration(work_type: WorkType) -> int:

    chain = WORKTYPE_SKILL_CHAIN.get(work_type)

    if not chain:
        raise ValueError(f"Unsupported work type: {work_type}")

    return sum(duration for _, duration in chain)


# =========================================================
# FACTORY: WORK TYPE → SUBTASKS
# =========================================================

def build_subtasks_from_worktype(
    *,
    task_id: str,
    work_type: str | WorkType,
    durations_override: dict[str | Skill, int] | None = None,
) -> list[SubTask]:

    # normalize work_type → WorkType
    if isinstance(work_type, str):
        try:
            work_type = WorkType[work_type]
        except KeyError:
            raise ValueError(f"Unknown WorkType: {work_type}")

    chain = WORKTYPE_SKILL_CHAIN.get(work_type)

    if not chain:
        raise ValueError(
            f"Unsupported work type for multi-skill: {work_type}"
        )

    # -----------------------------------------------------
    # normalize durations_override → dict[Skill, int]
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # build subtasks
    # -----------------------------------------------------

    subtasks: list[SubTask] = []

    for idx, (skill, default_days) in enumerate(chain):

        duration = normalized_durations.get(skill, default_days)

        subtasks.append(
            SubTask(
                task_id=task_id,
                skill=skill,
                sequence=idx,  # execution order
                duration_days=duration,
                start_date=None,
                end_date=None,
            )
        )

    return subtasks