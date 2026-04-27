from planner_v2.db.firestore_db import FirestoreDB

db = FirestoreDB().get_db()   # หรือ method ที่คุณมีจริง

@router.get("/{hotel_id}/archive")
def get_archive(hotel_id: str):

    logs = db.collection("task_history") \
        .where("hotel_id", "==", hotel_id) \
        .where("action", "==", "ARCHIVED") \
        .stream()

    result = [doc.to_dict() for doc in logs]

    return {"items": result}