import os, sys, json
sys.path.append(os.getcwd())

def parse_env():
    env = {}
    with open('.env') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                k, v = line.split('=', 1)
                env[k.strip()] = v.strip().strip("'\"")
    return env

env = parse_env()
import mysql.connector

conn = mysql.connector.connect(
    host=env.get('MYSQL_HOST', 'localhost'),
    user=env.get('MYSQL_USER', 'root'),
    password=env.get('MYSQL_PASSWORD', ''),
    database=env.get('MYSQL_DATABASE', 'hrmo_elog_db')
)

cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT * FROM pds_education LIMIT 5")
print("ROWS DUMP:")
for r in cursor.fetchall():
    print(r)
cursor.close()
conn.close()
