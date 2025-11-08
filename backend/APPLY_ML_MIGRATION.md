# Apply ML Database Migration

## Quick Start

To apply the ML database migration, follow these steps:

### Option 1: Supabase Dashboard (Recommended)

1. **Open Supabase Dashboard**
   - Go to: https://supabase.com/dashboard
   - Select your project: `osntrppbgqtdyfermffa`

2. **Open SQL Editor**
   - Click on "SQL Editor" in the left sidebar
   - Click "New Query"

3. **Copy and Paste Migration**
   - Open `backend/supabase_migration_ml_tables.sql`
   - Copy the entire contents
   - Paste into the SQL Editor

4. **Run Migration**
   - Click "Run" button
   - Wait for completion (should take 5-10 seconds)
   - You should see success messages

5. **Verify Tables**
   - Click on "Table Editor" in the left sidebar
   - You should see 5 new tables:
     - `ml_trade_features`
     - `ml_models`
     - `ml_predictions`
     - `ml_performance`
     - `position_exits`

### Option 2: Command Line (psql)

If you have PostgreSQL client installed:

```bash
# Set your database connection string
export DATABASE_URL="postgresql://postgres:[YOUR-PASSWORD]@db.osntrppbgqtdyfermffa.supabase.co:5432/postgres"

# Apply migration
psql $DATABASE_URL < backend/supabase_migration_ml_tables.sql
```

### Option 3: Python Script (Alternative)

We can create a direct PostgreSQL connection:

```bash
# Install psycopg2
pip install psycopg2-binary

# Run migration script
python backend/apply_ml_migration_psql.py
```

## What Gets Created

### Tables (5)
1. **ml_trade_features** - Feature vectors for ML training
2. **ml_models** - Trained model storage
3. **ml_predictions** - Prediction logging
4. **ml_performance** - Daily performance metrics
5. **position_exits** - Exit tracking and analysis

### Views (3)
1. **ml_model_performance_summary** - Model performance overview
2. **daily_exit_performance** - Exit strategy analysis
3. **ml_feature_statistics** - Feature statistics by regime/session

### Indexes (15+)
- Optimized for fast queries on common patterns
- Trade ID lookups
- Date range queries
- Model performance tracking

## Verification

After applying the migration, verify it worked:

```sql
-- Check tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE 'ml_%' OR table_name = 'position_exits';

-- Check views exist
SELECT table_name 
FROM information_schema.views 
WHERE table_schema = 'public' 
AND table_name LIKE 'ml_%' OR table_name LIKE '%exit%';
```

You should see:
- 5 tables
- 3 views

## Next Steps

Once migration is complete:

1. ✅ Task 2 complete!
2. Move to Task 3: Set up ML module structure
3. Begin feature engineering

## Troubleshooting

### Error: "relation already exists"
- Tables already created, migration already applied
- Safe to ignore or drop tables first

### Error: "permission denied"
- Make sure you're using SUPABASE_SERVICE_KEY (not anon key)
- Check your Supabase project permissions

### Error: "syntax error"
- Make sure you copied the entire SQL file
- Check for any truncation

## Manual Cleanup (if needed)

To remove all ML tables and start fresh:

```sql
-- Drop tables (in order due to foreign keys)
DROP TABLE IF EXISTS ml_predictions CASCADE;
DROP TABLE IF EXISTS ml_performance CASCADE;
DROP TABLE IF EXISTS position_exits CASCADE;
DROP TABLE IF NOT EXISTS ml_trade_features CASCADE;
DROP TABLE IF EXISTS ml_models CASCADE;

-- Drop views
DROP VIEW IF EXISTS ml_model_performance_summary;
DROP VIEW IF EXISTS daily_exit_performance;
DROP VIEW IF EXISTS ml_feature_statistics;
```

Then re-apply the migration.
