#!/usr/bin/env python3
"""
Test the dynamic position sizer to see how it adapts to buying power constraints.
"""

from core.alpaca_client import AlpacaClient
from utils.dynamic_position_sizer import DynamicPositionSizer

def test_dynamic_sizer():
    print("🎯 Testing Dynamic Position Sizer")
    print("=" * 60)
    
    # Initialize
    alpaca = AlpacaClient()
    sizer = DynamicPositionSizer(alpaca)
    
    # Get current status
    status = sizer.get_buying_power_status()
    print(f"💰 Account Status:")
    print(f"  Equity: ${status['equity']:,.0f}")
    print(f"  Day Trading BP: ${status['day_trading_bp']:,.0f}")
    print(f"  Open Positions: {status['positions_count']} (${status['positions_value']:,.0f})")
    
    # Test different stocks and confidence levels
    test_cases = [
        ("NVDA", 188.0, 65),   # High confidence
        ("TSLA", 445.0, 50),   # Medium confidence  
        ("AMD", 238.0, 75),    # High confidence
        ("META", 619.0, 40),   # Lower confidence
        ("AAPL", 186.0, 60),   # Medium-high confidence
    ]
    
    print(f"\n🧪 Position Sizing Tests:")
    print("-" * 60)
    
    for symbol, price, confidence in test_cases:
        qty, reasoning = sizer.calculate_optimal_size(
            symbol=symbol,
            price=price,
            confidence=confidence
        )
        
        if qty > 0:
            value = qty * price
            print(f"✅ {symbol:4s}: {qty:3d} shares @ ${price:6.2f} = ${value:8,.0f}")
            print(f"     {reasoning}")
        else:
            print(f"❌ {symbol:4s}: {reasoning}")
        print()
    
    print("=" * 60)
    print("✅ Dynamic sizer test complete!")

if __name__ == "__main__":
    test_dynamic_sizer()