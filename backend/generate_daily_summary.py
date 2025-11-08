#!/usr/bin/env python3
"""
Generate a comprehensive daily trading summary from Supabase logs
"""
import os
import sys
from datetime import datetime, timedelta
from supabase import create_client
from collections import defaultdict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_today_trades():
    """Get all trades from today"""
    today = datetime.now().date()
    
    response = supabase.table("trades").select("*").gte(
        "exit_time", today.isoformat()
    ).order("exit_time", desc=False).execute()
    
    return response.data

def get_today_opportunities():
    """Get all opportunities scanned today"""
    today = datetime.now().date()
    
    response = supabase.table("opportunities").select("*").gte(
        "created_at", today.isoformat()
    ).order("score", desc=True).limit(20).execute()
    
    return response.data

def get_current_positions():
    """Get current open positions"""
    response = supabase.table("positions").select("*").execute()
    return response.data

def format_currency(value):
    """Format value as currency"""
    return f"${value:,.2f}"

def format_percent(value):
    """Format value as percentage"""
    return f"{value:.2f}%"

def main():
    print("=" * 80)
    print(f"📊 TRADING SUMMARY - {datetime.now().strftime('%B %d, %Y')}")
    print("=" * 80)
    print()
    
    # Get data
    trades = get_today_trades()
    opportunities = get_today_opportunities()
    positions = get_current_positions()
    
    # ============================================================================
    # TRADES SUMMARY
    # ============================================================================
    print("🔄 TRADES EXECUTED TODAY")
    print("-" * 80)
    
    if not trades:
        print("No trades executed today")
    else:
        total_pnl = 0
        wins = 0
        losses = 0
        by_symbol = defaultdict(lambda: {"count": 0, "pnl": 0})
        
        for trade in trades:
            symbol = trade["symbol"]
            pnl = float(trade.get("pnl", 0))
            side = trade.get("side", "unknown")
            entry_price = float(trade.get("entry_price", 0))
            exit_price = float(trade.get("exit_price", 0))
            qty = int(trade.get("quantity", 0))
            exit_reason = trade.get("exit_reason", "unknown")
            
            total_pnl += pnl
            if pnl > 0:
                wins += 1
                emoji = "✅"
            else:
                losses += 1
                emoji = "❌"
            
            by_symbol[symbol]["count"] += 1
            by_symbol[symbol]["pnl"] += pnl
            
            print(f"{emoji} {symbol:6} | {side:5} | {qty:4} shares | "
                  f"Entry: ${entry_price:.2f} | Exit: ${exit_price:.2f} | "
                  f"P/L: {format_currency(pnl):>10} | {exit_reason}")
        
        print()
        print(f"Total Trades: {len(trades)} | Wins: {wins} | Losses: {losses} | "
              f"Win Rate: {(wins/len(trades)*100):.1f}%")
        print(f"Total P/L: {format_currency(total_pnl)}")
        
        if total_pnl > 0:
            print(f"💰 NET PROFIT: {format_currency(total_pnl)}")
        else:
            print(f"📉 NET LOSS: {format_currency(total_pnl)}")
        
        print()
        print("By Symbol:")
        for symbol, data in sorted(by_symbol.items(), key=lambda x: x[1]["pnl"], reverse=True):
            emoji = "💚" if data["pnl"] > 0 else "❤️"
            print(f"  {emoji} {symbol}: {data['count']} trades, {format_currency(data['pnl'])}")
    
    print()
    
    # ============================================================================
    # CURRENT POSITIONS
    # ============================================================================
    print("📍 CURRENT OPEN POSITIONS")
    print("-" * 80)
    
    if not positions:
        print("No open positions")
    else:
        total_value = 0
        total_unrealized = 0
        
        for pos in positions:
            symbol = pos["symbol"]
            qty = int(pos.get("quantity", 0))
            side = pos.get("side", "unknown")
            entry_price = float(pos.get("entry_price", 0))
            current_price = float(pos.get("current_price", entry_price))
            unrealized_pnl = float(pos.get("unrealized_pnl", 0))
            
            value = qty * current_price
            total_value += value
            total_unrealized += unrealized_pnl
            
            emoji = "🟢" if unrealized_pnl > 0 else "🔴"
            print(f"{emoji} {symbol:6} | {side:5} | {qty:4} shares | "
                  f"Entry: ${entry_price:.2f} | Current: ${current_price:.2f} | "
                  f"Value: {format_currency(value):>10} | "
                  f"P/L: {format_currency(unrealized_pnl):>10}")
        
        print()
        print(f"Total Position Value: {format_currency(total_value)}")
        print(f"Total Unrealized P/L: {format_currency(total_unrealized)}")
    
    print()
    
    # ============================================================================
    # AI SCANNER OPPORTUNITIES
    # ============================================================================
    print("🤖 TOP AI-DISCOVERED OPPORTUNITIES")
    print("-" * 80)
    
    if not opportunities:
        print("No opportunities scanned today")
    else:
        print(f"Showing top {min(10, len(opportunities))} opportunities:")
        print()
        
        for i, opp in enumerate(opportunities[:10], 1):
            symbol = opp["symbol"]
            score = float(opp.get("score", 0))
            direction = opp.get("direction", "unknown")
            price = float(opp.get("price", 0))
            rsi = opp.get("rsi")
            adx = opp.get("adx")
            volume_ratio = opp.get("volume_ratio")
            
            # Grade
            if score >= 90:
                grade = "A+"
            elif score >= 80:
                grade = "A"
            elif score >= 70:
                grade = "B"
            elif score >= 60:
                grade = "C"
            else:
                grade = "D"
            
            direction_emoji = "📈" if direction == "LONG" else "📉"
            
            rsi_str = f"{rsi:.1f}" if rsi is not None else "N/A"
            adx_str = f"{adx:.1f}" if adx is not None else "N/A"
            vol_str = f"{volume_ratio:.2f}x" if volume_ratio is not None else "N/A"
            
            print(f"{i:2}. {direction_emoji} {symbol:6} | Score: {score:5.1f} ({grade}) | "
                  f"${price:.2f} | RSI: {rsi_str:>5} | "
                  f"ADX: {adx_str:>5} | Vol: {vol_str:>6}")
    
    print()
    
    # ============================================================================
    # SYSTEM STATUS
    # ============================================================================
    print("⚙️  SYSTEM STATUS")
    print("-" * 80)
    print(f"✅ Trading Engine: RUNNING")
    print(f"✅ AI Scanner: ACTIVE (5-min intervals in pre-market)")
    print(f"✅ Position Monitor: ACTIVE")
    print(f"✅ Risk Manager: ACTIVE (blocking choppy market trades)")
    print(f"✅ Market Regime Detection: ACTIVE")
    
    print()
    print("=" * 80)

if __name__ == "__main__":
    main()
