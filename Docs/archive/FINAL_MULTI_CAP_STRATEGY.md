# Final Multi-Cap Trading Strategy
## Engineered for Maximum Opportunities with Proper Risk Management

### Executive Summary

**Portfolio Allocation Strategy:**
- **50% Large-Cap** (>$10B) - Stable, liquid, 2-5% positions
- **35% Mid-Cap** ($2B-$10B) - Balanced, 1.5-3% positions  
- **15% Small-Cap** ($300M-$2B, $5-$50) - High volatility, 0.5-1% positions

**Expected Outcome:** 2-3x more opportunities, better risk-adjusted returns, adaptable to any market condition.

---

## The Three-Tier Query System

### Tier 1: Large-Cap Query (50% allocation, 12-15 stocks)

**Purpose:** Stable base with consistent returns, high liquidity

**Query Structure:**
```
LARGE-CAP INTRADAY OPPORTUNITIES (Next 1-2 Hours)

MARKET CAP: >$10 Billion
VOLUME: >5M shares/day
PRICE: Any

Find 15 opportunities (8 LONG, 7 SHORT):

LONG SETUPS (Bullish for next 1-2 hours):
- Breaking above resistance
- Strong institutional buying
- Positive momentum confirmed by volume
- VWAP support holding
- Technical indicators aligned (MACD, RSI)

SHORT SETUPS (Bearish for next 1-2 hours):
- Breaking below support
- Institutional selling pressure
- Negative momentum with volume
- VWAP resistance rejecting
- Overbought conditions reversing

FOCUS STOCKS:
- Mega tech: AAPL, MSFT, NVDA, GOOGL, AMZN, META, TSLA
- Major ETFs: SPY, QQQ, IWM, DIA
- High-volume leaders: AMD, NFLX, AVGO, CRM, ORCL

REQUIRED FORMAT:
**LONG:**
1. NVDA - $520, breaking $515 resistance, volume 2x, AI chip demand, Target $530
2. AAPL - $185, bouncing off VWAP, institutional buying, Target $188
...

**SHORT:**
1. TSLA - $240, breaking $242 support, delivery concerns, Target $235
2. META - $350, rejected at $355, profit-taking, Target $345
...

Include: Current price, technical setup, catalyst, volume confirmation, target
```

### Tier 2: Mid-Cap Query (35% allocation, 8-10 stocks)

**Purpose:** Balance of volatility and liquidity, sector rotation plays

**Query Structure:**
```
MID-CAP INTRADAY OPPORTUNITIES (Next 1-2 Hours)

MARKET CAP: $2B - $10B
VOLUME: >1M shares/day
PRICE: Any

Find 12 opportunities (6 LONG, 6 SHORT):

LONG SETUPS (Bullish momentum for next 1-2 hours):
- News catalysts (earnings beats, upgrades, contracts)
- Sector rotation into this space
- Breakout above key resistance
- Volume spike >2x average
- Gap-and-go setups holding

SHORT SETUPS (Bearish momentum for next 1-2 hours):
- Negative catalysts (downgrades, earnings miss)
- Sector rotation away
- Breakdown below support
- Volume confirming selling
- Failed breakout reversals

FOCUS SECTORS:
- Fintech/Crypto: PLTR, COIN, SOFI, HOOD, AFRM
- EV/Transport: RIVN, LCID, NIO, XPEV, GRAB
- Cloud/SaaS: SNOW, DDOG, CRWD, ZS, NET
- Gaming: RBLX, U, DKNG, PENN
- Biotech: CRSP, EDIT, VRTX, MRNA

REQUIRED FORMAT:
**LONG:**
1. PLTR - $25, earnings beat +15%, breaking $24 resistance, volume 5x, Target $27
2. COIN - $180, Bitcoin rally correlation, VWAP bounce, volume 3x, Target $190
...

**SHORT:**
1. RIVN - $15, production miss, breaking $15.50 support, volume 4x, Target $13
2. DKNG - $35, sector weakness, failed breakout, volume 2x, Target $32
...

Include: Current price, catalyst, technical setup, volume, target, timeframe
```

### Tier 3: Small-Cap Query (15% allocation, 5-8 stocks)

**Purpose:** High-volatility opportunities with explosive potential

**Query Structure:**
```
SMALL-CAP HIGH-VOLATILITY OPPORTUNITIES (Next 1-2 Hours)

MARKET CAP: $300M - $2B
PRICE: $5 - $50
VOLUME: >1M shares/day
EXCHANGE: NYSE or NASDAQ only (NO OTC)

Find 10 opportunities (5 LONG, 5 SHORT):

LONG SETUPS (Explosive upside potential):
- MUST have news catalyst (FDA, earnings, contracts, sector news)
- Volume spike >3x average
- Low float (<50M shares) preferred
- Gap-up holding or breakout pattern
- Short squeeze potential (high short interest)
- Social media momentum (meme potential)

SHORT SETUPS (Rapid downside potential):
- Negative catalyst or failed catalyst
- Volume spike on selling
- Breakdown from support
- Pump-and-dump reversal pattern
- Overbought exhaustion

FOCUS SECTORS:
- Crypto mining: MARA, RIOT, BTBT, HUT (Bitcoin correlation)
- Meme stocks: AMC, GME (social momentum)
- Biotech: ZBIO, CRSP, EDIT (FDA catalysts)
- Cannabis: SNDL, TLRY, CGC (sector plays)
- Energy: PUMP, FCEL, PLUG (commodity driven)

EXCLUDE:
- Pump-and-dump patterns
- Stocks with manipulation history
- Volume <1M shares/day
- OTC or pink sheets

REQUIRED FORMAT:
**LONG:**
1. MARA - $18, Bitcoin +5%, breaking $17.50, volume 8x, short squeeze setup, Target $22
2. ZBIO - $15, FDA approval news, gap-up +20%, volume 10x, Target $20
...

**SHORT:**
1. SNDL - $3.50, sector weakness, breaking $3.60 support, volume 5x, Target $3.00
2. AMC - $8, failed breakout, profit-taking, volume 15x, Target $7
...

Include: Current price, catalyst (REQUIRED), technical setup, volume spike, target
```

---

## How the System Works (Step-by-Step)

### Step 1: Sequential Query Execution (Every 30-60 minutes)

```python
async def discover_multi_cap_opportunities():
    """
    Execute three queries sequentially to get opportunities across all caps.
    """
    all_opportunities = []
    
    # Query 1: Large-Cap (50% allocation target)
    large_cap_query = build_large_cap_query()
    large_cap_results = await perplexity.search(large_cap_query)
    large_cap_symbols = extract_symbols_with_direction(large_cap_results)
    
    # Query 2: Mid-Cap (35% allocation target)
    mid_cap_query = build_mid_cap_query()
    mid_cap_results = await perplexity.search(mid_cap_query)
    mid_cap_symbols = extract_symbols_with_direction(mid_cap_results)
    
    # Query 3: Small-Cap (15% allocation target)
    small_cap_query = build_small_cap_query()
    small_cap_results = await perplexity.search(small_cap_query)
    small_cap_symbols = extract_symbols_with_direction(small_cap_results)
    
    # Combine all opportunities
    all_opportunities = {
        'large_cap': large_cap_symbols,  # ~15 symbols
        'mid_cap': mid_cap_symbols,      # ~12 symbols
        'small_cap': small_cap_symbols   # ~10 symbols
    }
    
    return all_opportunities  # Total: ~37 opportunities
```

### Step 2: Symbol Extraction with Direction

```python
def extract_symbols_with_direction(perplexity_response):
    """
    Extract symbols and determine if LONG or SHORT.
    """
    content = perplexity_response['content']
    
    # Find LONG section
    long_section = extract_section(content, 'LONG')
    long_symbols = []
    for match in parse_opportunities(long_section):
        long_symbols.append({
            'symbol': match['symbol'],
            'direction': 'LONG',
            'price': match['price'],
            'catalyst': match['catalyst'],
            'setup': match['setup'],
            'target': match['target'],
            'confidence': 'HIGH' if 'volume' in match else 'MEDIUM'
        })
    
    # Find SHORT section
    short_section = extract_section(content, 'SHORT')
    short_symbols = []
    for match in parse_opportunities(short_section):
        short_symbols.append({
            'symbol': match['symbol'],
            'direction': 'SHORT',
            'price': match['price'],
            'catalyst': match['catalyst'],
            'setup': match['setup'],
            'target': match['target'],
            'confidence': 'HIGH' if 'volume' in match else 'MEDIUM'
        })
    
    return long_symbols + short_symbols
```

### Step 3: Scoring and Ranking

```python
async def score_and_rank_opportunities(all_opportunities):
    """
    Score each opportunity and rank by quality.
    """
    scored = []
    
    for tier, opportunities in all_opportunities.items():
        for opp in opportunities:
            # Get market data
            data = await get_market_data(opp['symbol'])
            
            # Calculate technical score
            tech_score = calculate_technical_score(data)
            
            # Calculate volume score
            volume_score = calculate_volume_score(data)
            
            # Catalyst bonus
            catalyst_score = 20 if opp.get('catalyst') else 0
            
            # Direction confirmation
            direction_score = confirm_direction(data, opp['direction'])
            
            # Total score
            total_score = tech_score + volume_score + catalyst_score + direction_score
            
            scored.append({
                **opp,
                'tier': tier,
                'score': total_score,
                'grade': get_grade(total_score)
            })
    
    # Sort by score
    scored.sort(key=lambda x: x['score'], reverse=True)
    
    return scored
```

### Step 4: Portfolio Construction

```python
def build_portfolio(scored_opportunities, account_value):
    """
    Build balanced portfolio respecting allocation targets.
    """
    portfolio = {
        'large_cap': [],
        'mid_cap': [],
        'small_cap': []
    }
    
    # Allocation targets
    targets = {
        'large_cap': 0.50,   # 50%
        'mid_cap': 0.35,     # 35%
        'small_cap': 0.15    # 15%
    }
    
    # Position size by tier
    position_sizes = {
        'large_cap': 0.04,   # 4% per position
        'mid_cap': 0.025,    # 2.5% per position
        'small_cap': 0.01    # 1% per position
    }
    
    # Select top opportunities from each tier
    for tier in ['large_cap', 'mid_cap', 'small_cap']:
        tier_opps = [o for o in scored_opportunities if o['tier'] == tier]
        tier_allocation = account_value * targets[tier]
        position_size = account_value * position_sizes[tier]
        
        max_positions = int(tier_allocation / position_size)
        
        # Take top N opportunities
        selected = tier_opps[:max_positions]
        
        for opp in selected:
            portfolio[tier].append({
                **opp,
                'position_value': position_size,
                'position_pct': position_sizes[tier],
                'shares': calculate_shares(position_size, opp['price'])
            })
    
    return portfolio
```

### Step 5: Execution with Direction

```python
async def execute_portfolio(portfolio):
    """
    Execute trades based on direction (LONG or SHORT).
    """
    for tier, positions in portfolio.items():
        for position in positions:
            symbol = position['symbol']
            direction = position['direction']
            shares = position['shares']
            
            if direction == 'LONG':
                # Buy to open long position
                await place_order(
                    symbol=symbol,
                    side='buy',
                    qty=shares,
                    type='limit',
                    limit_price=position['price'] * 1.002  # 0.2% above
                )
                
            elif direction == 'SHORT':
                # Sell short to open short position
                await place_order(
                    symbol=symbol,
                    side='sell',
                    qty=shares,
                    type='limit',
                    limit_price=position['price'] * 0.998  # 0.2% below
                )
            
            # Set stop loss and target
            await set_bracket_orders(
                symbol=symbol,
                direction=direction,
                entry_price=position['price'],
                target=position['target'],
                stop_loss=calculate_stop(position, tier)
            )
```

---

## Live Example: Let me test this RIGHT NOW

Let me run the Mid-Cap query with Perplexity to show you real results:
