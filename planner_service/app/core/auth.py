# =========================================================
# PSAI ENGINE
# File: auth.py
# Version: v1.0.0-d0/22.4.26
# Layer: API
# Role: 
# Status: ACTIVE
# Debug:
# 
# =========================================================

from fastapi import Request, HTTPException
from firebase_admin import auth

def get_current_user(request: Request):
    """
    🔐 Source of Truth
    - Read Firebase token
    - Decode → return user info
    """

    auth_header = request.headers.get("Authorization")

    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    try:
        token = auth_header.split(" ")[1]
    except:
        raise HTTPException(status_code=401, detail="Invalid token format")

    try:
        decoded = auth.verify_id_token(token)

        return {
            "uid": decoded.get("uid"),
            "email": decoded.get("email"),
        }

    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid Firebase token")