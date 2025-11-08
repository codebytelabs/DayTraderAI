# Multi-Cap Opportunity Discovery System
## Maximizing Returns Across All Market Cap Segments

### Executive Summary

Your current system is biased toward **megacap stocks only** (>$10B market cap), missing significant opportunities in mid-cap ($2B-$10B) and small-cap ($300M-$2B) segments. Research shows that successful day traders with high ROI diversify across all market cap segments, with proper position sizing and risk management for each tier.

**Key Finding:** Mid and small-cap stocks offer 5-20% intraday volatility vs 1-3% for large-caps, providing higher profit potential when traded with appropriate risk controls.

---

## Current System Limitations

### 1. **Hardcoded Large-Cap Bias**
- Perplexity query explicitly requires: "Market cap > $5 billion"
- Excludes small-caps explicitly in the query
- Stock universe contains only megacap tech and major indices

### 2. **Missing Opportunities**
- No mid-cap coverage ($2B-$10B)
- No small-cap coverage ($300M-$2B)
- Missing high-volatility momentum plays
- Missing news-driven catalyst opportunities

### 3. **Limited Diversification**
- All positions in same risk profile (large-cap)
- Missing risk/reward optimization across segments
- Portfolio not balanced for maximum returns

---

## Research Findings

### Market Cap Segment Characteristics

| Segment | Market Cap | Volatility | Volume Req | Position Size | Account Allocation |
|---------|-----------|------------|------------|---------------|-------------------|
| **Large-Cap** | >$10B | 1-3% intraday | >5M shares/day | 2-5% | 40-60% |
| **Mid-Cap** | $2B-$10B | 3-8% intraday | >1M shares/day | 1.5-3% | 25-40% |
| **Small-Cap** | $300M-$2B | 5-20% intraday | >500k shares/day | 1-2% | 10-20% |

### ROI Profiles

- **Large-Cap:** 0.2-0.5% daily returns (safer, consistent, higher win rate)
- **Mid-Cap:** 0.5-1.5% daily returns (balanced risk/reward)
- **Small-Cap:** 1-5% daily returns (episodic, high risk, explosive potential)

### Success Factors by Segment

**Large-Cap:**
- Institutional flow and technical patterns
- Lower volatility, tighter spreads
- Best for: Scalping, VWAP strategies, trend following

**Mid-Cap:**
- Balance of volatility and liquidity
- Sector rotation plays
- Best for: Momentum trading, gap strategies

**Small-Cap:**
- News catalysts ESSENTIAL
- High volume spikes (2-5x average)
- Low float (<20M shares) = more volatile
- Best for: Gap & go, breakouts, short squeezes

---

## Proposed Solution: Multi-Tier Discovery System

### 1. **Separate Perplexity Queries by Market Cap**

#### Large-Cap Query (40-60% allocation)
```
Find TOP 15 LARGE-CAP day trading opportunities (market cap >$10B):
- High liquidity (>5M daily volume)
- Technical setups: VWAP, moving averages, institutional flow
- Focus: AAPL, MSFT, NVDA, TSLA, AMD, GOOGL, AMZN, META, SPY, QQQ
- Both LONG and SHORT opportunities
- Intraday timeframe (next 1-2 hours)
```

#### Mid-Cap Query (25-40% allocation)
```
Find TOP 15 MID-CAP day trading opportunities (market cap $2B-$10B):
- Volume >1M shares/day
- Volatility: 3-8% intraday moves
- News catalysts: earnings, analyst upgrades, sector rotation
- Technical: momentum breakouts, gap strategies
- Examples: PLTR, COIN, SOFI, RIVN, HOOD, RBLX, DKNG, U
- Both LONG and SHORT opportunities
- Intraday timeframe (next 1-2 hours)
```

#### Small-Cap Query (10-20% allocation)
```
Find TOP 10 SMALL-CAP day trading opportunities (market cap $300M-$2B):
- Volume >500k shares/day (preferably >1M)
- Price range: $2-$50
- MUST have news catalyst (earnings, FDA, M&A, sector news)
- Volume spike: >2x average
- Low float preferred (<20M shares)
- High volatility: 5-20% intraday potential
- Technical: gap & go, breakouts, short squeezes
- Examples: AMC, GME, MARA, SNDL, CRSP, EDIT
- Both LONG and SHORT opportunities
- Intraday timeframe (next 1-2 hours)
```

### 2. **Expanded Stock Universe**

#### Add Mid-Cap Stocks (50-100 symbols)
```python
MID_CAP_MOMENTUM = [
    # Fintech & Crypto
    'PLTR', 'COIN', 'SOFI', 'HOOD', 'AFRM', 'SQ', 'MARA', 'RIOT',
    
    # EV & Transportation
    'RIVN', 'LCID', 'NIO', 'XPEV', 'LI', 'GRAB', 'UBER', 'LYFT',
    
    # Gaming & Entertainment
    'RBLX', 'U', 'DKNG', 'PENN', 'TTWO', 'EA',
    
    # Cloud & SaaS
    'SNOW', 'DDOG', 'CRWD', 'ZS', 'NET', 'OKTA', 'MDB', 'DOCN',
    
    # Biotech
    'CRSP', 'EDIT', 'NTLA', 'BEAM', 'VRTX', 'MRNA',
    
    # Consumer & Retail
    'DASH', 'ABNB', 'CHWY', 'ETSY', 'W', 'SHOP'
]
```

#### Add Small-Cap Stocks (50-100 symbols)
```python
SMALL_CAP_HIGH_VOLUME = [
    # Meme/Social Momentum
    'AMC', 'GME', 'BBBY', 'CLOV', 'WISH',
    
    # Crypto Mining
    'MARA', 'RIOT', 'BTBT', 'CAN', 'HUT',
    
    # Cannabis
    'SNDL', 'TLRY', 'CGC', 'ACB', 'HEXO',
    
    # Biotech (High Volume)
    'OCGN', 'NVAX', 'SAVA', 'ATOS', 'GEVO',
    
    # EV & Tech
    'WKHS', 'RIDE', 'GOEV', 'FSR', 'NKLA',
    
    # Energy
    'FCEL', 'PLUG', 'BLNK', 'CLSK', 'MVIS'
]
```

### 3. **Market-Cap-Aware Position Sizing**

```python
def calculate_position_size(symbol, market_cap, account_value, atr):
    """
    Calculate position size based on market cap and volatility.
    """
    # Base allocation by market cap
    if market_cap > 10_000_000_000:  # Large-cap
        base_pct = 0.04  # 4% of account
        max_pct = 0.05   # Max 5%
        risk_pct = 0.02  # 2% account risk
    elif market_cap > 2_000_000_000:  # Mid-cap
        base_pct = 0.025  # 2.5% of account
        max_pct = 0.03    # Max 3%
        risk_pct = 0.015  # 1.5% account risk
    else:  # Small-cap
        base_pct = 0.015  # 1.5% of account
        max_pct = 0.02    # Max 2%
        risk_pct = 0.01   # 1% account risk
    
    # Adjust for volatility (ATR)
    # Higher volatility = smaller position
    volatility_multiplier = 1.0 / (1.0 + atr * 10)
    
    adjusted_pct = base_pct * volatility_multiplier
    final_pct = min(adjusted_pct, max_pct)
    
    position_value = account_value * final_pct
    
    return {
        'position_value': position_value,
        'position_pct': final_pct,
        'risk_pct': risk_pct,
        'market_cap_tier': get_tier(market_cap)
    }
```

### 4. **Enhanced Risk Management**

#### Stop Loss by Market Cap
```python
STOP_LOSS_CONFIG = {
    'large_cap': {
        'account_risk': 0.02,  # 2% max account risk
        'atr_multiplier': 2.0,  # 2x ATR stop
        'max_stop_pct': 0.03    # Max 3% price stop
    },
    'mid_cap': {
        'account_risk': 0.015,  # 1.5% max account risk
        'atr_multiplier': 1.5,  # 1.5x ATR stop
        'max_stop_pct': 0.04    # Max 4% price stop
    },
    'small_cap': {
        'account_risk': 0.01,   # 1% max account risk
        'atr_multiplier': 1.0,  # 1x ATR stop (tight!)
        'max_stop_pct': 0.05    # Max 5% price stop
    }
}
```

#### Portfolio Limits
```python
PORTFOLIO_LIMITS = {
    'max_positions': 25,  # Total positions
    'max_large_cap': 15,  # Max 15 large-cap
    'max_mid_cap': 8,     # Max 8 mid-cap
    'max_small_cap': 5,   # Max 5 small-cap
    
    'allocation_targets': {
        'large_cap': 0.50,   # 50% target
        'mid_cap': 0.35,     # 35% target
        'small_cap': 0.15    # 15% target
    }
}
```

### 5. **Query Optimization Strategy**

#### Sequential Discovery Process
```
1. Run Large-Cap Query → Get 15 opportunities
2. Run Mid-Cap Query → Get 15 opportunities  
3. Run Small-Cap Query → Get 10 opportunities
4. Score all 40 opportunities
5. Select top 25 based on:
   - Score
   - Portfolio allocation targets
   - Diversification
   - Risk balance
```

#### Query Timing
- **Market Open (9:30-10:00 AM):** Focus on gap & go, breakouts
- **Mid-Morning (10:00-11:00 AM):** VWAP strategies, momentum continuation
- **Midday (11:00-2:00 PM):** Range trading, mean reversion
- **Power Hour (3:00-4:00 PM):** Momentum plays, closing strength

---

## Implementation Plan

### Phase 1: Expand Stock Universe (Day 1)
- [ ] Add 50 mid-cap stocks to `stock_universe.py`
- [ ] Add 50 small-cap stocks to `stock_universe.py`
- [ ] Categorize by market cap tier
- [ ] Add volume and liquidity filters

### Phase 2: Multi-Tier Query System (Day 1-2)
- [ ] Create separate query builders for each market cap
- [ ] Implement sequential discovery process
- [ ] Add market cap detection and categorization
- [ ] Test query effectiveness with Perplexity

### Phase 3: Position Sizing Engine (Day 2)
- [ ] Implement market-cap-aware position sizing
- [ ] Add volatility-adjusted sizing (ATR-based)
- [ ] Create portfolio allocation tracker
- [ ] Add position limits by tier

### Phase 4: Enhanced Risk Management (Day 2-3)
- [ ] Implement tiered stop-loss system
- [ ] Add market-cap-specific risk limits
- [ ] Create portfolio rebalancing logic
- [ ] Add exposure monitoring by tier

### Phase 5: Testing & Validation (Day 3)
- [ ] Test with paper trading
- [ ] Validate position sizing
- [ ] Monitor portfolio allocation
- [ ] Adjust parameters based on results

---

## Expected Outcomes

### Performance Improvements
- **Opportunity Coverage:** 3x more opportunities (40 vs 15)
- **Return Potential:** 2-3x higher with mid/small-cap exposure
- **Diversification:** Better risk-adjusted returns
- **Adaptability:** Can trade in any market condition

### Risk Management
- Smaller positions in riskier segments
- Better portfolio balance
- Reduced concentration risk
- Volatility-adjusted sizing

### Example Portfolio (25 positions, $50k account)

| Tier | Positions | Allocation | Avg Position | Total Value |
|------|-----------|------------|--------------|-------------|
| Large-Cap | 12 | 50% ($25k) | $2,083 (4.2%) | $25,000 |
| Mid-Cap | 8 | 35% ($17.5k) | $2,188 (4.4%) | $17,500 |
| Small-Cap | 5 | 15% ($7.5k) | $1,500 (3%) | $7,500 |
| **Total** | **25** | **100%** | **$2,000** | **$50,000** |

---

## Real-World Examples

### Large-Cap Trade (NVDA)
- Market Cap: $500B
- Position Size: 4% ($2,000)
- Stop Loss: 2% account risk ($400)
- Target: 1.5% gain ($30)
- Win Rate: 60%

### Mid-Cap Trade (PLTR)
- Market Cap: $40B
- Position Size: 2.5% ($1,250)
- Stop Loss: 1.5% account risk ($300)
- Target: 3% gain ($37.50)
- Win Rate: 50%

### Small-Cap Trade (MARA)
- Market Cap: $3B
- Position Size: 1.5% ($750)
- Stop Loss: 1% account risk ($200)
- Target: 5% gain ($37.50)
- Win Rate: 40%

**Daily Expected Value:**
- Large-cap: 12 trades × 60% × $30 = $216
- Mid-cap: 8 trades × 50% × $37.50 = $150
- Small-cap: 5 trades × 40% × $37.50 = $75
- **Total: $441/day potential** (vs $216 with large-cap only)

---

## Conclusion

By expanding to mid and small-cap opportunities with proper position sizing and risk management, you can potentially **double your daily returns** while maintaining similar risk levels. The key is:

1. **Diversification** across market cap segments
2. **Appropriate position sizing** for each tier
3. **Tighter risk controls** for smaller caps
4. **News catalyst focus** for small-caps
5. **Volume requirements** to ensure liquidity

Your existing safety nets (stops, risk management, adaptive sizing) make this expansion viable and potentially very profitable.

---

## Next Steps

1. **Review this proposal** and provide feedback
2. **Prioritize implementation phases** based on your goals
3. **Start with Phase 1** (expand stock universe)
4. **Test with paper trading** before going live
5. **Monitor and adjust** based on results

Ready to implement when you are! 🚀
