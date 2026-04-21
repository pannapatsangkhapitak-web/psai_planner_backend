# =========================================================
# PSAI ENGINE
# File: models.py
# Version: v1.0.0-d0/21.1.26
# Layer: infra
# Role: 
# Status: ACTIVE
# Debug: 
# =========================================================

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional
from .enums import Skill, WorkType, TaskState


@dataclass
class Task:
    task_id: str
    name: str
    category: str
    work_type: WorkType
    leader: Skill
    start_date: Optional[date]
    state: TaskState = TaskState.DRAFT
    created_by: Optional[str] = None


@dataclass
class SubTask:
    task_id: str
    skill: Skill
    sequence: int
    duration_days: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    def apply_start(self, start: date):
        """used by AIEngine in search mode"""
        self.start_date = start
        self.end_date = start + timedelta(days=self.duration_days - 1)
