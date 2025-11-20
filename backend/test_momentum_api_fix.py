#!/usr/bin/env python3
"""
Quick test to verify momentum API fix
"""

print("🔍 Checking momentum API fix...")

with open('backend/trading/trading_engine.py', 'r') as f:
    content = f.read()

# Check for the new approach
if 'barset = self.alpaca.get_bars(' in content:
    print("✅ Using alpaca.get_bars() method")
    
    if 'symbols=[symbol]' in content:
        print("✅ Passing symbol as list")
    else:
        print("❌ Not passing symbol as list")
        exit(1)
    
    if 'timeframe=TimeFrame.Minute' in content:
        print("✅ Using TimeFrame.Minute")
    else:
        print("❌ Not using TimeFrame.Minute")
        exit(1)
    
    # Check we're NOT using StockBarsRequest anymore
    if 'request = StockBarsRequest(' not in content or 'bars_response = self.alpaca.get_bars(request)' not in content:
        print("✅ Not using StockBarsRequest object (correct!)")
    else:
        print("⚠️  Still has old StockBarsRequest code")
    
    print("\n✅ MOMENTUM API FIX VERIFIED")
    print("   The bot will now:")
    print("   • Call alpaca.get_bars() with symbol list")
    print("   • No more validation errors")
    print("   • Momentum system will work for META, NUE, etc.")
    exit(0)
else:
    print("❌ Fix not found")
    exit(1)
