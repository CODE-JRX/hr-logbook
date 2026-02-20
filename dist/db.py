import mysql.connector
from mysql.connector import pooling
import os
from dotenv import load_dotenv

load_dotenv()

# MySQL Configuration
db_config = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "hrmo_elog_db")
}

# Connection pool — created at startup if MySQL is available,
# otherwise lazily created on first successful get_db() call.
connection_pool = None

def _create_pool():
    """Attempt to create the connection pool. Returns pool or None."""
    try:
        pool = pooling.MySQLConnectionPool(
            pool_name="mypool",
            pool_size=5,
            **db_config
        )
        print("Connection pool created successfully.")
        return pool
    except mysql.connector.Error as err:
        print(f"Error creating connection pool: {err}")
        return None

# Try to create pool at import time
connection_pool = _create_pool()

def get_db():
    """Return a connection from the pool. If pool is None (MySQL was down
    at startup), try to create the pool first so the app auto-recovers
    after MySQL is fixed without needing a restart."""
    global connection_pool
    if connection_pool is None:
        connection_pool = _create_pool()
    if connection_pool:
        return connection_pool.get_connection()
    return None

