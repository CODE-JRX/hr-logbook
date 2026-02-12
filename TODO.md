# TODO: Ensure all string data stored in database is uppercase

## Tasks
- [x] Modify `add_client` in `models/client_model.py` to convert string parameters to uppercase
- [x] Modify `update_client` in `models/client_model.py` to convert string values in fields to uppercase
- [x] Modify `add_admin` in `models/admin_model.py` to convert first_name, last_name, email to uppercase
- [x] Modify `insert_csm_form` in `models/csm_form_model.py` to convert all string fields to uppercase
- [x] Modify `add_time_in` in `models/log_model.py` to convert client_id, purpose, additional_info to uppercase
- [x] Modify `add_face_embedding` in `models/face_embedding_model.py` to convert client_id to uppercase
- [x] Test the changes by running the application and verifying data in database
