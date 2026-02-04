-- Migration to add additional_info column to logs table
ALTER TABLE logs ADD COLUMN additional_info TEXT;
