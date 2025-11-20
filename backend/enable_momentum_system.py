"""
Enable the momentum-based bracket adjustment system.
Run this script to turn on momentum detection for live trading.
"""

import sys
from trading.trading_engine import get_trading_engine
from utils.logger import setup_logger

logger = setup_logger(__name__)

def enable_momentum(aggressive: bool = False):
    """Enable momentum system"""
    engine = get_trading_engine()
    
    if not engine:
        logger.error("❌ Trading engine not running")
        logger.info("Start the trading engine first with: python main.py")
        return False
    
    # Enable momentum system
    engine.enable_momentum_system(aggressive=aggressive)
    
    # Get stats
    stats = engine.get_momentum_stats()
    
    logger.info("=" * 60)
    logger.info("✅ Momentum System Enabled!")
    logger.info("=" * 60)
    logger.info(f"Mode: {'Aggressive' if aggressive else 'Conservative'}")
    logger.info(f"ADX Threshold: {stats['config']['adx_threshold']}")
    logger.info(f"Volume Threshold: {stats['config']['volume_threshold']}x")
    logger.info(f"Trend Threshold: {stats['config']['trend_threshold']}")
    logger.info(f"Extended Target: +{stats['config']['extended_target_r']}R")
    logger.info(f"Progressive Stop: +{stats['config']['progressive_stop_r']}R")
    logger.info("=" * 60)
    logger.info("")
    logger.info("The system will now:")
    logger.info("  • Evaluate positions at +0.75R profit")
    logger.info("  • Check ADX, Volume, and Trend indicators")
    logger.info("  • Extend targets to +3R when momentum is strong")
    logger.info("  • Move stops to breakeven + 0.5R")
    logger.info("")
    logger.info("Monitor logs for momentum signals:")
    logger.info("  🎯 = Target extended")
    logger.info("  ⏹️ = Keeping standard target")
    logger.info("")
    
    return True

def disable_momentum():
    """Disable momentum system"""
    engine = get_trading_engine()
    
    if not engine:
        logger.error("❌ Trading engine not running")
        return False
    
    engine.disable_momentum_system()
    
    logger.info("=" * 60)
    logger.info("⏹️ Momentum System Disabled")
    logger.info("=" * 60)
    
    return True

def show_stats():
    """Show momentum system stats"""
    engine = get_trading_engine()
    
    if not engine:
        logger.error("❌ Trading engine not running")
        return False
    
    stats = engine.get_momentum_stats()
    
    logger.info("=" * 60)
    logger.info("📊 Momentum System Stats")
    logger.info("=" * 60)
    logger.info(f"Status: {'✅ Enabled' if stats['enabled'] else '⏹️ Disabled'}")
    logger.info(f"Total Adjusted: {stats['total_adjusted']}")
    if stats['adjusted_symbols']:
        logger.info(f"Adjusted Symbols: {', '.join(stats['adjusted_symbols'])}")
    logger.info("=" * 60)
    
    return True

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Manage momentum-based bracket adjustment system')
    parser.add_argument('action', choices=['enable', 'disable', 'stats'], 
                       help='Action to perform')
    parser.add_argument('--aggressive', action='store_true',
                       help='Use aggressive settings (more signals)')
    
    args = parser.parse_args()
    
    if args.action == 'enable':
        success = enable_momentum(aggressive=args.aggressive)
    elif args.action == 'disable':
        success = disable_momentum()
    elif args.action == 'stats':
        success = show_stats()
    
    sys.exit(0 if success else 1)
