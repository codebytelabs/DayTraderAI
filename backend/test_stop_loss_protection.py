#!/usr/bin/env python3
"""
Test script for Stop Loss Protection Manager

This script tests the protection manager against current live positions
to verify it can create stop losses without conflicts.
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from core.alpaca_client import AlpacaClient
from core.state import trading_state
from trading.stop_loss_protection import StopLossProtectionManager
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


def test_protection_manager():
    """Test the stop loss protection manager."""
    
    print("\n" + "="*80)
    print("STOP LOSS PROTECTION MANAGER - TEST")
    print("="*80)
    
    # Initialize Alpaca client
    alpaca = AlpacaClient(
        api_key=settings.alpaca_api_key,
        secret_key=settings.alpaca_secret_key,
        base_url=settings.alpaca_base_url
    )
    
    print("\n📊 STEP 1: Load Current Positions")
    print("-" * 80)
    
    # Get positions from Alpaca
    positions = alpaca.get_positions()
    print(f"Found {len(positions)} open positions:")
    
    for pos in positions:
        print(f"\n  {pos.symbol}:")
        print(f"    Qty: {pos.qty}")
        print(f"    Entry: ${float(pos.avg_entry_price):.2f}")
        print(f"    Current: ${float(pos.current_price):.2f}")
        print(f"    P/L: ${float(pos.unrealized_pl):.2f} ({float(pos.unrealized_plpc)*100:.2f}%)")
        
        # Add to trading_state for testing
        from core.state import Position
        position = Position(
            symbol=pos.symbol,
            qty=float(pos.qty),
            side='buy',  # Assuming long
            avg_entry_price=float(pos.avg_entry_price),
            current_price=float(pos.current_price),
            unrealized_pl=float(pos.unrealized_pl),
            unrealized_pl_pct=float(pos.unrealized_plpc) * 100,
            market_value=float(pos.market_value)
        )
        trading_state.update_position(position)
    
    print("\n📊 STEP 2: Check Current Stop Loss Status")
    print("-" * 80)
    
    # Get all orders
    all_orders = alpaca.get_orders(status='all', limit=200)
    
    for pos in positions:
        symbol = pos.symbol
        
        # Check for active stop loss
        has_stop = False
        stop_status = "NONE"
        
        for order in all_orders:
            if order.symbol == symbol and order.type in ['stop', 'trailing_stop']:
                has_stop = True
                stop_status = f"{order.status} @ ${float(order.stop_price):.2f}" if hasattr(order, 'stop_price') else order.status
                break
        
        status_icon = "✅" if has_stop and 'new' in stop_status.lower() else "🚨"
        print(f"  {status_icon} {symbol}: {stop_status}")
    
    print("\n📊 STEP 3: Initialize Protection Manager")
    print("-" * 80)
    
    # Create protection manager
    protection_manager = StopLossProtectionManager(alpaca)
    print("✅ Protection manager initialized")
    
    print("\n📊 STEP 4: Run Protection Verification")
    print("-" * 80)
    
    # Run verification
    results = protection_manager.verify_all_positions()
    
    print("\nResults:")
    for symbol, status in results.items():
        icon = "✅" if status in ['protected', 'created'] else "❌"
        print(f"  {icon} {symbol}: {status.upper()}")
    
    print("\n📊 STEP 5: Verify Stop Losses Were Created")
    print("-" * 80)
    
    # Re-check orders
    all_orders = alpaca.get_orders(status='all', limit=200)
    
    for pos in positions:
        symbol = pos.symbol
        
        # Find stop loss orders
        stops = [
            order for order in all_orders
            if order.symbol == symbol and 
            order.type in ['stop', 'trailing_stop'] and
            order.status in ['new', 'accepted', 'pending_new']
        ]
        
        if stops:
            for stop in stops:
                stop_price = float(stop.stop_price) if hasattr(stop, 'stop_price') else 0
                print(f"  ✅ {symbol}: Stop loss at ${stop_price:.2f} (Status: {stop.status})")
        else:
            print(f"  ❌ {symbol}: NO ACTIVE STOP LOSS")
    
    print("\n📊 STEP 6: Protection Status Summary")
    print("-" * 80)
    
    status = protection_manager.get_protection_status()
    print(f"  Total Positions: {status['total_positions']}")
    print(f"  Protected: {status['protected_positions']}")
    print(f"  Unprotected: {status['unprotected']}")
    
    if status['unprotected'] == 0:
        print("\n✅ SUCCESS: All positions are protected!")
    else:
        print(f"\n⚠️  WARNING: {status['unprotected']} positions still unprotected")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    
    # Return success status
    return status['unprotected'] == 0


if __name__ == "__main__":
    try:
        success = test_protection_manager()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)
