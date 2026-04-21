# =========================================================
# PSAI ENGINE
# File: enums.py
# Version: v1.0.0-d0/21.1.26
# Layer: API
# Role: 
# Status: ACTIVE
# Debug: 
# =========================================================

from enum import Enum

class Skill(Enum):
    TECH = "TECH"
    CARPENTER = "CARPENTER"
    PAINTER = "PAINTER"
    POOL = "POOL"


def normalize_skill(skill: str) -> str:
    if not skill:
        return skill

    skill = skill.upper()

    if skill == "PM":
        return "TECH"

    return skill

class WorkType(Enum):
    INV = "INV"
    CNP = "CNP"
    PNP = "PNP"
    PCP = "PCP"

class TaskState(Enum):
    DRAFT = "DRAFT"
    PLANNED = "PLANNED"
    CONFLICT = "CONFLICT"
    DELAYED = "DELAYED"
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
