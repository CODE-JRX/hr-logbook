import mysql.connector, os, json
sys.path.append(os.getcwd())
# Run the flask app config to get db
from db import get_db

conn = get_db()
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT * FROM pds_education LIMIT 5")
rows = cursor.fetchall()
print(json.dumps(rows, indent=2))
