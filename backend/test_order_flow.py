"""
Test complete order flow to verify buying power fix
"""
import sys
from core.alpaca_client import AlpacaClient
from core.supabase_client import SupabaseClient
from trading.risk_manager import RiskManager
from utils.dynamic_position_sizer import DynamicPositionSizer
from utils.logger import setup_logger

logger = setup_logger(__name__)

def test_order_flow():
    """Test complete order flow from position sizing to risk check"""
    
    print("\n" + "="*80)
    print("COMPLETE ORDER FLOW TEST")
    print("="*80 + "\n")
    
    # Initialize components
    alpaca = AlpacaClient()
    supabase = SupabaseClient()
    risk_manager = RiskManager(alpaca)
    position_sizer = DynamicPositionSizer(alpaca)
    
    # Test parameters (from actual SOFI signal)
    symbol = "SOFI"
    side = "sell"
    entry_price = 28.35
    stop_price = 28.61
    stop_distance = abs(entry_price - stop_price)
    confidence = 74.0
    base_risk_pct = 0.005  # 0.5% (after time-based reduction)
    
    print(f"📊 TEST PARAMETERS:")
    print(f"  Symbol: {symbol}")
    print(f"  Side: {side.upper()}")
    print(f"  Entry Price: ${entry_price:.2f}")
    print(f"  Stop Price: ${stop_price:.2f}")
    print(f"  Stop Distance: ${stop_distance:.2f}")
    print(f"  Confidence: {confidence}%")
    print(f"  Risk %: {base_risk_pct*100:.2f}%")
    print()
    
    # Step 1: Position Sizing
    print("STEP 1: POSITION SIZING")
    print("-" * 80)
    qty, reasoning = position_sizer.calculate_optimal_size(
        symbol=symbol,
        price=entry_price,
        stop_distance=stop_distance,
        confidence=confidence,
        base_risk_pct=base_risk_pct,
        max_position_pct=0.10
    )
    
    print(f"  Calculated Quantity: {qty} shares")
    print(f"  Reasoning: {reasoning}")
    
    if qty == 0:
        print(f"  ❌ FAILED: Position sizer returned 0 shares")
        return False
    else:
        print(f"  ✅ PASSED: Position sizer returned {qty} shares")
    print()
    
    # Step 2: Risk Manager Check
    print("STEP 2: RISK MANAGER CHECK")
    print("-" * 80)
    
    approved, reason = risk_manager.check_order(
        symbol=symbol,
        side=side,
        qty=qty,
        price=entry_price
    )
    
    print(f"  Approved: {approved}")
    print(f"  Reason: {reason}")
    
    if not approved:
        print(f"  ❌ FAILED: Risk manager rejected order")
        print(f"     Rejection reason: {reason}")
        return False
    else:
        print(f"  ✅ PASSED: Risk manager approved order")
    print()
    
    # Step 3: Calculate order value
    print("STEP 3: ORDER VALUE CHECK")
    print("-" * 80)
    
    order_value = entry_price * qty
    account = alpaca.get_account()
    equity = float(account.equity)
    
    print(f"  Order Value: ${order_value:,.2f}")
    print(f"  Account Equity: ${equity:,.2f}")
    print(f"  Position Size: {(order_value/equity)*100:.2f}% of equity")
    
    if order_value > equity * 0.10:
        print(f"  ⚠️  WARNING: Position exceeds 10% of equity")
    else:
        print(f"  ✅ PASSED: Position within limits")
    print()
    
    # Summary
    print("="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    if qty > 0 and approved:
        print("✅ ALL CHECKS PASSED!")
        print(f"   Order ready: {side.upper()} {qty} {symbol} @ ${entry_price:.2f}")
        print(f"   Order value: ${order_value:,.2f}")
        print(f"   Stop loss: ${stop_price:.2f}")
        print(f"   Risk: ${qty * stop_distance:.2f}")
        return True
    else:
        print("❌ ORDER FLOW FAILED")
        if qty == 0:
            print("   Problem: Position sizer returned 0 shares")
        if not approved:
            print(f"   Problem: Risk manager rejected - {reason}")
        return False

if __name__ == "__main__":
    try:
        success = test_order_flow()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)
