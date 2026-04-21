# =========================================================
# PSAI ENGINE
# File: whatif_engine.py
# Version: v1.0.0-d0/21.1.26
# Layer: engine
# Role: 
# Status: ACTIVE
# Debug: 
# =========================================================

from datetime import date
from .ai_engine import AIEngine


class WhatIfEngine:

    def __init__(self, calendar_adapter):
        self.cal = calendar_adapter
        self.ai = AIEngine(calendar_adapter)

    # --------------------------------------------------------
    # MAIN ENTRY
    # --------------------------------------------------------
    def simulate(self, task_payload, subtasks):
        """
        task_payload = {
            "task_name": "...",
            "category": "...",
            "work_type": "...",
            "preferred_date": date | None,
            "prefer_mode": "FIXED" | "AI",
            "actor_uid": "U123"
        }
        """

        preferred = task_payload.get("preferred_date")
        prefer_mode = task_payload.get("prefer_mode", "AI")

        # =====================================================
        # CASE 1: FIXED (preferred date explicitly chosen)
        # =====================================================
        if prefer_mode == "FIXED" and preferred:
            slot = self.ai.suggest_fixed(preferred, subtasks)

            if slot is None:
                return {
                    "feasible": False,
                    "mode": "PREFERRED",
                    "initial_start_date": preferred.isoformat(),
                    "suggested_start_date": None,
                    "reason": "PREFERRED_DATE_NOT_AVAILABLE",
                    "timeline": [],
                    "conflict": True,
                }

            return {
                "feasible": True,
                "mode": "PREFERRED",
                "initial_start_date": preferred.isoformat(),
                "suggested_start_date": preferred.isoformat(),
                "reason": "PREFERRED_DATE_AVAILABLE",
                "timeline": self._timeline_to_api(slot.chain),
                "conflict": False,
            }

        # =====================================================
        # CASE 2: AI HELPER (search next available slot)
        # =====================================================
        slot = self.ai.suggest_ai(
        subtasks=subtasks,
        start_hint=preferred,   # ⭐ นี่แหละตัวหาย
         )

        if slot is None:
            return {
                "feasible": False,
                "mode": "AI",
                "initial_start_date": preferred.isoformat() if preferred else None,
                "suggested_start_date": None,
                "reason": "NO_SLOT_IN_180_DAYS",
                "timeline": [],
                "conflict": True,
            }

        return {
            "feasible": True,
            "mode": "AI",
            "initial_start_date": preferred.isoformat() if preferred else None,
            "suggested_start_date": slot.start.isoformat(),
            "reason": "AI_SLOT_FOUND",
            "timeline": self._timeline_to_api(slot.chain),
            "conflict": preferred is not None,
        }

    # --------------------------------------------------------
    # FORMAT timeline → API
    # --------------------------------------------------------
    def _timeline_to_api(self, chain):
        return [
            {
                "skill": st.skill,
                "start": st.start_date.isoformat(),
                "end": st.end_date.isoformat(),
            }
            for st in chain
        ]