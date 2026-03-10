import mysql.connector
import os
import sys

# Add parent directory to sys.path to allow importing from 'db'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db_cursor

def migrate_table_office(table_name, default_value, varchar_len=255):
    """
    Checks for the presence of the 'office' column in a table.
    Adds it if it doesn't exist, and populates NULL or empty entries.
    """
    print(f"\n--- Processing Table: {table_name} ---")
    try:
        with get_db_cursor(commit=True) as cursor:
            # 1. Check if column exists
            cursor.execute(f"SHOW COLUMNS FROM {table_name} LIKE 'office'")
            result = cursor.fetchone()
            
            if not result:
                print(f"Action: Adding column 'office' to '{table_name}'...")
                # Note: For 'logs' and 'csm_form', the schema implies they might already have it,
                # but we ensure it here just in case the physical DB is out of sync.
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN office VARCHAR({varchar_len}) NULL")
                print(f"Result: Column 'office' added successfully.")
            else:
                print(f"Info: Column 'office' already exists in '{table_name}'.")
                
            # 2. Update null or empty rows
            # We also handle rows that might have just spaces or are specifically empty strings
            print(f"Action: Populating empty 'office' rows with '{default_value}'...")
            query = f"UPDATE {table_name} SET office = %s WHERE office IS NULL OR TRIM(office) = ''"
            cursor.execute(query, (default_value,))
            affected = cursor.rowcount
            print(f"Result: Updated {affected} rows.")
            
    except Exception as e:
        print(f"Error: Failed to migrate '{table_name}': {e}")

def run_migrations():
    print("====================================================")
    print("   UNIFIED OFFICE COLUMN MIGRATION & POPULATION     ")
    print("====================================================")
    
    # 1. Admins: Set to 'ASIST/UA'
    migrate_table_office('admins', 'ASIST/UA')
    
    # 2. Logs: Set to 'HUMAN RESOURCE MANAGEMENT UNIT'
    migrate_table_office('logs', 'HUMAN RESOURCE MANAGEMENT UNIT')
    
    # 3. CSM Form: Set to 'HUMAN RESOURCE MANAGEMENT UNIT'
    migrate_table_office('csm_form', 'HUMAN RESOURCE MANAGEMENT UNIT')
    
    print("\n====================================================")
    print("Migration Process Finished.")
    print("====================================================")

if __name__ == "__main__":
    run_migrations()
