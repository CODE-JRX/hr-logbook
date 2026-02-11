# TODO: Implement Backend Support for Face Encoding in Admin Signup

## Completed Tasks
- [x] Update `models/admin_model.py`: Modify `add_admin` to accept `embedding_list` parameter and store it in the admin document.
- [x] Update `routes/all_routes.py`: In `admin_signup` POST handler, process `photo_data`, save image to "Admins" directory, compute face encoding, and pass to `add_admin`.
- [x] Add validation for required photo in `admin_signup` route.
- [x] Add `find_best_admin_match` function in `models/admin_model.py`.
- [x] Add `/admin/face_login` route in `routes/all_routes.py`.
- [x] Update `templates/admin/login.html` to make face login the default option.

## Followup Steps
- [ ] Install face_recognition_models dependency (in progress).
- [ ] Test admin signup with photo upload.
- [ ] Verify photo file saved in "Admins" directory.
- [ ] Check database for embedding in `admins` collection.
- [ ] Test face login functionality.
