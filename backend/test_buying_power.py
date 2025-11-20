"""
Test script to diagnose buying power issue
"""
import sys
from core.alpaca_client import AlpacaClient
from utils.logger import setup_logger

logger = setup_logger(__name__)

def test_buying_power():
    """Test buying power retrieval and logic"""
    
    print("\n" + "="*80)
    print("BUYING POWER DIAGNOSTIC TEST")
    print("="*80 + "\n")
    
    # Initialize Alpaca client
    alpaca = AlpacaClient()
    
    # Get account info
    account = alpaca.get_account()
    
    # Extract all buying power fields
    equity = float(account.equity)
    cash = float(account.cash)
    regular_bp = float(account.buying_power)
    daytrading_bp = float(account.daytrading_buying_power)
    is_pdt = account.pattern_day_trader
    
    print(f"📊 ACCOUNT STATUS:")
    print(f"  Equity:              ${equity:,.2f}")
    print(f"  Cash:                ${cash:,.2f}")
    print(f"  Regular BP:          ${regular_bp:,.2f}")
    print(f"  DayTrading BP:       ${daytrading_bp:,.2f}")
    print(f"  Pattern Day Trader:  {is_pdt}")
    print()
    
    # Test OLD logic (broken)
    print("🔴 OLD LOGIC (BROKEN):")
    if is_pdt:
        old_bp = daytrading_bp
        print(f"  Using daytrading_bp: ${old_bp:,.2f}")
    else:
        old_bp = regular_bp
        print(f"  Using regular_bp: ${old_bp:,.2f}")
    print(f"  Result: ${old_bp:,.2f} {'✅ OK' if old_bp > 0 else '❌ ZERO - BLOCKS ALL TRADES'}")
    print()
    
    # Test NEW logic (fixed)
    print("🟢 NEW LOGIC (FIXED):")
    if is_pdt and daytrading_bp > 0:
        new_bp = daytrading_bp
        print(f"  Using daytrading_bp: ${new_bp:,.2f}")
    else:
        new_bp = max(cash, regular_bp)
        print(f"  Fallback to max(cash, regular_bp): ${new_bp:,.2f}")
    print(f"  Result: ${new_bp:,.2f} {'✅ OK' if new_bp > 0 else '❌ STILL ZERO'}")
    print()
    
    # Test position sizing calculation
    print("💰 POSITION SIZING TEST:")
    test_symbol = "SOFI"
    test_price = 28.35
    test_qty = 485
    order_value = test_price * test_qty
    
    print(f"  Symbol: {test_symbol}")
    print(f"  Price: ${test_price:.2f}")
    print(f"  Quantity: {test_qty} shares")
    print(f"  Order Value: ${order_value:,.2f}")
    print()
    
    # Check if order would pass with OLD logic
    print(f"  OLD Logic Check:")
    if order_value <= old_bp:
        print(f"    ✅ PASS: ${order_value:,.2f} <= ${old_bp:,.2f}")
    else:
        print(f"    ❌ FAIL: ${order_value:,.2f} > ${old_bp:,.2f}")
    print()
    
    # Check if order would pass with NEW logic
    print(f"  NEW Logic Check:")
    if order_value <= new_bp:
        print(f"    ✅ PASS: ${order_value:,.2f} <= ${new_bp:,.2f}")
    else:
        print(f"    ❌ FAIL: ${order_value:,.2f} > ${new_bp:,.2f}")
    print()
    
    print("="*80)
    print("DIAGNOSIS COMPLETE")
    print("="*80 + "\n")
    
    # Summary
    if old_bp == 0 and new_bp > 0:
        print("✅ FIX CONFIRMED: New logic resolves the zero buying power issue!")
        print(f"   Old BP: ${old_bp:,.2f} (blocked trades)")
        print(f"   New BP: ${new_bp:,.2f} (allows trades)")
    elif old_bp == 0 and new_bp == 0:
        print("❌ PROBLEM PERSISTS: Both old and new logic return zero!")
        print("   This suggests a deeper issue with the Alpaca account.")
    else:
        print("⚠️  UNEXPECTED: Old logic was working?")
        print(f"   Old BP: ${old_bp:,.2f}")
        print(f"   New BP: ${new_bp:,.2f}")

if __name__ == "__main__":
    try:
        test_buying_power()
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)
