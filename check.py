
import sys
sys.path.append('.')
from db import get_db_cursor
with get_db_cursor() as cursor:
    cursor.execute('DESCRIBE pds_education')
    print([row['Field'] for row in cursor.fetchall()])
    
    cursor.execute('SELECT * FROM pds_education LIMIT 3')
    print(cursor.fetchall())
