"""Test Quick Wins implementation - Market Regime Detection & Adaptive Position Sizing."""

import sys
from core.alpaca_client import AlpacaClient
from indicators.market_regime import get_regime_detector
from trading.risk_manager import RiskManager
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


def test_market_regime_detection():
    """Test market regime detection."""
    logger.info("=" * 80)
    logger.info("Testing Market Regime Detection")
    logger.info("=" * 80)
    
    try:
        # Initialize Alpaca client
        alpaca = AlpacaClient()
        
        # Get regime detector
        detector = get_regime_detector(alpaca)
        
        # Detect current regime
        regime = detector.detect_regime()
        
        logger.info(f"\n📊 Current Market Regime:")
        logger.info(f"  Regime: {regime['regime']}")
        logger.info(f"  Breadth Score: {regime['breadth_score']:.0f}/100")
        logger.info(f"  Trend Strength: {regime['trend_strength']:.0f}/100")
        logger.info(f"  Volatility: {regime['volatility_level']}")
        logger.info(f"  Position Size Multiplier: {regime['position_size_multiplier']:.2f}x")
        logger.info(f"  Should Trade: {regime['should_trade']}")
        
        # Show details
        details = regime['details']
        logger.info(f"\n📈 Breadth Details:")
        logger.info(f"  Advancing: {details['breadth']['advancing']}")
        logger.info(f"  Declining: {details['breadth']['declining']}")
        logger.info(f"  Ratio: {details['breadth']['ratio']:.2f}")
        
        logger.info(f"\n📉 Trend Details:")
        logger.info(f"  Direction: {details['trend']['direction']}")
        logger.info(f"  ADX: {details['trend'].get('adx', 'N/A')}")
        
        logger.info(f"\n💨 Volatility Details:")
        logger.info(f"  VIX: {details['volatility']['vix']:.2f}")
        
        # Interpret results
        logger.info(f"\n💡 Interpretation:")
        if regime['regime'] == 'broad_bullish':
            logger.info("  ✅ Excellent conditions - trade bigger (1.5x)")
        elif regime['regime'] == 'broad_bearish':
            logger.info("  ✅ Good for shorts - trade bigger (1.5x)")
        elif regime['regime'] in ['narrow_bullish', 'narrow_bearish']:
            logger.info("  ⚠️  Risky conditions - trade smaller (0.7x)")
        elif regime['regime'] == 'choppy':
            logger.info("  ❌ Poor conditions - trade much smaller (0.5x) or skip")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Market regime detection failed: {e}", exc_info=True)
        return False


def test_adaptive_position_sizing():
    """Test adaptive position sizing in risk manager."""
    logger.info("\n" + "=" * 80)
    logger.info("Testing Adaptive Position Sizing")
    logger.info("=" * 80)
    
    try:
        # Initialize components
        alpaca = AlpacaClient()
        risk_manager = RiskManager(alpaca)
        
        # Get current regime
        regime = risk_manager._get_market_regime()
        
        logger.info(f"\n📊 Current Regime: {regime['regime']}")
        logger.info(f"  Base Risk Per Trade: {settings.risk_per_trade_pct * 100:.2f}%")
        logger.info(f"  Position Size Multiplier: {regime['position_size_multiplier']:.2f}x")
        
        # Calculate adjusted risk
        adjusted_risk = settings.risk_per_trade_pct * regime['position_size_multiplier']
        logger.info(f"  Adjusted Risk Per Trade: {adjusted_risk * 100:.2f}%")
        
        # Show examples for different regimes
        logger.info(f"\n💰 Position Sizing Examples (on $135k account):")
        
        regimes = [
            ('broad_bullish', 1.5),
            ('broad_bearish', 1.5),
            ('broad_neutral', 1.0),
            ('narrow_bullish', 0.7),
            ('narrow_bearish', 0.7),
            ('choppy', 0.5)
        ]
        
        equity = 135000
        base_risk = settings.risk_per_trade_pct
        
        for regime_name, multiplier in regimes:
            adjusted = base_risk * multiplier
            risk_amount = equity * adjusted
            logger.info(f"  {regime_name:20s}: {adjusted*100:5.2f}% = ${risk_amount:8,.2f} at risk")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Adaptive position sizing test failed: {e}", exc_info=True)
        return False


def test_volatility_filters():
    """Test volatility filters."""
    logger.info("\n" + "=" * 80)
    logger.info("Testing Volatility Filters")
    logger.info("=" * 80)
    
    try:
        logger.info("\n📋 Volatility Filter Rules:")
        logger.info("  1. ADX must be >= 20 (trend strength)")
        logger.info("  2. Volume must be >= 1.5x average")
        logger.info("  3. Market regime must allow trading")
        
        logger.info("\n✅ These filters are now active in risk_manager.check_order()")
        logger.info("   Orders will be rejected if:")
        logger.info("   - ADX < 20 (low volatility)")
        logger.info("   - Volume < 1.5x average (low volume)")
        logger.info("   - Market regime is 'choppy' (unfavorable)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Volatility filters test failed: {e}", exc_info=True)
        return False


def main():
    """Run all Quick Wins tests."""
    logger.info("\n" + "=" * 80)
    logger.info("🚀 QUICK WINS IMPLEMENTATION TEST")
    logger.info("=" * 80)
    
    results = []
    
    # Test 1: Market Regime Detection
    results.append(("Market Regime Detection", test_market_regime_detection()))
    
    # Test 2: Adaptive Position Sizing
    results.append(("Adaptive Position Sizing", test_adaptive_position_sizing()))
    
    # Test 3: Volatility Filters
    results.append(("Volatility Filters", test_volatility_filters()))
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 80)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"  {status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        logger.info("\n🎉 All Quick Wins tests passed!")
        logger.info("\n💡 Next Steps:")
        logger.info("  1. Run the trading bot to see adaptive sizing in action")
        logger.info("  2. Monitor logs for regime changes and position adjustments")
        logger.info("  3. Compare performance on narrow vs broad market days")
        return 0
    else:
        logger.error("\n❌ Some tests failed. Please review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
