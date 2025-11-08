#!/usr/bin/env python3
"""Test Phase 1 Enhanced Indicators"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add backend to path
import os
backend_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_path)

from data.features import FeatureEngine
from utils.logger import setup_logger

logger = setup_logger(__name__)


def create_test_data(periods=100):
    """Create realistic test OHLCV data."""
    dates = pd.date_range(start='2024-01-01', periods=periods, freq='5min')
    
    # Generate realistic price movement
    np.random.seed(42)
    base_price = 100.0
    returns = np.random.normal(0.0001, 0.02, periods)
    prices = [base_price]
    
    for ret in returns[1:]:
        new_price = prices[-1] * (1 + ret)
        prices.append(new_price)
    
    prices = np.array(prices)
    
    # Generate OHLC
    high = prices * (1 + np.random.uniform(0, 0.01, periods))
    low = prices * (1 - np.random.uniform(0, 0.01, periods))
    open_prices = prices * (1 + np.random.uniform(-0.005, 0.005, periods))
    close = prices
    volume = np.random.randint(100000, 1000000, periods)
    
    df = pd.DataFrame({
        'open': open_prices,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=dates)
    
    return df


def test_indicators():
    """Test all Phase 1 indicators."""
    logger.info("=" * 60)
    logger.info("PHASE 1 INDICATOR TEST")
    logger.info("=" * 60)
    
    # Create test data
    logger.info("\n1. Creating test data...")
    df = create_test_data(periods=100)
    logger.info(f"   ✓ Created {len(df)} periods of OHLCV data")
    logger.info(f"   Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
    
    # Calculate features
    logger.info("\n2. Calculating enhanced features...")
    features = FeatureEngine.calculate_features(df)
    
    if not features:
        logger.error("   ✗ Failed to calculate features!")
        return False
    
    logger.info(f"   ✓ Calculated {len(features)} features")
    
    # Display core indicators
    logger.info("\n3. Core Indicators:")
    logger.info(f"   Price: ${features['price']:.2f}")
    logger.info(f"   EMA Short (9): ${features['ema_short']:.2f}")
    logger.info(f"   EMA Long (21): ${features['ema_long']:.2f}")
    logger.info(f"   EMA Diff: {features['ema_diff_pct']:.2f}%")
    logger.info(f"   ATR: ${features['atr']:.2f}")
    
    # Display new indicators
    logger.info("\n4. Phase 1 Enhanced Indicators:")
    logger.info(f"   VWAP: ${features['vwap']:.2f}")
    logger.info(f"   RSI: {features['rsi']:.2f}")
    logger.info(f"   MACD: {features['macd']:.4f}")
    logger.info(f"   MACD Signal: {features['macd_signal']:.4f}")
    logger.info(f"   MACD Histogram: {features['macd_histogram']:.4f}")
    logger.info(f"   ADX: {features['adx']:.2f}")
    logger.info(f"   +DI: {features['plus_di']:.2f}")
    logger.info(f"   -DI: {features['minus_di']:.2f}")
    logger.info(f"   Market Regime: {features['market_regime']}")
    
    # Display volume indicators
    logger.info("\n5. Volume Indicators:")
    logger.info(f"   Volume: {features['volume']:,}")
    logger.info(f"   Volume Ratio: {features['volume_ratio']:.2f}x")
    logger.info(f"   Volume Spike: {features['volume_spike']}")
    logger.info(f"   Volume Z-Score: {features['volume_zscore']:.2f}")
    logger.info(f"   OBV: {features['obv']:,.0f}")
    
    # Display signal indicators
    logger.info("\n6. Signal Indicators:")
    logger.info(f"   VWAP Signal: {features['vwap_signal']}")
    logger.info(f"   RSI Momentum: {features['rsi_momentum']}")
    logger.info(f"   MACD Momentum: {features['macd_momentum']}")
    
    # Display confidence score
    logger.info("\n7. Confidence Score:")
    logger.info(f"   Score: {features['confidence_score']:.1f}/100")
    
    # Test signal detection
    logger.info("\n8. Testing Enhanced Signal Detection...")
    signal_info = FeatureEngine.detect_enhanced_signal(features)
    
    if signal_info:
        logger.info(f"   ✓ Signal detected: {signal_info['signal'].upper()}")
        logger.info(f"   Confidence: {signal_info['confidence']:.1f}/100")
        logger.info(f"   Confirmations: {signal_info['confirmation_count']}/4")
        logger.info(f"   Confirmed by: {', '.join(signal_info['confirmations'])}")
        logger.info(f"   Market Regime: {signal_info['market_regime']}")
    else:
        logger.info("   No signal detected (waiting for crossover)")
    
    # Validate all indicators are present
    logger.info("\n9. Validation:")
    required_indicators = [
        'vwap', 'rsi', 'macd', 'macd_signal', 'macd_histogram',
        'adx', 'plus_di', 'minus_di', 'market_regime',
        'volume_ratio', 'volume_spike', 'obv',
        'vwap_signal', 'rsi_momentum', 'macd_momentum',
        'confidence_score'
    ]
    
    missing = [ind for ind in required_indicators if ind not in features]
    
    if missing:
        logger.error(f"   ✗ Missing indicators: {', '.join(missing)}")
        return False
    else:
        logger.info(f"   ✓ All {len(required_indicators)} Phase 1 indicators present")
    
    # Test with different market conditions
    logger.info("\n10. Testing Different Market Conditions...")
    
    # Trending up
    df_trend_up = df.copy()
    df_trend_up['close'] = df_trend_up['close'] * np.linspace(1.0, 1.1, len(df_trend_up))
    features_up = FeatureEngine.calculate_features(df_trend_up)
    logger.info(f"   Trending Up - ADX: {features_up['adx']:.1f}, Regime: {features_up['market_regime']}")
    
    # Ranging
    df_range = df.copy()
    df_range['close'] = 100 + np.sin(np.linspace(0, 4*np.pi, len(df_range))) * 2
    features_range = FeatureEngine.calculate_features(df_range)
    logger.info(f"   Ranging - ADX: {features_range['adx']:.1f}, Regime: {features_range['market_regime']}")
    
    logger.info("\n" + "=" * 60)
    logger.info("✓ PHASE 1 INDICATORS TEST PASSED!")
    logger.info("=" * 60)
    
    return True


if __name__ == '__main__':
    try:
        success = test_indicators()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        sys.exit(1)
