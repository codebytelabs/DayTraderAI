#!/usr/bin/env python3
"""
Emergency script to close the TSLA position.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from core.alpaca_client import AlpacaClient
from utils.logger import setup_logger

logger = setup_logger(__name__)


def close_tsla():
    """Close the TSLA position."""
    
    print("\n" + "="*60)
    print("CLOSING TSLA POSITION")
    print("="*60 + "\n")
    
    alpaca = AlpacaClient()
    
    try:
        # Get current positions
        positions = alpaca.get_positions()
        
        tsla_position = None
        for pos in positions:
            if pos.symbol == "TSLA":
                tsla_position = pos
                break
        
        if not tsla_position:
            print("❌ No TSLA position found")
            return
        
        # Display position details
        qty = float(tsla_position.qty)
        current_price = float(tsla_position.current_price)
        avg_entry = float(tsla_position.avg_entry_price)
        market_value = float(tsla_position.market_value)
        unrealized_pl = float(tsla_position.unrealized_pl)
        
        print(f"Current TSLA Position:")
        print(f"  Quantity: {qty:,.0f} shares")
        print(f"  Entry Price: ${avg_entry:.2f}")
        print(f"  Current Price: ${current_price:.2f}")
        print(f"  Market Value: ${market_value:,.2f}")
        print(f"  Unrealized P/L: ${unrealized_pl:,.2f}")
        print()
        
        # Confirm
        response = input("Close this position? (yes/no): ")
        
        if response.lower() != 'yes':
            print("❌ Cancelled")
            return
        
        print("\n🔄 Closing position...")
        
        # Close position
        alpaca.close_position("TSLA")
        
        print("✅ TSLA position closed successfully")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Failed to close TSLA position: {e}", exc_info=True)


if __name__ == "__main__":
    close_tsla()
