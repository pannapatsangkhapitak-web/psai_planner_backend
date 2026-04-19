from pydantic import BaseModel
from typing import Optional, List

class SimulateRequest(BaseModel):
    property_id: str
    work_type: str
    duration: Dict[str, int]
    
class WhatIfRequest(BaseModel):
    task_name: str
    actor: Optional[str] = None
    preferred_date: Optional[str] = None
    subtasks: Optional[List[SubTaskInput]] = []