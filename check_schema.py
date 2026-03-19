import mysql.connector

try:
    conn = mysql.connector.connect(host="localhost", user="root", password="", database="hr_logbook")
    cursor = conn.cursor()
    
    tables = [
        'pds_work_experience', 'pds_civil_service_eligibility', 
        'pds_education', 'pds_voluntary_work', 'pds_training'
    ]
    
    for table in tables:
        print(f"\n--- {table} ---")
        cursor.execute(f"DESC {table}")
        for row in cursor.fetchall():
            print(row[0])
            
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
