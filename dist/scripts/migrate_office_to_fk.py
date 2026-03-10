import mysql.connector
import os
import sys

# Add parent directory to sys.path to allow importing from 'db'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db_cursor

def migrate_office_to_fk():
    print("====================================================")
    print("   OFFICE COLUMN TO FOREIGN KEY MIGRATION           ")
    print("====================================================")
    
    tables_to_migrate = ['logs', 'csm_form', 'admins']
    
    try:
        with get_db_cursor(commit=True) as cursor:
            # 1. Collect all unique office names from the tables
            unique_names = set()
            for table in tables_to_migrate:
                cursor.execute(f"SELECT DISTINCT office FROM {table} WHERE office IS NOT NULL AND TRIM(office) != ''")
                rows = cursor.fetchall()
                for row in rows:
                    office_val = row['office']
                    if office_val and isinstance(office_val, str):
                        unique_names.add(office_val.strip())
            
            print(f"Found {len(unique_names)} unique office names to ensure in 'offices' table.")
            
            # 2. Ensure all these names exist in 'offices' table
            for name in unique_names:
                cursor.execute("SELECT id FROM offices WHERE name = %s", (name,))
                if not cursor.fetchall():
                    print(f"Adding missing office: '{name}'")
                    cursor.execute("INSERT INTO offices (name, is_active) VALUES (%s, 1)", (name,))
            
            # 3. Create mapping of name -> id
            cursor.execute("SELECT id, name FROM offices")
            offices_mapping = {row['name']: row['id'] for row in cursor.fetchall()}
            
            # 4. Migrate each table
            for table in tables_to_migrate:
                print(f"\n--- Migrating Table: {table} ---")
                
                # Check current structure
                cursor.execute(f"DESCRIBE {table}")
                columns = {col['Field']: col for col in cursor.fetchall()}
                
                # Check if 'office' is already an INT
                if 'office' in columns and 'int' in columns['office']['Type'].lower():
                    print(f"Info: 'office' column in '{table}' is already an INT. Skipping schema changes.")
                else:
                    # a. Add temporary 'office_id' column if it doesn't exist
                    if 'office_id' not in columns:
                        print(f"Action: Adding temporary column 'office_id' to '{table}'...")
                        cursor.execute(f"ALTER TABLE {table} ADD COLUMN office_id INT NULL")
                    
                    # b. Populate 'office_id' based on mapping
                    print(f"Action: Populating 'office_id' based on string migration...")
                    for name, oid in offices_mapping.items():
                        cursor.execute(f"UPDATE {table} SET office_id = %s WHERE office = %s", (oid, name))
                    
                    # c. Handle special cases like indexes
                    if table == 'logs':
                        # logs has idx_logs_office_time_in (office, time_in)
                        print("Action: Updating index for 'logs' table...")
                        cursor.execute("SHOW INDEX FROM logs WHERE Key_name = 'idx_logs_office_time_in'")
                        if cursor.fetchall(): # Consume all index rows
                            cursor.execute("DROP INDEX idx_logs_office_time_in ON logs")
                    
                    # d. Swap columns
                    print(f"Action: Swapping 'office' (string) with 'office_id' (FK)...")
                    cursor.execute(f"ALTER TABLE {table} DROP COLUMN office")
                    cursor.execute(f"ALTER TABLE {table} CHANGE office_id office INT NULL")
                    
                    # e. Add Foreign Key constraint
                    print(f"Action: Adding Foreign Key constraint to '{table}'...")
                    cursor.execute(f"ALTER TABLE {table} ADD CONSTRAINT fk_{table}_office FOREIGN KEY (office) REFERENCES offices(id)")
                    
                    # f. Recreate index for logs
                    if table == 'logs':
                        print("Action: Recreating index for 'logs' table...")
                        cursor.execute("CREATE INDEX idx_logs_office_time_in ON logs(office, time_in)")
                
                print(f"Result: Migration for '{table}' complete.")

    except Exception as e:
        print(f"CRITICAL ERROR during migration: {e}")
        raise

    print("\n====================================================")
    print("Migration Process Finished Successfully.")
    print("====================================================")

if __name__ == "__main__":
    migrate_office_to_fk()
