"""
PDS Schema Migration Script — Run this to apply the improved PDS table structure.
Usage: python run_migration.py
"""
import mysql.connector
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "hrmo_elog_db"),
}

MIGRATION_SQL = """
ALTER TABLE pds_personal_information
    ADD COLUMN IF NOT EXISTS name_extension  VARCHAR(20)   NULL,
    ADD COLUMN IF NOT EXISTS civil_status    VARCHAR(30)   NULL,
    ADD COLUMN IF NOT EXISTS citizenship     VARCHAR(100)  NULL,
    ADD COLUMN IF NOT EXISTS country         VARCHAR(100)  NULL,
    ADD COLUMN IF NOT EXISTS place_of_birth  VARCHAR(255)  NULL,
    ADD COLUMN IF NOT EXISTS height          VARCHAR(20)   NULL,
    ADD COLUMN IF NOT EXISTS weight          VARCHAR(20)   NULL,
    ADD COLUMN IF NOT EXISTS blood_type      VARCHAR(10)   NULL,
    ADD COLUMN IF NOT EXISTS gsis_no         VARCHAR(50)   NULL,
    ADD COLUMN IF NOT EXISTS pagibig_id      VARCHAR(50)   NULL,
    ADD COLUMN IF NOT EXISTS philhealth_no   VARCHAR(50)   NULL,
    ADD COLUMN IF NOT EXISTS sss_no          VARCHAR(50)   NULL,
    ADD COLUMN IF NOT EXISTS tin_no          VARCHAR(50)   NULL,
    ADD COLUMN IF NOT EXISTS philsys_no      VARCHAR(50)   NULL,
    ADD COLUMN IF NOT EXISTS umid_id         VARCHAR(50)   NULL,
    ADD COLUMN IF NOT EXISTS telephone_no    VARCHAR(30)   NULL,
    ADD COLUMN IF NOT EXISTS residential_house        VARCHAR(100) NULL,
    ADD COLUMN IF NOT EXISTS residential_street       VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS residential_subdivision  VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS residential_barangay     VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS residential_city         VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS residential_province     VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS residential_zip          VARCHAR(10)  NULL,
    ADD COLUMN IF NOT EXISTS permanent_house          VARCHAR(100) NULL,
    ADD COLUMN IF NOT EXISTS permanent_street         VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS permanent_subdivision    VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS permanent_barangay       VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS permanent_city           VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS permanent_province       VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS permanent_zip            VARCHAR(10)  NULL,
    ADD COLUMN IF NOT EXISTS signature_path   VARCHAR(500) NULL,
    ADD COLUMN IF NOT EXISTS pds_excel_path   VARCHAR(500) NULL;

ALTER TABLE pds_spouse
    ADD COLUMN IF NOT EXISTS surname          VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS first_name       VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS middle_name      VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS name_extension   VARCHAR(20)  NULL,
    ADD COLUMN IF NOT EXISTS occupation       VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS employer         VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS business_address VARCHAR(500) NULL,
    ADD COLUMN IF NOT EXISTS telephone_no     VARCHAR(30)  NULL;

ALTER TABLE pds_parents
    ADD COLUMN IF NOT EXISTS father_surname        VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS father_first_name     VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS father_middle_name    VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS father_name_extension VARCHAR(20)  NULL,
    ADD COLUMN IF NOT EXISTS mother_maiden_surname VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS mother_first_name     VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS mother_middle_name    VARCHAR(255) NULL;

ALTER TABLE pds_children
    ADD COLUMN IF NOT EXISTS full_name      VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS date_of_birth  DATE         NULL;

ALTER TABLE pds_education
    ADD COLUMN IF NOT EXISTS level               VARCHAR(50)  NULL,
    ADD COLUMN IF NOT EXISTS school_name         VARCHAR(500) NULL,
    ADD COLUMN IF NOT EXISTS degree_course       VARCHAR(500) NULL,
    ADD COLUMN IF NOT EXISTS from_year           VARCHAR(10)  NULL,
    ADD COLUMN IF NOT EXISTS to_year             VARCHAR(10)  NULL,
    ADD COLUMN IF NOT EXISTS highest_level_units VARCHAR(100) NULL,
    ADD COLUMN IF NOT EXISTS year_graduated      VARCHAR(10)  NULL,
    ADD COLUMN IF NOT EXISTS scholarship_honors  VARCHAR(500) NULL;

ALTER TABLE pds_civil_service_eligibility
    ADD COLUMN IF NOT EXISTS eligibility    VARCHAR(500) NULL,
    ADD COLUMN IF NOT EXISTS rating         VARCHAR(20)  NULL,
    ADD COLUMN IF NOT EXISTS date_of_exam   DATE         NULL,
    ADD COLUMN IF NOT EXISTS place_of_exam  VARCHAR(500) NULL,
    ADD COLUMN IF NOT EXISTS license_number VARCHAR(100) NULL,
    ADD COLUMN IF NOT EXISTS valid_until    DATE         NULL;

ALTER TABLE pds_work_experience
    ADD COLUMN IF NOT EXISTS date_from                  DATE         NULL,
    ADD COLUMN IF NOT EXISTS date_to                    DATE         NULL,
    ADD COLUMN IF NOT EXISTS is_present                 TINYINT(1)   NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS position_title             VARCHAR(500) NULL,
    ADD COLUMN IF NOT EXISTS department_agency_company  VARCHAR(500) NULL,
    ADD COLUMN IF NOT EXISTS monthly_salary             DECIMAL(12,2) NULL,
    ADD COLUMN IF NOT EXISTS salary_job_pay_grade       VARCHAR(50)  NULL,
    ADD COLUMN IF NOT EXISTS status_of_appointment      VARCHAR(100) NULL,
    ADD COLUMN IF NOT EXISTS gov_service                CHAR(1)      NULL;

ALTER TABLE pds_voluntary_work
    ADD COLUMN IF NOT EXISTS organization   VARCHAR(500) NULL,
    ADD COLUMN IF NOT EXISTS date_from      DATE         NULL,
    ADD COLUMN IF NOT EXISTS date_to        DATE         NULL,
    ADD COLUMN IF NOT EXISTS hours          INT          NULL,
    ADD COLUMN IF NOT EXISTS position       VARCHAR(255) NULL;

ALTER TABLE pds_training
    ADD COLUMN IF NOT EXISTS title          VARCHAR(500) NULL,
    ADD COLUMN IF NOT EXISTS date_from      DATE         NULL,
    ADD COLUMN IF NOT EXISTS date_to        DATE         NULL,
    ADD COLUMN IF NOT EXISTS hours          INT          NULL,
    ADD COLUMN IF NOT EXISTS type           VARCHAR(50)  NULL,
    ADD COLUMN IF NOT EXISTS conducted_by   VARCHAR(500) NULL;

ALTER TABLE pds_other_information
    ADD COLUMN IF NOT EXISTS special_skills_hobbies   TEXT NULL,
    ADD COLUMN IF NOT EXISTS non_academic_distinctions TEXT NULL,
    ADD COLUMN IF NOT EXISTS membership_associations  TEXT NULL;

ALTER TABLE pds_declarations
    ADD COLUMN IF NOT EXISTS q34a_answer ENUM('yes','no') NULL,
    ADD COLUMN IF NOT EXISTS q34b_answer ENUM('yes','no') NULL,
    ADD COLUMN IF NOT EXISTS q35a_answer ENUM('yes','no') NULL,
    ADD COLUMN IF NOT EXISTS q35b_answer ENUM('yes','no') NULL,
    ADD COLUMN IF NOT EXISTS q36_answer  ENUM('yes','no') NULL,
    ADD COLUMN IF NOT EXISTS q37_answer  ENUM('yes','no') NULL,
    ADD COLUMN IF NOT EXISTS q38a_answer ENUM('yes','no') NULL,
    ADD COLUMN IF NOT EXISTS q38b_answer ENUM('yes','no') NULL,
    ADD COLUMN IF NOT EXISTS q39_answer  ENUM('yes','no') NULL,
    ADD COLUMN IF NOT EXISTS q40a_answer ENUM('yes','no') NULL,
    ADD COLUMN IF NOT EXISTS q40b_answer ENUM('yes','no') NULL,
    ADD COLUMN IF NOT EXISTS q40c_answer ENUM('yes','no') NULL;

ALTER TABLE pds_references
    ADD COLUMN IF NOT EXISTS full_name  VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS address    VARCHAR(500) NULL,
    ADD COLUMN IF NOT EXISTS contact    VARCHAR(50)  NULL;

ALTER TABLE pds_oath
    ADD COLUMN IF NOT EXISTS government_id          VARCHAR(100) NULL,
    ADD COLUMN IF NOT EXISTS id_number              VARCHAR(100) NULL,
    ADD COLUMN IF NOT EXISTS issuance_date_place    VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS signature              VARCHAR(500) NULL,
    ADD COLUMN IF NOT EXISTS thumbmark              VARCHAR(500) NULL,
    ADD COLUMN IF NOT EXISTS date_signed            DATE         NULL;
"""

INDEX_SQL_STATEMENTS = [
    "CREATE INDEX IF NOT EXISTS idx_pds_pi_name ON pds_personal_information (surname, first_name);",
    "CREATE INDEX IF NOT EXISTS idx_pds_pi_email ON pds_personal_information (email);",
    "CREATE INDEX IF NOT EXISTS idx_pds_pi_employee_no ON pds_personal_information (agency_employee_no);",
    "CREATE INDEX IF NOT EXISTS idx_pds_work_dates ON pds_work_experience (date_from, date_to);",
    "CREATE INDEX IF NOT EXISTS idx_pds_work_is_present ON pds_work_experience (is_present);",
    "CREATE INDEX IF NOT EXISTS idx_pds_edu_level ON pds_education (level);",
    "CREATE INDEX IF NOT EXISTS idx_pds_elig ON pds_civil_service_eligibility (eligibility(100));",
]

def run_migration():
    print(f"Connecting to MySQL at {DB_CONFIG['host']} / db={DB_CONFIG['database']} ...")
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as e:
        print(f"ERROR: Could not connect to MySQL: {e}")
        sys.exit(1)

    cursor = conn.cursor()

    # Run the ALTER TABLE block — split by semicolons and filter
    statements = [s.strip() for s in MIGRATION_SQL.split(';') if s.strip()]
    ok = 0
    fail = 0
    for stmt in statements:
        try:
            cursor.execute(stmt)
            print(f"  OK: {stmt[:70].replace(chr(10), ' ')}...")
            ok += 1
        except mysql.connector.Error as e:
            # Column already exists — not an error
            if e.errno == 1060:  # ER_DUP_FIELDNAME
                print(f"  SKIP (already exists): {stmt[:60].replace(chr(10),' ')}...")
                ok += 1
            else:
                print(f"  FAIL: {e}")
                fail += 1

    # Run index creation separately (errors are non-fatal)
    print("\nCreating performance indexes...")
    for stmt in INDEX_SQL_STATEMENTS:
        try:
            cursor.execute(stmt)
            print(f"  OK: {stmt[:80]}")
        except mysql.connector.Error as e:
            if e.errno == 1061:  # ER_DUP_KEYNAME
                print(f"  SKIP (index already exists): {stmt[:60]}")
            else:
                print(f"  WARN: {e}")

    conn.commit()
    cursor.close()
    conn.close()

    print(f"\n✅  Migration complete: {ok} OK, {fail} failed.")

    if fail > 0:
        print("Some statements failed — check output above.")
        sys.exit(1)

if __name__ == '__main__':
    run_migration()
