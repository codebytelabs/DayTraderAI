from typing import Optional, Tuple
from datetime import datetime
import asyncio
from config import settings
from core.state import trading_state, Position
from core.alpaca_client import AlpacaClient
from indicators.market_regime import get_regime_detector
from utils.logger import setup_logger

logger = setup_logger(__name__)


class RiskManager:
    """
    Pre-trade risk checks. Every order MUST pass through here.
    No direct order submission allowed.
    """
    
    def __init__(self, alpaca_client: AlpacaClient, sentiment_aggregator=None):
        self.alpaca = alpaca_client
        self.max_positions = settings.max_positions
        self.risk_per_trade_pct = settings.risk_per_trade_pct
        self.circuit_breaker_pct = settings.circuit_breaker_pct
        self.regime_detector = get_regime_detector(alpaca_client)
        self.sentiment_aggregator = sentiment_aggregator
        self.current_regime = None
        
        # Daily cache for enhanced risk management (Sprint 7+)
        try:
            from data.daily_cache import get_daily_cache
            self.daily_cache = get_daily_cache()
            logger.info("✅ Daily cache available for enhanced risk management")
        except Exception as e:
            self.daily_cache = None
            logger.warning(f"Daily cache not available: {e}")
        
        # AI Trade Validator for high-risk trades (Phase 1)
        try:
            from trading.ai_trade_validator import AITradeValidator
            self.ai_validator = AITradeValidator()
            logger.info("✅ AI Trade Validator initialized")
        except Exception as e:
            self.ai_validator = None
            logger.warning(f"AI Trade Validator not available: {e}")
    
    def check_order(
        self,
        symbol: str,
        side: str,
        qty: int,
        price: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        Comprehensive pre-trade risk check.
        Returns (approved, reason)
        """
        
        # 0. Get market regime for adaptive risk management
        # Note: We no longer block trades in choppy markets - we scale position size instead
        regime = self._get_market_regime()
        
        # 1. Check if trading is enabled
        if not trading_state.is_trading_allowed():
            return False, "Trading is disabled"
        
        # 2. Check circuit breaker
        metrics = trading_state.get_metrics()
        if metrics.circuit_breaker_triggered:
            return False, "Circuit breaker triggered"
        
        if metrics.daily_pl_pct < -self.circuit_breaker_pct * 100:
            trading_state.update_metrics(circuit_breaker_triggered=True)
            logger.error(f"CIRCUIT BREAKER TRIGGERED: Daily loss {metrics.daily_pl_pct:.2f}%")
            return False, "Circuit breaker triggered by daily loss"
        
        # 3. Check market is open
        if not self.alpaca.is_market_open():
            return False, "Market is closed"
        
        # 4. Check position limits
        current_positions = len(trading_state.get_all_positions())
        existing_position = trading_state.get_position(symbol)
        
        if existing_position is None and current_positions >= self.max_positions:
            return False, f"Max positions reached ({self.max_positions})"
        
        # 5. Check if opening opposite position (not allowed without closing first)
        if existing_position and existing_position.side != side.lower():
            return False, f"Cannot open {side} position while holding {existing_position.side} position"
        
        # 6. Check buying power and max position size
        try:
            account = self.alpaca.get_account()
            equity = float(account.equity)
            cash = float(account.cash)
            regular_bp = float(account.buying_power)
            daytrading_bp = float(account.daytrading_buying_power)
            
            # Use day trading buying power for intraday trades, with fallback
            if account.pattern_day_trader and daytrading_bp > 0:
                buying_power = daytrading_bp
                # Add safety margin for day trading buying power (10% buffer)
                buying_power *= 0.9  # Use 90% of available to avoid edge cases
            else:
                # Fallback: use cash or regular buying power (whichever is higher)
                buying_power = max(cash, regular_bp)
            
            if price:
                order_value = price * qty
            else:
                # Estimate for market order
                latest_bars = self.alpaca.get_latest_bars([symbol])
                if not latest_bars or symbol not in latest_bars:
                    return False, f"Cannot get price for {symbol}"
                price = float(latest_bars[symbol].close)
                order_value = price * qty
            
            if order_value > buying_power:
                return False, f"Insufficient day trading buying power: need ${order_value:.2f}, have ${buying_power:.2f}"
            
            # Check max position size as % of equity
            max_position_value = equity * settings.max_position_pct
            if order_value > max_position_value:
                return False, f"Position too large: ${order_value:.2f} exceeds max ${max_position_value:.2f} ({settings.max_position_pct*100}% of equity)"
        
        except Exception as e:
            logger.error(f"Failed to check buying power: {e}")
            return False, "Failed to verify buying power"
        
        # 7. Check position sizing (risk per trade) with adaptive sizing
        equity = float(account.equity)
        
        # Get features to extract confidence
        features = trading_state.get_features(symbol)
        confidence = features.get('confidence', 65) if features else 65
        
        # 1. Confidence Scaling (The "Gas Pedal")
        confidence_multiplier = self._get_confidence_multiplier(confidence)
        
        # 2. Regime Safety (The "Brake")
        regime = self._get_market_regime()
        regime_safety_multiplier = self._get_regime_safety_multiplier(regime)
        
        # 3. Sentiment Fine-Tuning
        sentiment_multiplier = self._get_sentiment_multiplier()
        
        # 4. Trend Alignment
        trend_multiplier = self._get_trend_strength_multiplier(symbol, price, side)
        
        # 5. Sector Concentration
        sector_multiplier = self._get_sector_concentration_multiplier(symbol)
        
        # Combined multiplier
        # Base: Confidence * Regime Safety
        # Fine-tuning: Sentiment * Trend * Sector
        combined_multiplier = (
            confidence_multiplier * 
            regime_safety_multiplier * 
            sentiment_multiplier * 
            trend_multiplier * 
            sector_multiplier
        )
        
        # Hard cap at 2.5x to prevent excessive risk
        combined_multiplier = min(combined_multiplier, 2.5)
        
        adjusted_risk_pct = self.risk_per_trade_pct * combined_multiplier
        max_risk_amount = equity * adjusted_risk_pct
        
        logger.info(
            f"Risk Multipliers: Conf({confidence})={confidence_multiplier:.1f}x | "
            f"Safety={regime_safety_multiplier:.2f}x | "
            f"Sent={sentiment_multiplier:.2f}x | "
            f"Trend={trend_multiplier:.2f}x | "
            f"Combined={combined_multiplier:.2f}x | "
            f"Risk={adjusted_risk_pct*100:.2f}%"
        )
        
        # Get features for stop loss calculation
        features = trading_state.get_features(symbol)
        if features and 'atr' in features:
            atr = features['atr']
            
            # Adaptive volatility filter - ADX threshold varies by market regime
            adx = features.get('adx', 25)
            
            # Adjust ADX threshold based on market regime
            # Industry standard: 15-18 for day trading, 20+ for swing trading
            if regime['regime'] == 'choppy':
                adx_threshold = 12  # Very lenient in choppy markets
            elif regime['volatility_level'] == 'high':
                adx_threshold = 15  # Lenient in high volatility
            else:
                adx_threshold = 18  # Day trading threshold (was 20)
            
            if adx < adx_threshold:
                return False, f"Low volatility setup rejected: ADX {adx:.1f} < {adx_threshold} (regime: {regime['regime']})"
            
            # Adaptive volume filter - threshold varies by market regime
            volume_ratio = features.get('volume_ratio', 1.0)
            
            # Determine volume threshold based on regime and time of day
            # Industry standard: 0.5x midday, 0.8x morning, 1.0x+ for breakouts
            import pytz
            from datetime import datetime
            et_time = datetime.now(tz=pytz.timezone('US/Eastern'))
            hour = et_time.hour
            
            # Time-based volume adjustment (volume drops midday)
            if 11 <= hour <= 14:  # Midday lull
                time_volume_mult = 0.6
            elif hour >= 15:  # Afternoon pickup
                time_volume_mult = 0.8
            else:  # Morning
                time_volume_mult = 1.0
            
            if regime['regime'] == 'choppy':
                volume_threshold = 0.4 * time_volume_mult
            elif regime['volatility_level'] == 'high':
                volume_threshold = 0.6 * time_volume_mult
            else:
                volume_threshold = 0.7 * time_volume_mult
            
            if volume_ratio < volume_threshold:
                return False, f"Low volume rejected: {volume_ratio:.2f}x < {volume_threshold:.1f}x (regime: {regime['regime']})"
            
            stop_distance = atr * settings.stop_loss_atr_mult
            risk_per_share = stop_distance
            max_qty = int(max_risk_amount / risk_per_share)
            
            if qty > max_qty:
                return False, f"Position size too large: max {max_qty} shares for {adjusted_risk_pct*100:.2f}% risk"
        
        # 8. Basic sanity checks
        if qty <= 0:
            return False, "Invalid quantity"
        
        # Removed static watchlist check - AI can discover any symbol
        # if symbol not in settings.watchlist_symbols:
        #     return False, f"{symbol} not in watchlist"
        
        # 9. AI validation for high-risk trades (Phase 1)
        if self.ai_validator and settings.ENABLE_AI_VALIDATION:
            # Build context for AI validation
            context = self._build_ai_context(
                symbol, side, qty, price, equity, 
                combined_multiplier, adjusted_risk_pct, features
            )
            
            # Check if this is a high-risk trade
            is_high_risk, risk_reason = self.ai_validator.is_high_risk(symbol, side, context)
            
            if is_high_risk:
                logger.warning(f"🤖 High-risk trade detected for {symbol}: {risk_reason}")
                
                # Run async AI validation
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                approved, ai_reason = loop.run_until_complete(
                    self.ai_validator.validate(symbol, side, features or {}, context)
                )
                
                if not approved:
                    return False, f"AI rejected: {ai_reason}"
                else:
                    logger.info(f"🤖 AI approved high-risk trade: {ai_reason}")
        
        # All checks passed
        logger.info(f"Risk check PASSED: {side} {qty} {symbol}")
        return True, "Approved"
    
    def check_circuit_breaker(self):
        """Check and update circuit breaker status."""
        metrics = trading_state.get_metrics()
        
        if metrics.daily_pl_pct < -self.circuit_breaker_pct * 100:
            if not metrics.circuit_breaker_triggered:
                trading_state.update_metrics(circuit_breaker_triggered=True)
                logger.error(f"CIRCUIT BREAKER TRIGGERED: Daily loss {metrics.daily_pl_pct:.2f}%")
                return True
        
        return metrics.circuit_breaker_triggered
    
    def reset_circuit_breaker(self):
        """Manually reset circuit breaker (use with caution)."""
        trading_state.update_metrics(circuit_breaker_triggered=False)
        logger.warning("Circuit breaker manually reset")
    
    def check_options_trade(self, symbol: str, cost: float, contracts: int) -> bool:
        """
        Check if an options trade is allowed.
        
        Args:
            symbol: Underlying symbol
            cost: Total cost of the options trade
            contracts: Number of contracts
            
        Returns:
            True if trade is allowed
        """
        try:
            # 1. Check if options trading is enabled
            if not settings.options_enabled:
                logger.warning("Options trading is disabled")
                return False
            
            # 2. Check circuit breaker
            if self.check_circuit_breaker():
                logger.warning("Circuit breaker active - options trade rejected")
                return False
            
            # 3. Check max options positions
            positions = trading_state.get_all_positions()
            options_positions = sum(
                1 for p in positions 
                if len(p.get('symbol', '')) > 10  # Options symbols are longer
            )
            
            if options_positions >= settings.max_options_positions:
                logger.warning(
                    f"Max options positions reached: {options_positions}/{settings.max_options_positions}"
                )
                return False
            
            # 4. Check buying power
            account = self.alpaca.get_account()
            if not account:
                logger.error("Failed to get account info")
                return False
            
            buying_power = float(account.buying_power)
            if cost > buying_power:
                logger.warning(
                    f"Insufficient buying power for options: need ${cost:.2f}, have ${buying_power:.2f}"
                )
                return False
            
            # 5. Check risk per trade
            equity = float(account.equity)
            max_risk = equity * settings.options_risk_per_trade_pct
            
            if cost > max_risk:
                logger.warning(
                    f"Options cost exceeds risk limit: ${cost:.2f} > ${max_risk:.2f}"
                )
                return False
            
            # 6. Sanity checks
            if contracts <= 0:
                logger.warning("Invalid number of contracts")
                return False
            
            if contracts > 100:  # Reasonable limit
                logger.warning(f"Too many contracts: {contracts}")
                return False
            
            logger.info(f"Options risk check PASSED: {contracts} contracts, cost ${cost:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Error in options risk check: {e}", exc_info=True)
            return False
    
    def _get_sentiment_multiplier(self) -> float:
        """
        Get position size multiplier based on market sentiment.
        
        Returns:
            float: Multiplier (0.7 in extreme conditions, 1.0 in neutral)
        """
        try:
            if not self.sentiment_aggregator:
                return 1.0  # No adjustment if sentiment not available
            
            sentiment = self.sentiment_aggregator.get_sentiment()
            strategy = self.sentiment_aggregator.get_sentiment_strategy(sentiment['score'])
            
            return strategy['position_size_mult']
            
        except Exception as e:
            logger.error(f"Error getting sentiment multiplier: {e}")
            return 1.0  # Default to no adjustment on error
    
    def _get_trend_strength_multiplier(self, symbol: str, price: float, side: str = 'long') -> float:
        """
        Get position size multiplier based on daily trend strength AND trade direction (Sprint 7+ enhancement).
        
        NOW SUPPORTS BOTH LONG AND SHORT!
        
        Args:
            symbol: Stock symbol
            price: Current price
            side: 'long' or 'short' - determines multiplier logic
            
        Returns:
            float: Multiplier (0.8-1.2 based on trend strength and direction)
        """
        if not self.daily_cache:
            return 1.0
        
        try:
            daily_data = self.daily_cache.get_daily_data(symbol)
            
            if not daily_data:
                return 1.0
            
            ema_200 = daily_data.get('ema_200', 0)
            
            if ema_200 <= 0:
                return 1.0
            
            # Calculate distance from 200-EMA
            distance_pct = ((price - ema_200) / ema_200) * 100
            
            if side == 'long':
                # LONG: Increase size for uptrends (above 200-EMA)
                if distance_pct > 10:  # >10% above 200-EMA
                    return 1.2  # Increase 20%
                elif distance_pct > 5:  # >5% above
                    return 1.1  # Increase 10%
                elif distance_pct > 0:  # Above EMA
                    return 1.0  # Normal size
                elif distance_pct > -5:  # Slightly below
                    return 0.9  # Reduce 10%
                else:  # >5% below
                    return 0.8  # Reduce 20%
            
            elif side == 'short':
                # SHORT: Increase size for downtrends (below 200-EMA)
                if distance_pct < -10:  # >10% below 200-EMA
                    return 1.2  # Increase 20% (strong downtrend)
                elif distance_pct < -5:  # >5% below
                    return 1.1  # Increase 10%
                elif distance_pct < 0:  # Below EMA
                    return 1.0  # Normal size
                elif distance_pct < 5:  # Slightly above
                    return 0.9  # Reduce 10%
                else:  # >5% above
                    return 0.8  # Reduce 20%
            
            return 1.0  # Default
                
        except Exception as e:
            logger.error(f"Error calculating trend multiplier: {e}")
            return 1.0
    
    def _get_sector_concentration_multiplier(self, symbol: str) -> float:
        """
        Get position size multiplier based on sector concentration (Sprint 7+ enhancement).
        
        Reduces position size if too much exposure to one sector.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            float: Multiplier (0.5-1.0 based on sector exposure)
        """
        # TODO: Implement sector tracking
        # For now, return 1.0 (no adjustment)
        # Future: Track sector exposure and reduce if >40% in one sector
        return 1.0

    def _get_confidence_multiplier(self, confidence: float) -> float:
        """
        Get multiplier based on AI confidence score.
        
        Scales risk for high-conviction trades:
        - 85-100%: 2.0x (Double size)
        - 75-84%:  1.5x (1.5x size)
        - 65-74%:  1.0x (Normal size)
        - <65%:    0.0x (Should be rejected by strategy anyway)
        
        Args:
            confidence: Score 0-100
            
        Returns:
            float: Multiplier (1.0-2.0)
        """
        if confidence >= 85:
            return 2.0
        elif confidence >= 75:
            return 1.5
        elif confidence >= 65:
            return 1.0
        else:
            return 1.0  # Default to 1.0 if low confidence passes strategy
            
    def _get_regime_safety_multiplier(self, regime: dict) -> float:
        """
        Get safety multiplier based on market regime.
        
        Reduces risk in difficult trading conditions.
        
        Args:
            regime: Market regime dict
            
        Returns:
            float: Multiplier (0.5-1.0)
        """
        if not regime:
            return 1.0
            
        regime_type = regime.get('regime', 'neutral')
        volatility = regime.get('volatility_level', 'normal')
        
        if regime_type == 'trending':
            return 1.0  # Full size in trends
        elif regime_type == 'bear':
            return 0.50  # Reduce 50% in bear (highest priority for safety)
        elif regime_type == 'choppy':
            return 0.75  # Reduce 25% in chop
        elif volatility == 'high':
            return 0.85  # Reduce 15% in high vol
        else:
            return 1.0
    
    def _get_market_regime(self):
        """Get current market regime (cached for 5 minutes)."""
        from datetime import timedelta
        
        # Use cached regime if less than 5 minutes old
        if (self.current_regime and 
            self.regime_detector.last_update and 
            datetime.now() - self.regime_detector.last_update < timedelta(minutes=5)):
            return self.current_regime
        
        # Detect new regime
        self.current_regime = self.regime_detector.detect_regime()
        return self.current_regime
    
    def _build_ai_context(
        self, 
        symbol: str, 
        side: str, 
        qty: int, 
        price: float, 
        equity: float,
        combined_multiplier: float,
        adjusted_risk_pct: float,
        features: dict
    ) -> dict:
        """Build context dictionary for AI validation."""
        
        # Get symbol cooldown status (handled by trading engine)
        in_cooldown = False
        cooldown_hours = 0
        consecutive_losses = 0
        
        # Get symbol win rate (simplified - no historical stats needed)
        symbol_win_rate = 1.0  # Default to neutral
        
        # Calculate position size as % of equity
        position_value = price * qty
        position_pct = (position_value / equity) * 100
        
        # Check if counter-trend
        counter_trend = False
        daily_trend = 'unknown'
        if self.daily_cache:
            daily_data = self.daily_cache.get_daily_data(symbol)
            if daily_data:
                daily_trend = daily_data.get('ema_trend', 'unknown')
                # Counter-trend if going long in bearish trend or short in bullish trend
                if (side == 'buy' and daily_trend == 'bearish') or \
                   (side == 'sell' and daily_trend == 'bullish'):
                    counter_trend = True
        
        # Get confidence from features
        confidence = features.get('confidence', 100) if features else 100
        
        return {
            'symbol': symbol,
            'side': side,
            'qty': qty,
            'price': price,
            'position_pct': position_pct,
            'in_cooldown': in_cooldown,
            'cooldown_hours': cooldown_hours,
            'consecutive_losses': consecutive_losses,
            'symbol_win_rate': symbol_win_rate,
            'counter_trend': counter_trend,
            'daily_trend': daily_trend,
            'confidence': confidence,
            'combined_multiplier': combined_multiplier,
            'adjusted_risk_pct': adjusted_risk_pct * 100
        }
    
    def emergency_stop(self):
        """Emergency: disable trading and close all positions."""
        logger.error("EMERGENCY STOP TRIGGERED")
        trading_state.disable_trading()
        
        try:
            self.alpaca.close_all_positions()
            logger.info("All positions closed")
        except Exception as e:
            logger.error(f"Failed to close positions during emergency stop: {e}")
