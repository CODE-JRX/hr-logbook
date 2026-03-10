import mysql.connector
import os
import sys

# Add parent directory to sys.path to allow importing from 'db'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db_cursor

def ensure_office_exists(cursor, office_name):
    """Ensures an office exists in the offices table and returns its ID."""
    if not office_name: return None
    cursor.execute("SELECT id FROM offices WHERE name = %s", (office_name.strip().upper(),))
    row = cursor.fetchone()
    if row:
        return row['id']
    else:
        print(f"Action: Creating missing office entry for '{office_name}'...")
        # Special handling for Super Admin to keep established ID 1
        if office_name.upper() == 'SUPER ADMIN':
            try:
                cursor.execute("INSERT INTO offices (id, name, is_active) VALUES (1, %s, 1)", (office_name.upper(),))
                return 1
            except:
                cursor.execute("INSERT INTO offices (name, is_active) VALUES (%s, 1)", (office_name.upper(),))
                return cursor.lastrowid
        else:
            cursor.execute("INSERT INTO offices (name, is_active) VALUES (%s, 1)", (office_name.upper(),))
            return cursor.lastrowid

def migrate_table_office(table_name, default_office_name):
    print(f"\n--- Migrating Table: {table_name} ---")
    try:
        with get_db_cursor(commit=True) as cursor:
            # 1. Ensure column exists
            cursor.execute(f"DESCRIBE {table_name}")
            columns = {col['Field']: col for col in cursor.fetchall()}
            
            if 'office' not in columns:
                print(f"Action: Adding 'office' column to {table_name}...")
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN office VARCHAR(255) NULL")
                cursor.execute(f"DESCRIBE {table_name}")
                columns = {col['Field']: col for col in cursor.fetchall()}

            col_type = columns['office']['Type'].lower()
            
            # 2. If it's VARCHAR, we need to convert names to IDs
            if 'varchar' in col_type:
                print(f"Action: Converting string names to IDs in {table_name}...")
                cursor.execute(f"SELECT DISTINCT office FROM {table_name} WHERE office IS NOT NULL AND office != ''")
                distinct_offices = [row['office'] for row in cursor.fetchall()]
                
                for office_val in distinct_offices:
                    if not str(office_val).isdigit():
                        oid = ensure_office_exists(cursor, office_val)
                        if oid:
                            cursor.execute(f"UPDATE {table_name} SET office = %s WHERE office = %s", (oid, office_val))
                            print(f"   Converted '{office_val}' -> ID {oid}")

                # 3. Change column type to INT
                print(f"Action: Changing column type to INT for {table_name}...")
                # We use SET FOREIGN_KEY_CHECKS = 0 in case there are constraints
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
                cursor.execute(f"ALTER TABLE {table_name} MODIFY COLUMN office INT NULL")
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            
            # 4. Populate Defaults
            target_id = ensure_office_exists(cursor, default_office_name)
            cursor.execute(f"UPDATE {table_name} SET office = %s WHERE office IS NULL", (target_id,))
            affected = cursor.rowcount
            if affected > 0:
                print(f"Action: Populated {affected} empty rows with default ID {target_id} ({default_office_name})")

            print(f"Success: {table_name} is up to date.")

    except Exception as e:
        print(f"Error migrating {table_name}: {e}")

def run_migrations():
    print("====================================================")
    print("   PRODUCTION-READY OFFICE MIGRATION (UPSCALE)      ")
    print("====================================================")
    
    # Order matters: admins first
    migrate_table_office('admins', 'SUPER ADMIN')
    migrate_table_office('logs', 'HUMAN RESOURCE MANAGEMENT OFFICE')
    migrate_table_office('csm_form', 'HUMAN RESOURCE MANAGEMENT OFFICE')
    
    print("\n====================================================")
    print("Migration Finished Successfully.")
    print("====================================================")

if __name__ == "__main__":
    run_migrations()
