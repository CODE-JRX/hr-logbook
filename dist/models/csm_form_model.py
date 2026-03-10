from db import get_db, get_db_cursor
from datetime import datetime
import mysql.connector
from models.office_model import get_office_id_by_name

def insert_csm_form(
    control_no, date_val, office, client_type, sex, age, region_of_residence,
    email, service_availed, awareness_of_cc, cc_of_this_office_was, cc_help_you,
    sdq_vals, suggestion
):
    # Handle SDQ values
    sdqs = [None] * 9
    if sdq_vals:
        for i in range(min(len(sdq_vals), 9)):
            sdqs[i] = sdq_vals[i]

    # Convert office name to ID if it's a string (e.g. "REGISTRAR" -> 5)
    office_id = office
    if office and isinstance(office, str) and not office.isdigit():
        office_id = get_office_id_by_name(office)

    query = """INSERT INTO csm_form (
        control_no, date, office, client_type, sex, age, region_of_residence,
        email, service_availed, awareness_of_cc, cc_of_this_office_was, cc_help_you,
        sdq0, sdq1, sdq2, sdq3, sdq4, sdq5, sdq6, sdq7, sdq8, suggestion, created_at
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    
    values = (
        control_no.upper() if isinstance(control_no, str) else control_no,
        date_val,
        office_id,
        client_type.upper() if isinstance(client_type, str) else client_type,
        sex.upper() if isinstance(sex, str) else sex,
        age,
        region_of_residence.upper() if isinstance(region_of_residence, str) else region_of_residence,
        email.lower() if isinstance(email, str) else email,
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
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(query, values)
            last_id = cursor.lastrowid
            return str(last_id)
    except mysql.connector.Error as err:
        print(f"Error inserting CSM form: {err}")
        return None

def get_csm_forms_filtered(start_date=None, end_date=None, gender=None, region=None, age_min=None, age_max=None, service=None, limit=None, office=None):
    with get_db_cursor() as cursor:
        sql = """SELECT cf.*, o.name as office_name 
                 FROM csm_form cf
                 LEFT JOIN offices o ON cf.office = o.id"""
        where_clauses = []
        params = []
        
        if start_date:
            where_clauses.append("cf.date >= %s")
            params.append(start_date)
        if end_date:
            where_clauses.append("cf.date <= %s")
            params.append(end_date)
        if gender:
            where_clauses.append("cf.sex = %s")
            params.append(gender)
        if region:
            where_clauses.append("cf.region_of_residence LIKE %s")
            params.append(f"%{region}%")
        if age_min is not None:
            where_clauses.append("cf.age >= %s")
            params.append(age_min)
        if age_max is not None:
            where_clauses.append("cf.age <= %s")
            params.append(age_max)
        if service:
            where_clauses.append("cf.service_availed LIKE %s")
            params.append(f"%{service}%")
        if office:
            if isinstance(office, str) and not office.isdigit():
                oid = get_office_id_by_name(office)
                where_clauses.append("cf.office = %s")
                params.append(oid)
            else:
                where_clauses.append("cf.office = %s")
                params.append(office)
            
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
            
        sql += " ORDER BY cf.date DESC, cf.id DESC"
        
        if limit and limit != 'all':
            sql += " LIMIT %s"
            params.append(int(limit))
            
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        for doc in rows:
            doc['id'] = str(doc['id'])
            
        return rows

def get_offices():
    """Return a list of distinct offices from the offices table."""
    with get_db_cursor() as cursor:
        # Check if table has is_active column (which it does based on my earlier check)
        cursor.execute("SELECT name FROM offices WHERE is_active = 1 ORDER BY name ASC")
        rows = cursor.fetchall()
        return [row['name'] for row in rows]

def get_csm_form_count(office=None):
    """Return total number of rows in csm_form table, optionally filtered by office."""
    with get_db_cursor() as cursor:
        sql = "SELECT COUNT(*) as cnt FROM csm_form"
        params = []
        if office:
            if isinstance(office, str) and not office.isdigit():
                oid = get_office_id_by_name(office)
                sql += " WHERE office = %s"
                params.append(oid)
            else:
                sql += " WHERE office = %s"
                params.append(office)
        cursor.execute(sql, params)
        row = cursor.fetchone()
        return row['cnt'] if row else 0
