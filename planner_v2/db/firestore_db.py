# planner_v2/db/firestore_db.py

class FirestoreDB:
    def __init__(self):
        print("🔥 Firestore DISABLED (dev mode)")
        self._data = {}

    # =========================
    # GET USER
    # =========================
    def get_user(self, hotel_id: str, uid: str):
        return self._data.get((hotel_id, uid))

    # =========================
    # SET USER
    # =========================
    def set_user(self, hotel_id: str, uid: str, data: dict):
        self._data[(hotel_id, uid)] = data

    # =========================
    # UPDATE USER
    # =========================
    def update_user(self, hotel_id: str, uid: str, data: dict):
        if (hotel_id, uid) not in self._data:
            self._data[(hotel_id, uid)] = {}
        self._data[(hotel_id, uid)].update(data)

    # =========================
    # OVERRIDE LOG (DEV MODE)
    # =========================

    def log_override(self, data: dict):
        """
        Save override log (in-memory for dev)
        """
        if "override_logs" not in self._data:
            self._data["override_logs"] = []

        self._data["override_logs"].append(data)

    def get_override_logs(self, property_id: str):
        """
        Get override logs for a property
        """
        logs = self._data.get("override_logs", [])

        return [
        l for l in logs
        if l.get("property_id") == property_id
        ]
    # =========================
    #                   
    # =========================
    
    def list_committed(self):
        return self._data.get("committed_tasks", [])
    
    def commit_chain(self, task, subtasks, actor):
        """
        DEV MODE: store committed task in memory
        """

        if "committed_tasks" not in self._data:
            self._data["committed_tasks"] = []

        record = {
            "task_id": task.task_id,
            "name": task.name,
            "category": task.category,
            "work_type": task.work_type.name,
            "actor": actor,
            "subtasks": [
                {
                "skill": st.skill.name,
                "start": st.start_date.isoformat(),
                "end": st.end_date.isoformat(),
                }
            for st in subtasks
        ]
        }

        self._data["committed_tasks"].append(record)

        return task.task_id