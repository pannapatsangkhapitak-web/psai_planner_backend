from fastapi import APIRouter
from app.core.db import db

router = APIRouter()

@router.get("/{hotel_id}/archive")
def get_archive(hotel_id: str):

    logs = db.collection("task_history") \
        .where("hotel_id", "==", hotel_id) \
        .where("action", "==", "ARCHIVED") \
        .stream()

    result = []

    for doc in logs:
        result.append(doc.to_dict())

    return {"items": result}