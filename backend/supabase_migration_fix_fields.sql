-- Migration: Fix field lengths for advisories table
-- Run this in your Supabase SQL editor

-- Fix source and model fields to accommodate longer names
ALTER TABLE advisories 
ALTER COLUMN source TYPE VARCHAR(200);

-- Add model column if it doesn't exist, or alter if it does
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'advisories' AND column_name = 'model'
    ) THEN
        ALTER TABLE advisories ALTER COLUMN model TYPE VARCHAR(200);
    ELSE
        ALTER TABLE advisories ADD COLUMN model VARCHAR(200);
    END IF;
END $$;

-- Add type column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'advisories' AND column_name = 'type'
    ) THEN
        ALTER TABLE advisories ADD COLUMN type VARCHAR(50) DEFAULT 'analysis';
    END IF;
END $$;

-- Verify changes
SELECT column_name, data_type, character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'advisories' 
ORDER BY ordinal_position;
