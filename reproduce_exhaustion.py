
import sys
import threading
import time
from db import get_db, get_db_cursor

def worker(idx):
    try:
        # Use the new context manager
        with get_db_cursor() as cursor:
            # Re-check that dictionary=True is working
            cursor.execute("SELECT 1 as val")
            res = cursor.fetchone()
            print(f"Worker {idx}: Got connection, test query result: {res}")
            
            # Simulate an error inside the context
            raise RuntimeError("Simulated error inside context")
    except RuntimeError:
        print(f"Worker {idx}: Encountered error (BUT connection should be released by context manager)")
    except Exception as e:
        print(f"Worker {idx}: ERROR - {e}")

threads = []
print("Starting 15 threads to test pool of size 10 (with context manager)...")
for i in range(15):
    t = threading.Thread(target=worker, args=(i,))
    threads.append(t)
    t.start()
    time.sleep(0.1)

for t in threads:
    t.join()

print("\nTest complete.")
print("If all 15 workers reported 'Got connection' and 'Encountered error', the pool is working and connections are being released correctly.")
