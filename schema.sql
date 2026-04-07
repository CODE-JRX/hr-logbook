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
