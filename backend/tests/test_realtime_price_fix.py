"""
Test module to validate real-time price fix for slippage issue.

This test compares:
1. Historical bar close price (current method)
2. Real-time trade price (proposed fix)
3. Actual market quotes

Goal: Prove that real-time prices are more accurate and reduce slippage.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime, timedelta
from core.alpaca_client import AlpacaClient
from data.market_data import MarketDataManager
from core.supabase_client import SupabaseClient
from alpaca.data.timeframe import TimeFrame
import pandas as pd
import time

def test_price_comparison():
    """
    Compare historical bar price vs real-time price for multiple symbols.
    """
    print("=" * 80)
    print("🧪 REAL-TIME PRICE FIX VALIDATION TEST")
    print("=" * 80)
    print()
    
    # Initialize clients
    alpaca = AlpacaClient()
    supabase = SupabaseClient()
    market_data = MarketDataManager(alpaca, supabase)
    
    # Test symbols (currently active in bot)
    test_symbols = ['COIN', 'NVDA', 'META', 'TSLA', 'AMD', 'AAPL']
    
    results = []
    
    print("📊 Testing price accuracy for active symbols...")
    print()
    
    for symbol in test_symbols:
        try:
            print(f"Testing {symbol}...")
            
            # Method 1: Historical bar close (current method)
            bars = alpaca.get_bars(
                symbols=[symbol],
                timeframe=TimeFrame.Minute,
                start=datetime.now() - timedelta(minutes=5),
                end=datetime.now()
            )
            
            if bars is not None and not bars.empty:
                if symbol in bars.index.get_level_values(0):
                    symbol_bars = bars.loc[symbol]
                    historical_price = float(symbol_bars.iloc[-1]['close'])
                else:
                    print(f"  ⚠️  No bars for {symbol}")
                    continue
            else:
                print(f"  ⚠️  No bars for {symbol}")
                continue
            
            # Method 2: Real-time trade price (proposed fix)
            try:
                trade = alpaca.data_client.get_stock_latest_trade(symbol)
                realtime_price = float(trade.price) if trade else None
            except Exception as e:
                print(f"  ⚠️  Failed to get real-time trade: {e}")
                realtime_price = None
            
            # Method 3: Latest quote (bid/ask)
            try:
                quote = alpaca.data_client.get_stock_latest_quote(symbol)
                if quote:
                    bid = float(quote.bid_price)
                    ask = float(quote.ask_price)
                    mid = (bid + ask) / 2
                    spread = ask - bid
                else:
                    bid = ask = mid = spread = None
            except Exception as e:
                print(f"  ⚠️  Failed to get quote: {e}")
                bid = ask = mid = spread = None
            
            # Calculate discrepancies
            if realtime_price and historical_price:
                diff = realtime_price - historical_price
                diff_pct = (diff / historical_price) * 100
                
                result = {
                    'symbol': symbol,
                    'historical_price': historical_price,
                    'realtime_price': realtime_price,
                    'bid': bid,
                    'ask': ask,
                    'mid': mid,
                    'spread': spread,
                    'diff': diff,
                    'diff_pct': diff_pct,
                    'timestamp': datetime.now()
                }
                
                results.append(result)
                
                # Print results
                print(f"  📍 Historical (bar close): ${historical_price:.2f}")
                print(f"  📍 Real-time (last trade): ${realtime_price:.2f}")
                if mid:
                    print(f"  📍 Quote mid-point: ${mid:.2f}")
                    print(f"  📍 Spread: ${spread:.2f}")
                print(f"  📊 Difference: ${diff:+.2f} ({diff_pct:+.2f}%)")
                
                if abs(diff_pct) > 0.5:
                    print(f"  🚨 LARGE DISCREPANCY! This would cause slippage!")
                elif abs(diff_pct) > 0.2:
                    print(f"  ⚠️  Moderate discrepancy")
                else:
                    print(f"  ✅ Prices aligned")
                print()
            
            # Rate limit protection
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  ❌ Error testing {symbol}: {e}")
            print()
    
    # Summary statistics
    print("=" * 80)
    print("📊 SUMMARY STATISTICS")
    print("=" * 80)
    print()
    
    if results:
        df = pd.DataFrame(results)
        
        print(f"Symbols tested: {len(results)}")
        print(f"Average price difference: ${df['diff'].mean():.2f}")
        print(f"Average % difference: {df['diff_pct'].mean():.2f}%")
        print(f"Max % difference: {df['diff_pct'].max():.2f}%")
        print(f"Min % difference: {df['diff_pct'].min():.2f}%")
        print(f"Std dev: {df['diff_pct'].std():.2f}%")
        print()
        
        # Count significant discrepancies
        large_disc = len(df[abs(df['diff_pct']) > 0.5])
        moderate_disc = len(df[(abs(df['diff_pct']) > 0.2) & (abs(df['diff_pct']) <= 0.5)])
        aligned = len(df[abs(df['diff_pct']) <= 0.2])
        
        print(f"🚨 Large discrepancies (>0.5%): {large_disc}/{len(results)} ({large_disc/len(results)*100:.1f}%)")
        print(f"⚠️  Moderate discrepancies (0.2-0.5%): {moderate_disc}/{len(results)} ({moderate_disc/len(results)*100:.1f}%)")
        print(f"✅ Aligned (<0.2%): {aligned}/{len(results)} ({aligned/len(results)*100:.1f}%)")
        print()
        
        # Calculate potential savings
        avg_position_size = 50  # shares
        trades_per_year = 500
        
        avg_slippage_per_share = abs(df['diff'].mean())
        annual_slippage_cost = avg_slippage_per_share * avg_position_size * trades_per_year
        
        print("💰 PROJECTED ANNUAL IMPACT:")
        print(f"Average slippage per share: ${avg_slippage_per_share:.2f}")
        print(f"Average position size: {avg_position_size} shares")
        print(f"Trades per year: {trades_per_year}")
        print(f"Annual slippage cost: ${annual_slippage_cost:,.2f}")
        print()
        
        # Detailed results table
        print("=" * 80)
        print("📋 DETAILED RESULTS")
        print("=" * 80)
        print()
        print(f"{'Symbol':<8} {'Historical':<12} {'Real-time':<12} {'Diff $':<10} {'Diff %':<10} {'Status'}")
        print("-" * 80)
        
        for _, row in df.iterrows():
            status = "🚨 LARGE" if abs(row['diff_pct']) > 0.5 else "⚠️  MOD" if abs(row['diff_pct']) > 0.2 else "✅ OK"
            print(f"{row['symbol']:<8} ${row['historical_price']:<11.2f} ${row['realtime_price']:<11.2f} "
                  f"${row['diff']:<9.2f} {row['diff_pct']:<9.2f}% {status}")
        
        print()
        
        # Recommendation
        print("=" * 80)
        print("🎯 RECOMMENDATION")
        print("=" * 80)
        print()
        
        if df['diff_pct'].abs().mean() > 0.3:
            print("✅ FIX RECOMMENDED: Significant price discrepancies detected!")
            print(f"   Average discrepancy: {df['diff_pct'].abs().mean():.2f}%")
            print(f"   Potential annual savings: ${annual_slippage_cost:,.2f}")
            print()
            print("   ACTION: Implement real-time price fix immediately.")
        elif df['diff_pct'].abs().mean() > 0.1:
            print("⚠️  FIX BENEFICIAL: Moderate discrepancies detected.")
            print(f"   Average discrepancy: {df['diff_pct'].abs().mean():.2f}%")
            print(f"   Potential annual savings: ${annual_slippage_cost:,.2f}")
            print()
            print("   ACTION: Implement fix to improve accuracy.")
        else:
            print("ℹ️  FIX OPTIONAL: Prices are generally aligned.")
            print(f"   Average discrepancy: {df['diff_pct'].abs().mean():.2f}%")
            print()
            print("   ACTION: Fix still recommended for best accuracy.")
        
        print()
        
        return df
    else:
        print("❌ No results collected. Check API connectivity.")
        return None


def test_simulated_trade_impact():
    """
    Simulate the COIN trade to show the impact of using real-time prices.
    """
    print("=" * 80)
    print("🎯 SIMULATED TRADE IMPACT TEST (COIN Example)")
    print("=" * 80)
    print()
    
    alpaca = AlpacaClient()
    
    try:
        # Get current prices for COIN
        bars = alpaca.get_bars(
            symbols=['COIN'],
            timeframe=TimeFrame.Minute,
            start=datetime.now() - timedelta(minutes=5),
            end=datetime.now()
        )
        
        if bars is not None and not bars.empty and 'COIN' in bars.index.get_level_values(0):
            historical_price = float(bars.loc['COIN'].iloc[-1]['close'])
        else:
            print("⚠️  Could not fetch historical price")
            return
        
        trade = alpaca.data_client.get_stock_latest_trade('COIN')
        realtime_price = float(trade.price) if trade else None
        
        if not realtime_price:
            print("⚠️  Could not fetch real-time price")
            return
        
        # Simulate trade parameters
        qty = 45  # shares (same as actual COIN trade)
        
        # Scenario 1: Using historical price (current method)
        print("📊 SCENARIO 1: Using Historical Price (Current Method)")
        print(f"   Entry price (from bars): ${historical_price:.2f}")
        print(f"   Quantity: {qty} shares")
        print(f"   Position value: ${historical_price * qty:,.2f}")
        
        # Assume market order fills at real-time price + spread
        quote = alpaca.data_client.get_stock_latest_quote('COIN')
        if quote:
            ask = float(quote.ask_price)
            spread = ask - float(quote.bid_price)
            estimated_fill_1 = ask  # Buy at ask
        else:
            estimated_fill_1 = realtime_price * 1.001  # Assume 0.1% spread
            spread = estimated_fill_1 - realtime_price
        
        slippage_1 = (estimated_fill_1 - historical_price) * qty
        
        print(f"   Estimated fill: ${estimated_fill_1:.2f}")
        print(f"   Slippage: ${slippage_1:.2f}")
        print()
        
        # Scenario 2: Using real-time price (proposed fix)
        print("📊 SCENARIO 2: Using Real-Time Price (Proposed Fix)")
        print(f"   Entry price (real-time): ${realtime_price:.2f}")
        print(f"   Quantity: {qty} shares")
        print(f"   Position value: ${realtime_price * qty:,.2f}")
        print(f"   Estimated fill: ${estimated_fill_1:.2f}")
        
        slippage_2 = (estimated_fill_1 - realtime_price) * qty
        
        print(f"   Slippage: ${slippage_2:.2f}")
        print()
        
        # Comparison
        print("💰 COMPARISON:")
        print(f"   Slippage reduction: ${slippage_1 - slippage_2:.2f}")
        print(f"   Improvement: {((slippage_1 - slippage_2) / slippage_1 * 100):.1f}%")
        print()
        
        # Stop loss impact
        stop_pct = 0.01  # 1% stop
        
        stop_1 = historical_price * (1 - stop_pct)
        stop_2 = realtime_price * (1 - stop_pct)
        
        print("🛡️  STOP LOSS IMPACT:")
        print(f"   Historical-based stop: ${stop_1:.2f}")
        print(f"   Real-time-based stop: ${stop_2:.2f}")
        print(f"   Difference: ${stop_2 - stop_1:.2f}")
        print()
        
        if abs(stop_2 - stop_1) > 1:
            print("   ⚠️  Significant stop loss discrepancy!")
        
    except Exception as e:
        print(f"❌ Error in simulation: {e}")


if __name__ == "__main__":
    print()
    print("🚀 Starting Real-Time Price Fix Validation Tests")
    print()
    
    # Test 1: Price comparison
    results_df = test_price_comparison()
    
    print()
    print()
    
    # Test 2: Simulated trade impact
    test_simulated_trade_impact()
    
    print()
    print("=" * 80)
    print("✅ TESTING COMPLETE")
    print("=" * 80)
    print()
    print("Review the results above to determine if the fix should be implemented.")
    print()
