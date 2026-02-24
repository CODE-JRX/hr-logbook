import sys
import importlib

def check_package(package_name):
    print(f"Checking {package_name}...", end=" ")
    try:
        importlib.import_module(package_name)
        print("OK")
        return True
    except ImportError:
        print("MISSING")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    print("--- HRMO E-Logbook Dependency Check ---")
    
    required = ["flask", "mysql.connector", "dotenv", "numpy"]
    optional = ["face_recognition", "face_recognition_models"]
    
    all_ok = True
    print("\nRequired Packages:")
    for pkg in required:
        if not check_package(pkg):
            all_ok = False
            
    print("\nOptional/Feature Packages:")
    for pkg in optional:
        check_package(pkg)
        
    print("\n--- Summary ---")
    if all_ok:
        print("Success: All required dependencies are present.")
    else:
        print("Warning: Some required dependencies are missing. Please check requirements.txt.")
        
    # Check face_recognition specific issue
    try:
        import face_recognition
        print("\nTesting face_recognition model loading...")
        # Just importing it might not be enough if models are missing
        # But usually face_recognition_models is a separate package.
    except Exception as e:
        if "face_recognition_models" in str(e):
            print("CRITICAL: face_recognition_models is missing. You must run:")
            print("pip install git+https://github.com/ageitgey/face_recognition_models")
        else:
            print(f"Face Recognition Error: {e}")

if __name__ == "__main__":
    main()
