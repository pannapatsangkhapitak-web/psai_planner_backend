# =========================================================
# PSAI ENGINE
# File: main.py
# Version: v1.0.0-d0/21.1.26
# Layer: main entry
# Role: main entry
# Status: ACTIVE
# Debug: 
# =========================================================

import os
import json
from firebase_admin import credentials, initialize_app
from fastapi import FastAPI

app = FastAPI()
cred_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ตอนนี้เปิดก่อน
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if cred_json:
    cred_dict = json.loads(cred_json)
    cred = credentials.Certificate(cred_dict)
    initialize_app(cred)

print("ENV LENGTH:", len(cred_json) if cred_json else "NONE")    
# import routes ที่มีอยู่จริง

from planner_service.app.routes import commit_routes
from planner_service.app.routes import ai_routes
from planner_service.app.routes import user_routes
from planner_service.app.routes import config_routes

# include router
app.include_router(ai_routes.router, prefix="/ai")
app.include_router(user_routes.router)
app.include_router(commit_routes.router)
app.include_router(config_routes.router, prefix="/config")



@app.get("/")
def root():
    return {"message": "PSAI Planner Backend Running"}