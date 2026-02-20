from db import get_db
from datetime import datetime, timedelta
import mysql.connector

def add_time_in(client_id, purpose=None, additional_info=None):
    db = get_db()
    cursor = db.cursor()
    now = datetime.now()
    query = """INSERT INTO logs (client_id, time_in, time_out, purpose, additional_info)
               VALUES (%s, %s, %s, %s, %s)"""
    values = (
        client_id.upper() if isinstance(client_id, str) else client_id,
        now,
        None,
        purpose.upper() if isinstance(purpose, str) else purpose,
        (additional_info or "").upper() if isinstance(additional_info, str) else (additional_info or "")
    )
    cursor.execute(query, values)
    db.commit()
    cursor.close()
    db.close()

def add_time_out(client_id, purpose=None):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    now = datetime.now()
    
    # Find latest active log
    query = "SELECT id FROM logs WHERE client_id = %s AND time_out IS NULL ORDER BY time_in DESC LIMIT 1"
    cursor.execute(query, (client_id,))
    log = cursor.fetchone()
    
    if log:
        cursor.execute("UPDATE logs SET time_out = %s WHERE id = %s", (now, log['id']))
        db.commit()
        
    cursor.close()
    db.close()

def get_logs(purpose=None, department=None, start_date=None, end_date=None, limit=None):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    sql = """SELECT l.*, c.full_name, c.department, c.gender, c.age 
             FROM logs l 
             LEFT JOIN clients c ON l.client_id = c.client_id"""
    
    where_clauses = []
    params = []
    
    if purpose:
        where_clauses.append("l.purpose LIKE %s")
        params.append(f"%{purpose}%")
    
    if start_date:
        sd = datetime.strptime(start_date, "%Y-%m-%d")
        where_clauses.append("l.time_in >= %s")
        params.append(sd)
        
    if end_date:
        ed = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        where_clauses.append("l.time_in < %s")
        params.append(ed)
        
    if department:
        where_clauses.append("c.department = %s")
        params.append(department)
        
    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)
        
    sql += " ORDER BY l.time_in DESC"
    
    if limit and limit != 'all':
        sql += " LIMIT %s"
        params.append(int(limit))

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    
    results = []
    for row in rows:
        row['id'] = str(row['id'])
        results.append(row)
        
    cursor.close()
    db.close()
    return results

def get_logs_by_day(days=14):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    start_date = datetime.now() - timedelta(days=days)
    
    sql = """SELECT DATE_FORMAT(time_in, '%Y-%m-%d') as day_key, 
                    DATE_FORMAT(time_in, '%m/%d') as day, 
                    COUNT(*) as cnt 
             FROM logs 
             WHERE time_in >= %s 
             GROUP BY day_key, day 
             ORDER BY day_key ASC"""
    
    cursor.execute(sql, (start_date,))
    rows = cursor.fetchall()
    
    cursor.close()
    db.close()
    return rows

def get_department_counts():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    sql = """SELECT IFNULL(c.department, 'Unspecified') as department, COUNT(*) as cnt 
             FROM logs l 
             LEFT JOIN clients c ON l.client_id = c.client_id 
             GROUP BY department 
             ORDER BY cnt DESC"""
    
    cursor.execute(sql)
    rows = cursor.fetchall()
    
    cursor.close()
    db.close()
    return rows

def get_purpose_counts():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Select all purposes (ignoring NULL/empty)
    sql = "SELECT purpose FROM logs WHERE purpose IS NOT NULL AND purpose != ''"
    cursor.execute(sql)
    rows = cursor.fetchall()
    
    counts = {}
    for row in rows:
        purpose_str = row['purpose']
        if purpose_str:
            # Multi-purpose is comma-separated (e.g., "INQUIRE, PROCESS APPOINTMENT")
            purposes = [p.strip() for p in purpose_str.split(',')]
            for p in purposes:
                if p:
                    counts[p] = counts.get(p, 0) + 1
    
    # Sort by count descending
    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    
    # Reformat to match expect chart data: [{'purpose': 'P1', 'cnt': 10}, ...]
    rows_reformatted = [{'purpose': p, 'cnt': c} for p, c in sorted_counts]
    
    cursor.close()
    db.close()
    return rows_reformatted

def get_total_logs():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM logs")
    count = cursor.fetchone()[0]
    cursor.close()
    db.close()
    return count
