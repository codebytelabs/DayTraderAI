#!/usr/bin/env python3
"""
Deploy Phase 1 Fixes
Actually fixes all positions with incomplete protection
"""

import sys
import time
from datetime import datetime
from core.alpaca_client import AlpacaClient
from core.supabase_client import SupabaseClient
from core.state import trading_state
from trading.stop_loss_protection import get_protection_manager
from trading.position_manager import PositionManager
from utils.logger import setup_logger

logger = setup_logger(__name__)


def deploy_stop_loss_fixes():
    """Deploy stop-loss protection fixes to all positions"""
    logger.info("=" * 80)
    logger.info("🚀 DEPLOYING PHASE 1 FIXES")
    logger.info("=" * 80)
    
    try:
        # Initialize clients
        alpaca = AlpacaClient()
        supabase = SupabaseClient()
        
        # Sync positions first
        logger.info("\n📊 Syncing positions from Alpaca...")
        position_manager = PositionManager(alpaca, supabase)
        count = position_manager.sync_positions()
        logger.info(f"✅ Synced {count} positions")
        
        # Get protection manager
        protection_manager = get_protection_manager(alpaca)
        
        # Run protection verification (this will fix issues)
        logger.info("\n🔧 Running protection verification and fixes...")
        results = protection_manager.verify_all_positions()
        
        # Count results
        protected = sum(1 for status in results.values() if status in ['protected', 'created'])
        failed = sum(1 for status in results.values() if status == 'failed')
        
        logger.info(f"\n📊 Protection Results:")
        logger.info(f"   ✅ Protected/Created: {protected}")
        logger.info(f"   ❌ Failed: {failed}")
        
        # Show details
        for symbol, status in results.items():
            if status == 'created':
                logger.info(f"   🆕 {symbol}: Protection CREATED")
            elif status == 'protected':
                logger.info(f"   ✅ {symbol}: Already protected")
            else:
                logger.error(f"   ❌ {symbol}: Protection FAILED")
        
        # Wait a moment for orders to process
        logger.info("\n⏳ Waiting 3 seconds for orders to process...")
        time.sleep(3)
        
        # Verify final state
        logger.info("\n🔍 Verifying final protection state...")
        positions = alpaca.get_positions()
        orders = alpaca.get_orders(status='open')
        
        complete_protection = 0
        partial_protection = 0
        no_protection = 0
        
        for pos in positions:
            symbol = pos.symbol
            symbol_orders = [o for o in orders if o.symbol == symbol]
            
            has_stop = any(o.type.value in ['stop', 'trailing_stop'] for o in symbol_orders)
            has_tp = any(o.type.value == 'limit' and o.side.value == 'sell' for o in symbol_orders)
            
            if has_stop and has_tp:
                complete_protection += 1
                logger.info(f"   ✅ {symbol}: Complete protection")
            elif has_stop or has_tp:
                partial_protection += 1
                logger.warning(f"   ⚠️  {symbol}: Partial protection")
            else:
                no_protection += 1
                logger.error(f"   ❌ {symbol}: NO protection")
        
        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("📊 DEPLOYMENT SUMMARY")
        logger.info("=" * 80)
        logger.info(f"   ✅ Complete Protection: {complete_protection}/{len(positions)}")
        logger.info(f"   ⚠️  Partial Protection: {partial_protection}/{len(positions)}")
        logger.info(f"   ❌ No Protection: {no_protection}/{len(positions)}")
        
        if complete_protection == len(positions):
            logger.info("\n🎉 SUCCESS! All positions fully protected!")
            return 0
        elif no_protection == 0:
            logger.info("\n✅ GOOD! All positions have at least some protection.")
            logger.info("   Some positions may need manual review for complete protection.")
            return 0
        else:
            logger.error(f"\n⚠️  WARNING: {no_protection} positions have NO protection!")
            logger.error("   Manual intervention may be required.")
            return 1
        
    except Exception as e:
        logger.error(f"❌ DEPLOYMENT ERROR: {e}", exc_info=True)
        return 1


def main():
    """Main deployment function"""
    logger.info("🚀 Phase 1 Fix Deployment")
    logger.info(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
    
    result = deploy_stop_loss_fixes()
    
    if result == 0:
        logger.info("\n✅ DEPLOYMENT COMPLETE!")
        logger.info("\n📋 Next Steps:")
        logger.info("   1. Monitor bot logs for 'insufficient qty' errors (should be zero)")
        logger.info("   2. Check protection status regularly")
        logger.info("   3. Verify momentum system is working")
        logger.info("   4. Let bot run for 24 hours to validate")
    else:
        logger.error("\n⚠️  DEPLOYMENT HAD ISSUES!")
        logger.error("   Review errors above and consider manual intervention.")
    
    return result


if __name__ == "__main__":
    sys.exit(main())
