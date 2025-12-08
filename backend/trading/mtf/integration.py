"""
Multi-Timeframe Analysis Integration Module.

Provides a single entry point for integrating MTF analysis with the trading strategy.

Requirements: All
"""

import logging
from typing import Optional, Dict
import pandas as pd

from trading.mtf.models import MTFFeatures, MTFSignalResult, MTFConfig
from trading.mtf.data_manager import MTFDataManager
from trading.mtf.feature_engine import MTFFeatureEngine
from trading.mtf.signal_filter import MTFSignalFilter

logger = logging.getLogger(__name__)


class MTFIntegration:
    """Integrates all MTF components for strategy use.
    
    Provides a single entry point that:
    1. Fetches multi-timeframe data
    2. Calculates features for all timeframes
    3. Evaluates signals against MTF analysis
    4. Returns actionable results
    """
    
    def __init__(
        self,
        alpaca_client,
        config: MTFConfig = None,
    ):
        """Initialize MTF integration.
        
        Args:
            alpaca_client: AlpacaClient instance for data fetching
            config: Optional MTFConfig for customization
        """
        self.config = config or MTFConfig()
        self.data_manager = MTFDataManager(alpaca_client=alpaca_client)
        self.feature_engine = MTFFeatureEngine()
        self.signal_filter = MTFSignalFilter(config=self.config)
        
        logger.info(
            f"MTF Integration initialized: enabled={self.config.enabled}, "
            f"strict_mode={self.config.strict_mode}, "
            f"min_confidence={self.config.min_confidence}"
        )

    def get_mtf_signal_result(
        self,
        symbol: str,
        signal: str,
        force_refresh: bool = False,
    ) -> Optional[MTFSignalResult]:
        """Get MTF signal result for a symbol.
        
        Single entry point for strategy integration.
        
        Args:
            symbol: Stock symbol
            signal: Signal direction ('buy' or 'sell')
            force_refresh: Force refresh of all timeframe data
            
        Returns:
            MTFSignalResult with analysis results, or None if data unavailable
        """
        try:
            # Check if MTF is disabled
            if self.config.should_bypass():
                logger.debug(f"MTF bypassed for {symbol}")
                return self._create_bypass_result(symbol, signal)
            
            # Fetch multi-timeframe data
            data = self.data_manager.fetch_all_timeframes(symbol, force_refresh)
            
            if not data or len(data) < 4:
                logger.warning(f"Insufficient MTF data for {symbol}")
                return None
            
            # Calculate features
            features = self.feature_engine.calculate_mtf_features(symbol, data)
            
            if features is None:
                logger.warning(f"Failed to calculate MTF features for {symbol}")
                return None
            
            # Get 15-min DataFrame for S/R calculation
            df_15min = data.get('15min')
            
            # Evaluate signal
            result = self.signal_filter.evaluate_signal(
                symbol=symbol,
                signal=signal,
                features=features,
                df_15min=df_15min,
            )
            
            # Log result
            self._log_result(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in MTF analysis for {symbol}: {e}")
            return None
    
    def _create_bypass_result(
        self,
        symbol: str,
        signal: str,
    ) -> MTFSignalResult:
        """Create a bypass result when MTF is disabled."""
        from trading.mtf.models import TrendBias, SRLevels
        
        return MTFSignalResult(
            symbol=symbol,
            signal=signal,
            mtf_confidence=100.0,
            trend_bias=TrendBias.from_ema_values(100, 100),
            trend_aligned=True,
            momentum_aligned=True,
            rsi_alignment_count=3,
            macd_aligned=True,
            volume_confirmed=True,
            sr_levels=SRLevels(
                nearest_support=0.0,
                nearest_resistance=0.0,
                daily_high=0.0,
                daily_low=0.0,
                daily_close=0.0,
            ),
            position_size_multiplier=1.0,
            rejection_reason=None,
        )
    
    def _log_result(self, result: MTFSignalResult) -> None:
        """Log MTF analysis result."""
        if result.should_trade:
            logger.info(
                f"MTF APPROVED: {result.symbol} {result.signal.upper()} | "
                f"Confidence: {result.mtf_confidence:.1f} | "
                f"Size: {result.position_size_multiplier:.2f}x | "
                f"Trend: {result.trend_bias.direction.value}"
            )
        else:
            logger.info(
                f"MTF REJECTED: {result.symbol} {result.signal.upper()} | "
                f"Reason: {result.rejection_reason}"
            )
    
    def refresh_data(self, symbols: list, timeframe: str = None) -> None:
        """Refresh MTF data for symbols.
        
        Args:
            symbols: List of symbols to refresh
            timeframe: Specific timeframe to refresh, or None for all
        """
        if timeframe:
            self.data_manager.refresh_timeframe(timeframe, symbols)
        else:
            for symbol in symbols:
                self.data_manager.fetch_all_timeframes(symbol, force_refresh=True)
    
    def get_cache_status(self) -> Dict:
        """Get status of cached MTF data."""
        return self.data_manager.get_cache_status()
    
    def update_config(self, config: MTFConfig) -> None:
        """Update MTF configuration.
        
        Requirement 9.5: Apply changes without restart.
        """
        self.config = config
        self.signal_filter = MTFSignalFilter(config=config)
        logger.info(f"MTF config updated: enabled={config.enabled}")
