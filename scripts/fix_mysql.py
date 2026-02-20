import os
import shutil
import subprocess
import datetime
import sys
import time

def fix_mysql():
    base_path = r"D:\xampp\mysql"
    data_path = os.path.join(base_path, "data")
    backup_path = os.path.join(base_path, "backup")
    start_bat = r"D:\xampp\mysql_start.bat"
    
    print("--- XAMPP MySQL Troubleshooting Script ---")

    # 0. Simple Fix Attempt: Try starting MySQL first
    print("\n[Step 0] Attempting simple fix: Running mysql_start.bat...")
    if os.path.exists(start_bat):
        try:
            # Run the start script
            subprocess.Popen([start_bat], shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
            print("  Waiting 5 seconds for MySQL to start...")
            time.sleep(5)
            
            # Check if mysqld.exe is now running
            check_running = subprocess.run(["tasklist", "/FI", "IMAGENAME eq mysqld.exe"], capture_output=True, text=True)
            if "mysqld.exe" in check_running.stdout:
                print("\nSUCCESS: MySQL started successfully via simple fix!")
                print("No further troubleshooting needed.")
                return
            else:
                print("  MySQL failed to start via simple fix. Proceeding with complex repair...")
        except Exception as e:
            print(f"  Warning: Error trying simple fix: {e}")
    else:
        print(f"  Warning: {start_bat} not found. Skipping simple fix attempt.")
    
    # 1. Stop MySQL if running
    print("\n[Step 1] Stopping MySQL process...")
    try:
        subprocess.run(["taskkill", "/F", "/IM", "mysqld.exe"], capture_output=True)
        print("Done (either stopped or wasn't running).")
    except Exception as e:
        print(f"Warning: Could not stop MySQL: {e}")

    if not os.path.exists(data_path):
        print(f"Error: Path {data_path} does not exist. Check your XAMPP installation.")
        return

    # 2. Rename current data folder
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_data_path = f"{data_path}_old-{timestamp}"
    print(f"\n[Step 2] Renaming 'data' to '{os.path.basename(backup_data_path)}'...")
    try:
        os.rename(data_path, backup_data_path)
        print("Backup created successfully.")
    except Exception as e:
        print(f"Error: Could not rename data folder: {e}")
        print("Make sure no files are open in another program.")
        return

    # 3. Initialize new data folder from backup
    print(f"\n[Step 3] Initializing new 'data' folder from '{os.path.basename(backup_path)}'...")
    try:
        shutil.copytree(backup_path, data_path)
        print("New data folder initialized.")
    except Exception as e:
        print(f"Error: Could not copy backup folder: {e}")
        # Rollback rename if possible? Maybe too complex for a script. 
        return

    # 4. Copy database folders back
    print("\n[Step 4] Restoring database folders from old data...")
    system_folders = {'mysql', 'performance_schema', 'phpmyadmin', 'test', 'sys'}
    
    restored_count = 0
    try:
        for item in os.listdir(backup_data_path):
            item_path = os.path.join(backup_data_path, item)
            
            # If it's a directory and not a system directory, copy it
            if os.path.isdir(item_path) and item.lower() not in system_folders:
                target_path = os.path.join(data_path, item)
                print(f"  Restoring database: {item}")
                shutil.copytree(item_path, target_path, dirs_exist_ok=True)
                restored_count += 1
                
        # 5. Restore ibdata1 (necessary for InnoDB)
        ibdata1_old = os.path.join(backup_data_path, "ibdata1")
        ibdata1_new = os.path.join(data_path, "ibdata1")
        
        if os.path.exists(ibdata1_old):
            print("  Restoring ibdata1 file...")
            shutil.copy2(ibdata1_old, ibdata1_new)
            
        print(f"\nSuccess: {restored_count} database(s) restored.")
        print("\nYou can now try starting MySQL from the XAMPP Control Panel.")
        
    except Exception as e:
        print(f"Error during restoration: {e}")

if __name__ == "__main__":
    if not sys.platform.startswith("win"):
        print("This script is designed for Windows / XAMPP environments.")
        sys.exit(1)
        
    fix_mysql()
