CREATE DATABASE IF NOT EXISTS hrmo_elog_db;
USE hrmo_elog_db;

-- ============================================================
-- CORE TABLES
-- ============================================================

-- Offices Table
CREATE TABLE IF NOT EXISTS offices (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(255) NOT NULL UNIQUE,
    is_active  TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Seed default offices
INSERT IGNORE INTO offices (id, name, is_active) VALUES (1, 'SUPER ADMIN', 1);

-- Admins Table
CREATE TABLE IF NOT EXISTS admins (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    first_name     VARCHAR(255) NOT NULL,
    last_name      VARCHAR(255) NOT NULL,
    email          VARCHAR(255) UNIQUE NOT NULL,
    password_hash  VARCHAR(255) NOT NULL,
    pin_hash       VARCHAR(255) NULL,
    office         INT NULL,
    face_embedding LONGTEXT,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (office) REFERENCES offices(id) ON DELETE SET NULL
);

-- Clients Table
CREATE TABLE IF NOT EXISTS clients (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    client_id   VARCHAR(50) UNIQUE NOT NULL,
    full_name   VARCHAR(255) NOT NULL,
    fname       VARCHAR(100) NULL,
    lname       VARCHAR(100) NULL,
    mi          VARCHAR(10)  NULL,
    name_ext    VARCHAR(20)  NULL,
    department  VARCHAR(255),
    gender      VARCHAR(20),
    age         INT,
    client_type VARCHAR(50)
);

-- CSM Form Table
CREATE TABLE IF NOT EXISTS csm_form (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    control_no              VARCHAR(50) UNIQUE NOT NULL,
    date                    DATE NOT NULL,
    office                  INT,
    client_type             VARCHAR(50),
    sex                     VARCHAR(20),
    age                     INT,
    region_of_residence     VARCHAR(255),
    email                   VARCHAR(255),
    service_availed         VARCHAR(255),
    awareness_of_cc         INT,
    cc_of_this_office_was   INT,
    cc_help_you             INT,
    sdq0 INT, sdq1 INT, sdq2 INT, sdq3 INT, sdq4 INT,
    sdq5 INT, sdq6 INT, sdq7 INT, sdq8 INT,
    suggestion              TEXT,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (office) REFERENCES offices(id) ON DELETE SET NULL
);

-- Face Embeddings Table
CREATE TABLE IF NOT EXISTS face_embeddings (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    client_id       VARCHAR(50) NOT NULL,
    embedding_json  LONGTEXT NOT NULL,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
);

-- Logs Table
CREATE TABLE IF NOT EXISTS logs (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    client_id       VARCHAR(50) NOT NULL,
    time_in         DATETIME NOT NULL,
    time_out        DATETIME NULL,
    purpose         VARCHAR(255),
    additional_info TEXT,
    office          INT NULL,
    FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE,
    FOREIGN KEY (office) REFERENCES offices(id) ON DELETE SET NULL
);


-- ============================================================
-- PDS TABLES  (Philippine Government CS Form 212 – Pages 1–4)
-- ============================================================

-- ------------------------------------------------------------
-- PDS Page 1 — Section I: Personal Information
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pds_personal_information (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    -- Name
    surname                 VARCHAR(255) NULL,
    first_name              VARCHAR(255) NULL,
    middle_name             VARCHAR(255) NULL,
    name_extension          VARCHAR(20)  NULL COMMENT 'Jr., Sr., III, etc.',
    -- Birth & Identity
    date_of_birth           DATE         NULL,
    place_of_birth          VARCHAR(255) NULL,
    sex                     VARCHAR(10)  NULL COMMENT 'Male / Female',
    civil_status            VARCHAR(30)  NULL COMMENT 'Single / Married / Widow / Widower / Separated / Solo Parent / Others',
    citizenship             VARCHAR(100) NULL COMMENT 'Philippines / Dual / etc.',
    country                 VARCHAR(100) NULL COMMENT 'Country if dual citizen',
    -- Physical
    height                  VARCHAR(20)  NULL COMMENT 'in meters, e.g. 1.73',
    weight                  VARCHAR(20)  NULL COMMENT 'in kg, e.g. 65',
    blood_type              VARCHAR(10)  NULL,
    -- Government ID Numbers
    gsis_no                 VARCHAR(50)  NULL,
    pagibig_id              VARCHAR(50)  NULL,
    philhealth_no           VARCHAR(50)  NULL,
    sss_no                  VARCHAR(50)  NULL,
    tin_no                  VARCHAR(50)  NULL,
    philsys_no              VARCHAR(50)  NULL COMMENT 'Philippine Identification System (PhilSys) ID No.',
    umid_id                 VARCHAR(50)  NULL COMMENT 'UMID / CRN No.',
    agency_employee_no      VARCHAR(100) NULL,
    -- Contact
    telephone_no            VARCHAR(30)  NULL,
    mobile_no               VARCHAR(30)  NULL,
    email                   VARCHAR(255) NULL,
    -- Residential Address (Item 17)
    residential_house       VARCHAR(100) NULL COMMENT 'House/Block/Lot No.',
    residential_street      VARCHAR(255) NULL,
    residential_subdivision VARCHAR(255) NULL,
    residential_barangay    VARCHAR(255) NULL,
    residential_city        VARCHAR(255) NULL COMMENT 'City/Municipality',
    residential_province    VARCHAR(255) NULL,
    residential_zip         VARCHAR(10)  NULL COMMENT 'ZIP Code',
    -- Permanent Address (Item 18)
    permanent_house         VARCHAR(100) NULL COMMENT 'House/Block/Lot No.',
    permanent_street        VARCHAR(255) NULL,
    permanent_subdivision   VARCHAR(255) NULL,
    permanent_barangay      VARCHAR(255) NULL,
    permanent_city          VARCHAR(255) NULL COMMENT 'City/Municipality',
    permanent_province      VARCHAR(255) NULL,
    permanent_zip           VARCHAR(10)  NULL COMMENT 'ZIP Code',
    -- File attachments
    signature_path          VARCHAR(500) NULL COMMENT 'Path to uploaded signature image',
    pds_excel_path          VARCHAR(500) NULL COMMENT 'Path to uploaded CS Form 212 Excel file',
    -- Audit
    created_at              TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    -- Indexes
    INDEX idx_pds_pi_name        (surname, first_name),
    INDEX idx_pds_pi_email       (email),
    INDEX idx_pds_pi_employee_no (agency_employee_no)
);


-- ------------------------------------------------------------
-- PDS Page 1 — Section II, Item 22: Spouse Information
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pds_spouse (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    personal_info_id INT NOT NULL,
    surname          VARCHAR(255) NULL,
    first_name       VARCHAR(255) NULL,
    middle_name      VARCHAR(255) NULL,
    name_extension   VARCHAR(20)  NULL,
    occupation       VARCHAR(255) NULL,
    employer         VARCHAR(255) NULL COMMENT 'Employer/Business Name',
    business_address VARCHAR(500) NULL,
    telephone_no     VARCHAR(30)  NULL,
    created_at       TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP    NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (personal_info_id) REFERENCES pds_personal_information(id) ON DELETE CASCADE
);


-- ------------------------------------------------------------
-- PDS Page 1 — Section II, Items 24 & 25: Parents
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pds_parents (
    id                     INT AUTO_INCREMENT PRIMARY KEY,
    personal_info_id       INT NOT NULL,
    -- Father (Item 24)
    father_surname         VARCHAR(255) NULL,
    father_first_name      VARCHAR(255) NULL,
    father_middle_name     VARCHAR(255) NULL,
    father_name_extension  VARCHAR(20)  NULL,
    -- Mother (Item 25 — maiden name)
    mother_maiden_surname  VARCHAR(255) NULL COMMENT 'Mother maiden (birth) surname',
    mother_first_name      VARCHAR(255) NULL,
    mother_middle_name     VARCHAR(255) NULL,
    created_at             TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at             TIMESTAMP    NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (personal_info_id) REFERENCES pds_personal_information(id) ON DELETE CASCADE
);


-- ------------------------------------------------------------
-- PDS Page 1 — Section II, Item 23: Children
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pds_children (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    personal_info_id INT NOT NULL,
    full_name        VARCHAR(255) NULL,
    date_of_birth    DATE         NULL,
    created_at       TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (personal_info_id) REFERENCES pds_personal_information(id) ON DELETE CASCADE
);


-- ------------------------------------------------------------
-- PDS Page 1 — Section III, Item 26: Educational Background
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pds_education (
    id                   INT AUTO_INCREMENT PRIMARY KEY,
    personal_info_id     INT NOT NULL,
    level                VARCHAR(50)  NULL COMMENT 'ELEMENTARY / SECONDARY / VOCATIONAL / COLLEGE / GRADUATE STUDIES',
    school_name          VARCHAR(500) NULL,
    degree_course        VARCHAR(500) NULL COMMENT 'Basic Education / Degree / Course',
    from_year            VARCHAR(10)  NULL COMMENT '4-digit year e.g. 2010',
    to_year              VARCHAR(10)  NULL COMMENT '4-digit year or PRESENT',
    highest_level_units  VARCHAR(100) NULL COMMENT 'Highest Level/Units Earned (if not graduated)',
    year_graduated       VARCHAR(10)  NULL COMMENT '4-digit year',
    scholarship_honors   VARCHAR(500) NULL COMMENT 'Scholarship/Academic Honors Received',
    created_at           TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_pds_edu_level (level),
    FOREIGN KEY (personal_info_id) REFERENCES pds_personal_information(id) ON DELETE CASCADE
);


-- ------------------------------------------------------------
-- PDS Page 2 — Section IV, Item 27: Civil Service Eligibility
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pds_civil_service_eligibility (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    personal_info_id INT NOT NULL,
    eligibility      VARCHAR(500) NULL COMMENT 'Career service / board/bar / RA number / etc.',
    rating           VARCHAR(20)  NULL COMMENT 'Rating (if applicable)',
    date_of_exam     DATE         NULL,
    place_of_exam    VARCHAR(500) NULL,
    license_number   VARCHAR(100) NULL,
    valid_until      DATE         NULL COMMENT 'License validity / expiry date',
    created_at       TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_pds_elig (eligibility(100)),
    FOREIGN KEY (personal_info_id) REFERENCES pds_personal_information(id) ON DELETE CASCADE
);


-- ------------------------------------------------------------
-- PDS Page 2 — Section V, Item 28: Work Experience
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pds_work_experience (
    id                        INT AUTO_INCREMENT PRIMARY KEY,
    personal_info_id          INT NOT NULL,
    date_from                 DATE          NULL,
    date_to                   DATE          NULL COMMENT 'NULL = still employed (see is_present)',
    is_present                TINYINT(1)    NOT NULL DEFAULT 0 COMMENT '1 = currently employed here',
    position_title            VARCHAR(500)  NULL,
    department_agency_company VARCHAR(500)  NULL,
    monthly_salary            DECIMAL(12,2) NULL,
    salary_job_pay_grade      VARCHAR(50)   NULL COMMENT 'Salary Grade / Step Increment',
    status_of_appointment     VARCHAR(100)  NULL COMMENT 'Permanent / Temporary / Casual / Contractual',
    gov_service               CHAR(1)       NULL COMMENT 'Y or N — Government Service',
    created_at                TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_pds_work_dates      (date_from, date_to),
    INDEX idx_pds_work_is_present (is_present),
    FOREIGN KEY (personal_info_id) REFERENCES pds_personal_information(id) ON DELETE CASCADE
);


-- ------------------------------------------------------------
-- PDS Page 3 — Section VI, Item 29: Voluntary Work
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pds_voluntary_work (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    personal_info_id INT NOT NULL,
    organization     VARCHAR(500) NULL COMMENT 'Name and Address of Organization',
    date_from        DATE         NULL,
    date_to          DATE         NULL,
    hours            INT          NULL COMMENT 'Number of hours',
    position         VARCHAR(255) NULL COMMENT 'Nature of work / position',
    created_at       TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (personal_info_id) REFERENCES pds_personal_information(id) ON DELETE CASCADE
);


-- ------------------------------------------------------------
-- PDS Page 3 — Section VII, Item 30: Training / L&D
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pds_training (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    personal_info_id INT NOT NULL,
    title            VARCHAR(500) NULL COMMENT 'Title of L&D Intervention / Training Programs',
    date_from        DATE         NULL,
    date_to          DATE         NULL,
    hours            INT          NULL COMMENT 'Number of hours',
    type             VARCHAR(50)  NULL COMMENT 'Managerial / Supervisory / Technical / Foundation',
    conducted_by     VARCHAR(500) NULL COMMENT 'Conducted/Sponsored By',
    created_at       TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (personal_info_id) REFERENCES pds_personal_information(id) ON DELETE CASCADE
);


-- ------------------------------------------------------------
-- PDS Page 3 — Section VIII, Items 31–33: Other Information
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pds_other_information (
    id                       INT AUTO_INCREMENT PRIMARY KEY,
    personal_info_id         INT NOT NULL,
    special_skills_hobbies   TEXT NULL COMMENT 'Item 31: Special Skills and Hobbies (comma-separated)',
    non_academic_distinctions TEXT NULL COMMENT 'Item 32: Non-Academic Distinctions / Recognition',
    membership_associations  TEXT NULL COMMENT 'Item 33: Membership in Association/Organization',
    created_at               TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at               TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (personal_info_id) REFERENCES pds_personal_information(id) ON DELETE CASCADE
);


-- ------------------------------------------------------------
-- PDS Page 4 — Section IX: Declarations (Items 34–40)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pds_declarations (
    id                                      INT AUTO_INCREMENT PRIMARY KEY,
    personal_info_id                        INT NOT NULL,
    -- Item 34: Related to appointing authority
    q34a_answer                             ENUM('yes','no') NULL COMMENT '34a: Related within 3rd degree?',
    related_appointing_authority_3rd_degree VARCHAR(255) NULL COMMENT 'Details if yes (34a)',
    q34b_answer                             ENUM('yes','no') NULL COMMENT '34b: Related within 4th degree?',
    related_appointing_authority_4th_degree VARCHAR(255) NULL COMMENT 'Details if yes (34b)',
    -- Item 35: Administrative / Criminal
    q35a_answer                             ENUM('yes','no') NULL COMMENT '35a: Admin offense found guilty?',
    administrative_offense_details          TEXT NULL COMMENT 'Details if yes (35a)',
    q35b_answer                             ENUM('yes','no') NULL COMMENT '35b: Criminally charged?',
    criminal_charge_details                 TEXT NULL COMMENT 'Details if yes (35b)',
    criminal_charge_date                    DATE NULL COMMENT 'Date filed',
    criminal_charge_status                  VARCHAR(100) NULL COMMENT 'Status of case',
    -- Item 36: Conviction
    q36_answer                              ENUM('yes','no') NULL COMMENT '36: Convicted of any crime?',
    conviction_details                      TEXT NULL COMMENT 'Details if yes (36)',
    -- Item 37: Separation from service
    q37_answer                              ENUM('yes','no') NULL COMMENT '37: Separated from service involuntarily?',
    separation_details                      TEXT NULL COMMENT 'Details if yes (37)',
    -- Item 38: Election
    q38a_answer                             ENUM('yes','no') NULL COMMENT '38a: Candidate in any election?',
    election_candidacy_details              TEXT NULL COMMENT 'Details if yes (38a)',
    q38b_answer                             ENUM('yes','no') NULL COMMENT '38b: Resigned to campaign?',
    resignation_campaign_details            TEXT NULL COMMENT 'Details if yes (38b)',
    -- Item 39: Immigrant
    q39_answer                              ENUM('yes','no') NULL COMMENT '39: Immigrant status?',
    immigrant_status_country                VARCHAR(100) NULL COMMENT 'Country if yes (39)',
    -- Item 40: IP / PWD / Solo Parent
    q40a_answer                             ENUM('yes','no') NULL COMMENT '40a: IP/Indigenous group member?',
    indigenous_group                        VARCHAR(100) NULL COMMENT 'Group name if yes (40a)',
    q40b_answer                             ENUM('yes','no') NULL COMMENT '40b: PWD?',
    pwd_id                                  VARCHAR(50)  NULL COMMENT 'PWD ID number if yes (40b)',
    q40c_answer                             ENUM('yes','no') NULL COMMENT '40c: Solo Parent?',
    solo_parent_id                          VARCHAR(50)  NULL COMMENT 'Solo Parent ID if yes (40c)',
    -- Audit
    created_at                              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at                              TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (personal_info_id) REFERENCES pds_personal_information(id) ON DELETE CASCADE
);


-- ------------------------------------------------------------
-- PDS Page 4 — Item 41: Character References
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pds_references (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    personal_info_id INT NOT NULL,
    full_name        VARCHAR(255) NULL,
    address          VARCHAR(500) NULL,
    contact          VARCHAR(50)  NULL COMMENT 'Telephone or mobile number',
    created_at       TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (personal_info_id) REFERENCES pds_personal_information(id) ON DELETE CASCADE
);


-- ------------------------------------------------------------
-- PDS Page 4 — Item 42 + Oath: Government ID & Oath of Office
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pds_oath (
    id                   INT AUTO_INCREMENT PRIMARY KEY,
    personal_info_id     INT NOT NULL,
    government_id        VARCHAR(100) NULL COMMENT 'Government-issued ID type (Passport, GSIS, SSS, PhilSys, etc.)',
    id_number            VARCHAR(100) NULL COMMENT 'ID Number',
    issuance_date_place  VARCHAR(255) NULL COMMENT 'Date and Place of Issuance',
    signature            VARCHAR(500) NULL COMMENT 'Path to uploaded signature image',
    thumbmark            VARCHAR(500) NULL COMMENT 'Path to uploaded thumbmark image',
    date_signed          DATE         NULL COMMENT 'Date employee signed the PDS',
    created_at           TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMP    NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (personal_info_id) REFERENCES pds_personal_information(id) ON DELETE CASCADE
);
