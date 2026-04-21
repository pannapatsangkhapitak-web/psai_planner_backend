# =========================================================
# PSAI ENGINE
# File: ai_engine.py
# Version: v1.0.0-d0/21.1.26
# Layer: Engine
# Role: 
# Status: ACTIVE
# Debug: 
# =========================================================

from datetime import date, timedelta, datetime
from collections import defaultdict
from .models import Task, SubTask

MAX_HORIZON = 180


class AISlot:
    def __init__(self, start: date, chain: list[SubTask]):
        self.start = start
        self.chain = chain


class AIEngine:

    def __init__(self, calendar, base_date: date, max_per_day: int = 1):
        self.cal = calendar
        self.base_date = base_date
        self.max_per_day = max_per_day

    # =========================================================
    # MAIN ENTRY
    # =========================================================
    def suggest(
        self,
        task: Task,
        subtasks: list[SubTask],
        prefer_mode: str = "NONE",
    ) -> dict:

        slot = None
        failed_log = []

        # preferred start
        if task.start_date:
            slot, failed = self._try_chain(task.start_date, subtasks)
            failed_log.extend(failed)

        if slot:
            return self._success(slot, task.work_type.name, failed_log)

        if prefer_mode == "STRICT":
            return {
                "feasible": False,
                "reason": "PREFERRED_DATE_NOT_AVAILABLE",
            }

        # simulate search
        slot, failed_log = self._search(subtasks, self.base_date)

        if slot:
            return self._success(slot, task.work_type.name, failed_log)

        return {
            "feasible": False,
            "reason": "NO_SLOT_180D",
        }

    # =========================================================
    # TRY PLACE FULL CHAIN
    # =========================================================
    def _try_chain(self, start: date, subtasks: list[SubTask]):

        chain = []
        current = start
        failed = []

        for st in subtasks:

            dur = st.duration_days
            if dur <= 0:
                return None, failed

            s = current
            e = s + timedelta(days=dur - 1)

            skill = st.skill.value.upper()

            for i in range(dur):
                day = s + timedelta(days=i)
                load = self.cal.get_skill_load(day, skill)

                print(f"CHECK {skill} @ {day} → load={load}, max={self.max_per_day}")

                if load >= self.max_per_day:
                    failed.append({
                        "date": day,
                        "skill": skill,
                        "load": load,
                        "max": self.max_per_day
                    })
                    return None, failed

            chain.append(SubTask(
                task_id=st.task_id,
                skill=st.skill,
                sequence=st.sequence,
                duration_days=dur,
                start_date=s,
                end_date=e,
            ))

            current = e + timedelta(days=1)

        return AISlot(start, chain), failed

    # =========================================================
    # AI SEARCH
    # =========================================================
    def _search(self, subtasks: list[SubTask], base_date: date):

        all_failed = []

        for offset in range(MAX_HORIZON):

            start = base_date + timedelta(days=offset)

            slot, failed = self._try_chain(start, subtasks)

            if failed:
                all_failed.extend(failed)

            if slot:
                return slot, all_failed

        return None, all_failed

    # =========================================================
    # EXPLANATION HELPERS 🔥 NEW
    # =========================================================
    def _format_date(self, d: date):
        return d.strftime("%B %d").replace(" 0", " ")

    def _group_failed(self, failed_log):
        grouped = defaultdict(list)

        for f in failed_log:
            grouped[f["skill"]].append(f["date"])

        result = []

        for skill, dates in grouped.items():
            dates = sorted(dates)

            start = dates[0]
            prev = dates[0]

            for d in dates[1:]:
                if (d - prev).days == 1:
                    prev = d
                else:
                    result.append((skill, start, prev))
                    start = d
                    prev = d

            result.append((skill, start, prev))

        return result

    # =========================================================
    # EXPLANATION GENERATOR 🔥 MULTI-SKILL
    # =========================================================
    def _generate_explanation(self, failed_log, success_date: date):

        if not failed_log:
            return (
                f"No workload conflict detected. "
                f"Earliest available date is {self._format_date(success_date)}."
            )

        groups = self._group_failed(failed_log)

        lines = []

        for skill, start, end in groups:
            sample = next(f for f in failed_log if f["skill"] == skill)
            load = sample["load"]
            max_per_day = sample["max"]

            s = self._format_date(start)
            e = self._format_date(end)

            if s == e:
                date_text = f"{s} is unavailable"
            else:
                date_text = f"{s}–{e} are unavailable"

            lines.append(
                f"{date_text} — {skill} is fully occupied "
                f"({load}/{max_per_day} tasks per day)"
            )

        lines.append(
            f"Earliest available date is {self._format_date(success_date)}."
        )

        explanation = "\n".join(lines)

        print("🔥 MULTI-SKILL EXPLANATION")
        print(explanation)

        return explanation

    # =========================================================
    # FORMAT RESULT
    # =========================================================
    def _success(self, slot: AISlot, work_type: str, failed_log) -> dict:

        explanation = self._generate_explanation(
            failed_log,
            slot.start
        )

        return {
            "feasible": True,
            "work_type": work_type,
            "timeline": [
                {
                    "skill": st.skill.value,
                    "start": st.start_date.isoformat(),
                    "end": st.end_date.isoformat(),
                }
                for st in slot.chain
            ],
            "explanation": explanation,
        }