"""
Integration test for Intelligent Profit Protection System

Tests the complete system working together with simulated price movements.
"""

from unittest.mock import Mock, MagicMock
from trading.profit_protection import (
    get_profit_protection_manager,
    ProtectionStateEnum
)


def test_complete_position_lifecycle():
    """
    Test a complete position lifecycle from entry through 4R.
    Verifies all state transitions, stop updates, and profit taking.
    """
    # Create mock Alpaca client
    mock_alpaca = Mock()
    mock_alpaca.get_position = Mock(return_value=None)
    mock_alpaca.list_positions = Mock(return_value=[])
    
    # Create profit protection manager
    manager = get_profit_protection_manager(mock_alpaca)
    
    # Simulate opening a position
    symbol = "AAPL"
    entry_price = 150.00
    stop_loss = 147.00  # $3 risk (2%)
    quantity = 100
    
    print(f"\n{'='*60}")
    print(f"Testing Position Lifecycle: {symbol}")
    print(f"Entry: ${entry_price:.2f}, Stop: ${stop_loss:.2f}, Qty: {quantity}")
    print(f"{'='*60}\n")
    
    # Track the position
    position = manager.track_new_position(
        symbol=symbol,
        entry_price=entry_price,
        stop_loss=stop_loss,
        quantity=quantity,
        side='long'
    )
    
    assert position is not None
    assert position.r_multiple == 0.0
    assert position.protection_state.state == ProtectionStateEnum.INITIAL_RISK
    print(f"✅ Position opened: R=0.0, State=INITIAL_RISK\n")
    
    # Simulate price movement to 1.0R (breakeven)
    price_1r = 153.00  # Entry + $3 (1R)
    manager.tracker.update_current_price(symbol, price_1r)
    position = manager.tracker.get_position_state(symbol)
    
    assert abs(position.r_multiple - 1.0) < 0.01
    assert position.protection_state.state == ProtectionStateEnum.BREAKEVEN_PROTECTED
    print(f"✅ At 1.0R: Price=${price_1r:.2f}, State=BREAKEVEN_PROTECTED")
    
    # Check stop should move to breakeven
    new_stop = manager.stop_manager.calculate_trailing_stop(
        entry_price, price_1r, 3.0, 1.0
    )
    assert new_stop == entry_price
    print(f"   Stop should move to: ${new_stop:.2f} (breakeven)\n")
    
    # Simulate price movement to 2.0R
    price_2r = 156.00  # Entry + $6 (2R)
    manager.tracker.update_current_price(symbol, price_2r)
    position = manager.tracker.get_position_state(symbol)
    
    assert abs(position.r_multiple - 2.0) < 0.01
    print(f"✅ At 2.0R: Price=${price_2r:.2f}, State={position.protection_state.state.value}")
    
    # Check for profit action
    action = manager.profit_engine.check_profit_milestones(position)
    assert action is not None
    assert action.milestone == 2.0
    assert action.quantity == 50  # 50% of 100
    print(f"   Profit action: Exit {action.quantity} shares (50%)")
    
    # Check stop should lock in 1R
    new_stop = manager.stop_manager.calculate_trailing_stop(
        entry_price, price_2r, 3.0, 2.0
    )
    assert new_stop == 153.00  # Entry + 1R
    print(f"   Stop should move to: ${new_stop:.2f} (lock in 1R)\n")
    
    # Execute the partial exit
    result = manager.profit_engine.execute_partial_exit(symbol, 50, "2R milestone")
    assert result.success
    print(f"✅ Partial exit executed: {result.shares_sold} shares, ${result.profit_realized:.2f} profit\n")
    
    # Verify remaining quantity
    position = manager.tracker.get_position_state(symbol)
    assert position.share_allocation.remaining_quantity == 50
    assert len(position.share_allocation.partial_exits) == 1
    
    # Simulate price movement to 3.0R
    price_3r = 159.00  # Entry + $9 (3R)
    manager.tracker.update_current_price(symbol, price_3r)
    position = manager.tracker.get_position_state(symbol)
    
    assert abs(position.r_multiple - 3.0) < 0.01
    print(f"✅ At 3.0R: Price=${price_3r:.2f}, State={position.protection_state.state.value}")
    
    # Check for profit action
    action = manager.profit_engine.check_profit_milestones(position)
    assert action is not None
    assert action.milestone == 3.0
    assert action.quantity == 25  # 25% of original 100
    print(f"   Profit action: Exit {action.quantity} shares (25%)")
    
    # Check stop should lock in 1.5R
    new_stop = manager.stop_manager.calculate_trailing_stop(
        entry_price, price_3r, 3.0, 3.0
    )
    assert new_stop == 154.50  # Entry + 1.5R
    print(f"   Stop should move to: ${new_stop:.2f} (lock in 1.5R)\n")
    
    # Execute the partial exit
    result = manager.profit_engine.execute_partial_exit(symbol, 25, "3R milestone")
    assert result.success
    print(f"✅ Partial exit executed: {result.shares_sold} shares, ${result.profit_realized:.2f} profit\n")
    
    # Verify remaining quantity
    position = manager.tracker.get_position_state(symbol)
    assert position.share_allocation.remaining_quantity == 25
    assert len(position.share_allocation.partial_exits) == 2
    
    # Simulate price movement to 4.0R
    price_4r = 162.00  # Entry + $12 (4R)
    manager.tracker.update_current_price(symbol, price_4r)
    position = manager.tracker.get_position_state(symbol)
    
    assert abs(position.r_multiple - 4.0) < 0.01
    print(f"✅ At 4.0R: Price=${price_4r:.2f}, State={position.protection_state.state.value}")
    
    # Check for profit action
    action = manager.profit_engine.check_profit_milestones(position)
    assert action is not None
    assert action.milestone == 4.0
    assert action.quantity == 25  # Remaining shares
    print(f"   Profit action: Exit {action.quantity} shares (final 25%)")
    
    # Check stop should lock in 2R
    new_stop = manager.stop_manager.calculate_trailing_stop(
        entry_price, price_4r, 3.0, 4.0
    )
    assert new_stop == 156.00  # Entry + 2R
    print(f"   Stop should move to: ${new_stop:.2f} (lock in 2R)\n")
    
    # Execute the final exit
    result = manager.profit_engine.execute_partial_exit(symbol, 25, "4R milestone")
    assert result.success
    print(f"✅ Final exit executed: {result.shares_sold} shares, ${result.profit_realized:.2f} profit\n")
    
    # Get final summary
    summary = manager.get_position_summary(symbol)
    print(f"{'='*60}")
    print(f"Final Summary:")
    print(f"  Original Quantity: {summary['original_quantity']}")
    print(f"  Remaining Quantity: {summary['remaining_quantity']}")
    print(f"  Total Profit Realized: ${summary['profit_summary']['total_profit_realized']:.2f}")
    print(f"  Final R-Multiple: {summary['r_multiple']:.2f}")
    print(f"{'='*60}\n")
    
    print("🎉 Complete position lifecycle test PASSED!")


if __name__ == "__main__":
    test_complete_position_lifecycle()
