-- Migration: Add prev_ema columns to features table
-- Run this in your Supabase SQL editor

-- Add prev_ema_short column
ALTER TABLE features 
ADD COLUMN IF NOT EXISTS prev_ema_short DECIMAL(10, 4);

-- Add prev_ema_long column
ALTER TABLE features 
ADD COLUMN IF NOT EXISTS prev_ema_long DECIMAL(10, 4);

-- Verify changes
SELECT column_name, data_type, numeric_precision, numeric_scale
FROM information_schema.columns 
WHERE table_name = 'features' 
AND column_name IN ('ema_short', 'ema_long', 'prev_ema_short', 'prev_ema_long')
ORDER BY column_name;
