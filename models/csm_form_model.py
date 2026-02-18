from db import get_db
from datetime import datetime
import mysql.connector

def insert_csm_form(
    control_no, date_val, agency_visited, client_type, sex, age, region_of_residence,
    email, service_availed, awareness_of_cc, cc_of_this_office_was, cc_help_you,
    sdq_vals, suggestion
):
    db = get_db()
    cursor = db.cursor()
    
    # Handle SDQ values
    sdqs = [None] * 9
    if sdq_vals:
        for i in range(min(len(sdq_vals), 9)):
            sdqs[i] = sdq_vals[i]

    query = """INSERT INTO csm_form (
        control_no, date, agency_visited, client_type, sex, age, region_of_residence,
        email, service_availed, awareness_of_cc, cc_of_this_office_was, cc_help_you,
        sdq0, sdq1, sdq2, sdq3, sdq4, sdq5, sdq6, sdq7, sdq8, suggestion, created_at
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    
    values = (
        control_no.upper() if isinstance(control_no, str) else control_no,
        date_val,
        agency_visited.upper() if isinstance(agency_visited, str) else agency_visited,
        client_type.upper() if isinstance(client_type, str) else client_type,
        sex.upper() if isinstance(sex, str) else sex,
        age,
        region_of_residence.upper() if isinstance(region_of_residence, str) else region_of_residence,
        email.upper() if isinstance(email, str) else email,
        service_availed.upper() if isinstance(service_availed, str) else service_availed,
        awareness_of_cc,
        cc_of_this_office_was,
        cc_help_you,
        sdqs[0], sdqs[1], sdqs[2], sdqs[3], sdqs[4], 
        sdqs[5], sdqs[6], sdqs[7], sdqs[8],
        suggestion.upper() if isinstance(suggestion, str) else suggestion,
        datetime.now()
    )
    
    try:
        cursor.execute(query, values)
        db.commit()
        last_id = cursor.lastrowid
        return str(last_id)
    except mysql.connector.Error as err:
        print(f"Error inserting CSM form: {err}")
        return None
    finally:
        cursor.close()
        db.close()

def get_csm_forms_filtered(start_date=None, end_date=None, gender=None, region=None, age_min=None, age_max=None, service=None, limit=None):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    sql = "SELECT * FROM csm_form"
    where_clauses = []
    params = []
    
    if start_date:
        where_clauses.append("date >= %s")
        params.append(start_date)
    if end_date:
        where_clauses.append("date <= %s")
        params.append(end_date)
    if gender:
        where_clauses.append("sex = %s")
        params.append(gender)
    if region:
        where_clauses.append("region_of_residence LIKE %s")
        params.append(f"%{region}%")
    if age_min is not None:
        where_clauses.append("age >= %s")
        params.append(age_min)
    if age_max is not None:
        where_clauses.append("age <= %s")
        params.append(age_max)
    if service:
        where_clauses.append("service_availed LIKE %s")
        params.append(f"%{service}%")
        
    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)
        
    sql += " ORDER BY date DESC, id DESC"
    
    if limit and limit != 'all':
        sql += " LIMIT %s"
        params.append(int(limit))
        
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    
    for doc in rows:
        doc['id'] = str(doc['id'])
        
    cursor.close()
    db.close()
    return rows
