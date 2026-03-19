CREATE DATABASE IF NOT EXISTS hrmo_elog_db;
USE hrmo_elog_db;

-- Offices Table
CREATE TABLE IF NOT EXISTS offices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Seed default offices
INSERT IGNORE INTO offices (id, name, is_active) VALUES (1, 'SUPER ADMIN', 1);

-- Admins Table
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    pin_hash VARCHAR(255) NULL,
    office INT NULL,
    face_embedding LONGTEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (office) REFERENCES offices(id) ON DELETE SET NULL
);

-- Clients Table
CREATE TABLE IF NOT EXISTS clients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    fname VARCHAR(100) NULL,
    lname VARCHAR(100) NULL,
    mi VARCHAR(10) NULL,
    name_ext VARCHAR(20) NULL,
    department VARCHAR(255),
    gender VARCHAR(20),
    age INT,
    client_type VARCHAR(50)
);

-- CSM Form Table
CREATE TABLE IF NOT EXISTS csm_form (
    id INT AUTO_INCREMENT PRIMARY KEY,
    control_no VARCHAR(50) UNIQUE NOT NULL,
    date DATE NOT NULL,
    office INT,
    client_type VARCHAR(50),
    sex VARCHAR(20),
    age INT,
    region_of_residence VARCHAR(255),
    email VARCHAR(255),
    service_availed VARCHAR(255),
    awareness_of_cc INT,
    cc_of_this_office_was INT,
    cc_help_you INT,
    sdq0 INT, sdq1 INT, sdq2 INT, sdq3 INT, sdq4 INT, 
    sdq5 INT, sdq6 INT, sdq7 INT, sdq8 INT,
    suggestion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (office) REFERENCES offices(id) ON DELETE SET NULL
);

-- Face Embeddings Table
CREATE TABLE IF NOT EXISTS face_embeddings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id VARCHAR(50) NOT NULL,
    embedding_json LONGTEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
);

-- Logs Table
CREATE TABLE IF NOT EXISTS logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id VARCHAR(50) NOT NULL,
    time_in DATETIME NOT NULL,
    time_out DATETIME NULL,
    purpose VARCHAR(255),
    additional_info TEXT,
    office INT NULL,
    FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE,
    FOREIGN KEY (office) REFERENCES offices(id) ON DELETE SET NULL
);

-- PDS Tables (new tables for employee data)
CREATE TABLE IF NOT EXISTS pds_personal_information (
    id INT AUTO_INCREMENT PRIMARY KEY,
    surname VARCHAR(255),
    first_name VARCHAR(255),
    middle_name VARCHAR(255),
    sex VARCHAR(10),
    date_of_birth DATE,
    mobile_no VARCHAR(20),
    email VARCHAR(255),
    agency_employee_no VARCHAR(100),
    signature_path VARCHAR(255),
    pds_excel_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pds_spouse (
    id INT AUTO_INCREMENT PRIMARY KEY,
    personal_info_id INT NOT NULL,
    FOREIGN KEY (personal_info_id) REFERENCES pds_personal_information(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pds_parents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    personal_info_id INT NOT NULL,
    FOREIGN KEY (personal_info_id) REFERENCES pds_personal_information(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pds_children (
    id INT AUTO_INCREMENT PRIMARY KEY,
    personal_info_id INT NOT NULL,
    FOREIGN KEY (personal_info_id) REFERENCES pds_personal_information(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pds_education (
    id INT AUTO_INCREMENT PRIMARY KEY,
    personal_info_id INT NOT NULL,
    FOREIGN KEY (personal_info_id) REFERENCES pds_personal_information(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pds_work_experience (
    id INT AUTO_INCREMENT PRIMARY KEY,
    personal_info_id INT NOT NULL,
    FOREIGN KEY (personal_info_id) REFERENCES pds_personal_information(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pds_civil_service_eligibility (
    id INT AUTO_INCREMENT PRIMARY KEY,
    personal_info_id INT NOT NULL,
    FOREIGN KEY (personal_info_id) REFERENCES pds_personal_information(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pds_voluntary_work (
    id INT AUTO_INCREMENT PRIMARY KEY,
    personal_info_id INT NOT NULL,
    FOREIGN KEY (personal_info_id) REFERENCES pds_personal_information(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pds_training (
    id INT AUTO_INCREMENT PRIMARY KEY,
    personal_info_id INT NOT NULL,
    FOREIGN KEY (personal_info_id) REFERENCES pds_personal_information(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pds_other_information (
    id INT AUTO_INCREMENT PRIMARY KEY,
    personal_info_id INT NOT NULL,
    FOREIGN KEY (personal_info_id) REFERENCES pds_personal_information(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pds_declarations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    personal_info_id INT NOT NULL,
    FOREIGN KEY (personal_info_id) REFERENCES pds_personal_information(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pds_references (
    id INT AUTO_INCREMENT PRIMARY KEY,
    personal_info_id INT NOT NULL,
    FOREIGN KEY (personal_info_id) REFERENCES pds_personal_information(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pds_oath (
    id INT AUTO_INCREMENT PRIMARY KEY,
    personal_info_id INT NOT NULL,
    FOREIGN KEY (personal_info_id) REFERENCES pds_personal_information(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

