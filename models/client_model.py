from db import get_db
import os
import mysql.connector

def get_all_clients():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM clients ORDER BY id DESC")
    clients = cursor.fetchall()
    
    for client in clients:
        client['id'] = str(client['id'])
    
    cursor.close()
    db.close()
    return clients

def get_client_by_id(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM clients WHERE id = %s", (id,))
    client = cursor.fetchone()
    
    if client:
        client['id'] = str(client['id'])
    
    cursor.close()
    db.close()
    return client

def get_client_by_client_id(client_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM clients WHERE client_id = %s", (client_id,))
    client = cursor.fetchone()
    
    if client:
        client['id'] = str(client['id'])
    
    cursor.close()
    db.close()
    return client

def add_client(client_id, full_name, department=None, gender=None, age=None, client_type=None):
    db = get_db()
    cursor = db.cursor()
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
    db.commit()
    cursor.close()
    db.close()

def update_client(id, client_id=None, full_name=None, department=None, gender=None, age=None, client_type=None):
    db = get_db()
    cursor = db.cursor()
    
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
        cursor.close()
        db.close()
        return

    query = f"UPDATE clients SET {', '.join(updates)} WHERE id = %s"
    values.append(id)
    
    cursor.execute(query, values)
    db.commit()
    cursor.close()
    db.close()

def delete_client(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Get client_id first for related deletion
    cursor.execute("SELECT client_id FROM clients WHERE id = %s", (id,))
    cli = cursor.fetchone()
    if cli:
        client_id = cli['client_id']
        
        # Foreign keys will handle logs and face_embeddings if ON DELETE CASCADE is set
        # But for completeness:
        cursor.execute("DELETE FROM clients WHERE id = %s", (id,))
        
        # Delete image file
        try:
            clients_dir = os.path.join(os.getcwd(), 'Clients')
            file_path = os.path.join(clients_dir, f"{client_id}.jpg")
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
            
    db.commit()
    cursor.close()
    db.close()

def get_departments():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT DISTINCT department FROM clients WHERE department IS NOT NULL")
    deps = [row[0] for row in cursor.fetchall()]
    cursor.close()
    db.close()
    return sorted(deps)

def get_client_count():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM clients")
    count = cursor.fetchone()[0]
    cursor.close()
    db.close()
    return count

def get_next_client_id():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT client_id FROM clients")
    max_id = 0
    for (cid,) in cursor:
        try:
            val = int(cid)
            if val > max_id:
                max_id = val
        except:
            pass
    cursor.close()
    db.close()
    return str(max_id + 1)

def search_clients(query, limit=10):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    search_val = f"%{query}%"
    sql = """SELECT id, client_id, full_name, department, client_type 
             FROM clients 
             WHERE client_id LIKE %s OR full_name LIKE %s 
             ORDER BY full_name ASC LIMIT %s"""
    cursor.execute(sql, (search_val, search_val, limit))
    rows = cursor.fetchall()
    
    for row in rows:
        row['id'] = str(row['id'])
        
    cursor.close()
    db.close()
    return rows

def get_clients_filtered(search=None, limit=None):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
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
        
    cursor.close()
    db.close()
    return data
