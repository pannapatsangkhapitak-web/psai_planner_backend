from datetime import date
from planner_v2.db.firestore_db import FirestoreDB


def has_conflict(subtasks, hotel_id: str) -> bool:
    db = FirestoreDB()

    ref = db.db \
        .collection("properties") \
        .document(hotel_id) \
        .collection("tasks_committed")

    for doc in ref.stream():
        data = doc.to_dict()
        timeline = data.get("committed_timeline", [])

        for t in timeline:
            start = date.fromisoformat(t["start"])
            end = date.fromisoformat(t["end"])
            skill = t["skill"]

            for st in subtasks:
                if st.skill.name != skill:
                    continue

                # overlap check
                if not (st.end_date < start or st.start_date > end):
                    print(f"❌ CONFLICT: {skill} {start}-{end}")
                    return True

    return False