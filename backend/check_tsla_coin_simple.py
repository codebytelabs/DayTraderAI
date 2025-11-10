#!/usr/bin/env python3
"""Check TSLA and COIN from Supabase"""

from core.supabase_client import SupabaseClient
from core.alpaca_client import AlpacaClient

supabase = SupabaseClient()
alpaca = AlpacaClient()

print('=' * 80)
print('RECENT TRADES FROM DATABASE')
print('=' * 80)

# Get recent trades
trades = supabase.get_trades(limit=50)

tsla_trades = [t for t in trades if t.get('symbol') == 'TSLA']
coin_trades = [t for t in trades if t.get('symbol') == 'COIN']

if tsla_trades:
    print('\n🚗 TSLA TRADES:')
    for t in tsla_trades:
        print(f"  {t.get('exit_time', t.get('timestamp', 'N/A'))} | {t.get('side', 'N/A'):4s} {t.get('qty', 0):6.0f} @ ${t.get('entry_price', 0):8.2f} → ${t.get('exit_price', 0):8.2f}")
        print(f"     P/L: ${t.get('pnl', 0):8.2f} ({t.get('pnl_pct', 0):+6.2f}%) | Reason: {t.get('reason', 'N/A')}")
else:
    print('\n🚗 TSLA: No trades in database')

if coin_trades:
    print('\n🪙 COIN TRADES:')
    for t in coin_trades:
        print(f"  {t.get('exit_time', t.get('timestamp', 'N/A'))} | {t.get('side', 'N/A'):4s} {t.get('qty', 0):6.0f} @ ${t.get('entry_price', 0):8.2f} → ${t.get('exit_price', 0):8.2f}")
        print(f"     P/L: ${t.get('pnl', 0):8.2f} ({t.get('pnl_pct', 0):+6.2f}%) | Reason: {t.get('reason', 'N/A')}")
else:
    print('\n🪙 COIN: No trades in database')

# Get current positions
print('\n' + '=' * 80)
print('CURRENT OPEN POSITIONS FROM ALPACA')
print('=' * 80)
positions = alpaca.get_positions()

if not positions:
    print('No open positions')
else:
    for pos in positions:
        pnl = float(pos.unrealized_pl)
        pnl_pct = float(pos.unrealized_plpc) * 100
        entry = float(pos.avg_entry_price)
        current = float(pos.current_price)
        qty = int(pos.qty)
        
        emoji = '📈' if pnl > 0 else '📉'
        print(f"{emoji} {pos.symbol:6s} | {qty:4d} shares @ ${entry:8.2f} | Now: ${current:8.2f} | P/L: ${pnl:8.2f} ({pnl_pct:+6.2f}%)")
        
        if pos.symbol in ['COIN', 'TSLA']:
            print(f"   ⚠️  {pos.symbol} Entry Analysis:")
            print(f"      Entry Price: ${entry:.2f}")
            print(f"      Current Price: ${current:.2f}")
            print(f"      Move: {pnl_pct:+.2f}%")

print('\n' + '=' * 80)
