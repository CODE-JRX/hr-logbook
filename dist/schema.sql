CREATE DATABASE IF NOT EXISTS hrmo_elog_db;
USE hrmo_elog_db;

-- Admins Table
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    pin_hash VARCHAR(255) NOT NULL,
    face_embedding JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Clients Table
CREATE TABLE IF NOT EXISTS clients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
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
    agency_visited VARCHAR(255),
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Face Embeddings Table
CREATE TABLE IF NOT EXISTS face_embeddings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id VARCHAR(50) NOT NULL,
    embedding_json JSON NOT NULL,
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
    FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
);
