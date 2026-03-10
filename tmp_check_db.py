from db import get_db_cursor
try:
    with get_db_cursor() as cursor:
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print("Tables in database:")
        for table in tables:
            print(table)
except Exception as e:
    print(f"Error: {e}")
