# TODO: Add Face Data Encoding to Admin Signup

## Steps to Complete

1. **Update templates/admin/admin_signup.html**
   - Add photo upload section with camera/file upload, similar to clients/add.html
   - Include necessary CSS styles for media-frame, video, canvas
   - Add JavaScript for camera control, face verification, and form validation
   - Make photo required for signup

2. **Update routes/all_routes.py admin_signup route**
   - Handle photo_data from form (data URL)
   - Process face encoding using face_recognition
   - Store face embedding in face_embeddings collection with client_id as admin's id
   - Add error handling for face detection failures
   - Ensure embedding is saved after admin account creation

3. **Test the implementation**
   - Verify photo upload works
   - Check face encoding and storage
   - Ensure admin signup completes with embedding

## Dependent Files
- templates/admin/admin_signup.html
- routes/all_routes.py
- models/face_embedding_model.py (already supports adding embeddings)
- models/admin_model.py (may need to get admin id after creation)

## Followup Steps
- Test admin signup with photo
- Implement face-based admin login (future task)
- Handle edge cases like no face detected

## Completed Steps
- [x] Updated templates/admin/admin_signup.html with photo upload, CSS, and JS
- [x] Updated routes/all_routes.py admin_signup route to handle photo and store embedding
- [x] Tested basic functionality (pending user testing)
