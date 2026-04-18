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