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
            pool_size=10,
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

from contextlib import contextmanager

@contextmanager
def get_db_cursor(commit=False):
    """
    Context manager to get a database connection and cursor.
    Ensures that the connection is closed (returned to pool) even if an exception occurs.
    
    Usage:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(...)
            # commit happens automatically if no error
            
        with get_db_cursor() as cursor:
            cursor.execute(...)
            result = cursor.fetchall()
            # connection closed automatically
    """
    connection = get_db()
    if connection is None:
        raise Exception("Failed to get database connection")
        
    cursor = connection.cursor(dictionary=True)
    try:
        yield cursor
        if commit:
            connection.commit()
    except Exception:
        if commit:
            connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


