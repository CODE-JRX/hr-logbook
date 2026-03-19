import sys
import json
sys.path.append('.')
from db import get_db_cursor

tables = ['pds_spouse', 'pds_parents', 'pds_children', 'pds_education', 'pds_work_experience', 'pds_civil_service_eligibility']

res = {}
with get_db_cursor() as cursor:
    for table in tables:
        cursor.execute(f"DESCRIBE {table}")
        res[table] = [row['Field'] for row in cursor.fetchall()]

with open('schema_out.txt', 'w') as f:
    json.dump(res, f, indent=2)
