# Sentiment Extraction Issue - Root Cause Analysis

## Problem
The extracted sentiment score (23) doesn't match the actual CNN Fear & Greed Index (18).

## Root Cause
Perplexity AI is NOT accessing the official CNN Fear & Greed Index directly. Instead, it's pulling from third-party aggregators:

**Citations Received:**
1. finhacker.cz/fear-and-greed-index-historical-data-and-chart/
2. feargreedindex.net
3. macromicro.me/series/22748/cnn-fear-and-greed

**NOT Cited:**
- edition.cnn.com/markets/fear-and-greed (the official source)

## Why This Happens
1. **Third-party lag**: Aggregator sites may have delayed or cached data
2. **Different metrics**: Some sites show variations or their own calculations
3. **API limitations**: Perplexity may not have direct access to CNN's live data

## Impact
- 5-point difference (18 vs 23)
- Could affect trading decisions
- Reduces trust in the system

## Solutions

### Option 1: Accept Small Variance (RECOMMENDED)
- **Pros**: Single API call, still gets directional sentiment correct
- **Cons**: May be off by 3-5 points
- **Use Case**: When exact score isn't critical, just need "Extreme Fear" vs "Fear" vs "Neutral"

### Option 2: Separate Sentiment Query
- **Pros**: More explicit, might get better accuracy
- **Cons**: Requires 2 API calls (defeats the purpose of integration)
- **Use Case**: When exact score is critical

### Option 3: Direct CNN Scraping
- **Pros**: 100% accurate, no AI interpretation
- **Cons**: Requires web scraping, may break if CNN changes their site
- **Use Case**: Production system where accuracy is paramount

### Option 4: Use Alternative Sentiment Source
- **Pros**: Might be more reliable/accessible
- **Cons**: Not the "official" CNN index
- **Options**:
  - VIX (already implemented as fallback)
  - Put/Call Ratio
  - Market breadth indicators

## Recommendation

**For Now**: Accept the variance and use it directionally
- 18 = Extreme Fear
- 23 = Fear  
- Both indicate bearish sentiment
- The 5-point difference doesn't change the trading strategy

**For Production**: Implement Option 3 (Direct CNN Scraping)
- Add a dedicated CNN scraper
- Use as primary source
- Keep Perplexity as fallback
- This gives you the exact score you want

## Implementation Status

✅ Extraction logic works correctly
✅ Parses AI response properly  
⚠️  AI is not accessing official CNN source
⚠️  Getting data from third-party aggregators

## Next Steps

1. **Short-term**: Use current implementation, accept 3-5 point variance
2. **Medium-term**: Add CNN scraper for exact scores
3. **Long-term**: Build composite sentiment from multiple sources
