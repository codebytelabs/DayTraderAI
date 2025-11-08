"""
Simple test of multi-cap query generation.
"""

import re
from datetime import datetime


def build_multi_cap_query():
    """Build the multi-cap discovery query."""
    current_time = datetime.now().strftime("%B %d, %Y at %I:%M %p ET")
    
    query = f"""MULTI-CAP INTRADAY OPPORTUNITIES - {current_time}

⏰ TIME HORIZON: Next 1-2 hours (INTRADAY ONLY)

Find opportunities across ALL market cap segments with BOTH directions:

═══════════════════════════════════════════════════════════
📊 TIER 1: LARGE-CAP (Market Cap >$10B)
═══════════════════════════════════════════════════════════

CRITERIA:
- Volume: >5M shares/day
- Focus: AAPL, MSFT, NVDA, GOOGL, AMZN, META, TSLA, AMD, SPY, QQQ
- Setups: VWAP, institutional flow, technical breakouts

Find 8 LONG + 7 SHORT opportunities

═══════════════════════════════════════════════════════════
📊 TIER 2: MID-CAP (Market Cap $2B-$10B)
═══════════════════════════════════════════════════════════

CRITERIA:
- Volume: >1M shares/day
- Focus: PLTR, COIN, SOFI, RIVN, SNOW, DKNG, CRWD, ZS, RBLX
- Setups: News catalysts, sector rotation, breakouts

Find 6 LONG + 6 SHORT opportunities

═══════════════════════════════════════════════════════════
📊 TIER 3: SMALL-CAP (Market Cap $300M-$2B, Price $5-$50)
═══════════════════════════════════════════════════════════

CRITERIA:
- Volume: >1M shares/day
- Price: $5-$50 (NO penny stocks <$5)
- MUST have news catalyst
- Focus: MARA, RIOT, AMC, GME, ZBIO, PUMP, SNDL
- Setups: Gap-and-go, volume spikes, short squeezes

Find 5 LONG + 5 SHORT opportunities

═══════════════════════════════════════════════════════════
📈 LONG SETUPS (All Tiers):
═══════════════════════════════════════════════════════════
- Breaking above resistance
- Positive catalysts/news
- Volume spike >2x average
- VWAP support holding
- Bullish momentum confirmed

═══════════════════════════════════════════════════════════
📉 SHORT SETUPS (All Tiers):
═══════════════════════════════════════════════════════════
- Breaking below support
- Negative catalysts/news
- Volume spike on selling
- VWAP resistance rejecting
- Bearish momentum confirmed

═══════════════════════════════════════════════════════════
REQUIRED OUTPUT FORMAT:
═══════════════════════════════════════════════════════════

**LARGE-CAP LONG:**
1. NVDA - $520, AI chip demand, breaking $515 resistance, volume 2x, Target $530
2. AAPL - $185, earnings beat, VWAP bounce, volume 1.8x, Target $188

**LARGE-CAP SHORT:**
1. TSLA - $240, delivery miss, breaking $242 support, volume 2.5x, Target $235

**MID-CAP LONG:**
1. PLTR - $25, contract win, breakout, volume 3x, Target $27
2. COIN - $180, Bitcoin rally, momentum, volume 2.5x, Target $190

**MID-CAP SHORT:**
1. RIVN - $15, production miss, breakdown, volume 4x, Target $13

**SMALL-CAP LONG:**
1. MARA - $18, Bitcoin +5%, gap-up, volume 8x, Target $22
2. ZBIO - $15, FDA approval, breakout, volume 10x, Target $20

**SMALL-CAP SHORT:**
1. SNDL - $3.50, sector weakness, breakdown, volume 5x, Target $3.00

Include: Symbol, Price, Catalyst, Setup, Volume, Target for EACH opportunity"""
    
    return query


def main():
    print("=" * 80)
    print("🚀 MULTI-CAP QUERY GENERATOR TEST")
    print("=" * 80)
    print()
    
    query = build_multi_cap_query()
    
    print("Generated Query:")
    print("-" * 80)
    print(query)
    print("-" * 80)
    print()
    
    # Count expected opportunities
    large_cap_long = 8
    large_cap_short = 7
    mid_cap_long = 6
    mid_cap_short = 6
    small_cap_long = 5
    small_cap_short = 5
    
    total = large_cap_long + large_cap_short + mid_cap_long + mid_cap_short + small_cap_long + small_cap_short
    
    print("Expected Opportunities:")
    print(f"  Large-cap: {large_cap_long} LONG + {large_cap_short} SHORT = {large_cap_long + large_cap_short}")
    print(f"  Mid-cap:   {mid_cap_long} LONG + {mid_cap_short} SHORT = {mid_cap_long + mid_cap_short}")
    print(f"  Small-cap: {small_cap_long} LONG + {small_cap_short} SHORT = {small_cap_long + small_cap_short}")
    print(f"  TOTAL:     {total} opportunities")
    print()
    
    print("✅ Query generated successfully!")
    print()
    print("This query will be sent to Perplexity to discover real opportunities.")
    print()


if __name__ == '__main__':
    main()
