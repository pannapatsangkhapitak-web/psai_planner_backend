# planner_service/app/routes/user_routes.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# from planner_v2.db.firestore_db import FirestoreDB

router = APIRouter(tags=["User"])


# =========================
# MODELS
# =========================
class UserItem(BaseModel):
    email: str
    first_name: str
    last_name: str
    role: str


class CreateUsersRequest(BaseModel):
    users: list[UserItem]


# =========================
# GET CURRENT USER (DEV)
# =========================
@router.get("/{hotel_id}/me")
def get_me(hotel_id: str):
    return {
        "uid": "dev-user",
        "role": "DEV",
        "must_change_password": False,
    }


# =========================
# CREATE USERS (DEV)
# =========================
@router.post("/{hotel_id}/users")
def create_users(hotel_id: str, req: CreateUsersRequest):
    db = FirestoreDB()
    created = []

    for u in req.users:
        uid = f"dev-{u.email}"

        db.set_user(hotel_id, uid, {
            "email": u.email,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "role": u.role,
            "active": True,
            "must_change_password": False,
        })

        created.append({
            "uid": uid,
            "email": u.email,
        })

    return {"created": created}


# =========================
# CLEAR MUST CHANGE
# =========================
@router.post("/{hotel_id}/clear-must-change")
def clear_must_change(hotel_id: str):
    return {"ok": True}