from pymongo import MongoClient
from pymongo.errors import CollectionInvalid
from datetime import datetime

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["hrmo_elog_db"]

def init_db():
    print("Initializing Database...")

    # ================================
    # ADMINS
    # ================================
    try:
        db.create_collection("admins", validator={
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["first_name", "last_name", "email", "password_hash", "created_at"],
                "properties": {
                    "first_name": {"bsonType": "string"},
                    "last_name": {"bsonType": "string"},
                    "email": {"bsonType": "string", "pattern": "^.+@.+$"},
                    "password_hash": {"bsonType": "string"},
                    "created_at": {"bsonType": "date"}
                }
            }
        })
        print("Created 'admins' collection")
    except CollectionInvalid:
        print("'admins' collection already exists")

    db.admins.create_index("email", unique=True)
    print("Created index for 'admins'")

    # ================================
    # CLIENTS
    # ================================
    try:
        db.create_collection("clients", validator={
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["client_id", "client_type", "full_name", "gender", "age"],
                "properties": {
                    "client_id": {"bsonType": "string"},
                    "client_type": {"bsonType": "string"},
                    "full_name": {"bsonType": "string"},
                    "department": {"bsonType": ["string", "null"]},
                    "gender": {"bsonType": "string"},
                    "age": {"bsonType": "int", "minimum": 0}
                }
            }
        })
        print("Created 'clients' collection")
    except CollectionInvalid:
        print("'clients' collection already exists")
    
    db.clients.create_index("client_id", unique=True)
    print("Created index for 'clients'")

    # ================================
    # CSM FORM
    # ================================
    try:
        db.create_collection("csm_form", validator={
            "$jsonSchema": {
                "bsonType": "object",
                "required": [
                    "control_no", "date", "agency_visited", "client_type", 
                    "age", "service_availed", "created_at"
                ],
                "properties": {
                    "control_no": {"bsonType": "string"},
                    "date": {"bsonType": "string"},
                    "agency_visited": {"bsonType": "string"},
                    "client_type": {"bsonType": "string"},
                    "sex": {"bsonType": ["string", "null"]},
                    "age": {"bsonType": "int", "minimum": 0},
                    "region_of_residence": {"bsonType": ["string", "null"]},
                    "email": {"bsonType": ["string", "null"]},
                    "service_availed": {"bsonType": "string"},
                    "awareness_of_cc": {"bsonType": ["int", "null"], "minimum": 0, "maximum": 5},
                    "cc_of_this_office_was": {"bsonType": ["int", "null"], "minimum": 0, "maximum": 5},
                    "cc_help_you": {"bsonType": ["int", "null"], "minimum": 0, "maximum": 5},
                    "sdq0": {"bsonType": ["int", "null"], "minimum": 0, "maximum": 5},
                    "sdq1": {"bsonType": ["int", "null"], "minimum": 0, "maximum": 5},
                    "sdq2": {"bsonType": ["int", "null"], "minimum": 0, "maximum": 5},
                    "sdq3": {"bsonType": ["int", "null"], "minimum": 0, "maximum": 5},
                    "sdq4": {"bsonType": ["int", "null"], "minimum": 0, "maximum": 5},
                    "sdq5": {"bsonType": ["int", "null"], "minimum": 0, "maximum": 5},
                    "sdq6": {"bsonType": ["int", "null"], "minimum": 0, "maximum": 5},
                    "sdq7": {"bsonType": ["int", "null"], "minimum": 0, "maximum": 5},
                    "sdq8": {"bsonType": ["int", "null"], "minimum": 0, "maximum": 5},
                    "suggestion": {"bsonType": ["string", "null"]},
                    "created_at": {"bsonType": "date"}
                }
            }
        })
        print("Created 'csm_form' collection")
    except CollectionInvalid:
        print("'csm_form' collection already exists")

    db.csm_form.create_index("control_no", unique=True)
    print("Created index for 'csm_form'")

    # ================================
    # FACE EMBEDDINGS
    # ================================
    try:
        db.create_collection("face_embeddings", validator={
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["client_id", "embedding_json"],
                "properties": {
                    "client_id": {"bsonType": "string"},
                    "embedding_json": {
                        "bsonType": "array",
                        "items": {"bsonType": "double"}
                    }
                }
            }
        })
        print("Created 'face_embeddings' collection")
    except CollectionInvalid:
        print("'face_embeddings' collection already exists")
    
    db.face_embeddings.create_index("client_id")
    print("Created index for 'face_embeddings'")

    # ================================
    # LOGS
    # ================================
    try:
        db.create_collection("logs", validator={
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["client_id", "time_in", "additional_info"],
                "properties": {
                    "client_id": {"bsonType": "string"},
                    "time_in": {"bsonType": "date"},
                    "time_out": {"bsonType": ["date", "null"]},
                    "purpose": {"bsonType": ["string", "null"]},
                    "additional_info": {"bsonType": "string"}
                }
            }
        })
        print("Created 'logs' collection")
    except CollectionInvalid:
        print("'logs' collection already exists")

    db.logs.create_index("client_id")
    db.logs.create_index([("time_in", -1)])
    db.logs.create_index([("client_id", 1), ("time_in", -1)])
    db.logs.create_index("purpose")
    print("Created indexes for 'logs'")

    # ================================
    # INITIAL ADMIN DATA
    # ================================
    admins_data = [
        {
            "first_name": "HR",
            "last_name": "Admin",
            "email": "hradmin@hrlogbook.edu",
            "password_hash": "scrypt:32768:8:1$DDheXyVRYoFtLtuY$ec67861d8eb9951bf5d057135ebc1652a3939c20ae3e756f3e45bfa890064f0ced2a87d199ef28a7e71b8abbdbcab85bad371bbbccfd35a34db27b69f1e727bc",
            "created_at": datetime.strptime("2025-12-17T03:20:17Z", "%Y-%m-%dT%H:%M:%SZ")
        },
        {
            "first_name": "JERIC",
            "last_name": "BOLEZA",
            "email": "admin@admin.com",
            "password_hash": "scrypt:32768:8:1$Yoy4Y7pErORWtp16$7b16521e7e52d3097bc5ff198b33aed234cea72e9a8054a3ea8a628c28b9b98483bd52f67e09951a6ae0da844200fd88394d3735fd72e2952607d792c0353ed9",
            "created_at": datetime.strptime("2026-01-16T09:52:12Z", "%Y-%m-%dT%H:%M:%SZ")
        }
    ]

    for admin in admins_data:
        try:
            db.admins.insert_one(admin)
            print(f"Inserted admin: {admin['email']}")
        except Exception as e:
            print(f"Skipped admin {admin['email']} (likely exists): {e}")

    print("✓ hrmo_elog_db initialized successfully")

if __name__ == "__main__":
    init_db()
