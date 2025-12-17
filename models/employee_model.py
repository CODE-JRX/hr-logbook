from db import get_db_connection

def get_all_employees():
    """Return all rows from the employees table as dictionaries."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, employee_id, full_name, department FROM employees")
    data = cursor.fetchall()
    conn.close()
    return data


def get_employee_by_id(id):
    """Return a single employee by the integer primary key `id`."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, employee_id, full_name, department FROM employees WHERE id=%s", (id,))
    employee = cursor.fetchone()
    conn.close()
    return employee


def get_employee_by_employee_id(employee_id):
    """Return a single employee by the `employee_id` field (varchar)."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, employee_id, full_name, department FROM employees WHERE employee_id=%s", (employee_id,))
    employee = cursor.fetchone()
    conn.close()
    return employee


def add_employee(employee_id, full_name, department=None):
    """Insert a new employee row into the employees table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO employees (employee_id, full_name, department) VALUES (%s, %s, %s)",
        (employee_id, full_name, department)
    )
    conn.commit()
    conn.close()


def update_employee(id, employee_id=None, full_name=None, department=None):
    """Update fields for an employee. Only non-None arguments will be updated."""
    # Build dynamic SET clause depending on provided fields
    fields = []
    params = []
    if employee_id is not None:
        fields.append("employee_id=%s")
        params.append(employee_id)
    if full_name is not None:
        fields.append("full_name=%s")
        params.append(full_name)
    if department is not None:
        fields.append("department=%s")
        params.append(department)

    if not fields:
        return  # nothing to update

    params.append(id)
    set_clause = ", ".join(fields)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE employees SET {set_clause} WHERE id=%s", tuple(params))
    conn.commit()
    conn.close()


def delete_employee(id):
    """Delete an employee row by primary key `id`."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employees WHERE id=%s", (id,))
    conn.commit()
    conn.close()


def get_departments():
    """Return a list of distinct departments (non-null) from employees."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT department FROM employees WHERE department IS NOT NULL ORDER BY department")
    rows = [r[0] for r in cursor.fetchall()]
    conn.close()
    return rows


def get_employee_count():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM employees")
    total = cursor.fetchone()[0]
    conn.close()
    return total
