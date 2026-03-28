import os, sys
sys.path.append(os.getcwd())
# Run the flask app config to get db
from db import get_db_cursor

with get_db_cursor() as cursor:
    cursor.execute("DESCRIBE pds_education")
    for r in cursor.fetchall():
        print(f"{r['Field']} : {r['Type']}")
