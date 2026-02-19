from models.admin_model import add_admin

def create_admin():
    print("Creating test admin...")
    try:
        # Check if exists first to avoid duplicate error or handle it
        # Actually add_admin might handle it or error out. 
        # ID is auto-increment.
        # email must be unique.
        
        # We'll just try to add.
        # add_admin(first_name, last_name, email, password, face_embeddings, pin)
        # face_embeddings is json, log_model expects list? check definition.
        # definition: def add_admin(first_name, last_name, email, password, face_embeddings, pin):
        
        # We need a dummy embedding or None?
        # schema: face_embedding JSON
        # code: "face_embeddings": json.dumps(face_embeddings)
        
        new_id = add_admin("Test", "Admin", "test@test.com", "password", [], "1234")
        if new_id:
            print(f"Admin created with ID: {new_id}")
        else:
            print("Failed to create admin (maybe already exists?)")
            
    except Exception as e:
        print(f"Error creating admin: {e}")

if __name__ == "__main__":
    create_admin()
