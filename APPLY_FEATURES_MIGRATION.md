# Apply Features Table Migration

## Quick Fix

The backend is trying to save the new indicators to the `features` table, but it doesn't have the new columns yet.

### Apply This Migration:

**File**: `backend/supabase_migration_features_table.sql`

### Option 1: Supabase Dashboard (Easiest)

1. Go to your Supabase Dashboard
2. Click **SQL Editor**
3. Copy the contents of `backend/supabase_migration_features_table.sql`
4. Paste and click **Run**
5. Restart the backend

### Option 2: Command Line

```bash
# If you have psql access
psql -h your-supabase-host -U postgres -d postgres -f backend/supabase_migration_features_table.sql
```

### What This Does:

Adds 16 new columns to the `features` table:
- vwap, rsi, macd, macd_signal, macd_histogram
- adx, plus_di, minus_di, market_regime
- volume_ratio, volume_spike, obv
- vwap_signal, rsi_momentum, macd_momentum
- confidence_score
- prev_ema_short, prev_ema_long

### After Migration:

The errors will disappear and you'll see:
```
✓ Enhanced signal for TSLA: BUY | Confidence: 85.5/100 | ...
```

---

**Status**: Ready to apply - this will fix the database errors!
