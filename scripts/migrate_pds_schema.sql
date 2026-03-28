-- Safe ALTER TABLE to add missing PDS columns (if not exists)
ALTER TABLE pds_personal_information 
ADD COLUMN IF NOT EXISTS civil_status VARCHAR(50),
ADD COLUMN IF NOT EXISTS name
