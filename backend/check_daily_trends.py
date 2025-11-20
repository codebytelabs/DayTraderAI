#!/usr/bin/env python3
"""Check daily trend data."""

import sys
sys.path.insert(0, '/Users/vishnuvardhanmedara/DayTraderAI/backend')

from data.daily_cache import get_daily_cache

daily_cache = get_daily_cache()
symbols = ['NVDA', 'AMD', 'AAPL', 'TSLA', 'PLTR', 'MSFT']

print("=" * 80)
print("DAILY TREND DATA")
print("=" * 80)

for symbol in symbols:
    daily_data = daily_cache.get_daily_data(symbol)
    if daily_data:
        print(f"\n{symbol}:")
        print(f"  Daily Trend: {daily_data['trend']}")
        print(f"  Daily Price: ${daily_data['price']:.2f}")
        print(f"  Daily EMA9: ${daily_data['ema_9']:.2f}")
        print(f"  Daily EMA21: ${daily_data['ema_21']:.2f}")
        print(f"  Daily 200-EMA: ${daily_data['ema_200']:.2f}")
        print(f"  EMA9 > EMA21: {daily_data['ema_9'] > daily_data['ema_21']}")
    else:
        print(f"\n{symbol}: NO DAILY DATA")
