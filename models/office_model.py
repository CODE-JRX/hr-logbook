from db import get_db, get_db_cursor
from datetime import datetime
import mysql.connector

def get_offices():
    """Return a list of all offices from the offices table."""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM offices ORDER BY name ASC")
        return cursor.fetchall()

def get_active_offices():
    """Return a list of active office objects (id and name)."""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT id, name FROM offices WHERE is_active = 1 ORDER BY name ASC")
        return cursor.fetchall()

def add_office(name):
    """Add a new office to the offices table."""
    name = name.strip().upper()
    query = "INSERT INTO offices (name, is_active, created_at, updated_at) VALUES (%s, 1, %s, %s)"
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(query, (name, datetime.now(), datetime.now()))
            return cursor.lastrowid
    except mysql.connector.Error as err:
        print(f"Error adding office: {err}")
        return None

def update_office_status(office_id, is_active):
    """Update the active status of an office."""
    query = "UPDATE offices SET is_active = %s, updated_at = %s WHERE id = %s"
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(query, (1 if is_active else 0, datetime.now(), office_id))
            return cursor.rowcount > 0
    except mysql.connector.Error as err:
        print(f"Error updating office status: {err}")
        return False

def update_office(office_id, name):
    """Update the name of an office."""
    name = name.strip().upper()
    query = "UPDATE offices SET name = %s, updated_at = %s WHERE id = %s"
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(query, (name, datetime.now(), office_id))
            return cursor.rowcount > 0
    except mysql.connector.Error as err:
        print(f"Error updating office name: {err}")
        return False

def delete_office(office_id):
    """Delete an office from the offices table."""
    query = "DELETE FROM offices WHERE id = %s"
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(query, (office_id,))
            return cursor.rowcount > 0
    except mysql.connector.Error as err:
        print(f"Error deleting office: {err}")
        return False

def get_office_id_by_name(name):
    """Get the ID of an office by its name."""
    if not name: return None
    with get_db_cursor() as cursor:
        cursor.execute("SELECT id FROM offices WHERE name = %s", (name.strip().upper(),))
        row = cursor.fetchone()
        return row['id'] if row else None

def get_office_name_by_id(office_id):
    """Get the name of an office by its ID."""
    if not office_id: return None
    with get_db_cursor() as cursor:
        cursor.execute("SELECT name FROM offices WHERE id = %s", (office_id,))
        row = cursor.fetchone()
        return row['name'] if row else None
