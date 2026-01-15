from db import get_db_connection


def insert_csm_form(
    control_no, date_val, agency_visited, client_type, sex, age, region_of_residence,
    email, service_availed, awareness_of_cc, cc_of_this_office_was, cc_help_you,
    sdq_vals, suggestion
):
    """Insert a CSM form row into csm_form table.

    `sdq_vals` is expected to be a list/tuple of 9 ints (sdq0..sdq8) or shorter/None.
    Returns the new row id on success.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # prepare sdq values (ensure length 9)
    sdq = [(sdq_vals[i] if sdq_vals and i < len(sdq_vals) else None) for i in range(9)]

    sql = (
        "INSERT INTO csm_form (control_no, date, agency_visited, client_type, sex, age, region_of_residence, email, "
        "service_availed, awareness_of_cc, cc_of_this_office_was, cc_help_you, sdq0, sdq1, sdq2, sdq3, sdq4, sdq5, sdq6, sdq7, sdq8, suggestion) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )

    params = [
        control_no, date_val, agency_visited, client_type, sex, age, region_of_residence,
        email, service_availed, awareness_of_cc, cc_of_this_office_was, cc_help_you
    ] + sdq + [suggestion]

    cursor.execute(sql, tuple(params))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def get_csm_forms_filtered(start_date=None, end_date=None, gender=None, region=None, age_min=None, age_max=None, service=None):
    """Fetch CSM form records with optional filters.
    
    Args:
        start_date: Filter by date >= (YYYY-MM-DD format)
        end_date: Filter by date <= (YYYY-MM-DD format)
        gender: Filter by sex (M, F, etc.)
        region: Filter by region_of_residence (case-insensitive substring match)
        age_min, age_max: Filter by age range (assumes 'age' column exists)
        service: Filter by service_availed (case-insensitive substring match)
    
    Returns:
        List of dictionaries with all CSM form fields
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    sql = "SELECT * FROM csm_form WHERE 1=1"
    params = []
    
    if start_date:
        sql += " AND date >= %s"
        params.append(start_date)
    
    if end_date:
        sql += " AND date <= %s"
        params.append(end_date)
    
    if gender:
        sql += " AND sex = %s"
        params.append(gender)
    
    if region:
        sql += " AND region_of_residence LIKE %s"
        params.append(f"%{region}%")
    
    if age_min is not None:
        sql += " AND age >= %s"
        params.append(age_min)
    
    if age_max is not None:
        sql += " AND age <= %s"
        params.append(age_max)
    
    if service:
        sql += " AND service_availed LIKE %s"
        params.append(f"%{service}%")
    
    sql += " ORDER BY date DESC, id DESC"
    
    cursor.execute(sql, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    
    return rows
