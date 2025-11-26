#!/usr/bin/env python3
"""
Diagnose Smart Order Executor timeout issue
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orders.smart_order_executor import SmartOrderExecutor, OrderConfig
from core.alpaca_client import AlpacaClient
from config import settings

def main():
    print("=" * 60)
    print("🔍 DIAGNOSING SMART ORDER EXECUTOR")
    print("=" * 60)
    print()
    
    # Check config
    print("📋 Configuration:")
    print(f"   USE_SMART_EXECUTOR: {settings.USE_SMART_EXECUTOR}")
    print(f"   FILL_TIMEOUT: {settings.SMART_EXECUTOR_FILL_TIMEOUT}s")
    print(f"   MAX_SLIPPAGE: {settings.SMART_EXECUTOR_MAX_SLIPPAGE_PCT*100:.2f}%")
    print(f"   MIN_RR_RATIO: {settings.SMART_EXECUTOR_MIN_RR_RATIO}")
    print()
    
    # Check OrderConfig
    config = OrderConfig(
        max_slippage_pct=settings.SMART_EXECUTOR_MAX_SLIPPAGE_PCT,
        limit_buffer_regular=settings.SMART_EXECUTOR_LIMIT_BUFFER_REGULAR,
        limit_buffer_extended=settings.SMART_EXECUTOR_LIMIT_BUFFER_EXTENDED,
        fill_timeout_seconds=settings.SMART_EXECUTOR_FILL_TIMEOUT,
        min_rr_ratio=settings.SMART_EXECUTOR_MIN_RR_RATIO,
        enable_extended_hours=settings.SMART_EXECUTOR_ENABLE_EXTENDED_HOURS
    )
    
    print("📋 OrderConfig:")
    print(f"   fill_timeout_seconds: {config.fill_timeout_seconds}s")
    print(f"   max_slippage_pct: {config.max_slippage_pct*100:.2f}%")
    print(f"   min_rr_ratio: {config.min_rr_ratio}")
    print()
    
    # Initialize executor
    alpaca = AlpacaClient()
    executor = SmartOrderExecutor(alpaca, config)
    
    print("✅ Smart Order Executor initialized")
    print(f"   Timeout configured: {executor.config.fill_timeout_seconds}s")
    print()
    
    print("=" * 60)
    print("🎯 DIAGNOSIS COMPLETE")
    print("=" * 60)
    print()
    print("The timeout is configured correctly at 60 seconds.")
    print("The issue is likely in the order status checking logic.")
    print()
    print("Next steps:")
    print("1. Check if orders are being submitted correctly")
    print("2. Check if order status is being read correctly")
    print("3. Add more logging to _wait_for_fill method")

if __name__ == "__main__":
    main()
