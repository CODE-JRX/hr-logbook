from db import get_db_connection
from datetime import datetime


def add_time_in(employee_id, purpose=None, additional_info=None):
    """Insert a new log with time_in = now."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(
        "INSERT INTO logs (employee_id, time_in, purpose, additional_info) VALUES (%s, %s, %s, %s)",
        (employee_id, now, purpose, additional_info)
    )
    conn.commit()
    conn.close()


def add_time_out(employee_id, purpose=None):
    """Set time_out = now on the latest log for employee where time_out IS NULL.

    Note: purpose is intentionally NOT updated here — purpose should be set at time_in only.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(
        "UPDATE logs SET time_out=%s WHERE employee_id=%s AND time_out IS NULL ORDER BY time_in DESC LIMIT 1",
        (now, employee_id)
    )
    conn.commit()
    conn.close()


def get_logs(purpose=None, department=None, start_date=None, end_date=None):
    """Return logs optionally filtered by purpose (partial match), department, and a time_in date range.

    start_date and end_date should be strings in YYYY-MM-DD format (inclusive).
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    sql = (
        "SELECT l.id, l.employee_id, e.full_name, e.department, e.gender, e.age, l.time_in, l.time_out, l.purpose "
        "FROM logs l LEFT JOIN employees e ON l.employee_id = e.employee_id WHERE 1=1"
    )
    params = []
    if purpose:
        sql += " AND l.purpose LIKE %s"
        params.append(f"%{purpose}%")
    if department:
        sql += " AND e.department = %s"
        params.append(department)
    if start_date:
        sql += " AND l.time_in >= %s"
        params.append(f"{start_date} 00:00:00")
    if end_date:
        sql += " AND l.time_in <= %s"
        params.append(f"{end_date} 23:59:59")

    sql += " ORDER BY l.time_in DESC"
    cursor.execute(sql, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_logs_by_day(days=14):
    """Return list of dicts with day and count for the last `days` days (inclusive)."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT DATE(time_in) as day, COUNT(*) as cnt FROM logs WHERE time_in >= DATE_SUB(CURDATE(), INTERVAL %s DAY) GROUP BY DATE(time_in) ORDER BY day ASC",
        (days-1,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_department_counts():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT COALESCE(e.department, 'Unspecified') as department, COUNT(*) as cnt FROM logs l LEFT JOIN employees e ON l.employee_id = e.employee_id GROUP BY department ORDER BY cnt DESC"
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_purpose_counts():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT COALESCE(purpose, 'Unspecified') as purpose, COUNT(*) as cnt FROM logs GROUP BY purpose ORDER BY cnt DESC"
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_total_logs():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM logs")
    total = cursor.fetchone()[0]
    conn.close()
    return total
