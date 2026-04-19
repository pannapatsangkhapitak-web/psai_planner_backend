from pydantic import BaseModel
from typing import Optional, List

class SubTaskInput(BaseModel):
    property_id: str   # 🔥 เพิ่มบรรทัดนี้
    skill: str
    duration: int

class WhatIfRequest(BaseModel):
    task_name: str
    actor: Optional[str] = None
    preferred_date: Optional[str] = None
    subtasks: Optional[List[SubTaskInput]] = []