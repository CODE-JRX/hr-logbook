import face_recognition
import ast
import reg_emp_v2
import sys

def add_face_encoding_v2(emp_id, image_path):
    # Load the image file
    image = face_recognition.load_image_file(image_path)
    # Compute the face encodings
    encoding = face_recognition.face_encodings(image)[0]
    # Assign the current dictionary to a new dictionary
    known_faces_here = dict(reg_emp_v2.known_faces)
    # Append the new data to the dictionary
    known_faces_here[emp_id] = list(encoding)

    print(known_faces_here)
    # Convert dictionary to Python code string
    dict_str = repr(known_faces_here)

    # Write Python code string to file
    with open('reg_emp_v2.py', 'w') as file:
        file.write(f"known_faces = {dict_str}")
    return 'Success updating reg_emp_v2.py'
# Example usage
#add_face_encoding_v2("36", "Employees/36.jpg")
# Get the parameter from command line argument
emp_id = sys.argv[1]
image_path = sys.argv[2]

# Call the function with the parameters
add_face_encoding_v2(emp_id, image_path)

