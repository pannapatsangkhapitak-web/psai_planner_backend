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

def get_user_role(uid: str) -> str:
    db = FirestoreDB()

    doc = db.db.collection("users").document(uid).get()
    
    if not doc.exists:
        return "USER"  # default

    data = doc.to_dict()
    return data.get("role", "USER")


def require_master(uid: str):
    role = get_user_role(uid)

    if role != "MASTER":
        raise HTTPException(
            status_code=403,
            detail="Override requires MASTER role"
        )