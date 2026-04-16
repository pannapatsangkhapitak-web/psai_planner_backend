from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from firebase_admin import auth

from planner_service.app.auth_utils import get_current_user
from planner_v2.db.firestore_db import FirestoreDB
from fastapi import APIRouter, Depends, HTTPException
from fastapi_mail import FastMail, MessageSchema
from planner_service.app.email_config import conf
from planner_service.app.services.email_service import send_invite_email

router = APIRouter(tags=["User"])


# =========================
# MODEL
# =========================
class UserItem(BaseModel):
    email: str
    password: str | None = None  # 🔥 optional (ยังรองรับของเดิม)
    first_name: str
    last_name: str
    role: str


class CreateUsersRequest(BaseModel):
    users: list[UserItem]


# =========================
# GET CURRENT USER
# =========================
@router.get("/{hotel_id}/me")
def get_me(
    hotel_id: str,
    user=Depends(get_current_user),
):
    uid = user["uid"]

    db = FirestoreDB()

    doc = db.client \
        .collection("properties") \
        .document(hotel_id) \
        .collection("users") \
        .document(uid) \
        .get()

    if not doc.exists:
        return {
            "uid": uid,
            "role": "TECH",
            "must_change_password": False,
        }

    data = doc.to_dict()

    return {
        "uid": uid,
        "role": data.get("role", "TECH"),
        "must_change_password": data.get("must_change_password", False),
    }


# =========================
# CREATE / INVITE USERS
# =========================
from app.services.email_service import send_invite_email


@router.post("/{hotel_id}/users")
async def create_users(   # ✅ เปลี่ยนเป็น async
    hotel_id: str,
    req: CreateUsersRequest,
):
    if len(req.users) > 10:
        raise HTTPException(status_code=400, detail="Max 10 users per tenant")

    db = FirestoreDB()
    created = []

    for u in req.users:
        try:
            # 🔹 create or get Firebase user
            try:
                fb_user = auth.get_user_by_email(u.email)
            except:
                fb_user = auth.create_user(
                    email=u.email,
                    email_verified=False,
                    display_name=f"{u.first_name} {u.last_name}"
                )

            uid = fb_user.uid

            # 🔥 generate reset link
            try:
                link = auth.generate_password_reset_link(u.email)

                # ✅ ส่ง email จริง
                await send_invite_email(u.email, link)

                print(f"✅ Email sent to {u.email}")

            except Exception as e:
                print(f"⚠️ Email error: {e}")

            # 🔹 save in Firestore
            db.client \
                .collection("properties") \
                .document(hotel_id) \
                .collection("users") \
                .document(uid) \
                .set({
                    "email": u.email,
                    "first_name": u.first_name,
                    "last_name": u.last_name,
                    "role": u.role,
                    "active": True,
                    "must_change_password": False,
                }, merge=True)

            created.append({
                "uid": uid,
                "email": u.email,
            })

        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    return {"created": created}


# =========================
# CLEAR MUST CHANGE PASSWORD
# =========================
@router.post("/{hotel_id}/clear-must-change")
def clear_must_change(
    hotel_id: str,
    user=Depends(get_current_user),
):
    uid = user["uid"]

    db = FirestoreDB()

    db.client \
        .collection("properties") \
        .document(hotel_id) \
        .collection("users") \
        .document(uid) \
        .update({
            "must_change_password": False
        })

    return {"ok": True}