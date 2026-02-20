from db import get_db, get_db_cursor
import os
import mysql.connector

def get_all_clients():
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM clients ORDER BY id DESC")
        clients = cursor.fetchall()
        
        for client in clients:
            client['id'] = str(client['id'])
        
        return clients

def get_client_by_id(id):
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM clients WHERE id = %s", (id,))
        client = cursor.fetchone()
        
        if client:
            client['id'] = str(client['id'])
        
        return client

def get_client_by_client_id(client_id):
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM clients WHERE client_id = %s", (client_id,))
        client = cursor.fetchone()
        
        if client:
            client['id'] = str(client['id'])
        
        return client

def add_client(client_id, full_name, department=None, gender=None, age=None, client_type=None):
    with get_db_cursor(commit=True) as cursor:
        query = """INSERT INTO clients (client_id, full_name, department, gender, age, client_type)
                   VALUES (%s, %s, %s, %s, %s, %s)"""
        values = (
            client_id.upper() if isinstance(client_id, str) else client_id,
            full_name.upper() if isinstance(full_name, str) else full_name,
            department.upper() if isinstance(department, str) else department,
            gender.upper() if isinstance(gender, str) else gender,
            age,
            client_type.upper() if isinstance(client_type, str) else client_type
        )
        cursor.execute(query, values)

def update_client(id, client_id=None, full_name=None, department=None, gender=None, age=None, client_type=None):
    with get_db_cursor(commit=True) as cursor:
        updates = []
        values = []
        
        if client_id is not None:
            updates.append("client_id = %s")
            values.append(client_id.upper() if isinstance(client_id, str) else client_id)
        if full_name is not None:
            updates.append("full_name = %s")
            values.append(full_name.upper() if isinstance(full_name, str) else full_name)
        if department is not None:
            updates.append("department = %s")
            values.append(department.upper() if isinstance(department, str) else department)
        if gender is not None:
            updates.append("gender = %s")
            values.append(gender.upper() if isinstance(gender, str) else gender)
        if age is not None:
            updates.append("age = %s")
            values.append(age)
        if client_type is not None:
            updates.append("client_type = %s")
            values.append(client_type.upper() if isinstance(client_type, str) else client_type)

        if not updates:
            return

        query = f"UPDATE clients SET {', '.join(updates)} WHERE id = %s"
        values.append(id)
        
        cursor.execute(query, values)

def delete_client(id):
    with get_db_cursor(commit=True) as cursor:
        # Get client_id first for related deletion
        cursor.execute("SELECT client_id FROM clients WHERE id = %s", (id,))
        cli = cursor.fetchone()
        if cli:
            client_id = cli['client_id']
            
            cursor.execute("DELETE FROM clients WHERE id = %s", (id,))
            
            # Delete image file
            try:
                clients_dir = os.path.join(os.getcwd(), 'Clients')
                file_path = os.path.join(clients_dir, f"{client_id}.jpg")
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass

def get_departments():
    with get_db_cursor() as cursor:
        cursor.execute("SELECT DISTINCT department FROM clients WHERE department IS NOT NULL")
        deps = [row['department'] for row in cursor.fetchall()]
        return sorted(deps)

def get_client_count():
    with get_db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as cnt FROM clients")
        result = cursor.fetchone()
        return result['cnt']

def get_next_client_id():
    with get_db_cursor() as cursor:
        cursor.execute("SELECT client_id FROM clients")
        max_id = 0
        for row in cursor.fetchall():
            try:
                # cursor is dictionary=True now, so we access by key
                cid = row['client_id']
                val = int(cid)
                if val > max_id:
                    max_id = val
            except:
                pass
        return str(max_id + 1)

def search_clients(query, limit=10):
    with get_db_cursor() as cursor:
        search_val = f"%{query}%"
        sql = """SELECT id, client_id, full_name, department, client_type 
                 FROM clients 
                 WHERE client_id LIKE %s OR full_name LIKE %s 
                 ORDER BY full_name ASC LIMIT %s"""
        cursor.execute(sql, (search_val, search_val, limit))
        rows = cursor.fetchall()
        
        for row in rows:
            row['id'] = str(row['id'])
            
        return rows

def get_clients_filtered(search=None, limit=None):
    with get_db_cursor() as cursor:
        sql = "SELECT *, client_id as employee_id FROM clients"
        params = []
        if search:
            sql += " WHERE full_name LIKE %s OR client_id LIKE %s"
            search_val = f"%{search}%"
            params.extend([search_val, search_val])
        
        sql += " ORDER BY id DESC"
        
        if limit and limit != 'all':
            sql += " LIMIT %s"
            params.append(int(limit))
        
        cursor.execute(sql, params)
        data = cursor.fetchall()
        
        for doc in data:
            doc['id'] = str(doc['id'])
            
        return data
