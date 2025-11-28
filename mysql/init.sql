-- mysql/init.sql

CREATE DATABASE IF NOT EXISTS finance;

USE finance;

CREATE TABLE IF NOT EXISTS transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,           -- Unique identifier
    trx_date DATE NOT NULL,                      -- Transaction date
    description VARCHAR(255),                    -- Transaction description
    category VARCHAR(100),                       -- Category / expense type
    amount DECIMAL(12,2) NOT NULL,              -- Amount (supports large numbers and cents)
    source ENUM('Bank','Chase') NOT NULL,       -- Source of data
    transaction_type VARCHAR(50),               -- Optional: "Credit", "Debit", etc.
    reference_number VARCHAR(50),               -- Optional bank reference
    check_number VARCHAR(50),                    -- Optional
    memo VARCHAR(255),                           -- Optional notes
    balance DECIMAL(12,2),                       -- Optional running balance if needed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);