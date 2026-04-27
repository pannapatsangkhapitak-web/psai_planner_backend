# =========================================================
# PSAI ENGINE
# File: firestore_db.py
# Version: v1.0.0-d0/21.1.26
# Layer: infra
# Role: 
# Status: ACTIVE
# Debug: 
# =========================================================

import os
import json
from datetime import date, datetime, timezone
from google.cloud import firestore
from google.oauth2 import service_account

print("🔥 ENV KEYS:", os.environ.keys())

# =========================
# 🔐 INIT FIRESTORE (REAL)
# =========================

key_dict = json.loads(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
cred = service_account.Credentials.from_service_account_info(key_dict)

db = firestore.Client(
    credentials=cred,
    project=cred.project_id,
)

# =========================
# 🔥 FIRESTORE DB CLASS
# =========================

class FirestoreDB:
    def __init__(self):
        self.db = db

    # =========================
    # 👤 USER
    # =========================

    def get_user(self, hotel_id: str, uid: str):
        doc = (
            self.db
                .collection("properties")
                .document(hotel_id)
                .collection("users")
                .document(uid)
                .get()
            )
        return doc.to_dict() if doc.exists else None

    def set_user(self, hotel_id: str, uid: str, data: dict):
            self.db \
                .collection("properties") \
                .document(hotel_id) \
                .collection("users") \
                .document(uid) \
                .set(data)

    def update_user(self, hotel_id: str, uid: str, data: dict):
            self.db \
                .collection("properties") \
                .document(hotel_id) \
                .collection("users") \
                .document(uid) \
                .set(data, merge=True)

    # =========================
    # 🧾 AUDIT / OVERRIDE LOG
    # =========================

    def log_audit(self, hotel_id: str, data: dict):
        data["timestamp"] = datetime.utcnow().isoformat()

        self.db \
            .collection("properties") \
            .document(hotel_id) \
            .collection("audit_logs") \
            .add(data)
        
    # =========================
    # 📦 COMMITTED TASKS
    # =========================

    def list_committed(self, hotel_id: str):
        docs = (
            self.db
            .collection("properties")
            .document(hotel_id)
            .collection("tasks_committed")   # 🔥 FIX spelling
            .stream()
        )

        return [doc.to_dict() for doc in docs]

    def commit_chain(self, task, subtasks, actor, hotel_id):
        doc_ref = (
            self.db
            .collection("properties")
            .document(hotel_id)
            .collection("tasks_committed")
            .document(task.task_id)
        )

        record = {
            "task_id": task.task_id,
            "task_name": task.task_name,
            "category": task.category,
            "work_type": task.work_type.name,
            "actor": actor,
            "created_at": firestore.SERVER_TIMESTAMP,
            "subtasks": [
                {
                    "skill": st.skill.name,
                    "start": st.start_date.isoformat(),
                    "end": st.end_date.isoformat(),
                }
                for st in subtasks
            ],
        }

        doc_ref.set(record)
        return task.task_id

    # =========================
    # 🔍 CONFLICT CHECK
    # =========================

    def check_conflict(self, subtasks, hotel_id):
        existing_tasks = self.list_committed(hotel_id)
        conflicts = []

        for st in subtasks:
            for task in existing_tasks:
                for t in task.get("subtasks", []):

                    same_skill = t["skill"] == st.skill.name

                try:
                    start = date.fromisoformat(t["start"])
                    end = date.fromisoformat(t["end"])
                except Exception:
                    continue
                
                overlap = not (
                        st.end_date < start or
                        st.start_date > end
                    )

                if same_skill and overlap:
                        conflicts.append(task)
                        break

        return conflicts

    # =========================
    # 📦 MOVE TO ARCHIVE (REMOVE + ARCHIVE)
    # =========================

    def move_to_archive(self, tasks, hotel_id, user_id):
        for task in tasks:
            task_id = task.get("task_id")

            task["archived_by"] = user_id
            task["archived_at"] = datetime.now(timezone.utc).isoformat()

            archive_ref = self.db \
                .collection("properties") \
                .document(hotel_id) \
                .collection("tasks_archive") \
                .document(task_id) \
                .set(task)
            if archive_ref.get().exists:
                raise Exception(f"Archive already exists for task {task_id}")
            
            archive_ref.set(task)
                    
            # 2) ลบจาก committed
            self.db \
                .collection("properties") \
                .document(hotel_id) \
                .collection("tasks_committed") \
                .document(task_id) \
                .delete()