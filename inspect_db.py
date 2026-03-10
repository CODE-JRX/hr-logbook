import os
import sys

# Add current directory to sys.path to allow importing from 'db'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import get_db_cursor

tables = ['logs']
for table in tables:
    print(f"--- Schema for {table} ---")
    try:
        with get_db_cursor() as cursor:
            cursor.execute(f"DESCRIBE {table}")
            info = cursor.fetchall()
            for col in info:
                print(col)
            
            cursor.execute(f"SHOW CREATE TABLE {table}")
            sql = cursor.fetchone()
            if sql:
                # SHOW CREATE TABLE returns a dictionary or tuple depending on cursor type
                # get_db_cursor uses dictionary=True
                create_sql = sql.get('Create Table') or sql[1]
                print(create_sql)
    except Exception as e:
        print(f"Error inspecting {table}: {e}")
    print("\n")
