# planner_v2/db/firestore_db.py
# planner_v2/db/firestore_db.py

from google.cloud import firestore
from google.oauth2 import service_account

# =========================
# 🔐 INIT FIRESTORE (REAL)
# =========================

key_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])

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
        self.db = db  # ✅ ใช้ instance ที่มี credential แล้ว

    # =========================
    # 👤 USER
    # =========================

    def get_user(self, hotel_id: str, uid: str):
        doc = self.db.collection("users").document(f"{hotel_id}_{uid}").get()
        return doc.to_dict() if doc.exists else None

    def set_user(self, hotel_id: str, uid: str, data: dict):
        self.db.collection("users").document(f"{hotel_id}_{uid}").set(data)

    def update_user(self, hotel_id: str, uid: str, data: dict):
        self.db.collection("users").document(f"{hotel_id}_{uid}").set(
            data, merge=True
        )

    # =========================
    # 🧾 OVERRIDE LOG
    # =========================

    def log_override(self, data: dict):
        self.db.collection("override_logs").add(data)

    def get_override_logs(self, property_id: str):
        docs = (
            self.db.collection("override_logs")
            .where("property_id", "==", property_id)
            .stream()
        )
        return [doc.to_dict() for doc in docs]

    # =========================
    # 📦 COMMITTED TASKS
    # =========================

    def list_committed(self):
        docs = self.db.collection("tasks").stream()
        return [doc.to_dict() for doc in docs]

    def commit_chain(self, task, subtasks, actor):
        doc_ref = self.db.collection("tasks").document(task.task_id)

        record = {
            "task_id": task.task_id,
            "name": task.name,
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