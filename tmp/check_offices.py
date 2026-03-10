import os
import sys

# Add parent directory to sys.path to allow importing from 'db'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db_cursor

with get_db_cursor() as cursor:
    print("\n--- TABLE: offices ---")
    cursor.execute("DESCRIBE offices")
    [print(f"{r['Field']}: {r['Type']}") for r in cursor.fetchall()]

    print("\n--- DATA: offices ---")
    cursor.execute("SELECT * FROM offices")
    [print(r) for r in cursor.fetchall()]
