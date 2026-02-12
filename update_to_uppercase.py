from pymongo import MongoClient
from bson.objectid import ObjectId

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["hrmo_elog_db"]

def update_collection_to_uppercase(collection_name, string_fields):
    collection = db[collection_name]
    cursor = collection.find({})
    updated_count = 0
    for doc in cursor:
        update_fields = {}
        for field in string_fields:
            if field in doc and isinstance(doc[field], str):
                update_fields[field] = doc[field].upper()
        if update_fields:
            collection.update_one({"_id": doc["_id"]}, {"$set": update_fields})
            updated_count += 1
    print(f"Updated {updated_count} documents in {collection_name}")

# Define string fields for each collection
collections_to_update = {
    "admins": ["first_name", "last_name", "email"],
    "clients": ["client_id", "client_type", "full_name", "department", "gender"],
    "csm_form": ["control_no", "agency_visited", "client_type", "sex", "region_of_residence", "email", "service_availed", "suggestion"],
    "face_embeddings": ["client_id"],
    "logs": ["client_id", "purpose", "additional_info"]
}

if __name__ == "__main__":
    print("Starting update to uppercase...")
    for coll, fields in collections_to_update.items():
        update_collection_to_uppercase(coll, fields)
    print("Update completed.")
