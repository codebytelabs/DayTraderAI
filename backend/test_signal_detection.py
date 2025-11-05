#!/usr/bin/env python3
"""
Test script to verify signal detection is working.
This simulates the trading engine's signal detection logic.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from core.alpaca_client import AlpacaClient
from core.supabase_client import SupabaseClient
from data.market_data import MarketDataManager
from data.features import FeatureEngine
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


def test_signal_detection():
    """Test if signals can be detected from current market data."""
    
    print("\n" + "="*60)
    print("SIGNAL DETECTION TEST")
    print("="*60 + "\n")
    
    # Initialize clients
    alpaca = AlpacaClient()
    supabase = SupabaseClient()
    market_data = MarketDataManager(alpaca, supabase)
    
    # Check market status
    is_open = alpaca.is_market_open()
    print(f"Market Status: {'🟢 OPEN' if is_open else '🔴 CLOSED'}")
    print(f"Watchlist: {', '.join(settings.watchlist_symbols)}")
    print(f"EMA Settings: Short={settings.ema_short}, Long={settings.ema_long}\n")
    
    # Fetch and analyze each symbol
    print("Analyzing symbols for signals...\n")
    
    signals_found = []
    no_signals = []
    errors = []
    
    for symbol in settings.watchlist_symbols:
        try:
            print(f"📊 {symbol}:")
            
            # Fetch historical data
            historical_bars = market_data.fetch_historical_bars([symbol], days=1)
            
            if symbol not in historical_bars:
                print(f"   ❌ No data available\n")
                errors.append(symbol)
                continue
            
            bars_df = historical_bars[symbol]
            print(f"   ✓ Fetched {len(bars_df)} bars")
            
            # Compute features
            features = market_data.compute_features(symbol, bars_df)
            
            if not features:
                print(f"   ❌ Failed to compute features\n")
                errors.append(symbol)
                continue
            
            # Display features
            print(f"   Price: ${features['price']:.2f}")
            print(f"   EMA({settings.ema_short}): ${features['ema_short']:.2f}")
            print(f"   EMA({settings.ema_long}): ${features['ema_long']:.2f}")
            print(f"   Prev EMA({settings.ema_short}): ${features['prev_ema_short']:.2f}")
            print(f"   Prev EMA({settings.ema_long}): ${features['prev_ema_long']:.2f}")
            print(f"   ATR: ${features['atr']:.2f}")
            
            # Check for signal
            signal = FeatureEngine.detect_ema_crossover(features)
            
            if signal:
                print(f"   🎯 SIGNAL DETECTED: {signal.upper()}")
                signals_found.append((symbol, signal))
            else:
                # Show relationship
                if features['ema_short'] > features['ema_long']:
                    print(f"   ➖ No signal (EMA{settings.ema_short} above EMA{settings.ema_long}, no crossover)")
                else:
                    print(f"   ➖ No signal (EMA{settings.ema_short} below EMA{settings.ema_long}, no crossover)")
                no_signals.append(symbol)
            
            print()
            
        except Exception as e:
            print(f"   ❌ Error: {e}\n")
            errors.append(symbol)
    
    # Summary
    print("="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total Symbols: {len(settings.watchlist_symbols)}")
    print(f"Signals Found: {len(signals_found)}")
    print(f"No Signals: {len(no_signals)}")
    print(f"Errors: {len(errors)}")
    
    if signals_found:
        print("\n🎯 SIGNALS DETECTED:")
        for symbol, signal in signals_found:
            print(f"   {symbol}: {signal.upper()}")
    else:
        print("\n➖ No crossover signals in current market conditions")
        print("   This is normal - crossovers don't happen frequently")
    
    if errors:
        print(f"\n❌ ERRORS:")
        for symbol in errors:
            print(f"   {symbol}")
    
    print("\n" + "="*60)
    
    # Test database save
    print("\nTesting database save...")
    try:
        # Try to save features for first symbol
        if settings.watchlist_symbols:
            test_symbol = settings.watchlist_symbols[0]
            historical_bars = market_data.fetch_historical_bars([test_symbol], days=1)
            if test_symbol in historical_bars:
                features = market_data.compute_features(test_symbol, historical_bars[test_symbol])
                if features:
                    print(f"✅ Features saved successfully for {test_symbol}")
                else:
                    print(f"❌ Failed to compute features for {test_symbol}")
            else:
                print(f"❌ No data for {test_symbol}")
    except Exception as e:
        print(f"❌ Database save error: {e}")
        print("   Make sure you've run the migration: supabase_migration_add_prev_ema.sql")
    
    print()


if __name__ == "__main__":
    test_signal_detection()
