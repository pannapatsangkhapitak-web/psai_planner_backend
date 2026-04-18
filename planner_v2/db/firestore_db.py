from typing import List, Dict, Any
from datetime import datetime

from google.cloud import firestore
from google.oauth2 import service_account
import pathlib

from planner_v2.core.models import Task, SubTask


class FirestoreDB:

    # ==================================================
    # INIT
    # ==================================================
    def __init__(self):

        BASE_DIR = pathlib.Path(__file__).resolve().parents[3]
        SERVICE_ACCOUNT = BASE_DIR / "secrets" / "firebase-service-account.json"

        print("FIRESTORE BASE =", BASE_DIR)
        print("FIRESTORE KEY =", SERVICE_ACCOUNT)

        credentials = service_account.Credentials.from_service_account_file(
            str(SERVICE_ACCOUNT)
        )

        self.client = firestore.Client(credentials=credentials)

    # ==================================================
    # 🔥 LOAD COMMITTED
    # ==================================================
    def list_committed(self, hotel_id: str) -> List[Dict[str, Any]]:

        docs = (
            self.client
            .collection("properties")
            .document(hotel_id)
            .collection("tasks_committed")
            .stream()
        )

        out: List[Dict[str, Any]] = []

        for doc in docs:
            data = doc.to_dict()
            data["task_id"] = doc.id
            out.append(data)

        print("🔥 LOADED TASKS =", len(out))
        return out

    # ==================================================
    # 🔥 CREATE TASK (NEW COMMIT)
    # ==================================================
    def create_task(
        self,
        hotel_id: str,
        task: Task,
        subtasks: List[SubTask],
        actor: str,
    ) -> str:

        if not subtasks:
            raise ValueError("Empty chain cannot be committed")

        doc_ref = (
            self.client
            .collection("properties")
            .document(hotel_id)
            .collection("tasks_committed")
            .document()
        )

        task_id = doc_ref.id

        committed_timeline = [
            {
                "skill": st.skill.value.upper(),
                "start": st.start_date.isoformat(),
                "end": st.end_date.isoformat(),
            }
            for st in subtasks
        ]

        entry = {
            "task_name": task.name,
            "work_type": task.work_type.value,
            "category": task.category,
            "created_by": actor,
            "state": "SCHEDULED",
            "committed_timeline": committed_timeline,
            "created_at": datetime.utcnow().isoformat(),
        }

        doc_ref.set(entry)

        return task_id

    # ==================================================
    # 🔥 GET TASK (ACTIVE)
    # ==================================================
    def get_task(self, hotel_id: str, task_id: str):

        doc = (
            self.client
            .collection("properties")
            .document(hotel_id)
            .collection("tasks_committed")
            .document(task_id)
            .get()
        )

        if doc.exists:
            data = doc.to_dict()
            data["task_id"] = doc.id
            return data

        return None

    # ==================================================
    # 🔥 DELETE TASK (ACTIVE)
    # ==================================================
    def delete_task(self, hotel_id: str, task_id: str):

        self.client \
            .collection("properties") \
            .document(hotel_id) \
            .collection("tasks_committed") \
            .document(task_id) \
            .delete()

    # ==================================================
    # 🔥 ARCHIVE TASK (OVERRIDE)
    # ==================================================
    def archive_task(self, hotel_id: str, task: Dict[str, Any], actor: str):

        task_id = task["task_id"]

        self.client \
            .collection("properties") \
            .document(hotel_id) \
            .collection("tasks_archive") \
            .document(task_id) \
            .set({
                **task,
                "removed_at": datetime.utcnow().isoformat(),
                "removed_by": actor,
                "reason": "OVERRIDE",
            })

    # ==================================================
    # 🔥 GET ARCHIVED TASK
    # ==================================================
    def get_archived_task(self, hotel_id: str, task_id: str):

        doc = (
            self.client
            .collection("properties")
            .document(hotel_id)
            .collection("tasks_archive")
            .document(task_id)
            .get()
        )

        if doc.exists:
            data = doc.to_dict()
            data["task_id"] = doc.id
            return data

        return None

    # ==================================================
    # 🔥 RESTORE TASK
    # ==================================================
    def restore_task(self, hotel_id: str, task: Dict[str, Any]):

        task_id = task["task_id"]

        # 1. put back to committed
        self.client \
            .collection("properties") \
            .document(hotel_id) \
            .collection("tasks_committed") \
            .document(task_id) \
            .set(task)

        # 2. remove from archive
        self.client \
            .collection("properties") \
            .document(hotel_id) \
            .collection("tasks_archive") \
            .document(task_id) \
            .delete()
    # ==================================================
    # 🔥 Audit logs
    # ==================================================
    def log_override(self, data: dict):
        hotel_id = data.get("hotel_id")

        if not hotel_id:
            raise ValueError("hotel_id is required for audit log")

        self.client \
            .collection("properties") \
            .document(hotel_id) \
            .collection("audit_logs") \
            .add(data)