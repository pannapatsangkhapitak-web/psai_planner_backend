# =========================================================
# PSAI ENGINE
# File: main.py
# Version: v1.0.0-d0/21.1.26
# Layer: main entry
# Role: main entry
# Status: ACTIVE
# =========================================================

import os
import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import credentials, initialize_app

# =========================
# INIT APP
# =========================
app = FastAPI()

# =========================
# CORS (เปิดก่อน)
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5509", "http://localhost:5509/"],  # หรือใส่ domain จริงก็ได้
    allow_credentials=False,
    allow_methods=["*"],  # 🔥 สำคัญ (ต้องมี OPTIONS)
    allow_headers=["*"],  # 🔥 สำคัญ (ต้อง allow Authorization)
)

# =========================
# FIREBASE INIT
# =========================
cred_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")

if cred_json:
    cred_dict = json.loads(cred_json)
    cred = credentials.Certificate(cred_dict)
    initialize_app(cred)

print("ENV LENGTH:", len(cred_json) if cred_json else "NONE")

# =========================
# IMPORT ROUTES
# =========================
from planner_service.app.routes import commit_routes
from planner_service.app.routes import ai_routes
from planner_service.app.routes import user_routes
from planner_service.app.routes import config_routes

# =========================
# INCLUDE ROUTERS
# =========================
app.include_router(ai_routes.router, prefix="/ai")
app.include_router(user_routes.router)
app.include_router(commit_routes.router)

# 🔥 CONFIG (สำคัญ)
app.include_router(config_routes.router, prefix="/config")

# =========================
# ROOT
# =========================
@app.get("/")
def root():
    return {"message": "PSAI Planner Backend Running"}