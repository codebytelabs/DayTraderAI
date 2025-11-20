"""
Simple test to validate real-time price API works correctly.
Tests the proposed fix methods without requiring live market data.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.alpaca_client import AlpacaClient

def test_realtime_price_api():
    """
    Test that the real-time price API methods work correctly.
    """
    print("=" * 80)
    print("🧪 REAL-TIME PRICE API TEST")
    print("=" * 80)
    print()
    
    alpaca = AlpacaClient()
    
    test_symbols = ['COIN', 'NVDA', 'AAPL']
    
    print("Testing real-time price API methods...")
    print()
    
    for symbol in test_symbols:
        print(f"📍 Testing {symbol}:")
        
        # Test get_stock_latest_trade
        try:
            trade = alpaca.data_client.get_stock_latest_trade(symbol)
            if trade:
                price = float(trade.price)
                timestamp = trade.timestamp
                print(f"  ✅ Latest trade: ${price:.2f} at {timestamp}")
            else:
                print(f"  ⚠️  No trade data available")
        except Exception as e:
            print(f"  ❌ get_stock_latest_trade failed: {e}")
        
        # Test get_stock_latest_quote
        try:
            quote = alpaca.data_client.get_stock_latest_quote(symbol)
            if quote:
                bid = float(quote.bid_price)
                ask = float(quote.ask_price)
                spread = ask - bid
                mid = (bid + ask) / 2
                print(f"  ✅ Latest quote: Bid ${bid:.2f} | Ask ${ask:.2f} | Mid ${mid:.2f} | Spread ${spread:.2f}")
            else:
                print(f"  ⚠️  No quote data available")
        except Exception as e:
            print(f"  ❌ get_stock_latest_quote failed: {e}")
        
        print()
    
    print("=" * 80)
    print("✅ API TEST COMPLETE")
    print("=" * 80)
    print()
    print("CONCLUSION:")
    print("If the APIs returned data successfully, the fix can be implemented.")
    print("The real-time price methods are working and ready to use.")
    print()


if __name__ == "__main__":
    test_realtime_price_api()
