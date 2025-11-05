-- Complete Migration: Add all missing columns to features table
-- Run this in your Supabase SQL Editor

-- Add prev_ema_short column (if not exists)
ALTER TABLE features 
ADD COLUMN IF NOT EXISTS prev_ema_short DECIMAL(10, 4);

-- Add prev_ema_long column (if not exists)
ALTER TABLE features 
ADD COLUMN IF NOT EXISTS prev_ema_long DECIMAL(10, 4);

-- Add timestamp column (if not exists)
ALTER TABLE features 
ADD COLUMN IF NOT EXISTS timestamp TIMESTAMPTZ;

-- Verify all columns exist
SELECT column_name, data_type, numeric_precision, numeric_scale
FROM information_schema.columns 
WHERE table_name = 'features' 
ORDER BY column_name;
