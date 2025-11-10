# Phase 2: Quick Start Guide 🚀

## Enable Dynamic Watchlist in 3 Steps

### Step 1: Apply Database Migration

**Supabase Dashboard:**
1. Go to SQL Editor
2. Copy contents of `backend/supabase_migration_phase2_opportunities.sql`
3. Run the migration

**Or via command line:**
```bash
psql -h your-host -U postgres -f backend/supabase_migration_phase2_opportunities.sql
```

### Step 2: Enable in Configuration

**Edit `backend/.env`:**
```bash
# Add these lines
USE_DYNAMIC_WATCHLIST=true
SCANNER_INTERVAL_HOURS=1
SCANNER_MIN_SCORE=60.0
SCANNER_WATCHLIST_SIZE=20
```

### Step 3: Restart Backend

```bash
# The backend will automatically:
# - Initialize scanner
# - Run initial scan
# - Update watchlist hourly
# - Log all activities
```

---

## What to Expect

### On Startup:
```
Opportunity scanner initialized (dynamic watchlist: True)
🔍 Dynamic watchlist enabled - scanner loop started
🔍 Scanner loop started (interval: 1h)
🔍 Running opportunity scan...
```

### Every Hour:
```
🔍 Running opportunity scan...
✓ Scan complete: Found 45 opportunities (min score: 60.0)

📊 Top 5 Opportunities:
  1. NVDA: 105.0 (A+) - $201.23
  2. TSLA: 98.5 (A+) - $245.67
  3. AMD: 92.0 (A+) - $145.89
  4. AAPL: 88.5 (A) - $178.45
  5. MSFT: 85.0 (A) - $378.92

✓ Watchlist updated: 20 symbols (avg score: 78.5)
  Added: NVDA, CRM, ADBE
  Removed: SPY, QQQ, DIA
```

---

## API Endpoints

### Get Top Opportunities
```bash
curl http://localhost:8006/scanner/opportunities?min_score=70&limit=10
```

### Get Current Watchlist
```bash
curl http://localhost:8006/scanner/watchlist
```

### Trigger Manual Scan
```bash
curl -X POST http://localhost:8006/scanner/scan
```

### Get Scan Summary
```bash
curl http://localhost:8006/scanner/summary
```

### Get Stock Universe
```bash
curl http://localhost:8006/scanner/universe
```

### Get Sector Stocks
```bash
curl http://localhost:8006/scanner/universe/tech
```

---

## Configuration Options

### Scanner Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `USE_DYNAMIC_WATCHLIST` | false | Enable dynamic watchlist |
| `SCANNER_INTERVAL_HOURS` | 1 | Hours between scans |
| `SCANNER_MIN_SCORE` | 60.0 | Minimum score (B- grade) |
| `SCANNER_WATCHLIST_SIZE` | 20 | Number of stocks |

### Scoring Thresholds

**Grades:**
- A+ (90-110): Exceptional - Best opportunities
- A (85-89): Excellent - Great setups
- B (70-84): Good - Solid opportunities
- C (55-69): Moderate - Acceptable
- D (45-54): Weak - Avoid
- F (<45): Poor - Never trade

**Recommended Min Scores:**
- Conservative: 70+ (B or better)
- Balanced: 60+ (B- or better)
- Aggressive: 50+ (C or better)

---

## Monitoring

### Watch Scanner Logs
```bash
tail -f backend/logs/trading.log | grep "Scanner\|Scan\|Watchlist"
```

### Check Opportunities
```bash
# Get top 5
curl http://localhost:8006/scanner/opportunities?limit=5 | jq '.opportunities[] | {symbol, score, grade, price}'
```

### Monitor Watchlist Changes
```bash
# Check current watchlist
curl http://localhost:8006/scanner/watchlist | jq '.watchlist'
```

---

## Troubleshooting

### "Scanner not available"
- Check if `USE_DYNAMIC_WATCHLIST=true` in config
- Restart backend
- Check logs for initialization errors

### "No opportunities found"
- Lower `SCANNER_MIN_SCORE` (try 50.0)
- Check if markets are open
- Verify data feed connection

### "Watchlist not updating"
- Check `SCANNER_INTERVAL_HOURS` setting
- Verify scanner loop is running
- Check for errors in logs

### Slow Scans
- Reduce universe size (use high priority only)
- Increase `SCANNER_INTERVAL_HOURS`
- Check API rate limits

---

## Testing

### Run Test Suite
```bash
cd backend
python test_opportunity_scanner.py
```

### Expected Output:
```
TEST 1: Stock Universe
  ✓ Full Universe: 150+ stocks
  ✓ High Priority: 30 stocks

TEST 2: Opportunity Scorer
  ✓ Sample Stock Scores: 85.0/110 (Grade: A)

TEST 3: Opportunity Scanner
  ✓ Found 6 opportunities
  ✓ Top: NVDA (105.0, A+)

✓ ALL TESTS PASSED!
```

---

## Performance Tips

### Optimize Scan Speed
1. Use high-priority list (30 stocks) instead of full universe
2. Increase scan interval during slow markets
3. Cache market data when possible

### Improve Quality
1. Raise minimum score threshold (70+ for best setups)
2. Monitor grade distribution
3. Track win rate by opportunity grade

### Balance Coverage
1. Start with 20 stocks in watchlist
2. Increase to 30 if you have capacity
3. Monitor position utilization

---

## What's Next

### Monitor for 1 Week:
- Track scan results
- Analyze opportunity quality
- Review watchlist changes
- Measure performance impact

### Optimize:
- Adjust scoring weights if needed
- Fine-tune thresholds
- Customize sector preferences

### Phase 3:
- Multiple trading strategies
- Strategy switching based on conditions
- Advanced entry/exit logic

---

## Quick Commands

```bash
# Apply migration
psql -h your-host -U postgres -f backend/supabase_migration_phase2_opportunities.sql

# Enable dynamic watchlist
echo "USE_DYNAMIC_WATCHLIST=true" >> backend/.env

# Restart backend
# (restart your terminal/process)

# Watch logs
tail -f backend/logs/trading.log | grep Scanner

# Test API
curl http://localhost:8006/scanner/summary | jq

# Trigger manual scan
curl -X POST http://localhost:8006/scanner/scan | jq '.opportunities[:5]'
```

---

**You're ready to go!** The scanner will automatically find the best opportunities and keep your watchlist fresh! 💰🚀

---

*Phase 2 Quick Start*  
*For support, check logs or run test suite*
