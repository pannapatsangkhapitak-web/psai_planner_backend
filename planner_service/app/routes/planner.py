from fastapi import APIRouter
from planner_v2.db.firestore_db import FirestoreDB

router = APIRouter()

db = FirestoreDB().db


@router.get("/{hotel_id}/archive")
def get_archive(hotel_id: str):

    logs = db.collection("properties") \
        .document(hotel_id) \
        .collection("tasks_archive") \
        .stream()

    return {"items": [doc.to_dict() for doc in logs]}