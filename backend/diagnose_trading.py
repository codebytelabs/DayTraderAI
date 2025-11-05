#!/usr/bin/env python3
"""
Comprehensive diagnostic script for trading system.
Run this to understand why no positions are being taken.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from core.alpaca_client import AlpacaClient
from core.supabase_client import SupabaseClient
from core.state import trading_state
from trading.risk_manager import RiskManager
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


def diagnose():
    """Run comprehensive diagnostics."""
    
    print("\n" + "="*70)
    print(" "*20 + "TRADING SYSTEM DIAGNOSTICS")
    print("="*70 + "\n")
    
    # Initialize
    alpaca = AlpacaClient()
    supabase = SupabaseClient()
    risk_manager = RiskManager(alpaca)
    
    # 1. Market Status
    print("1. MARKET STATUS")
    print("-" * 70)
    is_open = alpaca.is_market_open()
    print(f"   Market: {'🟢 OPEN' if is_open else '🔴 CLOSED'}")
    if not is_open:
        print("   ⚠️  Trading only occurs when market is open")
    print()
    
    # 2. Account Status
    print("2. ACCOUNT STATUS")
    print("-" * 70)
    try:
        account = alpaca.get_account()
        equity = float(account.equity)
        cash = float(account.cash)
        buying_power = float(account.buying_power)
        
        print(f"   Equity: ${equity:,.2f}")
        print(f"   Cash: ${cash:,.2f}")
        print(f"   Buying Power: ${buying_power:,.2f}")
        print(f"   Account Status: {account.status}")
        
        if buying_power < 1000:
            print("   ⚠️  Low buying power - may limit trading")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    print()
    
    # 3. Trading State
    print("3. TRADING STATE")
    print("-" * 70)
    is_allowed = trading_state.is_trading_allowed()
    print(f"   Trading Enabled: {'✅ YES' if is_allowed else '❌ NO'}")
    
    if not is_allowed:
        print("   ⚠️  Trading is disabled - enable it to start trading")
    
    metrics = trading_state.get_metrics()
    print(f"   Circuit Breaker: {'🔴 TRIGGERED' if metrics.circuit_breaker_triggered else '✅ OK'}")
    print(f"   Daily P/L: ${metrics.daily_pl:,.2f} ({metrics.daily_pl_pct:.2f}%)")
    print(f"   Open Positions: {metrics.open_positions}/{settings.max_positions}")
    print()
    
    # 4. Position Limits
    print("4. POSITION LIMITS")
    print("-" * 70)
    current_positions = len(trading_state.get_all_positions())
    print(f"   Current Positions: {current_positions}")
    print(f"   Max Positions: {settings.max_positions}")
    print(f"   Available Slots: {settings.max_positions - current_positions}")
    
    if current_positions >= settings.max_positions:
        print("   ⚠️  Max positions reached - no new trades until positions close")
    print()
    
    # 5. Strategy Configuration
    print("5. STRATEGY CONFIGURATION")
    print("-" * 70)
    print(f"   EMA Short: {settings.ema_short}")
    print(f"   EMA Long: {settings.ema_long}")
    print(f"   Risk Per Trade: {settings.risk_per_trade_pct * 100}%")
    print(f"   Stop Loss: {settings.stop_loss_atr_mult}x ATR")
    print(f"   Take Profit: {settings.take_profit_atr_mult}x ATR")
    print(f"   Circuit Breaker: {settings.circuit_breaker_pct * 100}%")
    print()
    
    # 6. Watchlist
    print("6. WATCHLIST")
    print("-" * 70)
    print(f"   Symbols: {', '.join(settings.watchlist_symbols)}")
    print(f"   Count: {len(settings.watchlist_symbols)}")
    print()
    
    # 7. Database Connection
    print("7. DATABASE CONNECTION")
    print("-" * 70)
    try:
        # Test features table
        result = supabase.client.table("features").select("*").limit(1).execute()
        print("   ✅ Supabase connected")
        
        # Check for prev_ema columns
        if result.data:
            sample = result.data[0]
            has_prev_short = 'prev_ema_short' in sample
            has_prev_long = 'prev_ema_long' in sample
            
            if has_prev_short and has_prev_long:
                print("   ✅ Schema migration applied (prev_ema columns exist)")
            else:
                print("   ❌ Schema migration NOT applied")
                print("   ⚠️  Run: backend/supabase_migration_add_prev_ema.sql")
        else:
            print("   ⚠️  No features data yet")
            
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        if "prev_ema" in str(e):
            print("   ⚠️  Run migration: backend/supabase_migration_add_prev_ema.sql")
    print()
    
    # 8. Recent Features
    print("8. RECENT FEATURES")
    print("-" * 70)
    try:
        result = supabase.client.table("features").select("*").order("updated_at", desc=True).limit(5).execute()
        
        if result.data:
            print(f"   Found {len(result.data)} recent feature records:")
            for feat in result.data:
                symbol = feat.get('symbol', 'N/A')
                price = feat.get('price', 0)
                ema_s = feat.get('ema_short', 0)
                ema_l = feat.get('ema_long', 0)
                updated = feat.get('updated_at', 'N/A')
                print(f"   - {symbol}: ${price:.2f}, EMA({settings.ema_short})=${ema_s:.2f}, EMA({settings.ema_long})=${ema_l:.2f} @ {updated}")
        else:
            print("   ⚠️  No features in database yet")
            print("   System needs to run for ~1 minute to populate features")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    print()
    
    # 9. Recent Orders
    print("9. RECENT ORDERS")
    print("-" * 70)
    try:
        result = supabase.client.table("orders").select("*").order("created_at", desc=True).limit(5).execute()
        
        if result.data:
            print(f"   Found {len(result.data)} recent orders:")
            for order in result.data:
                symbol = order.get('symbol', 'N/A')
                side = order.get('side', 'N/A')
                qty = order.get('qty', 0)
                status = order.get('status', 'N/A')
                created = order.get('created_at', 'N/A')
                print(f"   - {side.upper()} {qty} {symbol} [{status}] @ {created}")
        else:
            print("   No orders yet")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    print()
    
    # 10. Order Rejections
    print("10. ORDER REJECTIONS")
    print("-" * 70)
    try:
        result = supabase.client.table("order_rejections").select("*").order("timestamp", desc=True).limit(5).execute()
        
        if result.data:
            print(f"   ⚠️  Found {len(result.data)} recent rejections:")
            for rej in result.data:
                symbol = rej.get('symbol', 'N/A')
                side = rej.get('side', 'N/A')
                reason = rej.get('reason', 'N/A')
                timestamp = rej.get('timestamp', 'N/A')
                print(f"   - {side.upper()} {symbol}: {reason} @ {timestamp}")
        else:
            print("   ✅ No order rejections")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    print()
    
    # Summary
    print("="*70)
    print("DIAGNOSIS SUMMARY")
    print("="*70)
    
    issues = []
    
    if not is_open:
        issues.append("Market is closed - wait for market hours")
    
    if not is_allowed:
        issues.append("Trading is disabled - enable trading")
    
    if metrics.circuit_breaker_triggered:
        issues.append("Circuit breaker triggered - reset or wait for new day")
    
    if current_positions >= settings.max_positions:
        issues.append("Max positions reached - wait for positions to close")
    
    try:
        result = supabase.client.table("features").select("*").limit(1).execute()
        if result.data and 'prev_ema_short' not in result.data[0]:
            issues.append("Database schema needs migration - run supabase_migration_add_prev_ema.sql")
    except:
        issues.append("Database connection issue - check Supabase credentials")
    
    if issues:
        print("\n❌ ISSUES FOUND:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
    else:
        print("\n✅ NO CRITICAL ISSUES FOUND")
        print("\nSystem appears healthy. If no positions are being taken:")
        print("   1. Market conditions may not have EMA crossovers right now")
        print("   2. This is normal - crossovers don't happen frequently")
        print("   3. System will trade automatically when signals occur")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    diagnose()
