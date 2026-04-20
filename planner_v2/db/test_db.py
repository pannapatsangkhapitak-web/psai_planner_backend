from firestore_db import FirestoreDB

db = FirestoreDB()

# 🔥 simulate override
db.log_override({
    "property_id": "DEMO",
    "work_type": "CNP",
    "override_by": "GM"
})

# 🔥 read back
logs = db.get_override_logs("DEMO")

print("RESULT:", logs)