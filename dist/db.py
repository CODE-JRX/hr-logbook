from pymongo import MongoClient

# Global client to reuse connection
# In production, you might want to manage this differently (e.g., Flask g object)
# but for this scale, a module-level client is fine.
client = MongoClient("mongodb://localhost:27017/")
db = client["hrmo_elog_db"]

def get_db():
    return db

