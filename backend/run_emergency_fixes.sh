#!/bin/bash

echo "🚨 RUNNING EMERGENCY FIXES"
echo "=========================="
echo ""

echo "1️⃣ Fixing NFLX order conflicts..."
python backend/emergency_fix_order_conflicts.py

echo ""
echo "2️⃣ Momentum data fetching fixed in code ✅"
echo ""

echo "3️⃣ Checking current position status..."
python -c "
from core.alpaca_client import AlpacaClient
client = AlpacaClient()

positions = client.list_positions()
print(f'\n📊 Current Positions: {len(positions)}')
for pos in positions:
    pnl = float(pos.unrealized_pl)
    pnl_pct = float(pos.unrealized_plpc) * 100
    print(f'  {pos.symbol}: {pos.qty} shares | P/L: \${pnl:.2f} ({pnl_pct:+.2f}%)')

orders = client.get_orders(status='open')
print(f'\n📋 Open Orders: {len(orders)}')
for order in orders:
    print(f'  {order.symbol}: {order.side} {order.qty} @ {order.stop_price or order.limit_price} ({order.type})')
"

echo ""
echo "=========================="
echo "✅ Emergency fixes complete!"
echo ""
echo "⚠️  NEXT STEPS:"
echo "1. Restart the trading bot"
echo "2. Monitor logs for 'No bars response' (should be gone)"
echo "3. Watch for successful partial profit taking"
echo "4. Verify NFLX has both stop-loss AND take-profit"
