#import cv2
import face_recognition
import reg_emp_v2
import sys

def identify_faces(image_path):
    # Load the image
    frame = cv2.imread(image_path)
    final_emp_id = None
    if frame is None:
        print("Error reading image")
        return None
    # Convert the image to RGB
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # Resize the frame for better performance
    resized_frame = cv2.resize(frame, (640, 480))
    # Find all face locations and face encodings in the current frame
    face_locations = face_recognition.face_locations(resized_frame)
    face_encodings = face_recognition.face_encodings(resized_frame, face_locations)
    # Initialize variables
    known_face_detected = False
    # Draw rectangles around the detected faces
    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        #cv2.rectangle(resized_frame, (left, top), (right, bottom), (0, 255, 0), 2)
        # Initialize face_encoding_matched before the loop
        face_encoding_matched = False
        # Check if a known face is detected
        for emp_id, known_encoding in reg_emp_v2.known_faces.items():
            match = face_recognition.compare_faces([known_encoding], face_encoding, tolerance=0.4)  # Adjust tolerance as needed
            if match and match[0]:
                known_face_detected = True
                face_encoding_matched = True
                final_emp_id = emp_id
                break
        # Check if a known face was not detected
        if not face_encoding_matched:
            known_face_detected = False
    # Display employee information or "Unknown Face Detected"
    if known_face_detected:
        return final_emp_id
    else:
        return "Unknown Face Detected!"

# Get the parameter from command line argument
param = sys.argv[1]
print(identify_faces(param))
