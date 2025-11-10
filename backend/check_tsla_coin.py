#!/usr/bin/env python3
"""Check TSLA and COIN trading history"""

from core.alpaca_client import AlpacaClient
from datetime import datetime, timedelta

alpaca = AlpacaClient()

# Get recent closed positions (last 7 days)
print('=' * 80)
print('RECENT CLOSED POSITIONS (Last 7 Days)')
print('=' * 80)
end = datetime.now()
start = end - timedelta(days=7)

activities = alpaca.trading_client.get_activities(activity_types='FILL', date=start.strftime('%Y-%m-%d'))

# Group by symbol
trades = {}
for activity in activities:
    symbol = activity.symbol
    if symbol not in trades:
        trades[symbol] = []
    trades[symbol].append({
        'time': activity.transaction_time,
        'side': activity.side,
        'qty': float(activity.qty),
        'price': float(activity.price),
        'type': activity.type
    })

# Show TSLA trades
if 'TSLA' in trades:
    print('\n🚗 TSLA TRADES:')
    for t in sorted(trades['TSLA'], key=lambda x: x['time']):
        print(f"  {t['time']} | {t['side']:4s} {t['qty']:6.0f} @ ${t['price']:8.2f} | {t['type']}")
    
    # Calculate P/L
    buys = [t for t in trades['TSLA'] if t['side'] == 'buy']
    sells = [t for t in trades['TSLA'] if t['side'] == 'sell']
    if buys and sells:
        avg_buy = sum(t['price'] * t['qty'] for t in buys) / sum(t['qty'] for t in buys)
        avg_sell = sum(t['price'] * t['qty'] for t in sells) / sum(t['qty'] for t in sells)
        total_qty = sum(t['qty'] for t in buys)
        pnl = (avg_sell - avg_buy) * total_qty
        pnl_pct = ((avg_sell - avg_buy) / avg_buy) * 100
        print(f"  📊 P/L: ${pnl:,.2f} ({pnl_pct:+.2f}%)")
else:
    print('\n🚗 TSLA: No recent trades')

# Show COIN trades
if 'COIN' in trades:
    print('\n🪙 COIN TRADES:')
    for t in sorted(trades['COIN'], key=lambda x: x['time']):
        print(f"  {t['time']} | {t['side']:4s} {t['qty']:6.0f} @ ${t['price']:8.2f} | {t['type']}")
    
    # Calculate P/L if closed
    buys = [t for t in trades['COIN'] if t['side'] == 'buy']
    sells = [t for t in trades['COIN'] if t['side'] == 'sell']
    if buys and sells:
        avg_buy = sum(t['price'] * t['qty'] for t in buys) / sum(t['qty'] for t in buys)
        avg_sell = sum(t['price'] * t['qty'] for t in sells) / sum(t['qty'] for t in sells)
        total_qty = sum(t['qty'] for t in buys)
        pnl = (avg_sell - avg_buy) * total_qty
        pnl_pct = ((avg_sell - avg_buy) / avg_buy) * 100
        print(f"  📊 P/L: ${pnl:,.2f} ({pnl_pct:+.2f}%)")
else:
    print('\n🪙 COIN: No recent trades')

# Get current positions
print('\n' + '=' * 80)
print('CURRENT OPEN POSITIONS')
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
        
        if pos.symbol == 'COIN':
            print(f"   ⚠️  COIN Details:")
            print(f"      Entry: ${entry:.2f}")
            print(f"      Current: ${current:.2f}")
            print(f"      Unrealized P/L: ${pnl:.2f} ({pnl_pct:+.2f}%)")

print('\n' + '=' * 80)
