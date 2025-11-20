#!/usr/bin/env python3
"""Check current signal generation for debugging."""

from data.market_data import MarketData
from data.features import FeatureEngine
from alpaca.trading.client import TradingClient
import os

api_key = os.getenv('ALPACA_API_KEY')
api_secret = os.getenv('ALPACA_SECRET_KEY')
alpaca = TradingClient(api_key, api_secret, paper=True)

market_data = MarketData(alpaca)
symbols = ['NVDA', 'AAPL', 'PLTR', 'MSFT', 'AMD']

print("=" * 80)
print("CURRENT SIGNAL ANALYSIS")
print("=" * 80)

for symbol in symbols:
    features = market_data.get_features(symbol)
    if features:
        signal_info = FeatureEngine.detect_enhanced_signal(features)
        
        print(f'\n{symbol}:')
        print(f'  Price: ${features.get("price", 0):.2f}')
        print(f'  EMA9: ${features.get("ema_short", 0):.2f}')
        print(f'  EMA21: ${features.get("ema_long", 0):.2f}')
        print(f'  EMA Diff: {features.get("ema_diff_pct", 0):.2f}%')
        print(f'  RSI: {features.get("rsi", 0):.1f}')
        
        ema9 = features.get("ema_short", 0)
        ema21 = features.get("ema_long", 0)
        print(f'  Trend: {"BULLISH (EMA9 > EMA21)" if ema9 > ema21 else "BEARISH (EMA9 < EMA21)"}')
        
        if signal_info:
            print(f'  Signal: {signal_info["signal"].upper()}')
            print(f'  Confidence: {signal_info["confidence"]:.1f}/100')
            print(f'  Confirmations: {signal_info["confirmation_count"]}/4 {signal_info["confirmations"]}')
        else:
            print(f'  Signal: NONE (no clear trend)')
