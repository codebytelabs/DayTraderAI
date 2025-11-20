#!/usr/bin/env python3
"""
Test the buying power fix to ensure orders don't exceed available funds.
"""

from core.alpaca_client import AlpacaClient
from trading.risk_manager import RiskManager

def test_buying_power():
    print("🔍 Testing Buying Power Validation")
    print("=" * 50)
    
    # Initialize clients
    alpaca = AlpacaClient()
    risk_manager = RiskManager(alpaca)
    
    # Get account info
    account = alpaca.get_account()
    positions = alpaca.get_positions()
    
    print(f"📊 Account Status:")
    print(f"  Equity: ${float(account.equity):,.2f}")
    print(f"  Day Trading BP: ${float(account.daytrading_buying_power):,.2f}")
    print(f"  Open Positions: {len(positions)}")
    
    # Test various order sizes
    test_symbol = "NVDA"
    test_price = 188.0
    
    test_quantities = [10, 25, 50, 75, 100]
    
    print(f"\n🧪 Testing {test_symbol} orders at ${test_price:.2f}:")
    print("-" * 50)
    
    for qty in test_quantities:
        order_value = qty * test_price
        approved, reason = risk_manager.check_order(test_symbol, "sell", qty, test_price)
        
        status = "✅ APPROVED" if approved else "❌ REJECTED"
        print(f"  {qty:3d} shares (${order_value:>8,.2f}): {status}")
        if not approved:
            print(f"      Reason: {reason}")
    
    # Find the maximum safe order size
    print(f"\n🎯 Finding maximum safe order size:")
    max_safe_qty = 0
    for qty in range(1, 200):
        order_value = qty * test_price
        approved, reason = risk_manager.check_order(test_symbol, "sell", qty, test_price)
        if approved:
            max_safe_qty = qty
        else:
            break
    
    if max_safe_qty > 0:
        max_value = max_safe_qty * test_price
        print(f"  Maximum safe quantity: {max_safe_qty} shares (${max_value:,.2f})")
    else:
        print(f"  No orders can be placed with current buying power")
    
    print("\n" + "=" * 50)
    print("✅ Buying power test complete!")

if __name__ == "__main__":
    test_buying_power()