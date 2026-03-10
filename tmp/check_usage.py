import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db_cursor

with get_db_cursor() as cursor:
    print("\n--- Checking Office usage ---")
    for table in ['admins', 'logs', 'csm_form']:
        cursor.execute(f"SELECT COUNT(*) as cnt FROM {table} WHERE office = 19")
        cnt19 = cursor.fetchone()['cnt']
        cursor.execute(f"SELECT COUNT(*) as cnt FROM {table} WHERE office = 20")
        cnt20 = cursor.fetchone()['cnt']
        print(f"Table {table}: ID 19 ({cnt19} rows), ID 20 ({cnt20} rows)")

    cursor.execute("SELECT id, name FROM offices WHERE id IN (19, 20)")
    offices = cursor.fetchall()
    print(f"\nOffices in DB: {offices}")
