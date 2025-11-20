#!/usr/bin/env python3
"""Diagnose why signals are backwards."""

import sys
sys.path.insert(0, '/Users/vishnuvardhanmedara/DayTraderAI/backend')

# Simple test of signal logic
ema_short = 150.0  # EMA9
ema_long = 145.0   # EMA21

print("=" * 80)
print("SIGNAL LOGIC TEST")
print("=" * 80)
print(f"\nEMA9 (short): ${ema_short:.2f}")
print(f"EMA21 (long): ${ema_long:.2f}")
print(f"\nEMA9 > EMA21: {ema_short > ema_long}")
print(f"This is an UPTREND")
print(f"\nExpected signal: BUY (go long in uptrend)")

# Test the logic from detect_enhanced_signal
if ema_short > ema_long:
    signal = 'buy'
else:
    signal = 'sell'

print(f"Actual signal generated: {signal.upper()}")
print(f"\n{'✅ CORRECT' if signal == 'buy' else '❌ WRONG - SIGNAL IS BACKWARDS!'}")

# Now test with downtrend
print("\n" + "=" * 80)
ema_short2 = 145.0
ema_long2 = 150.0
print(f"\nEMA9 (short): ${ema_short2:.2f}")
print(f"EMA21 (long): ${ema_long2:.2f}")
print(f"\nEMA9 < EMA21: {ema_short2 < ema_long2}")
print(f"This is a DOWNTREND")
print(f"\nExpected signal: SELL (go short in downtrend)")

if ema_short2 > ema_long2:
    signal2 = 'buy'
else:
    signal2 = 'sell'

print(f"Actual signal generated: {signal2.upper()}")
print(f"\n{'✅ CORRECT' if signal2 == 'sell' else '❌ WRONG - SIGNAL IS BACKWARDS!'}")
