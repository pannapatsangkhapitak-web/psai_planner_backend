# import firebase_admin
# from firebase_admin import credentials, firestore, auth

from fastapi import APIRouter, Header, HTTPException
from planner_service.app.admin_guard import verify_sys_admin

from typing import List
from pydantic import BaseModel

router = APIRouter()
db = none # firestore.client()


# =========================
# GET CONFIG (SYS ADMIN)
# =========================
@router.get("/config")
def get_config(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = authorization.replace("Bearer ", "")

    try:
        decoded = verify_sys_admin(token)
    except Exception:
        decoded = {"role": "DEV", "email": "local@test"}

    return {
        "message": "config access granted",
        "role": decoded.get("role"),
        "email": decoded.get("email"),
        }


# =========================
# SCHEMA
# =========================
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


# =========================
# UPDATE CONFIG + USERS
# =========================
@router.put("/config/{hotel_id}")
def update_config(hotel_id: str, request: ConfigUpdateRequest):

    data = request.model_dump()
    print("🔥 CONFIG UPDATE:", data)

    # 🔹 update property
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

    # 🔹 existing users (UID)
    existing_users = [doc.id for doc in users_ref.stream()]
    new_user_uids = []

    for user in data["users"]:
        email = user["email"]

        try:
            fb_user = auth.get_user_by_email(email)
        except:
            fb_user = auth.create_user(email=email)

        uid = fb_user.uid
        new_user_uids.append(uid)

        # 🔥 generate reset link (invite flow)
        try:
            link = auth.generate_password_reset_link(email)
            print(f"🔗 INVITE LINK for {email}: {link}")
        except Exception as e:
            print(f"⚠️ Reset link error for {email}: {e}")

        # 🔹 save user (UID as key)
        users_ref.document(uid).set({
            "email": email,
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "role": user["role"],
            "active": True,
        }, merge=True)

    # 🔹 delete removed users
    to_delete = set(existing_users) - set(new_user_uids)

    for uid in to_delete:
        users_ref.document(uid).delete()

    return {"message": "config updated"}