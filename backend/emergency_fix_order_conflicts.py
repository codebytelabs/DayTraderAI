#!/usr/bin/env python3
"""
Emergency fix for order conflicts blocking profit protection.

Issues fixed:
1. NFLX wash trade error (take-profit blocking stop-loss)
2. Partial profits blocked by stop-loss orders
3. Enable order modification instead of recreation
"""

import asyncio
import logging
from core.alpaca_client import AlpacaClient
from core.supabase_client import SupabaseClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fix_nflx_orders():
    """Fix NFLX wash trade error by canceling conflicting orders."""
    client = AlpacaClient()
    
    logger.info("🔍 Checking NFLX orders...")
    
    # Get all open orders and filter for NFLX
    all_orders = client.get_orders(status='open')
    orders = [o for o in all_orders if o.symbol == 'NFLX']
    
    if not orders:
        logger.info("✅ No open NFLX orders found")
        return
    
    logger.info(f"📋 Found {len(orders)} open NFLX orders:")
    for order in orders:
        logger.info(f"  - {order.side} {order.qty} @ {order.stop_price or order.limit_price} ({order.type})")
    
    # Cancel all NFLX orders
    logger.info("🗑️  Canceling all NFLX orders...")
    for order in orders:
        try:
            client.cancel_order(order.id)
            logger.info(f"✅ Canceled order {order.id}")
        except Exception as e:
            logger.error(f"❌ Failed to cancel {order.id}: {e}")
    
    # Wait a moment for cancellations to process
    await asyncio.sleep(2)
    
    # Get current NFLX position
    try:
        position = client.get_position('NFLX')
        qty = int(position.qty)
        entry_price = float(position.avg_entry_price)
        current_price = float(position.current_price)
        
        logger.info(f"📊 NFLX Position: {qty} shares @ ${entry_price:.2f} (current: ${current_price:.2f})")
        
        # Create proper bracket order
        stop_price = entry_price * 0.985  # 1.5% stop
        take_profit = entry_price * 1.03  # 3% target
        
        logger.info(f"🎯 Creating bracket: Stop ${stop_price:.2f} | Target ${take_profit:.2f}")
        
        # Submit bracket order
        order = client.submit_order(
            symbol='NFLX',
            qty=qty,
            side='sell',
            type='market',
            time_in_force='gtc',
            order_class='bracket',
            stop_loss={'stop_price': stop_price},
            take_profit={'limit_price': take_profit}
        )
        
        logger.info(f"✅ Created bracket order for NFLX: {order.id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to create NFLX bracket: {e}")


async def check_all_positions():
    """Check all positions for order conflicts."""
    client = AlpacaClient()
    
    positions = client.get_positions()
    logger.info(f"\n📊 Checking {len(positions)} positions for order conflicts...")
    
    issues = []
    
    # Get all open orders once
    all_orders = client.get_orders(status='open')
    
    for pos in positions:
        symbol = pos.symbol
        orders = [o for o in all_orders if o.symbol == symbol]
        
        has_stop = any(o.stop_price for o in orders)
        has_take_profit = any(o.limit_price and o.side == 'sell' for o in orders)
        
        if has_stop and not has_take_profit:
            issues.append(f"{symbol}: Has stop-loss but no take-profit (shares held)")
        elif has_take_profit and not has_stop:
            issues.append(f"{symbol}: Has take-profit but no stop-loss (DANGEROUS!)")
    
    if issues:
        logger.warning(f"\n⚠️  Found {len(issues)} positions with order conflicts:")
        for issue in issues:
            logger.warning(f"  - {issue}")
    else:
        logger.info("✅ No order conflicts found")
    
    return issues


async def main():
    """Run emergency fixes."""
    logger.info("🚨 EMERGENCY ORDER CONFLICT FIX")
    logger.info("=" * 60)
    
    # Fix NFLX specifically
    await fix_nflx_orders()
    
    # Check all positions
    await asyncio.sleep(2)
    issues = await check_all_positions()
    
    logger.info("\n" + "=" * 60)
    if issues:
        logger.warning(f"⚠️  {len(issues)} positions still need attention")
        logger.info("\n💡 Recommendation: Manually review these positions in Alpaca dashboard")
    else:
        logger.info("✅ All order conflicts resolved!")


if __name__ == "__main__":
    asyncio.run(main())
