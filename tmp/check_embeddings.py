import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db_cursor

with get_db_cursor() as cursor:
    print("\n--- TABLE: face_embeddings ---")
    cursor.execute("DESCRIBE face_embeddings")
    [print(f"{r['Field']}: {r['Type']}") for r in cursor.fetchall()]

    print("\n--- DATA: face_embeddings (limit 1) ---")
    cursor.execute("SELECT * FROM face_embeddings LIMIT 1")
    [print(r) for r in cursor.fetchall()]
