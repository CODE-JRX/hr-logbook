-- ============================================================
-- PDS TABLE SCHEMA IMPROVEMENT MIGRATION
-- UA HRIS / hr-logbook  (Generated: 2026-03-24)
-- ============================================================
-- This migration adds ALL missing columns to every PDS table
-- so that full PDS data from pages 1–4 is correctly stored.
-- Run this ONCE on the existing database. Safe to run again
-- (uses IF NOT EXISTS / only ALTERs if column is missing).
-- ============================================================

-- ============================================================
-- 1. pds_personal_information  (PDS Page 1 — Section I)
-- ============================================================
ALTER TABLE pds_personal_information
    -- Name fields
    ADD COLUMN IF NOT EXISTS name_extension  VARCHAR(20)   NULL COMMENT 'Jr., Sr., III, etc.',
    ADD COLUMN IF NOT EXISTS civil_status    VARCHAR(30)   NULL COMMENT 'Single / Married / Widow / etc.',
    ADD COLUMN IF NOT EXISTS citizenship     VARCHAR(100)  NULL COMMENT 'Philippines / Dual / etc.',
    ADD COLUMN IF NOT EXISTS country         VARCHAR(100)  NULL COMMENT 'Country if dual citizen',
    -- Birth
    ADD COLUMN IF NOT EXISTS place_of_birth  VARCHAR(255)  NULL,
    -- Physical
    ADD COLUMN IF NOT EXISTS height          VARCHAR(20)   NULL COMMENT 'in meters',
    ADD COLUMN IF NOT EXISTS weight          VARCHAR(20)   NULL COMMENT 'in kg',
    ADD COLUMN IF NOT EXISTS blood_type      VARCHAR(10)   NULL,
    -- Government IDs
    ADD COLUMN IF NOT EXISTS gsis_no         VARCHAR(50)   NULL,
    ADD COLUMN IF NOT EXISTS pagibig_id      VARCHAR(50)   NULL,
    ADD COLUMN IF NOT EXISTS philhealth_no   VARCHAR(50)   NULL,
    ADD COLUMN IF NOT EXISTS sss_no          VARCHAR(50)   NULL,
    ADD COLUMN IF NOT EXISTS tin_no          VARCHAR(50)   NULL,
    ADD COLUMN IF NOT EXISTS philsys_no      VARCHAR(50)   NULL,
    ADD COLUMN IF NOT EXISTS umid_id         VARCHAR(50)   NULL,
    ADD COLUMN IF NOT EXISTS telephone_no    VARCHAR(30)   NULL,
    -- Residential Address
    ADD COLUMN IF NOT EXISTS residential_house        VARCHAR(100) NULL,
    ADD COLUMN IF NOT EXISTS residential_street       VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS residential_subdivision  VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS residential_barangay     VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS residential_city         VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS residential_province     VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS residential_zip          VARCHAR(10)  NULL,
    -- Permanent Address
    ADD COLUMN IF NOT EXISTS permanent_house          VARCHAR(100) NULL,
    ADD COLUMN IF NOT EXISTS permanent_street         VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS permanent_subdivision    VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS permanent_barangay       VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS permanent_city           VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS permanent_province       VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS permanent_zip            VARCHAR(10)  NULL,
    -- File paths
    ADD COLUMN IF NOT EXISTS signature_path   VARCHAR(500) NULL,
    ADD COLUMN IF NOT EXISTS pds_excel_path   VARCHAR(500) NULL;


-- ============================================================
-- 2. pds_spouse  (PDS Page 1 — Section II, Item 22)
-- ============================================================
ALTER TABLE pds_spouse
    ADD COLUMN IF NOT EXISTS surname          VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS first_name       VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS middle_name      VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS name_extension   VARCHAR(20)  NULL,
    ADD COLUMN IF NOT EXISTS occupation       VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS employer         VARCHAR(255) NULL COMMENT 'Employer/Business Name',
    ADD COLUMN IF NOT EXISTS business_address VARCHAR(500) NULL,
    ADD COLUMN IF NOT EXISTS telephone_no     VARCHAR(30)  NULL,
    ADD COLUMN IF NOT EXISTS updated_at       TIMESTAMP    NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;


-- ============================================================
-- 3. pds_parents  (PDS Page 1 — Section II, Items 24 & 25)
-- ============================================================
ALTER TABLE pds_parents
    ADD COLUMN IF NOT EXISTS father_surname        VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS father_first_name     VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS father_middle_name    VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS father_name_extension VARCHAR(20)  NULL,
    ADD COLUMN IF NOT EXISTS mother_maiden_surname VARCHAR(255) NULL COMMENT 'Mother maiden (birth) surname',
    ADD COLUMN IF NOT EXISTS mother_first_name     VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS mother_middle_name    VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS updated_at            TIMESTAMP    NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;


-- ============================================================
-- 4. pds_children  (PDS Page 1 — Section II, Item 23)
-- ============================================================
ALTER TABLE pds_children
    ADD COLUMN IF NOT EXISTS full_name      VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS date_of_birth  DATE         NULL;


-- ============================================================
-- 5. pds_education  (PDS Page 1 — Section III, Item 26)
-- ============================================================
ALTER TABLE pds_education
    ADD COLUMN IF NOT EXISTS level               VARCHAR(50)  NULL COMMENT 'ELEMENTARY/SECONDARY/VOCATIONAL/COLLEGE/GRADUATE STUDIES',
    ADD COLUMN IF NOT EXISTS school_name         VARCHAR(500) NULL,
    ADD COLUMN IF NOT EXISTS degree_course       VARCHAR(500) NULL COMMENT 'Basic Education / Degree / Course',
    ADD COLUMN IF NOT EXISTS from_year           VARCHAR(10)  NULL COMMENT '4-digit year',
    ADD COLUMN IF NOT EXISTS to_year             VARCHAR(10)  NULL COMMENT '4-digit year or PRESENT',
    ADD COLUMN IF NOT EXISTS highest_level_units VARCHAR(100) NULL COMMENT 'Highest Level/Units Earned (if not graduated)',
    ADD COLUMN IF NOT EXISTS year_graduated      VARCHAR(10)  NULL COMMENT '4-digit year',
    ADD COLUMN IF NOT EXISTS scholarship_honors  VARCHAR(500) NULL;


-- ============================================================
-- 6. pds_civil_service_eligibility  (PDS Page 2 — Section IV, Item 27)
-- ============================================================
ALTER TABLE pds_civil_service_eligibility
    ADD COLUMN IF NOT EXISTS eligibility    VARCHAR(500) NULL COMMENT 'Career service / RA number / etc.',
    ADD COLUMN IF NOT EXISTS rating         VARCHAR(20)  NULL,
    ADD COLUMN IF NOT EXISTS date_of_exam   DATE         NULL,
    ADD COLUMN IF NOT EXISTS place_of_exam  VARCHAR(500) NULL,
    ADD COLUMN IF NOT EXISTS license_number VARCHAR(100) NULL,
    ADD COLUMN IF NOT EXISTS valid_until    DATE         NULL COMMENT 'License validity date';


-- ============================================================
-- 7. pds_work_experience  (PDS Page 2 — Section V, Item 28)
-- ============================================================
ALTER TABLE pds_work_experience
    ADD COLUMN IF NOT EXISTS date_from                  DATE         NULL,
    ADD COLUMN IF NOT EXISTS date_to                    DATE         NULL COMMENT 'NULL means PRESENT',
    ADD COLUMN IF NOT EXISTS is_present                 TINYINT(1)   NOT NULL DEFAULT 0 COMMENT '1 = currently working here',
    ADD COLUMN IF NOT EXISTS position_title             VARCHAR(500) NULL,
    ADD COLUMN IF NOT EXISTS department_agency_company  VARCHAR(500) NULL,
    ADD COLUMN IF NOT EXISTS monthly_salary             DECIMAL(12,2) NULL,
    ADD COLUMN IF NOT EXISTS salary_job_pay_grade       VARCHAR(50)  NULL COMMENT 'Pay grade / Step increment',
    ADD COLUMN IF NOT EXISTS status_of_appointment      VARCHAR(100) NULL COMMENT 'Permanent / Temporary / Casual / etc.',
    ADD COLUMN IF NOT EXISTS gov_service                CHAR(1)      NULL COMMENT 'Y or N';


-- ============================================================
-- 8. pds_voluntary_work  (PDS Page 3 — Section VI, Item 29)
-- ============================================================
ALTER TABLE pds_voluntary_work
    ADD COLUMN IF NOT EXISTS organization   VARCHAR(500) NULL,
    ADD COLUMN IF NOT EXISTS date_from      DATE         NULL,
    ADD COLUMN IF NOT EXISTS date_to        DATE         NULL,
    ADD COLUMN IF NOT EXISTS hours          INT          NULL COMMENT 'Number of hours',
    ADD COLUMN IF NOT EXISTS position       VARCHAR(255) NULL COMMENT 'Nature of work / position held';


-- ============================================================
-- 9. pds_training  (PDS Page 3 — Section VII, Item 30)
-- ============================================================
ALTER TABLE pds_training
    ADD COLUMN IF NOT EXISTS title          VARCHAR(500) NULL COMMENT 'Title of L&D Intervention / Training Programs',
    ADD COLUMN IF NOT EXISTS date_from      DATE         NULL,
    ADD COLUMN IF NOT EXISTS date_to        DATE         NULL,
    ADD COLUMN IF NOT EXISTS hours          INT          NULL COMMENT 'Number of hours',
    ADD COLUMN IF NOT EXISTS type           VARCHAR(50)  NULL COMMENT 'Managerial / Supervisory / Technical / etc.',
    ADD COLUMN IF NOT EXISTS conducted_by   VARCHAR(500) NULL COMMENT 'Conducted/Sponsored By';


-- ============================================================
-- 10. pds_other_information  (PDS Page 3 — Section VIII, Items 31–33)
-- ============================================================
ALTER TABLE pds_other_information
    ADD COLUMN IF NOT EXISTS special_skills_hobbies   TEXT NULL COMMENT 'Item 31: Special Skills and Hobbies (comma-separated)',
    ADD COLUMN IF NOT EXISTS non_academic_distinctions TEXT NULL COMMENT 'Item 32: Non-Academic Distinctions/Recognition',
    ADD COLUMN IF NOT EXISTS membership_associations  TEXT NULL COMMENT 'Item 33: Membership in Association/Organization',
    ADD COLUMN IF NOT EXISTS updated_at               TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;


-- ============================================================
-- 11. pds_declarations  — already has good columns from latest schema
--     but we add missing YES/NO boolean columns for reporting
-- ============================================================
ALTER TABLE pds_declarations
    ADD COLUMN IF NOT EXISTS q34a_answer ENUM('yes','no') NULL COMMENT 'Related to appointing authority 3rd degree',
    ADD COLUMN IF NOT EXISTS q34b_answer ENUM('yes','no') NULL COMMENT 'Related to appointing authority 4th degree',
    ADD COLUMN IF NOT EXISTS q35a_answer ENUM('yes','no') NULL COMMENT 'Admin offense found guilty',
    ADD COLUMN IF NOT EXISTS q35b_answer ENUM('yes','no') NULL COMMENT 'Criminally charged',
    ADD COLUMN IF NOT EXISTS q36_answer  ENUM('yes','no') NULL COMMENT 'Convicted of any crime',
    ADD COLUMN IF NOT EXISTS q37_answer  ENUM('yes','no') NULL COMMENT 'Separated from service',
    ADD COLUMN IF NOT EXISTS q38a_answer ENUM('yes','no') NULL COMMENT 'Candidate in any election',
    ADD COLUMN IF NOT EXISTS q38b_answer ENUM('yes','no') NULL COMMENT 'Resigned to campaign',
    ADD COLUMN IF NOT EXISTS q39_answer  ENUM('yes','no') NULL COMMENT 'Immigrant status',
    ADD COLUMN IF NOT EXISTS q40a_answer ENUM('yes','no') NULL COMMENT 'IP/Indigenous group member',
    ADD COLUMN IF NOT EXISTS q40b_answer ENUM('yes','no') NULL COMMENT 'PWD',
    ADD COLUMN IF NOT EXISTS q40c_answer ENUM('yes','no') NULL COMMENT 'Solo parent';


-- ============================================================
-- 12. pds_references  (PDS Page 4 — Item 41)
-- ============================================================
ALTER TABLE pds_references
    ADD COLUMN IF NOT EXISTS full_name  VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS address    VARCHAR(500) NULL,
    ADD COLUMN IF NOT EXISTS contact    VARCHAR(50)  NULL COMMENT 'Telephone or mobile number';


-- ============================================================
-- 13. pds_oath  (PDS Page 4 — Item 42 + Oath section)
-- ============================================================
ALTER TABLE pds_oath
    ADD COLUMN IF NOT EXISTS government_id          VARCHAR(100) NULL COMMENT 'Government-issued ID type (Passport, GSIS, SSS, etc.)',
    ADD COLUMN IF NOT EXISTS id_number              VARCHAR(100) NULL COMMENT 'ID Number',
    ADD COLUMN IF NOT EXISTS issuance_date_place    VARCHAR(255) NULL COMMENT 'Date and Place of Issuance',
    ADD COLUMN IF NOT EXISTS signature              VARCHAR(500) NULL COMMENT 'Path to uploaded signature image',
    ADD COLUMN IF NOT EXISTS thumbmark              VARCHAR(500) NULL COMMENT 'Path to uploaded thumbmark image',
    ADD COLUMN IF NOT EXISTS date_signed            DATE         NULL COMMENT 'Date signed by employee',
    ADD COLUMN IF NOT EXISTS updated_at             TIMESTAMP    NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;


-- ============================================================
-- USEFUL INDEXES for reporting / search performance
-- ============================================================

-- Index for employee search by name/email/id
CREATE INDEX IF NOT EXISTS idx_pds_pi_name
    ON pds_personal_information (surname, first_name);

CREATE INDEX IF NOT EXISTS idx_pds_pi_email
    ON pds_personal_information (email);

CREATE INDEX IF NOT EXISTS idx_pds_pi_employee_no
    ON pds_personal_information (agency_employee_no);

-- Index for work experience date range queries
CREATE INDEX IF NOT EXISTS idx_pds_work_dates
    ON pds_work_experience (date_from, date_to);

CREATE INDEX IF NOT EXISTS idx_pds_work_is_present
    ON pds_work_experience (is_present);

-- Index for education level look-up
CREATE INDEX IF NOT EXISTS idx_pds_edu_level
    ON pds_education (level);

-- Index for eligibility queries
CREATE INDEX IF NOT EXISTS idx_pds_elig
    ON pds_civil_service_eligibility (eligibility(100));

-- ============================================================
-- VERIFICATION: show final column lists (for manual check)
-- ============================================================
-- After running this migration you can verify with:
--   DESCRIBE pds_personal_information;
--   DESCRIBE pds_spouse;
--   DESCRIBE pds_parents;
--   DESCRIBE pds_children;
--   etc.
-- ============================================================
