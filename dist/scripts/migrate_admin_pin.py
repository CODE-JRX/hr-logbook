import mysql.connector
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import get_db

def migrate():
    print("Starting migration: Adding pin_hash to admins table...")
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Check if column exists
        cursor.execute("SHOW COLUMNS FROM admins LIKE 'pin_hash'")
        result = cursor.fetchone()
        
        if not result:
            cursor.execute("ALTER TABLE admins ADD COLUMN pin_hash VARCHAR(255) AFTER password_hash")
            db.commit()
            print("Successfully added 'pin_hash' column to 'admins' table.")
        else:
            print("'pin_hash' column already exists.")
            
    except mysql.connector.Error as err:
        print(f"Error migrating database: {err}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'db' in locals() and db:
            db.close()

if __name__ == "__main__":
    migrate()
