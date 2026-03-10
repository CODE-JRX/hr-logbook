import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db_cursor

def merge_offices():
    """Consolidates 'HUMAN RESOURCE MANAGEMENT UNIT' into 'HUMAN RESOURCE MANAGEMENT OFFICE'."""
    with get_db_cursor(commit=True) as cursor:
        print("\n--- Merging Office IDs ---")
        
        # 1. Get IDs
        cursor.execute("SELECT id FROM offices WHERE name = 'HUMAN RESOURCE MANAGEMENT UNIT'")
        unit_res = cursor.fetchone()
        cursor.execute("SELECT id FROM offices WHERE name = 'HUMAN RESOURCE MANAGEMENT OFFICE'")
        office_res = cursor.fetchone()
        
        if not unit_res:
            print("UNIT office not found, maybe already renamed?")
            return
            
        unit_id = unit_res['id']
        
        if not office_res:
            print("Action: Renaming UNIT to OFFICE in offices table...")
            cursor.execute("UPDATE offices SET name = 'HUMAN RESOURCE MANAGEMENT OFFICE' WHERE id = %s", (unit_id,))
            print(f"Renamed office ID {unit_id} to 'HUMAN RESOURCE MANAGEMENT OFFICE'")
        else:
            office_id = office_res['id']
            print(f"Action: Merging records from ID {unit_id} (UNIT) into ID {office_id} (OFFICE)...")
            
            for table in ['admins', 'logs', 'csm_form']:
                cursor.execute(f"UPDATE {table} SET office = %s WHERE office = %s", (office_id, unit_id))
                affected = cursor.rowcount
                if affected > 0:
                    print(f"   Updated {affected} rows in {table}")
            
            print(f"Action: Deleting duplicate office entry (ID {unit_id})...")
            cursor.execute("DELETE FROM offices WHERE id = %s", (unit_id,))
            print(f"Deleted office entry ID {unit_id}")

    print("\nMerge complete.")

if __name__ == "__main__":
    merge_offices()
