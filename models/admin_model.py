from db import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash


def ensure_admins_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INT PRIMARY KEY AUTO_INCREMENT,
        first_name VARCHAR(100),
        last_name VARCHAR(100),
        email VARCHAR(255) UNIQUE,
        password_hash VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;
    """)
    conn.commit()
    cur.close()
    conn.close()


def add_admin(first_name, last_name, email, password):
    ensure_admins_table()
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    ph = generate_password_hash(password)
    cur.execute("INSERT INTO admins (first_name, last_name, email, password_hash) VALUES (%s,%s,%s,%s)",
                (first_name, last_name, email, ph))
    conn.commit()
    cur.close()
    conn.close()


def get_admin_by_email(email):
    ensure_admins_table()
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM admins WHERE email=%s", (email,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def verify_admin_credentials(email, password):
    admin = get_admin_by_email(email)
    if not admin:
        return None
    if check_password_hash(admin.get('password_hash', ''), password):
        return admin
    return None
