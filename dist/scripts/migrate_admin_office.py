import mysql.connector
import os
import sys

# Add parent directory to sys.path to allow importing from 'db'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db_cursor

def migrate():
    print("Starting migration: adding 'office' column to 'admins' table...")
    try:
        with get_db_cursor(commit=True) as cursor:
            # Check if column exists
            cursor.execute("SHOW COLUMNS FROM admins LIKE 'office'")
            result = cursor.fetchone()
            
            if not result:
                cursor.execute("ALTER TABLE admins ADD COLUMN office VARCHAR(100) NULL AFTER pin_hash")
                print("Column 'office' added successfully.")
                
                # Update existing admins to 'ASIST/UA' so they remain universal by default
                cursor.execute("UPDATE admins SET office = 'ASIST/UA' WHERE office IS NULL")
                print("Existing admins updated to 'ASIST/UA'.")
            else:
                print("Column 'office' already exists.")
                
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate()
