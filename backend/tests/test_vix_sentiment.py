"""
Test VIX Sentiment Data Retrieval
"""

import os
import sys
from datetime import datetime, timedelta

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from core.alpaca_client import AlpacaClient
from indicators.sentiment_aggregator import SentimentAggregator


def test_vix_direct():
    """Test VIX data retrieval directly"""
    print("\n" + "="*80)
    print("  TEST 1: Direct VIX Data Retrieval")
    print("="*80 + "\n")
    
    try:
        alpaca = AlpacaClient()
        
        from alpaca.data.timeframe import TimeFrame
        
        end = datetime.now()
        start = end - timedelta(days=5)
        
        print(f"Fetching VIX data from {start.date()} to {end.date()}...")
        
        bars = alpaca.get_bars(
            'VIX',
            start=start.strftime('%Y-%m-%d'),
            end=end.strftime('%Y-%m-%d'),
            timeframe=TimeFrame.Day
        )
        
        print(f"Response type: {type(bars)}")
        print(f"Response: {bars}")
        
        if bars:
            print("✓ VIX data retrieved successfully")
            
            # Try to extract value
            import pandas as pd
            if isinstance(bars, dict):
                vix_bars = bars.get('VIX', [])
                if vix_bars:
                    current_vix = float(vix_bars[-1].close)
                    print(f"✓ Current VIX: {current_vix:.2f}")
                    return True
            elif isinstance(bars, pd.DataFrame):
                if not bars.empty:
                    current_vix = float(bars.iloc[-1]['close'])
                    print(f"✓ Current VIX: {current_vix:.2f}")
                    return True
            else:
                if bars and len(bars) > 0:
                    current_vix = float(bars[-1].close)
                    print(f"✓ Current VIX: {current_vix:.2f}")
                    return True
        
        print("✗ No VIX data returned")
        return False
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sentiment_aggregator():
    """Test sentiment aggregator"""
    print("\n" + "="*80)
    print("  TEST 2: Sentiment Aggregator")
    print("="*80 + "\n")
    
    try:
        alpaca = AlpacaClient()
        aggregator = SentimentAggregator(alpaca)
        
        print("Getting sentiment...")
        sentiment = aggregator.get_sentiment()
        
        print(f"\nSentiment Result:")
        print(f"  Score: {sentiment['score']}/100")
        print(f"  Classification: {sentiment['classification']}")
        print(f"  Source: {sentiment['source']}")
        print(f"  Confidence: {sentiment['confidence']}")
        
        if sentiment['source'] == 'vix':
            print(f"  VIX Value: {sentiment.get('vix_value', 'N/A')}")
            print("✓ VIX sentiment working")
            return True
        elif sentiment['source'] == 'perplexity':
            print("✓ Perplexity sentiment working")
            return True
        else:
            print("⚠️  Using default sentiment (sources failed)")
            return False
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_alternative_vix():
    """Test alternative VIX retrieval methods"""
    print("\n" + "="*80)
    print("  TEST 3: Alternative VIX Methods")
    print("="*80 + "\n")
    
    try:
        alpaca = AlpacaClient()
        
        # Try getting latest quote
        print("Trying latest quote for VIX...")
        try:
            quote = alpaca.get_latest_quote('VIX')
            if quote:
                print(f"✓ VIX quote: bid={quote.bid_price}, ask={quote.ask_price}")
                return True
        except Exception as e:
            print(f"  Quote failed: {e}")
        
        # Try getting latest trade
        print("\nTrying latest trade for VIX...")
        try:
            trade = alpaca.get_latest_trade('VIX')
            if trade:
                print(f"✓ VIX trade: price={trade.price}")
                return True
        except Exception as e:
            print(f"  Trade failed: {e}")
        
        # Try getting snapshot
        print("\nTrying snapshot for VIX...")
        try:
            snapshot = alpaca.get_snapshot('VIX')
            if snapshot:
                print(f"✓ VIX snapshot: {snapshot}")
                return True
        except Exception as e:
            print(f"  Snapshot failed: {e}")
        
        print("\n✗ All VIX methods failed")
        return False
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    print("\n" + "="*80)
    print("  VIX SENTIMENT DATA TEST")
    print("="*80)
    
    results = []
    
    # Test 1: Direct VIX
    passed = test_vix_direct()
    results.append(("Direct VIX", passed))
    
    # Test 2: Sentiment Aggregator
    passed = test_sentiment_aggregator()
    results.append(("Sentiment Aggregator", passed))
    
    # Test 3: Alternative methods
    passed = test_alternative_vix()
    results.append(("Alternative VIX", passed))
    
    # Summary
    print("\n" + "="*80)
    print("  TEST SUMMARY")
    print("="*80 + "\n")
    
    for test_name, passed in results:
        status = "✓" if passed else "✗"
        print(f"{status} {test_name}")
    
    passed_count = sum(1 for _, p in results if p)
    print(f"\nResults: {passed_count}/{len(results)} passed")
    
    if passed_count == 0:
        print("\n⚠️  VIX data not available from Alpaca")
        print("   Recommendation: Use web scraping for Fear & Greed Index")
        print("   Source: https://edition.cnn.com/markets/fear-and-greed")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
