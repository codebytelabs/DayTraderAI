"""
GO-LIVE Script for Momentum-Based Bracket Adjustment System

This script enables the momentum system for live trading.
Run this AFTER the trading engine is started.

Usage:
    # Conservative mode (recommended to start)
    python golive_momentum.py
    
    # Aggressive mode (after validation)
    python golive_momentum.py --aggressive
"""

import sys
import time
from utils.logger import setup_logger

logger = setup_logger(__name__)

def golive_momentum(aggressive: bool = False):
    """Enable momentum system for live trading"""
    
    logger.info("=" * 70)
    logger.info("🚀 MOMENTUM SYSTEM GO-LIVE")
    logger.info("=" * 70)
    logger.info("")
    
    # Import here to ensure trading engine is initialized
    try:
        from trading.trading_engine import get_trading_engine
        engine = get_trading_engine()
        
        if not engine:
            logger.error("❌ Trading engine not running!")
            logger.info("")
            logger.info("Please start the trading engine first:")
            logger.info("  python main.py")
            logger.info("")
            return False
        
        logger.info("✅ Trading engine detected")
        logger.info("")
        
        # Show current status
        logger.info("📊 Current System Status:")
        logger.info(f"  • Market Open: {engine.alpaca.is_market_open()}")
        logger.info(f"  • Positions: {len(engine.position_manager.position_manager.get_all_positions()) if hasattr(engine.position_manager, 'position_manager') else 'N/A'}")
        logger.info(f"  • Watchlist: {len(engine.watchlist)} symbols")
        logger.info("")
        
        # Enable momentum system
        mode = "aggressive" if aggressive else "conservative"
        logger.info(f"🎯 Enabling Momentum System ({mode} mode)...")
        logger.info("")
        
        engine.enable_momentum_system(aggressive=aggressive)
        
        # Get configuration
        stats = engine.get_momentum_stats()
        config = stats['config']
        
        logger.info("=" * 70)
        logger.info("✅ MOMENTUM SYSTEM IS NOW LIVE!")
        logger.info("=" * 70)
        logger.info("")
        logger.info("📋 Configuration:")
        logger.info(f"  • Mode: {mode.upper()}")
        logger.info(f"  • ADX Threshold: {config['adx_threshold']} (trending market)")
        logger.info(f"  • Volume Threshold: {config['volume_threshold']}x average")
        logger.info(f"  • Trend Threshold: {config['trend_threshold']}")
        logger.info(f"  • Evaluation Trigger: +{config['evaluation_profit_r']}R profit")
        logger.info("")
        logger.info("🎯 Bracket Adjustments:")
        logger.info(f"  • Extended Target: +{config['extended_target_r']}R (from +2R)")
        logger.info(f"  • Progressive Stop: +{config['progressive_stop_r']}R (from entry)")
        logger.info(f"  • ATR Trailing: {'Enabled' if config['use_atr_trailing'] else 'Disabled'}")
        logger.info("")
        logger.info("🔍 How It Works:")
        logger.info("  1. Position reaches +0.75R profit")
        logger.info("  2. System evaluates momentum (ADX, Volume, Trend)")
        logger.info("  3. If ALL indicators pass → Extend target to +3R")
        logger.info("  4. Move stop to breakeven + 0.5R to protect profits")
        logger.info("  5. One-time adjustment per position")
        logger.info("")
        logger.info("📊 Monitor These Logs:")
        logger.info("  • 📊 Evaluating momentum for [SYMBOL] at +X.XXR")
        logger.info("  • 🎯 Extended target for [SYMBOL]!")
        logger.info("  • ⏹️ Keeping standard target for [SYMBOL]")
        logger.info("")
        logger.info("=" * 70)
        logger.info("🎉 System is monitoring positions for momentum opportunities")
        logger.info("=" * 70)
        logger.info("")
        
        # Show example
        logger.info("💡 Example Scenario:")
        logger.info("  • You enter AAPL at $150.00")
        logger.info("  • Stop loss at $148.00 (risk = $2.00)")
        logger.info("  • Initial target at $154.00 (+2R = $4.00 profit)")
        logger.info("  • Price moves to $151.50 (+0.75R)")
        logger.info("  • System detects strong momentum")
        logger.info("  • 🎯 Target extended to $156.00 (+3R = $6.00 profit)")
        logger.info("  • 🛡️ Stop moved to $151.00 (BE + 0.5R)")
        logger.info("  • Result: Larger wins, protected profits!")
        logger.info("")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error enabling momentum system: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_status():
    """Show current momentum system status"""
    try:
        from trading.trading_engine import get_trading_engine
        engine = get_trading_engine()
        
        if not engine:
            logger.error("❌ Trading engine not running")
            return False
        
        stats = engine.get_momentum_stats()
        
        logger.info("=" * 70)
        logger.info("📊 MOMENTUM SYSTEM STATUS")
        logger.info("=" * 70)
        logger.info(f"Status: {'✅ ENABLED' if stats['enabled'] else '⏹️ DISABLED'}")
        logger.info(f"Positions Adjusted: {stats['total_adjusted']}")
        
        if stats['adjusted_symbols']:
            logger.info(f"Adjusted Symbols: {', '.join(stats['adjusted_symbols'])}")
        
        if stats['enabled']:
            config = stats['config']
            logger.info("")
            logger.info("Configuration:")
            logger.info(f"  • ADX: {config['adx_threshold']}")
            logger.info(f"  • Volume: {config['volume_threshold']}x")
            logger.info(f"  • Trend: {config['trend_threshold']}")
            logger.info(f"  • Target: +{config['extended_target_r']}R")
            logger.info(f"  • Stop: +{config['progressive_stop_r']}R")
        
        logger.info("=" * 70)
        
        return True
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return False

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Enable momentum-based bracket adjustment system for live trading',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Enable in conservative mode (recommended)
  python golive_momentum.py
  
  # Enable in aggressive mode (after validation)
  python golive_momentum.py --aggressive
  
  # Check current status
  python golive_momentum.py --status
        """
    )
    
    parser.add_argument('--aggressive', action='store_true',
                       help='Use aggressive settings (more signals, lower thresholds)')
    parser.add_argument('--status', action='store_true',
                       help='Show current momentum system status')
    
    args = parser.parse_args()
    
    if args.status:
        success = show_status()
    else:
        success = golive_momentum(aggressive=args.aggressive)
    
    sys.exit(0 if success else 1)
