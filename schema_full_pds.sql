USE hrmo_elog_db;

-- FULL PDS Schema with all columns
ALTER TABLE pds_personal_information 
ADD COLUMN IF NOT EXISTS civil_status VARCHAR(50),
ADD COLUMN IF NOT EXISTS name_extension VARCHAR(20),
ADD COLUMN IF NOT EXISTS place_of_birth VARCHAR(255),
ADD COLUMN IF NOT EXISTS height VARCHAR(10),
ADD COLUMN IF
