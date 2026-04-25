# =========================================================
# PSAI ENGINE
# File: role_service.py
# Version: v1.0.0-d0/23.4.26
# Layer: API
# Role: )
# Status: ACTIVE
# Debug:
# =========================================================

from fastapi import HTTPException
from planner_v2.db.firestore_db import FirestoreDB

def get_user_role(uid: str, hotel_id: str) -> str:
    db = FirestoreDB()

    doc = db.db \
        .collection("properties") \
        .document(hotel_id) \
        .collection("users") \
        .document(uid) \
        .get()

    if not doc.exists:
        return "USER"

    data = doc.to_dict()
    return data.get("role", "USER")

def require_master(uid: str, hotel_id: str):
    role = get_user_role(uid, hotel_id)

    if role != "MASTER":
        raise HTTPException(
            status_code=403,
            detail="Override requires MASTER role"
        )