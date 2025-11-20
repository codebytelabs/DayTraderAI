# Momentum signal validator - combines all indicators
# Determines if momentum is strong enough to extend targets

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from .config import MomentumConfig
from .signals import MomentumSignal
from .indicators import ADXCalculator, VolumeAnalyzer, TrendStrengthCalculator

logger = logging.getLogger(__name__)

class MomentumSignalValidator:
    """
    Validates momentum signals by combining multiple technical indicators.
    Returns a MomentumSignal with the decision and all indicator values.
    """
    
    def __init__(self, config: MomentumConfig):
        self.config = config
        
        # Initialize calculators
        self.adx_calculator = ADXCalculator(period=config.adx_period)
        self.volume_analyzer = VolumeAnalyzer(lookback_period=config.volume_lookback)
        self.trend_calculator = TrendStrengthCalculator()
        
        logger.info("✅ Momentum Signal Validator initialized")
        self.config.log_config()
    
    def validate_momentum(
        self,
        symbol: str,
        high: List[float],
        low: List[float],
        close: List[float],
        volume: List[float],
        current_profit_r: float,
        data_timestamp: Optional[datetime] = None
    ) -> MomentumSignal:
        """
        Validate if momentum is strong enough to extend target.
        
        Args:
            symbol: Stock symbol
            high: List of high prices (most recent last)
            low: List of low prices
            close: List of close prices
            volume: List of volume values
            current_profit_r: Current profit in R-multiples
            data_timestamp: Timestamp of the data (for freshness check)
            
        Returns:
            MomentumSignal with decision and all indicator values
        """
        try:
            # Check if feature is enabled
            if not self.config.enabled:
                return MomentumSignal(
                    extend=False,
                    reason="Momentum system disabled",
                    symbol=symbol,
                    current_profit_r=current_profit_r
                )
            
            # Validate data freshness
            data_fresh = self._check_data_freshness(data_timestamp)
            if not data_fresh:
                return MomentumSignal(
                    extend=False,
                    reason="Data not fresh enough",
                    symbol=symbol,
                    current_profit_r=current_profit_r,
                    data_fresh=False
                )
            
            # Validate data length
            min_length = max(
                self.config.adx_period + 10,
                self.config.volume_lookback + 1,
                50  # For trend strength
            )
            
            if len(close) < min_length:
                logger.warning(f"Insufficient data for {symbol}: {len(close)} bars, need {min_length}")
                return MomentumSignal(
                    extend=False,
                    reason=f"Insufficient data ({len(close)} bars)",
                    symbol=symbol,
                    current_profit_r=current_profit_r
                )
            
            # Calculate all indicators
            adx = self.adx_calculator.calculate(high, low, close)
            volume_ratio = self.volume_analyzer.calculate_volume_ratio(volume)
            trend_strength = self.trend_calculator.calculate(close, high, low)
            
            # Check each indicator against thresholds
            adx_pass = adx > self.config.adx_threshold
            volume_pass = volume_ratio > self.config.volume_threshold
            trend_pass = trend_strength > self.config.trend_threshold
            
            # Make decision: ALL indicators must pass
            extend = adx_pass and volume_pass and trend_pass
            
            # Build reason string
            if extend:
                reason = f"Strong momentum detected (ADX: {adx:.1f}, Vol: {volume_ratio:.2f}x, Trend: {trend_strength:.2f})"
            else:
                failed = []
                if not adx_pass:
                    failed.append(f"ADX {adx:.1f} < {self.config.adx_threshold}")
                if not volume_pass:
                    failed.append(f"Vol {volume_ratio:.2f}x < {self.config.volume_threshold}x")
                if not trend_pass:
                    failed.append(f"Trend {trend_strength:.2f} < {self.config.trend_threshold}")
                reason = "Weak momentum: " + ", ".join(failed)
            
            # Create signal
            signal = MomentumSignal(
                extend=extend,
                adx=adx,
                volume_ratio=volume_ratio,
                trend_strength=trend_strength,
                reason=reason,
                symbol=symbol,
                current_profit_r=current_profit_r,
                adx_pass=adx_pass,
                volume_pass=volume_pass,
                trend_pass=trend_pass,
                data_fresh=data_fresh
            )
            
            # Log the signal
            signal.log_signal()
            
            return signal
            
        except Exception as e:
            logger.error(f"Error validating momentum for {symbol}: {e}")
            return MomentumSignal(
                extend=False,
                reason=f"Error: {str(e)}",
                symbol=symbol,
                current_profit_r=current_profit_r
            )
    
    def _check_data_freshness(self, data_timestamp: Optional[datetime]) -> bool:
        """Check if data is fresh enough"""
        if data_timestamp is None:
            # If no timestamp provided, assume fresh
            return True
        
        age_seconds = (datetime.now() - data_timestamp).total_seconds()
        is_fresh = age_seconds <= self.config.data_freshness_seconds
        
        if not is_fresh:
            logger.warning(f"Data is {age_seconds:.0f}s old (max: {self.config.data_freshness_seconds}s)")
        
        return is_fresh
    
    def validate_with_rsi(
        self,
        symbol: str,
        high: List[float],
        low: List[float],
        close: List[float],
        volume: List[float],
        rsi: float,
        current_profit_r: float,
        data_timestamp: Optional[datetime] = None
    ) -> MomentumSignal:
        """
        Validate momentum with optional RSI component.
        
        Args:
            symbol: Stock symbol
            high: List of high prices
            low: List of low prices
            close: List of close prices
            volume: List of volume values
            rsi: RSI value (0-100)
            current_profit_r: Current profit in R-multiples
            data_timestamp: Timestamp of the data
            
        Returns:
            MomentumSignal with decision and all indicator values including RSI
        """
        # Get base signal
        signal = self.validate_momentum(
            symbol=symbol,
            high=high,
            low=low,
            close=close,
            volume=volume,
            current_profit_r=current_profit_r,
            data_timestamp=data_timestamp
        )
        
        # Add RSI component if enabled
        if self.config.include_rsi:
            signal.rsi = rsi
            
            # RSI should be > 60 for bullish momentum
            rsi_pass = rsi > 60
            
            # Update decision: require RSI to pass as well
            if signal.extend and not rsi_pass:
                signal.extend = False
                signal.reason += f" | RSI {rsi:.1f} < 60"
            elif signal.extend and rsi_pass:
                signal.reason += f" | RSI {rsi:.1f} confirms"
        
        return signal
    
    def batch_validate(
        self,
        positions: List[Dict],
        market_data: Dict[str, Dict]
    ) -> Dict[str, MomentumSignal]:
        """
        Validate momentum for multiple positions at once.
        
        Args:
            positions: List of position dicts with symbol, entry_price, current_price, etc.
            market_data: Dict mapping symbol to OHLCV data
            
        Returns:
            Dict mapping symbol to MomentumSignal
        """
        results = {}
        
        for position in positions:
            symbol = position['symbol']
            
            if symbol not in market_data:
                logger.warning(f"No market data for {symbol}")
                continue
            
            data = market_data[symbol]
            
            # Calculate current profit in R
            entry_price = position['entry_price']
            current_price = position['current_price']
            stop_loss = position['stop_loss']
            
            risk = abs(entry_price - stop_loss)
            if risk == 0:
                logger.warning(f"Zero risk for {symbol}, skipping")
                continue
            
            profit = current_price - entry_price
            profit_r = profit / risk
            
            # Validate momentum
            signal = self.validate_momentum(
                symbol=symbol,
                high=data['high'],
                low=data['low'],
                close=data['close'],
                volume=data['volume'],
                current_profit_r=profit_r,
                data_timestamp=data.get('timestamp')
            )
            
            results[symbol] = signal
        
        logger.info(f"Validated momentum for {len(results)} positions")
        return results
    
    def update_config(self, new_config: MomentumConfig):
        """Update configuration and reinitialize calculators if needed"""
        self.config = new_config
        
        # Reinitialize calculators with new periods
        self.adx_calculator = ADXCalculator(period=new_config.adx_period)
        self.volume_analyzer = VolumeAnalyzer(lookback_period=new_config.volume_lookback)
        
        logger.info("✅ Momentum validator config updated")
        self.config.log_config()
