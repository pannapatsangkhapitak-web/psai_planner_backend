"""
Trace & State Transition Log

Responsibilities:
- Record every task state transition
- Preserve reason & timestamp
- Provide auditable history per task
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from .enums import TaskState


# ==================================================
# Trace Event
# ==================================================

@dataclass
class TraceEvent:
    task_id: str
    from_state: TaskState
    to_state: TaskState
    reason: str
    timestamp: datetime


# ==================================================
# Trace Log (In-memory)
# ==================================================

class TraceLog:
    """
    Simple in-memory trace log.
    Can be replaced by DB / file storage later.
    """

    def __init__(self):
        self._events: List[TraceEvent] = []

    def record(
        self,
        task_id: str,
        from_state: TaskState,
        to_state: TaskState,
        reason: str,
    ) -> None:
        """
        Record a state transition.
        """
        self._events.append(
            TraceEvent(
                task_id=task_id,
                from_state=from_state,
                to_state=to_state,
                reason=reason,
                timestamp=datetime.now(),
            )
        )

    def history(self, task_id: str) -> List[TraceEvent]:
        """
        Get full trace history of a task.
        """
        return [e for e in self._events if e.task_id == task_id]

    def last_event(self, task_id: str) -> Optional[TraceEvent]:
        """
        Get last trace event for a task.
        """
        events = self.history(task_id)
        return events[-1] if events else None

    def all_events(self) -> List[TraceEvent]:
        """
        Get all trace events.
        """
        return list(self._events)
