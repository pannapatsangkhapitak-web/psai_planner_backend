from datetime import date, datetime
from typing import List, Dict, Any


class CalendarAdapter:
    """
    Normalized calendar view for AIEngine
    """

    def __init__(self, committed_docs: List[Dict[str, Any]]):
        self.items = []

        for doc in committed_docs:
            task_id = doc.get("task_id")
            timeline = doc.get("committed_timeline", [])

            for t in timeline:
                skill = t.get("skill")
                start = t.get("start")
                end = t.get("end")

                if not skill or not start or not end:
                    continue

                self.items.append({
                    "task_id": task_id,
                    "skill": self._normalize_skill(skill),
                    "start": self._parse_date(start),
                    "end": self._parse_date(end),
                })

        print("=== CALENDAR ITEMS ===")
        for i in self.items:
            print(i)

    def _parse_date(self, value) -> date:
        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        value = str(value)

        try:
            return date.fromisoformat(value)
        except:
            return datetime.fromisoformat(value).date()

    def _normalize_skill(self, skill) -> str:
        if hasattr(skill, "value"):
            skill = skill.value

        skill = str(skill).upper()

        if skill == "PM":
            return "TECH"

        return skill

    def get_skill_load(self, day: date, skill) -> int:
        skill = self._normalize_skill(skill)

        return sum(
            1
            for itm in self.items
            if itm["skill"] == skill and itm["start"] <= day <= itm["end"]
        )

    def is_skill_full(self, skill, day: date, max_per_day: int = 1) -> bool:
        return self.get_skill_load(day, skill) >= max_per_day

    def get_conflicts(self, skill, start: date, end: date):
        skill = self._normalize_skill(skill)
        conflicts = []

        for itm in self.items:
            if itm["skill"] != skill:
                continue

            if not (itm["end"] < start or itm["start"] > end):
                conflicts.append(itm["task_id"])

        return conflicts