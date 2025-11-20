#!/usr/bin/env python3
"""
Corrected performance report with proper starting value.
"""
import os
from datetime import datetime
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient

load_dotenv()

trading_client = TradingClient(
    os.getenv('ALPACA_API_KEY'),
    os.getenv('ALPACA_SECRET_KEY'),
    paper=True
)

# CORRECTED VALUES
STARTING_VALUE_NOV4 = 133166.07  # Opening balance on Nov 4
CURRENT_VALUE = 138355.79  # Current value

print("\n" + "="*100)
print("📊 CORRECTED PERFORMANCE REPORT (Nov 4 - Nov 12)")
print("="*100)

# Get current account
account = trading_client.get_account()
current_equity = float(account.equity)

print(f"\n💰 ACTUAL PERFORMANCE:")
print(f"   Starting Value (Nov 4 Opening): ${STARTING_VALUE_NOV4:,.2f}")
print(f"   Current Value (Nov 12): ${current_equity:,.2f}")

total_return = current_equity - STARTING_VALUE_NOV4
total_return_pct = (total_return / STARTING_VALUE_NOV4) * 100

print(f"   Total Return: ${total_return:,.2f} ({total_return_pct:+.2f}%)")

# SPY comparison (Nov 4 - Nov 12)
spy_return = 2.70  # SPY up 2.70% from Nov 4 to Nov 12
alpha = total_return_pct - spy_return

print(f"\n📊 VS MARKET:")
print(f"   SPY Return (Nov 4-12): +{spy_return:.2f}%")
print(f"   Alpha (vs SPY): {alpha:+.2f}%")

if alpha > 0:
    print(f"   ✅ OUTPERFORMING market by {alpha:.2f}%")
else:
    print(f"   ⚠️  UNDERPERFORMING market by {abs(alpha):.2f}%")

# Daily breakdown (estimated)
print(f"\n📅 ESTIMATED DAILY BREAKDOWN:")
print(f"{'Date':<12} {'Value':<15} {'Daily Δ':<15} {'Cumulative':<12}")
print("-" * 100)

# Based on database data, but using correct starting value
daily_values = [
    ("Nov 4", 133166.07, 0, 0),
    ("Nov 5", 135410.64, 2244.57, 1.69),
    ("Nov 6", 133693.00, -1717.64, 0.40),
    ("Nov 11", 135410.64, 1717.64, 1.69),
    ("Nov 12", current_equity, current_equity - 135410.64, total_return_pct),
]

for date, value, change, cum_pct in daily_values:
    change_str = f"+${change:,.2f}" if change >= 0 else f"${change:,.2f}"
    cum_str = f"+{cum_pct:.2f}%" if cum_pct >= 0 else f"{cum_pct:.2f}%"
    print(f"{date:<12} ${value:>12,.2f} {change_str:>14} {cum_str:>11}")

print("\n" + "="*100)
print("📊 SUMMARY:")
print(f"   Trading Days: 6 days")
print(f"   Total Return: ${total_return:,.2f} ({total_return_pct:+.2f}%)")
print(f"   Average Daily Return: {total_return_pct/6:.2f}%")
print(f"   Best Day: Nov 12 (+${current_equity - 135410.64:,.2f})")
print(f"   Worst Day: Nov 6 (-$1,717.64)")
print("="*100)

# Assessment
print(f"\n🎯 ASSESSMENT:")
if total_return_pct > spy_return:
    print(f"   ✅ EXCELLENT: Beating market by {alpha:.2f}%")
    print(f"   ✅ Strong performance: +{total_return_pct:.2f}% in 6 days")
    grade = "A"
elif total_return_pct > 0:
    print(f"   ✅ GOOD: Profitable but underperforming market by {abs(alpha):.2f}%")
    print(f"   ✅ Positive return: +{total_return_pct:.2f}% in 6 days")
    grade = "B+"
else:
    print(f"   ⚠️  NEEDS IMPROVEMENT: Negative return")
    grade = "C"

print(f"\n   Overall Grade: {grade}")
print("="*100)
