# =========================================================
# PSAI ENGINE
# File: user_route.py
# Version: v1.0.0-d2/22.1.26
# Layer: API
# Role: User Management + Identity (TOKEN-BASED)
# Status: ACTIVE (SECURED)
# =========================================================
#
# 🔥 CURRENT STATE
# - Authentication via Firebase ID Token
# - Identity extracted from Authorization header
# - /me returns real authenticated user
#
# ⚠️ REQUIREMENTS
# - Frontend must send Authorization: Bearer <token>
#
# 🧭 NEXT STEP
# - Map role from Firestore (per hotel_id)
# - Enforce role in protected routes
#
# =========================================================

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from firebase_admin import auth

from planner_v2.db.firestore_db import FirestoreDB

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
# 🔐 HELPER: VERIFY TOKEN
# =========================
def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")

    if not auth_header or "Bearer " not in auth_header:
        raise HTTPException(status_code=401, detail="Missing token")

    token = auth_header.split(" ")[1]

    try:
        decoded = auth.verify_id_token(token)
        return decoded
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


# =========================
# GET CURRENT USER (REAL)
# =========================
@router.get("/{hotel_id}/me")
def get_me(hotel_id: str, request: Request):
    decoded = get_current_user(request)

    uid = decoded["uid"]
    email = decoded.get("email")

    db = FirestoreDB()

    # 🔥 optional: ดึง role จาก Firestore
    user_data = db.get_user(hotel_id, uid)

    role = user_data.get("role") if user_data else "USER"

    return {
        "uid": uid,
        "email": email,
        "role": role,
    }


# =========================
# CREATE USERS
# =========================
@router.post("/{hotel_id}/users")
def create_users(hotel_id: str, req: CreateUsersRequest, request: Request):
    decoded = get_current_user(request)

    # 🔥 (optional) check role
    # if decoded["uid"] != "admin_uid": ...

    db = FirestoreDB()
    created = []

    for u in req.users:
        uid = f"user-{u.email}"  # 🔥 หรือใช้ Firebase Admin create user ในอนาคต

        db.set_user(hotel_id, uid, {
            "email": u.email,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "role": u.role,
            "active": True,
        })

        created.append({
            "uid": uid,
            "email": u.email,
        })

    return {"created": created}


# =========================
# CLEAR (DEPRECATED)
# =========================
@router.post("/{hotel_id}/clear-must-change")
def clear_must_change():
    return {"ok": True}