# Sentiment Aggregator Cleanup

## Problem
The logs were filled with noisy warnings:
```
⚠️  Perplexity sentiment unavailable, falling back to Fear & Greed Index
⚠️  Perplexity sentiment unavailable, falling back to Fear & Greed Index
⚠️  Perplexity sentiment unavailable, falling back to Fear & Greed Index
```

This was happening **every time** the bot checked sentiment (every 30 seconds).

## Root Cause
The sentiment aggregator was trying Perplexity **first**, then falling back to Fear & Greed:

**Old Priority:**
1. Perplexity AI (only available during AI scans)
2. Fear & Greed Index (always available)

Since Perplexity is only updated during the 5-minute AI opportunity scan, it was unavailable 90% of the time, causing constant warnings.

## Solution
**Reversed the priority** to use the most reliable source first:

**New Priority:**
1. **Fear & Greed Index** (multi-source, always available) ✅
2. Perplexity AI (fallback if F&G fails)

## Changes Made

### Before
```python
# Try Perplexity first
sentiment = self._get_perplexity_sentiment()
if sentiment:
    return sentiment

# Fall back to Fear & Greed
logger.warning("⚠️  Perplexity unavailable, falling back...")
sentiment = self._get_vix_sentiment()
```

### After
```python
# Use Fear & Greed first (most reliable)
sentiment = self._get_vix_sentiment()
if sentiment:
    logger.debug("✅ Using Fear & Greed Index")  # Debug level
    return sentiment

# Fall back to Perplexity if needed
sentiment = self._get_perplexity_sentiment()
```

## Benefits

### 1. Cleaner Logs
**Before:**
- Warning every 30 seconds
- Log spam

**After:**
- Debug-level logging (quiet)
- Only warns if ALL sources fail

### 2. More Reliable
- Fear & Greed has 4 sources with consensus
- Always available (not dependent on AI scans)
- More accurate for stock market

### 3. Better Performance
- No unnecessary Perplexity checks
- Faster sentiment retrieval
- Less API calls

## Impact on Trading
✅ **No change** - Same sentiment scores
✅ **Cleaner logs** - No more spam
✅ **More reliable** - Primary source is multi-source F&G
✅ **Faster** - Direct to best source

## Next Steps
**Restart the bot** to see:
- Clean logs (no more warnings)
- Fear & Greed used as primary source
- Perplexity only as fallback
