# =========================================================
# PSAI ENGINE
# File: schemas.py
# Version: v1.0.0-d0/21.1.26
# Layer: API
# Role: 
# Status: ACTIVE
# Debug: 
# =========================================================
from pydantic import BaseModel
from typing import Optional, List, Dict

class TimelineItem(BaseModel):
    skill: str
    start: str
    end: str

class TaskPayload(BaseModel):
    task_id: str
    name: str
    category: str
    work_type: str
    durations_by_skill: Optional[Dict[str, int]] = None

class SubTaskInput(BaseModel):
    skill: str
    duration_days: int
    
class SimulateRequest(BaseModel):
    property_id: str
    work_type: str
    duration: Dict[str, int]
    
class WhatIfRequest(BaseModel):
    task_name: str
    actor: Optional[str] = None
    preferred_date: Optional[str] = None
    subtasks: Optional[List[SubTaskInput]] = []

class CommitRequest(BaseModel):
    task: TaskPayload
    actor: str
    timeline: List[TimelineItem]

    # optional controls
    decision_policy: Optional[str] = "STRICT"
    use_ai_helper: Optional[bool] = False

class CommitResponse(BaseModel):
    task_id: str
    final_state: str
    committed_start_date: str
    committed_timeline: List[Dict]
    actor: str
    created_at: str

CommitRequest.model_rebuild()
CommitResponse.model_rebuild()