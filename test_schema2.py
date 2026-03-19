import sys
import json
sys.path.append('.')
from db import get_db_cursor

tables = ['pds_voluntary_work', 'pds_training', 'pds_other_information', 'pds_declarations', 'pds_references', 'pds_oath']

res = {}
with get_db_cursor() as cursor:
    for table in tables:
        cursor.execute(f"DESCRIBE {table}")
        res[table] = [row['Field'] for row in cursor.fetchall()]

with open('schema_out2.txt', 'w') as f:
    json.dump(res, f, indent=2)
