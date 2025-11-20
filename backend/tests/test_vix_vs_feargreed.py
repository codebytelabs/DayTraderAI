"""Test to show difference between VIX and Fear & Greed Index."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("\n" + "="*80)
print("🔍 VIX vs FEAR & GREED INDEX COMPARISON")
print("="*80 + "\n")

# Test VIX Fetcher
print("1️⃣  FETCHING REAL VIX DATA")
print("-" * 80)

try:
    from indicators.vix_fetcher import get_vix_fetcher
    vix_fetcher = get_vix_fetcher()
    vix_value = vix_fetcher.get_vix()
    print(f"✅ Real VIX: {vix_value:.2f}")
    
    # Interpret VIX
    if vix_value < 15:
        vix_interpretation = "LOW volatility (calm market)"
    elif vix_value < 25:
        vix_interpretation = "NORMAL volatility"
    else:
        vix_interpretation = "HIGH volatility (fearful market)"
    
    print(f"   Interpretation: {vix_interpretation}")
except Exception as e:
    print(f"❌ Failed to fetch VIX: {e}")
    vix_value = None

print()

# Test Fear & Greed
print("2️⃣  FETCHING FEAR & GREED INDEX")
print("-" * 80)

try:
    from indicators.fear_greed_scraper import FearGreedScraper
    fg_scraper = FearGreedScraper()
    fg_data = fg_scraper.get_fear_greed_index()
    
    if fg_data:
        fg_value = fg_data['score']
        fg_label = fg_data['label']
        print(f"✅ Fear & Greed Index: {fg_value}/100 ({fg_label})")
        
        # Interpret Fear & Greed
        if fg_value < 25:
            fg_interpretation = "EXTREME FEAR (potential buying opportunity)"
        elif fg_value < 45:
            fg_interpretation = "FEAR (cautious sentiment)"
        elif fg_value < 55:
            fg_interpretation = "NEUTRAL"
        elif fg_value < 75:
            fg_interpretation = "GREED (optimistic sentiment)"
        else:
            fg_interpretation = "EXTREME GREED (potential selling opportunity)"
        
        print(f"   Interpretation: {fg_interpretation}")
    else:
        print("❌ Failed to fetch Fear & Greed Index")
        fg_value = None
except Exception as e:
    print(f"❌ Failed to fetch Fear & Greed: {e}")
    fg_value = None

print()

# Show the difference
print("3️⃣  KEY DIFFERENCES")
print("-" * 80)

print("\n📊 VIX (Volatility Index):")
print("   • Measures: IMPLIED VOLATILITY of S&P 500 options")
print("   • Scale: 10-80+ (lower = calmer, higher = more volatile)")
print("   • Use case: Position sizing, stop loss width, risk management")
print(f"   • Current: {vix_value:.2f if vix_value else 'N/A'}")

print("\n😱 Fear & Greed Index (CNN):")
print("   • Measures: MARKET SENTIMENT (composite of 7 indicators)")
print("   • Scale: 0-100 (0 = extreme fear, 100 = extreme greed)")
print("   • Use case: Trade direction bias, contrarian signals")
print(f"   • Current: {fg_value if fg_value else 'N/A'}/100")

print()

# Show impact on trading
print("4️⃣  IMPACT ON YOUR BOT")
print("-" * 80)

if vix_value and fg_value:
    print(f"\n✅ With REAL VIX ({vix_value:.2f}):")
    if vix_value < 20:
        print(f"   → Choppy regime multiplier: 0.75x (low volatility)")
        print(f"   → Wider stops acceptable, more aggressive sizing")
    elif vix_value <= 30:
        print(f"   → Choppy regime multiplier: 0.5x (medium volatility)")
        print(f"   → Standard risk management")
    else:
        print(f"   → Choppy regime multiplier: 0.25x (high volatility)")
        print(f"   → Very conservative, tight risk control")
    
    print(f"\n😱 With Fear & Greed ({fg_value}/100):")
    if fg_value < 35:
        print(f"   → Reject SHORT trades (bounce risk)")
        print(f"   → Favor LONG trades (contrarian)")
    elif fg_value > 65:
        print(f"   → Reject LONG trades (pullback risk)")
        print(f"   → Favor SHORT trades (contrarian)")
    else:
        print(f"   → Neutral bias, trade both directions")
    
    print(f"\n🎯 RECOMMENDATION:")
    print(f"   • Use VIX for: Volatility-based position sizing")
    print(f"   • Use Fear & Greed for: Sentiment-based trade filtering")
    print(f"   • Keep them SEPARATE - they measure different things!")

print("\n" + "="*80)
print("✅ TEST COMPLETE")
print("="*80 + "\n")
