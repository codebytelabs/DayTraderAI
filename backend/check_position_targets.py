#!/usr/bin/env python3
"""Check position profit targets"""

import sys
sys.path.insert(0, '/Users/vishnuvardhanmedara/DayTraderAI/backend')

from core.alpaca_client import AlpacaClient

alpaca_client = AlpacaClient()

def check_targets():
    print("=" * 80)
    print("🎯 CHECKING POSITION PROFIT TARGETS")
    print("=" * 80)
    
    positions = alpaca_client.get_positions()
    
    for pos in positions:
        symbol = pos.symbol
        qty = float(pos.qty)
        side = pos.side
        entry = float(pos.avg_entry_price)
        current = float(pos.current_price)
        pnl = float(pos.unrealized_pl)
        pnl_pct = float(pos.unrealized_plpc) * 100
        
        print(f"\n{'='*80}")
        print(f"📊 {symbol} - {side.upper()} {abs(qty)} shares")
        print(f"   Entry: ${entry:.2f}")
        print(f"   Current: ${current:.2f}")
        print(f"   P&L: ${pnl:.2f} ({pnl_pct:+.2f}%)")
        
        # Calculate expected targets
        if side == 'buy':
            expected_tp = entry * 1.025  # 2.5% above
            expected_sl = entry * 0.985  # 1.5% below
        else:
            expected_tp = entry * 0.975  # 2.5% below
            expected_sl = entry * 1.015  # 1.5% above
        
        print(f"\n   🎯 Expected Targets:")
        print(f"      Take-Profit: ${expected_tp:.2f}")
        print(f"      Stop-Loss: ${expected_sl:.2f}")
        
        # Calculate R (risk)
        risk_per_share = abs(entry - expected_sl)
        current_r = abs(current - entry) / risk_per_share if risk_per_share > 0 else 0
        
        print(f"\n   📈 Profit Status:")
        print(f"      Risk per share: ${risk_per_share:.2f}")
        print(f"      Current R: {current_r:.2f}R")
        
        if current_r >= 2.0:
            print(f"      ✅ TRAILING STOPS SHOULD BE ACTIVE!")
        elif current_r >= 1.0:
            print(f"      ⏳ Approaching trailing stop activation (need 2.0R)")
        else:
            print(f"      ⏳ Not yet profitable enough for trailing stops")
    
    print(f"\n{'='*80}")

if __name__ == "__main__":
    check_targets()
