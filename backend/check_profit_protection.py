#!/usr/bin/env python3
"""
Quick diagnostic to check profit protection status.
Shows which positions are at risk and why.
"""

from core.alpaca_client import AlpacaClient
from colorama import Fore, Style, init

init(autoreset=True)

def main():
    client = AlpacaClient()
    
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}🛡️  PROFIT PROTECTION STATUS CHECK")
    print(f"{Fore.CYAN}{'='*70}\n")
    
    # Get positions
    positions = client.list_positions()
    print(f"{Fore.WHITE}📊 Total Positions: {len(positions)}\n")
    
    total_profit = 0
    unprotected_profit = 0
    issues = []
    
    for pos in positions:
        symbol = pos.symbol
        qty = int(pos.qty)
        entry = float(pos.avg_entry_price)
        current = float(pos.current_price)
        pnl = float(pos.unrealized_pl)
        pnl_pct = float(pos.unrealized_plpc) * 100
        
        total_profit += pnl
        
        # Get orders for this symbol
        orders = client.get_orders(status='open', symbols=[symbol])
        
        has_stop = any(o.stop_price for o in orders)
        has_take_profit = any(o.limit_price and o.side == 'sell' for o in orders)
        
        # Determine status
        if pnl > 0:
            if not has_stop and not has_take_profit:
                status = f"{Fore.RED}❌ NO PROTECTION"
                issues.append(f"{symbol}: No stop-loss or take-profit")
                unprotected_profit += pnl
            elif not has_stop:
                status = f"{Fore.YELLOW}⚠️  NO STOP-LOSS"
                issues.append(f"{symbol}: Missing stop-loss (wash trade?)")
                unprotected_profit += pnl
            elif not has_take_profit:
                status = f"{Fore.YELLOW}⚠️  NO TAKE-PROFIT"
            else:
                status = f"{Fore.GREEN}✅ PROTECTED"
        else:
            if not has_stop:
                status = f"{Fore.RED}❌ NO STOP (LOSING!)"
                issues.append(f"{symbol}: Losing position without stop-loss")
            else:
                status = f"{Fore.BLUE}🔵 PROTECTED (LOSS)"
        
        # Print position
        color = Fore.GREEN if pnl > 0 else Fore.RED
        print(f"{Fore.WHITE}{symbol:6} | {qty:3} shares @ ${entry:7.2f} → ${current:7.2f} | "
              f"{color}${pnl:+7.2f} ({pnl_pct:+6.2f}%) {status}")
        
        # Show orders
        if orders:
            for order in orders:
                order_type = order.type
                price = order.stop_price or order.limit_price or 0
                side = order.side
                print(f"       └─ {side.upper()} {order.qty} @ ${price:.2f} ({order_type})")
    
    # Summary
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.WHITE}💰 Total P/L: {Fore.GREEN if total_profit > 0 else Fore.RED}${total_profit:+.2f}")
    print(f"{Fore.WHITE}⚠️  Unprotected Profit: {Fore.YELLOW}${unprotected_profit:.2f}")
    print(f"{Fore.CYAN}{'='*70}\n")
    
    if issues:
        print(f"{Fore.RED}🚨 CRITICAL ISSUES FOUND:\n")
        for issue in issues:
            print(f"   {Fore.YELLOW}• {issue}")
        print(f"\n{Fore.WHITE}💡 Run: {Fore.CYAN}python backend/emergency_fix_order_conflicts.py")
    else:
        print(f"{Fore.GREEN}✅ All positions have protection!\n")
    
    # Check for partial profit opportunities
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}🎯 PARTIAL PROFIT OPPORTUNITIES")
    print(f"{Fore.CYAN}{'='*70}\n")
    
    for pos in positions:
        pnl = float(pos.unrealized_pl)
        pnl_pct = float(pos.unrealized_plpc) * 100
        
        if pnl_pct > 3:  # More than 3% profit
            qty = int(pos.qty)
            partial_qty = qty // 2
            partial_profit = pnl * 0.5
            
            print(f"{Fore.GREEN}{pos.symbol}: Sell {partial_qty}/{qty} shares → Lock in ${partial_profit:.2f}")
            print(f"       {Fore.YELLOW}⚠️  Currently BLOCKED by stop-loss holding shares")
    
    print(f"\n{Fore.CYAN}{'='*70}\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"{Fore.RED}Error: {e}")
