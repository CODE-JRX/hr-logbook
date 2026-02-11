from db import get_db
from bson.objectid import ObjectId
import os

def get_all_clients():
    """Return all rows from the clients collection."""
    db = get_db()
    # Sort by _id desc (approx like id desc)
    cursor = db.clients.find().sort("_id", -1)
    clients = []
    for doc in cursor:
        doc['id'] = str(doc['_id'])
        clients.append(doc)
    return clients


def get_client_by_id(id):
    """Return a single client by the MongoDB _id string."""
    db = get_db()
    try:
        oid = ObjectId(id)
    except:
        return None
    client = db.clients.find_one({"_id": oid})
    if client:
        client['id'] = str(client['_id'])
    return client


def get_client_by_client_id(client_id):
    """Return a single client by the `client_id` field."""
    db = get_db()
    client = db.clients.find_one({"client_id": client_id})
    if client:
        client['id'] = str(client['_id'])
    return client


def add_client(client_id, full_name, department=None, gender=None, age=None, client_type=None):
    """Insert a new client into the clients collection."""
    db = get_db()
    doc = {
        "client_id": client_id,
        "full_name": full_name,
        "department": department,
        "gender": gender,
        "age": age,
        "client_type": client_type
    }
    db.clients.insert_one(doc)


def update_client(id, client_id=None, full_name=None, department=None, gender=None, age=None, client_type=None):
    """Update fields for a client."""
    db = get_db()
    fields = {}
    if client_id is not None:
        fields["client_id"] = client_id
    if full_name is not None:
        fields["full_name"] = full_name
    if department is not None:
        fields["department"] = department
    if gender is not None:
        fields["gender"] = gender
    if age is not None:
        fields["age"] = age
    if client_type is not None:
        fields["client_type"] = client_type

    if not fields:
        return

    try:
        oid = ObjectId(id)
        db.clients.update_one({"_id": oid}, {"$set": fields})
    except:
        pass


def delete_client(id):
    """Delete a client and related data."""
    db = get_db()
    try:
        oid = ObjectId(id)
        # Get client_id first
        cli = db.clients.find_one({"_id": oid})
        if cli:
            client_id = cli.get('client_id')
            
            # 1. Delete face embeddings
            db.face_embeddings.delete_many({"client_id": client_id})
            
            # 2. Delete logs
            db.logs.delete_many({"client_id": client_id})

            # 3. Delete image file
            try:
                clients_dir = os.path.join(os.getcwd(), 'Clients')
                file_path = os.path.join(clients_dir, f"{client_id}.jpg")
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass
            
            # 4. Delete client
            db.clients.delete_one({"_id": oid})
    except:
        pass


def get_departments():
    """Return a list of distinct departments."""
    db = get_db()
    # distinct returns a list of values
    deps = db.clients.distinct("department")
    # Filter out None and sort
    return sorted([d for d in deps if d])


def get_client_count():
    db = get_db()
    return db.clients.count_documents({})


def get_next_client_id():
    """Generate the next client_id."""
    # This might be slow if many docs, but safe enough for now. 
    # Better to find max using regex or numeric check if mixed.
    # Assuming client_id are numeric strings.
    db = get_db()
    # Fetch all client_ids to find max (heavy, but flexible) or sort by client_id desc if purely numeric string format is guaranteed?
    # String sorting "10" < "2", so better to cast. 
    # Let's fetch just client_id strings.
    cursor = db.clients.find({}, {"client_id": 1})
    max_id = 0
    for doc in cursor:
        cid = doc.get("client_id")
        try:
            val = int(cid)
            if val > max_id:
                max_id = val
        except:
            pass
    return str(max_id + 1)


def search_clients(query, limit=10):
    """Search clients by client_id or full_name."""
    db = get_db()
    # Regex search (case insensitive)
    rgx = {"$regex": query, "$options": "i"}
    criteria = {
        "$or": [
            {"client_id": rgx},
            {"full_name": rgx}
        ]
    }
    cursor = db.clients.find(criteria).sort("full_name", 1).limit(limit)
    rows = []
    for doc in cursor:
        # map for frontend compatibility
        rows.append({
            "id": str(doc["_id"]),
            "client_id": doc.get("client_id"),
            "full_name": doc.get("full_name"),
            "department": doc.get("department"),
            "client_type": doc.get("client_type")
        })
    return rows


def get_clients_filtered(search=None, limit=None):
    """Return clients filtered by search query and limited by number."""
    db = get_db()
    criteria = {}
    if search:
        rgx = {"$regex": search, "$options": "i"}
        criteria = {
            "$or": [
                {"full_name": rgx},
                {"client_id": rgx}
            ]
        }
    
    cursor = db.clients.find(criteria).sort("_id", -1)
    
    if limit and limit != 'all':
        try:
            cursor = cursor.limit(int(limit))
        except:
            pass
            
    data = []
    for doc in cursor:
        doc['id'] = str(doc['_id'])
        # doc['client_id'] is already correct, no alias needed if we update callers
        # but let's redundant alias if templates still use employee_id
        doc['employee_id'] = doc.get('client_id') 
        data.append(doc)
    return data

