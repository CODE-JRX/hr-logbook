from db import get_db_cursor
try:
    with get_db_cursor() as cursor:
        cursor.execute("DESCRIBE offices")
        print("Offices Table Structure:")
        for row in cursor.fetchall():
            print(row)
        
        cursor.execute("SELECT * FROM offices")
        print("\nOffices Table Content:")
        for row in cursor.fetchall():
            print(row)
except Exception as e:
    print(f"Error: {e}")
