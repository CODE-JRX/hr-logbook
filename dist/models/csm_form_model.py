from db import get_db
from bson.objectid import ObjectId
from datetime import datetime

def insert_csm_form(
    control_no, date_val, agency_visited, client_type, sex, age, region_of_residence,
    email, service_availed, awareness_of_cc, cc_of_this_office_was, cc_help_you,
    sdq_vals, suggestion
):
    """Insert a CSM form row into csm_form collection."""
    db = get_db()
    
    # Store sdq values as individual fields to match legacy expectation if needed, 
    # or just keep them as they were. The original SQL inserted sdq0..sdq8.
    # We'll just insert a document with these fields.
    
    doc = {
        "control_no": control_no.upper() if isinstance(control_no, str) else control_no,
        "date": date_val,
        "agency_visited": agency_visited.upper() if isinstance(agency_visited, str) else agency_visited,
        "client_type": client_type.upper() if isinstance(client_type, str) else client_type,
        "sex": sex.upper() if isinstance(sex, str) else sex,
        "age": age,
        "region_of_residence": region_of_residence.upper() if isinstance(region_of_residence, str) else region_of_residence,
        "email": email.upper() if isinstance(email, str) else email,
        "service_availed": service_availed.upper() if isinstance(service_availed, str) else service_availed,
        "awareness_of_cc": awareness_of_cc.upper() if isinstance(awareness_of_cc, str) else awareness_of_cc,
        "cc_of_this_office_was": cc_of_this_office_was.upper() if isinstance(cc_of_this_office_was, str) else cc_of_this_office_was,
        "cc_help_you": cc_help_you.upper() if isinstance(cc_help_you, str) else cc_help_you,
        "suggestion": suggestion.upper() if isinstance(suggestion, str) else suggestion,
        "created_at": datetime.now()
    }

    # Add SDQ values
    for i in range(9):
        val = sdq_vals[i] if sdq_vals and i < len(sdq_vals) else None
        doc[f"sdq{i}"] = val

    result = db.csm_form.insert_one(doc)
    return str(result.inserted_id)


def get_csm_forms_filtered(start_date=None, end_date=None, gender=None, region=None, age_min=None, age_max=None, service=None, limit=None):
    """Fetch CSM form records with optional filters."""
    db = get_db()
    query = {}
    
    if start_date:
        query["date"] = {"$gte": start_date}
    if end_date:
         # Merge if date already in query (range)
        if "date" in query:
            query["date"]["$lte"] = end_date
        else:
            query["date"] = {"$lte": end_date}
            
    if gender:
        query["sex"] = gender
        
    if region:
        query["region_of_residence"] = {"$regex": region, "$options": "i"}
        
    if age_min is not None or age_max is not None:
        age_query = {}
        if age_min is not None:
            age_query["$gte"] = age_min
        if age_max is not None:
            age_query["$lte"] = age_max
        if age_query:
            query["age"] = age_query

    if service:
        query["service_availed"] = {"$regex": service, "$options": "i"}

    cursor = db.csm_form.find(query).sort([("date", -1), ("_id", -1)])

    if limit and limit != 'all':
        try:
            cursor = cursor.limit(int(limit))
        except:
            pass

    rows = []
    for doc in cursor:
        doc['id'] = str(doc['_id'])
        rows.append(doc)
    return rows

