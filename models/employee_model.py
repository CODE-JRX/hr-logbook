from db import get_db_connection

def get_all_employees():
    """Return all rows from the employees table as dictionaries."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, employee_id, full_name, department, gender, age, client_type FROM employees ORDER BY id DESC")
    data = cursor.fetchall()
    conn.close()
    return data


def get_employee_by_id(id):
    """Return a single employee by the integer primary key `id`."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, employee_id, full_name, department, gender, age, client_type FROM employees WHERE id=%s", (id,))
    employee = cursor.fetchone()
    conn.close()
    return employee


def get_employee_by_employee_id(employee_id):
    """Return a single employee by the `employee_id` field (varchar)."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, employee_id, full_name, department, gender, age, client_type FROM employees WHERE employee_id=%s", (employee_id,))
    employee = cursor.fetchone()
    conn.close()
    return employee


def add_employee(employee_id, full_name, department=None, gender=None, age=None, client_type=None):
    """Insert a new employee row into the employees table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO employees (employee_id, full_name, department, gender, age, client_type) VALUES (%s, %s, %s, %s, %s, %s)",
        (employee_id, full_name, department, gender, age, client_type)
    )
    conn.commit()
    conn.close()


def update_employee(id, employee_id=None, full_name=None, department=None, gender=None, age=None, client_type=None):
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
    if gender is not None:
        fields.append("gender=%s")
        params.append(gender)
    if age is not None:
        fields.append("age=%s")
        params.append(age)
    if client_type is not None:
        fields.append("client_type=%s")
        params.append(client_type)

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
    # To avoid foreign key constraint errors, remove related resources first:
    # 1) delete face_embeddings entries that reference this employee_id
    # 2) delete stored image file in Employees/<employee_id>.jpg if present

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Lookup employee to obtain the employee_id (varchar) used by other tables
    cursor.execute("SELECT employee_id FROM employees WHERE id=%s", (id,))
    row = cursor.fetchone()
    if row:
        emp_id = row.get('employee_id')
        try:
            # delete face embedding rows referencing this employee_id
            # use a separate cursor without dictionary results for writes
            write_cur = conn.cursor()
            write_cur.execute("DELETE FROM face_embeddings WHERE employee_id=%s", (emp_id,))
            # remove stored image file if exists
            try:
                import os
                employees_dir = os.path.join(os.getcwd(), 'Employees')
                file_path = os.path.join(employees_dir, f"{emp_id}.jpg")
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                # non-fatal: ignore file removal errors
                pass
        except Exception:
            # If deleting related rows failed, continue to attempt employee delete
            pass
    #delete related logs from `logs` table
    try:
        write_cur = conn.cursor()
        write_cur.execute("DELETE FROM logs WHERE employee_id=%s", (emp_id,))
    except Exception:
        pass
    # finally delete the employee row
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


def get_next_employee_id():
    """Generate the next employee_id by finding the maximum existing employee_id (as int) and incrementing by 1."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(CAST(employee_id AS UNSIGNED)) FROM employees")
    result = cursor.fetchone()
    max_id = result[0] if result[0] is not None else 0
    next_id = max_id + 1
    conn.close()
    return str(next_id)


def search_employees(query, limit=10):
    """Search employees by employee_id or full_name (partial match).

    Returns a list of dict rows: {id, employee_id, full_name, department, client_type}
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    like_q = f"%{query}%"
    cursor.execute(
        "SELECT id, employee_id, full_name, department, client_type FROM employees WHERE employee_id LIKE %s OR full_name LIKE %s ORDER BY full_name ASC LIMIT %s",
        (like_q, like_q, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_employees_filtered(search=None, limit=None):
    """Return employees filtered by search query and limited by number.

    search: string to search in full_name or employee_id
    limit: int or 'all' for no limit
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT id, employee_id, full_name, department, gender, age, client_type FROM employees"
    params = []
    if search:
        query += " WHERE full_name LIKE %s OR employee_id LIKE %s"
        like_q = f"%{search}%"
        params.extend([like_q, like_q])
    query += " ORDER BY id DESC"
    if limit and limit != 'all':
        try:
            limit_int = int(limit)
            query += " LIMIT %s"
            params.append(limit_int)
        except ValueError:
            pass  # ignore invalid limit
    cursor.execute(query, tuple(params))
    data = cursor.fetchall()
    conn.close()
    return data
