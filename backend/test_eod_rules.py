#!/usr/bin/env python3
"""Test script for End-of-Day trading rules."""

from datetime import datetime
import pytz
from config import settings

print('=== EOD RULES CONFIGURATION ===')
print(f'Entry Cutoff Time: {settings.entry_cutoff_time} ET (no new positions after this)')
print(f'Entry Cutoff Enabled: {settings.entry_cutoff_enabled}')
print(f'EOD Exit Time: {settings.eod_exit_time} ET (close all positions)')
print(f'Force EOD Exit: {settings.force_eod_exit}')
print(f'EOD Close All: {settings.eod_close_all}')
print()

# Test current time
ny_tz = pytz.timezone('America/New_York')
now_ny = datetime.now(ny_tz)
print(f'Current ET Time: {now_ny.strftime("%H:%M:%S")}')

# Parse times
cutoff_hour, cutoff_minute = map(int, settings.entry_cutoff_time.split(':'))
eod_hour, eod_minute = map(int, settings.eod_exit_time.split(':'))

current_minutes = now_ny.hour * 60 + now_ny.minute
cutoff_minutes = cutoff_hour * 60 + cutoff_minute
eod_minutes = eod_hour * 60 + eod_minute

print(f'Entry Cutoff Active: {current_minutes >= cutoff_minutes}')
print(f'EOD Close Active: {current_minutes >= eod_minutes}')
print()
print('=== TIMELINE ===')
print('9:30 AM - 3:30 PM: Normal trading allowed')
print('3:30 PM - 3:55 PM: No new positions, existing positions can run')
print('3:55 PM - 4:00 PM: All positions closed, no trading')
print('4:00 PM: Market closes')
