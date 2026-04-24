# =========================================================
# PSAI ENGINE
# File: config_route.py
# Version: v1.1.0-d1/23.4.26
# Layer: API
# Role: SYS_ADMIN only (GLOBAL USER)
# Status: ACTIVE
# =========================================================

from fastapi import APIRouter, Header, HTTPException
from typing import List
from pydantic import BaseModel

from firebase_admin import auth, firestore

# 🔥 ใช้ Firestore client จริง
db = firestore.client()

router = APIRouter()


# =========================================================
# 🔐 AUTH: VERIFY SYS ADMIN (GLOBAL USER)
# =========================================================
from fastapi import HTTPException

def verify_sys_admin(token: str):
    try:
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token["uid"]

        doc = db.collection("system_users").document(uid).get()

        print("🔥 UID:", uid)
        print("🔥 USER DOC:", doc.to_dict())

        if not doc.exists:
            raise HTTPException(status_code=403, detail="User profile not found")

        user_data = doc.to_dict()
        role = user_data.get("role")

        print("🔥 ROLE:", role)

        if role is None:
            raise HTTPException(status_code=403, detail="User role missing")

        if role.lower() != "sys_admin":
            raise HTTPException(status_code=403, detail="SYS_ADMIN only")

        return {
            "uid": uid,
            "email": decoded_token.get("email"),
            "role": role,
        }

    except HTTPException:
        raise  # 🔥 ปล่อย error เดิม

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    
# =========================================================
# 📥 GET CONFIG (SYS ADMIN ONLY)
# =========================================================
@router.get("/config")
def get_config(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = authorization.replace("Bearer ", "")

    decoded = verify_sys_admin(token)

    return {
        "message": "config access granted",
        "role": decoded["role"],
        "email": decoded["email"],
    }


# =========================================================
# 📦 SCHEMA
# =========================================================
class ConfigUserItem(BaseModel):
    email: str
    first_name: str
    last_name: str
    role: str


class ConfigUpdateRequest(BaseModel):
    hotel_name: str
    address: str
    contact_email: str
    modules: List[str]
    users: List[ConfigUserItem]


# =========================================================
# 📤 UPDATE CONFIG (SYS ADMIN ONLY)
# =========================================================
@router.put("/config/{hotel_id}")
def update_config(
    hotel_id: str,
    request: ConfigUpdateRequest,
    authorization: str = Header(...)
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = authorization.replace("Bearer ", "")

    # 🔥 enforce sys_admin ก่อนทำอะไร
    verify_sys_admin(token)

    data = request.model_dump()
    print("🔥 CONFIG UPDATE:", data)

    # -----------------------------
    # 🏨 UPDATE PROPERTY
    # -----------------------------
    db.collection("properties").document(hotel_id).set(
        {
            "hotel_name": data["hotel_name"],
            "address": data["address"],
            "contact_email": data["contact_email"],
            "modules": data["modules"],
        },
        merge=True
    )

    users_ref = db.collection("properties").document(hotel_id).collection("users")

    # -----------------------------
    # 👤 EXISTING USERS
    # -----------------------------
    existing_users = [doc.id for doc in users_ref.stream()]
    new_user_uids = []

    for user in data["users"]:
        email = user["email"]

        # -------------------------
        # 🔐 GET OR CREATE USER
        # -------------------------
        try:
            fb_user = auth.get_user_by_email(email)
        except:
            fb_user = auth.create_user(email=email)

        uid = fb_user.uid
        new_user_uids.append(uid)

        # -------------------------
        # 🔗 INVITE LINK
        # -------------------------
        try:
            link = auth.generate_password_reset_link(email)
            print(f"🔗 INVITE LINK for {email}: {link}")
        except Exception as e:
            print(f"⚠️ Reset link error for {email}: {e}")

        # -------------------------
        # 💾 SAVE TENANT USER
        # -------------------------
        users_ref.document(uid).set({
            "email": email,
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "role": user["role"],
            "active": True,
        }, merge=True)

    # -----------------------------
    # 🗑 REMOVE OLD USERS
    # -----------------------------
    to_delete = set(existing_users) - set(new_user_uids)

    for uid in to_delete:
        users_ref.document(uid).delete()

    return {"message": "config updated"}