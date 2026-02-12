from db import get_db
from datetime import datetime, timedelta

def add_time_in(client_id, purpose=None, additional_info=None):
    """Insert a new log with time_in = now."""
    db = get_db()
    # Ensure time is stored as Date object for queries
    now = datetime.now() # MongoDB native Date
    db.logs.insert_one({
        "client_id": client_id.upper() if isinstance(client_id, str) else client_id,
        "time_in": now,
        "time_out": None,
        "purpose": purpose.upper() if isinstance(purpose, str) else purpose,
        "additional_info": (additional_info or "").upper() if isinstance(additional_info, str) else (additional_info or "")
    })


def add_time_out(client_id, purpose=None):
    """Set time_out = now on the latest log for client where time_out IS NULL."""
    db = get_db()
    now = datetime.now()
    
    # Find latest active log
    # Sort by time_in desc to get most recent
    log = db.logs.find_one(
        {"client_id": client_id, "time_out": None},
        sort=[("time_in", -1)]
    )
    
    if log:
        db.logs.update_one(
            {"_id": log["_id"]},
            {"$set": {"time_out": now}}
        )


def get_logs(purpose=None, department=None, start_date=None, end_date=None, limit=None):
    """Return logs with client details joined."""
    db = get_db()
    
    match = {}
    if purpose:
        match["purpose"] = {"$regex": purpose, "$options": "i"}
    
    if start_date or end_date:
        date_filter = {}
        if start_date:
            # Parse date string to datetime
            sd = datetime.strptime(start_date, "%Y-%m-%d")
            date_filter["$gte"] = sd
        if end_date:
            ed = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1) # inclusive of that day
            date_filter["$lt"] = ed
        match["time_in"] = date_filter

    # Aggregation to join with clients
    pipeline = []
    if match:
        pipeline.append({"$match": match})
        
    pipeline.append({
        "$lookup": {
            "from": "clients",
            "localField": "client_id",
            "foreignField": "client_id",
            "as": "employee_docs"
        }
    })
    
    # Flatten the lookup info (unwind) - but it's possible employee is missing, so preserveNullAndEmptyArrays
    pipeline.append({
        "$unwind": {
            "path": "$employee_docs",
            "preserveNullAndEmptyArrays": True
        }
    })
    
    # Filter by department if needed (post-lookup)
    if department:
        pipeline.append({
            "$match": {"employee_docs.department": department}
        })

    pipeline.append({"$sort": {"time_in": -1}})
    
    if limit and limit != 'all':
        try:
            pipeline.append({"$limit": int(limit)})
        except:
            pass

    results = []
    cursor = db.logs.aggregate(pipeline)
    for doc in cursor:
        emp = doc.get("employee_docs", {})
        
        # Flatten structure for template compatibility
        # SQL returned: id, employee_id, full_name, department, gender, age, time_in, time_out, purpose, additional_info
        item = {
            "id": str(doc["_id"]),
            "client_id": doc.get("client_id"),
            "full_name": emp.get("full_name"),
            "department": emp.get("department"),
            "gender": emp.get("gender"),
            "age": emp.get("age"),
            "time_in": doc.get("time_in"),
            "time_out": doc.get("time_out"),
            "purpose": doc.get("purpose"),
            "additional_info": doc.get("additional_info")
        }
        results.append(item)
        
    return results


def get_logs_by_day(days=14):
    """Return list of dicts with day and count for the last `days` days."""
    db = get_db()
    start_date = datetime.now() - timedelta(days=days)
    
    pipeline = [
        {"$match": {"time_in": {"$gte": start_date}}},
        {
            "$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$time_in"}
                },
                "cnt": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    
    cursor = db.logs.aggregate(pipeline)
    rows = []
    for doc in cursor:
        # SQL Query returned `day` as day of month string?
        # "LPAD(DATE_FORMAT(time_in, '%d'), 2, '0')" returns '04', '05' etc.
        # The chart probably expects just the day number or full date?
        # Let's adjust to match exact return of SQL if possible, or just the date string if frontend handles it.
        # Javascript often parses it. Let's return day-of-month to be safe.
        date_str = doc["_id"] # YYYY-MM-DD
        day_str = date_str.split("-")[2]
        
        rows.append({
            "day": day_str,
            "cnt": doc["cnt"]
        })
    return rows


def get_department_counts():
    db = get_db()
    
    pipeline = [
        {
            "$lookup": {
                "from": "clients",
                "localField": "client_id",
                "foreignField": "client_id",
                "as": "emp"
            }
        },
        {"$unwind": {"path": "$emp", "preserveNullAndEmptyArrays": True}},
        {
            "$group": {
                "_id": {"$ifNull": ["$emp.department", "Unspecified"]},
                "cnt": {"$sum": 1}
            }
        },
        {"$sort": {"cnt": -1}}
    ]
    
    cursor = db.logs.aggregate(pipeline)
    rows = []
    for doc in cursor:
        rows.append({
            "department": doc["_id"],
            "cnt": doc["cnt"]
        })
    return rows


def get_purpose_counts():
    db = get_db()
    
    pipeline = [
         {
            "$group": {
                "_id": {"$ifNull": ["$purpose", "Unspecified"]},
                "cnt": {"$sum": 1}
            }
        },
        {"$sort": {"cnt": -1}}
    ]

    cursor = db.logs.aggregate(pipeline)
    rows = []
    for doc in cursor:
        rows.append({
            "purpose": doc["_id"],
            "cnt": doc["cnt"]
        })
    return rows


def get_total_logs():
    db = get_db()
    return db.logs.count_documents({})

