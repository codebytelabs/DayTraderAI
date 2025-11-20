#!/usr/bin/env python3
"""Test the symbol cooldown system"""

from core.supabase_client import SupabaseClient
from trading.symbol_cooldown import SymbolCooldownManager

print("=" * 80)
print("SYMBOL COOLDOWN SYSTEM TEST")
print("=" * 80)

# Initialize
supabase = SupabaseClient()
cooldown_mgr = SymbolCooldownManager(supabase)

print("\n1. CHECKING ACTIVE COOLDOWNS")
print("-" * 80)
active = cooldown_mgr.get_active_cooldowns()
if active:
    for symbol, info in active.items():
        print(f"🚫 {symbol}:")
        print(f"   Consecutive Losses: {info['consecutive_losses']}")
        print(f"   Hours Remaining: {info['hours_remaining']:.1f}h")
        print(f"   Cooldown Until: {info['cooldown_until']}")
else:
    print("✅ No active cooldowns")

print("\n2. TESTING SYMBOL CHECKS")
print("-" * 80)

test_symbols = ['TSLA', 'COIN', 'NVDA', 'AAPL']
for symbol in test_symbols:
    is_allowed, reason = cooldown_mgr.is_symbol_allowed(symbol)
    if is_allowed:
        print(f"✅ {symbol}: ALLOWED")
    else:
        print(f"🚫 {symbol}: BLOCKED - {reason}")

print("\n3. POSITION SIZE MULTIPLIERS")
print("-" * 80)
for symbol in test_symbols:
    multiplier = cooldown_mgr.get_position_size_multiplier(symbol)
    confidence_boost = cooldown_mgr.get_confidence_boost_required(symbol)
    
    if multiplier < 1.0 or confidence_boost > 0:
        print(f"⚠️  {symbol}:")
        print(f"   Position Size: {multiplier*100:.0f}% of normal")
        print(f"   Confidence Boost Required: +{confidence_boost:.0f} points")

print("\n4. RECENT TRADE HISTORY (for context)")
print("-" * 80)
trades = supabase.get_trades(limit=20)

for symbol in ['TSLA', 'COIN']:
    symbol_trades = [t for t in trades if t.get('symbol') == symbol]
    if symbol_trades:
        print(f"\n{symbol} Recent Trades:")
        for t in symbol_trades[:5]:  # Last 5 trades
            pnl = t.get('pnl', 0)
            emoji = '✅' if pnl > 0 else '❌'
            print(f"  {emoji} {t.get('exit_time', 'N/A')[:19]} | P/L: ${pnl:7.2f} | {t.get('reason', 'N/A')}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
