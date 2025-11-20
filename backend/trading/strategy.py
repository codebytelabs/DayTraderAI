from typing import Optional, Dict, Tuple
from datetime import datetime
import pytz
from config import settings
from core.state import trading_state
from data.features import FeatureEngine
from data.daily_cache import get_daily_cache
from trading.order_manager import OrderManager
from trading.adaptive_thresholds import AdaptiveThresholds
from utils.helpers import calculate_position_size, calculate_atr_stop, calculate_atr_target
from utils.dynamic_position_sizer import DynamicPositionSizer
from utils.logger import setup_logger

logger = setup_logger(__name__)


class EMAStrategy:
    """
    EMA Crossover Strategy with ATR-based stops and targets.
    Entry: EMA(9) crosses EMA(21)
    Exit: Stop loss or take profit based on ATR
    """
    
    def __init__(self, order_manager: OrderManager, ml_shadow_mode=None):
        self.order_manager = order_manager
        self.ml_shadow_mode = ml_shadow_mode
        self.ema_short = settings.ema_short
        self.ema_long = settings.ema_long
        self.stop_mult = settings.stop_loss_atr_mult
        self.target_mult = settings.take_profit_atr_mult
        
        # Order cooldown tracking to prevent duplicates
        self.last_order_times = {}  # {symbol: timestamp}
        self.order_cooldown_seconds = 180  # 3 minutes between orders for same symbol (day trading velocity)
        
        # Dynamic position sizer
        self.alpaca = order_manager.alpaca  # Get alpaca client from order manager
        self.position_sizer = DynamicPositionSizer(self.alpaca)
        
        # Adaptive thresholds
        self.adaptive_thresholds = AdaptiveThresholds()
        logger.info("✅ Adaptive thresholds initialized")
        
        # Initialize sentiment aggregator once (reuse for all checks)
        try:
            from indicators.sentiment_aggregator import SentimentAggregator
            self.sentiment_aggregator = SentimentAggregator(self.alpaca)
            logger.info("✅ Sentiment aggregator initialized for short filtering")
        except Exception as e:
            logger.warning(f"⚠️  Could not initialize sentiment aggregator: {e}")
            self.sentiment_aggregator = None
    
    def _get_sentiment_score(self) -> int:
        """
        Get current market sentiment score (0-100).
        FIX: Proper async handling to prevent coroutine errors.
        """
        try:
            if self.sentiment_aggregator:
                # FIXED: Proper sync wrapper for async sentiment calls
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If loop is running, use cached value
                        # (avoid nested event loop issues)
                        if hasattr(self.sentiment_aggregator, '_cached_sentiment'):
                            return self.sentiment_aggregator._cached_sentiment.get('score', 50)
                        return 50
                    else:
                        sentiment = loop.run_until_complete(self.sentiment_aggregator.get_sentiment())
                        return sentiment.get('score', 50)
                except RuntimeError:
                    # No event loop, create new one
                    sentiment = asyncio.run(self.sentiment_aggregator.get_sentiment())
                    return sentiment.get('score', 50)
            return 50  # Neutral if unavailable
        except Exception as e:
            logger.warning(f"Could not get sentiment: {e}")
            return 50
    
    def evaluate(self, symbol: str, features: Dict) -> Optional[str]:
        """
        Evaluate strategy for a symbol using enhanced multi-indicator system.
        Returns signal: 'buy', 'sell', or None
        """
        if not features:
            return None
        
        # Check if we already have a position
        existing_position = trading_state.get_position(symbol)
        if existing_position:
            # Don't generate new signals if we have a position
            return None
        
        # Sprint 7: Time-of-day filter (FIRST - eliminates 60-70%, FREE)
        if settings.enable_time_of_day_filter:
            passed, reason = self._is_optimal_trading_time()
            if not passed:
                logger.debug(f"⏰ {symbol} skipped: {reason}")
                return None
        
        # Check order cooldown to prevent duplicates
        from datetime import datetime, timedelta
        now = datetime.now()
        if symbol in self.last_order_times:
            time_since_last = (now - self.last_order_times[symbol]).total_seconds()
            if time_since_last < self.order_cooldown_seconds:
                logger.debug(
                    f"Order cooldown active for {symbol}: {int(time_since_last)}s / {self.order_cooldown_seconds}s"
                )
                return None
        
        # Use enhanced signal detection with multi-indicator confirmation
        signal_info = FeatureEngine.detect_enhanced_signal(features)
        
        if not signal_info:
            return None
        
        signal = signal_info['signal']
        confidence = signal_info['confidence']
        confirmations = signal_info['confirmations']
        confirmation_count = signal_info['confirmation_count']
        market_regime = signal_info['market_regime']
        
        # DEBUG: Log signal generation details
        price = features.get('price', 0)
        ema9 = features.get('ema_short', 0)
        ema21 = features.get('ema_long', 0)
        logger.debug(
            f"🔍 {symbol} signal: {signal.upper()} | "
            f"Price: ${price:.2f} | EMA9: ${ema9:.2f} | EMA21: ${ema21:.2f} | "
            f"EMA9>EMA21: {ema9 > ema21} | Confidence: {confidence:.1f}%"
        )
        
        # Sprint 7: 200-EMA daily trend filter (DISABLED - too restrictive)
        if settings.enable_200_ema_filter:
            passed, reason = self._check_daily_trend(symbol, signal)
            if not passed:
                logger.info(f"📊 {symbol} rejected: {reason}")
                return None
        
        # Sprint 7: Multi-timeframe alignment filter (DISABLED - blocking valid opportunities)
        if settings.enable_multitime_frame_filter:
            passed, reason = self._check_timeframe_alignment(symbol, signal)
            if not passed:
                logger.info(f"📈 {symbol} rejected: {reason}")
                return None
        
        # Log that filters are disabled
        logger.debug(f"✓ {symbol} passed disabled filters (200-EMA: {settings.enable_200_ema_filter}, MTF: {settings.enable_multitime_frame_filter})")
        
        # CRITICAL: Enhanced short entry filters (professional criteria)
        if signal == 'sell':
            # 1. Market sentiment filter - avoid shorting in uptrends
            if self.sentiment_aggregator:
                try:
                    sentiment_data = self.sentiment_aggregator.get_sentiment()
                    market_score = sentiment_data['score']
                    
                    # Don't short when market is bullish (score > 55)
                    if market_score > 55:
                        logger.info(
                            f"⛔ Short rejected {symbol}: Market too bullish (sentiment: {market_score}/100)"
                        )
                        return None
                    
                    # SIMPLIFIED SENTIMENT FILTER FOR DAY TRADING
                    # In extreme fear (< 20), require good confidence (65%+)
                    # Otherwise trust multi-indicator confirmation
                    if market_score < 20 and confidence < 65:
                        logger.info(
                            f"⛔ Short rejected {symbol}: Extreme fear - need 65%+ confidence (got {confidence}%, sentiment: {market_score}/100)"
                        )
                        return None
                    
                    # In fear (15-35), require strong confirmation (3+ indicators)
                    if market_score < 35 and confirmation_count < 3:
                        logger.info(
                            f"⛔ Short rejected {symbol}: Fear environment needs 3+ confirmations (sentiment: {market_score}/100, confirmations: {confirmation_count}/4)"
                        )
                        return None
                    
                    # Log when proceeding in fear conditions
                    if market_score < 35:
                        logger.info(
                            f"⚠️  Short in fear environment {symbol}: Sentiment {market_score}/100, confirmations: {confirmation_count}/4 - Proceeding"
                        )
                    
                    # Log when short passes sentiment filter
                    logger.debug(f"✓ Short sentiment check passed for {symbol}: Sentiment {market_score}/100, confirmations: {confirmation_count}/4")
                        
                except Exception as e:
                    logger.warning(f"Could not check market sentiment for short filter: {e}")
            
            # 2. Price action filter - IMPROVED EMA LOGIC
            price = features.get('price', 0)
            ema_short = features.get('ema_short', 0)
            ema_long = features.get('ema_long', 0)
            
            # IMPROVED: Check EMA relationship, not just price position
            # For shorts, prefer EMA9 < EMA21 (bearish crossover)
            ema_bearish = ema_short < ema_long
            
            if not ema_bearish:
                logger.info(
                    f"⛔ Short rejected {symbol}: EMAs not in bearish alignment (EMA9: ${ema_short:.2f}, EMA21: ${ema_long:.2f})"
                )
                return None
            
            # Allow price slightly above EMA9 if confidence is high
            price_position_pct = (price - ema_short) / ema_short * 100
            max_above_pct = 0.5 if confidence >= 60 else 0.2
            
            if price_position_pct > max_above_pct:
                logger.info(
                    f"⛔ Short rejected {symbol}: Price too far above EMA9 "
                    f"({price_position_pct:.2f}% above, max {max_above_pct}% for {confidence:.0f}% confidence)"
                )
                return None
            
            # 3. Volume confirmation - ADAPTIVE VOLUME THRESHOLDS
            # Lower thresholds in fear markets for high-confidence setups
            volume_ratio = signal_info.get('volume_ratio', 0)
            sentiment_score = self._get_sentiment_score()
            
            # Adaptive volume threshold based on market conditions
            # FIXED: Much lower thresholds for 1-minute bars
            if sentiment_score < 30:
                # In fear markets, require higher confidence for lower volume
                if confidence >= 65:
                    min_volume = 0.25  # High-confidence shorts can use lower volume
                else:
                    min_volume = 0.30  # Lower threshold for 1-min bars
            else:
                min_volume = 0.30  # Lower threshold for 1-min bars in normal markets
            
            if volume_ratio < min_volume:
                logger.info(
                    f"⛔ Short rejected {symbol}: Extremely low volume for short "
                    f"(volume: {volume_ratio:.2f}x, need {min_volume:.2f}x+ for {confidence:.0f}% confidence in {sentiment_score}/100 sentiment)"
                )
                return None
            
            # 4. RSI filter - avoid shorting oversold (RSI < 30)
            rsi = signal_info.get('rsi', 50)
            if rsi < 30:
                logger.info(
                    f"⛔ Short rejected {symbol}: Oversold - bounce risk (RSI: {rsi:.1f})"
                )
                return None
            
            # 5. Require HIGHER confidence for shorts - ADAPTIVE THRESHOLDS
            # Get dynamic threshold based on market conditions
            sentiment_score = self._get_sentiment_score()
            regime_multiplier = signal_info.get('regime_multiplier', 0.5)
            
            _, short_threshold = self.adaptive_thresholds.get_thresholds(
                market_regime=market_regime,
                regime_multiplier=regime_multiplier,
                sentiment_score=sentiment_score
            )
            
            # Apply reasonable cap on short threshold in fear markets
            # Industry standard: Max 70-75% confidence requirement
            capped_short_threshold = min(short_threshold, 0.75)
            if confidence < capped_short_threshold * 100:
                logger.info(
                    f"⛔ Short rejected {symbol}: Insufficient confidence "
                    f"({confidence:.1f}/100, need {capped_short_threshold*100:.0f}+ in current conditions)"
                )
                return None
            
            logger.info(
                f"✓ Short entry validated for {symbol}: "
                f"Below EMAs, Volume {volume_ratio:.2f}x, RSI {rsi:.1f}, Confidence {confidence:.1f}%"
            )
        
        # ADAPTIVE VOLUME FILTER FOR LONGS
        # Apply volume filter for long signals too
        # FIX: Volume ratio on 1-minute bars is too granular - only reject VERY low volume
        if signal == 'buy':
            volume_ratio = signal_info.get('volume_ratio', 0)
            sentiment_score = self._get_sentiment_score()
            
            # FIXED: Much lower thresholds for 1-minute bars (0.38x is normal for META!)
            # Only reject if volume is EXTREMELY low (< 0.2x = red flag)
            if sentiment_score < 30:
                # In fear markets, allow even lower volume for high-confidence longs
                if confidence >= 60:
                    min_volume = 0.15  # Very low threshold for high-confidence
                else:
                    min_volume = 0.20  # Only reject extreme low volume
            else:
                min_volume = 0.20  # Only reject extreme low volume in normal markets
            
            if volume_ratio < min_volume:
                logger.info(
                    f"⛔ Long rejected {symbol}: Extremely low volume "
                    f"(volume: {volume_ratio:.2f}x, need {min_volume:.2f}x+ for {confidence:.0f}% confidence in {sentiment_score}/100 sentiment)"
                )
                return None
        
        # CRITICAL: Check if opportunity has enough profit potential
        # Calculate expected R/R ratio from features
        price = features.get('price', 0)
        atr = features.get('atr', 0)
        
        if atr > 0:
            # Calculate potential stop and target
            potential_stop = calculate_atr_stop(price, atr, self.stop_mult, signal)
            potential_target = calculate_atr_target(price, atr, self.target_mult, signal)
            
            risk = abs(price - potential_stop)
            reward = abs(potential_target - price)
            potential_rr = reward / risk if risk > 0 else 0
            
            # Require minimum 2.0:1 R/R for quality setups (with small tolerance for rounding)
            if potential_rr < 1.95:  # 1.95 allows for rounding to 2.0
                logger.info(
                    f"⛔ {symbol} rejected: Insufficient profit potential "
                    f"(R/R {potential_rr:.2f}:1, need 2.0:1+) - "
                    f"Risk ${risk:.2f}, Reward ${reward:.2f}"
                )
                return None
            
            # Log stop distance for monitoring (no minimum check - trust ATR)
            risk_pct = (risk / price) * 100
            logger.debug(f"✓ {symbol} stop distance: {risk_pct:.2f}% (ATR-based)")
            
            logger.info(
                f"✓ {symbol} profit potential validated: "
                f"R/R {potential_rr:.2f}:1, Risk {risk_pct:.1f}%, "
                f"Stop ${potential_stop:.2f}, Target ${potential_target:.2f}"
            )
        
        # Require HIGH confidence score - ADAPTIVE THRESHOLDS
        # Get dynamic threshold based on market conditions
        sentiment_score = self._get_sentiment_score()
        regime_multiplier = signal_info.get('regime_multiplier', 0.5)
        
        long_threshold, short_threshold = self.adaptive_thresholds.get_thresholds(
            market_regime=market_regime,
            regime_multiplier=regime_multiplier,
            sentiment_score=sentiment_score
        )
        
        # Use appropriate threshold based on signal direction
        required_threshold = short_threshold if signal == 'sell' else long_threshold
        
        # Check if trading should be paused entirely
        should_pause, pause_reason = self.adaptive_thresholds.should_pause_trading(
            market_regime=market_regime,
            regime_multiplier=regime_multiplier,
            sentiment_score=sentiment_score
        )
        
        if should_pause:
            logger.warning(
                f"⏸️  Trading paused for {symbol}: {pause_reason}"
            )
            return None
        
        # Check confidence against adaptive threshold
        if confidence < required_threshold * 100:
            logger.info(
                f"⛔ {symbol} rejected: Insufficient confidence "
                f"({confidence:.1f}/100, need {required_threshold*100:.0f}+ in current conditions)"
            )
            return None
        
        # Require at least 2 confirmations with high confidence, or 3 with lower confidence
        # Industry standard: 2/4 confirmations acceptable for day trading
        min_confirmations = 2 if confidence >= 65 else 3
        if confirmation_count < min_confirmations:
            logger.debug(
                f"Signal rejected for {symbol}: Insufficient confirmations {confirmation_count}/4 "
                f"(need {min_confirmations}+ for {confidence:.0f}% confidence)"
            )
            return None
        
        # Allow ranging markets too - we can trade them with proper risk management
        # (Removed the ranging market filter)
        
        # Log enhanced signal details
        logger.info(
            f"✓ Enhanced signal for {symbol}: {signal.upper()} | "
            f"Confidence: {confidence:.1f}/100 | "
            f"Confirmations: {confirmation_count}/4 {confirmations} | "
            f"Regime: {market_regime} | "
            f"RSI: {signal_info['rsi']:.1f} | "
            f"ADX: {signal_info['adx']:.1f} | "
            f"Volume: {signal_info['volume_ratio']:.2f}x"
        )
        
        # Store signal info for position sizing
        features['_signal_info'] = signal_info
        
        return signal
    
    def execute_signal(self, symbol: str, signal: str, features: Dict) -> bool:
        """
        Execute trading signal with proper position sizing.
        Returns True if order submitted successfully.
        """
        try:
            # Get account info for position sizing
            metrics = trading_state.get_metrics()
            equity = metrics.equity
            
            if equity <= 0:
                logger.error("Invalid equity for position sizing")
                return False
            
            # Calculate position size based on risk
            # CRITICAL FIX: Get REAL-TIME price, not stale bar data
            # Historical bars can be 1-2 minutes old, causing slippage!
            features_price = features.get('price', 0)
            
            # Try to get real-time trade price first (most accurate)
            realtime_price = self.alpaca.get_latest_trade_price(symbol)
            
            if realtime_price:
                # Use real-time price for order execution
                price = realtime_price
                
                # Log price difference for monitoring
                price_diff = abs(realtime_price - features_price)
                price_diff_pct = (price_diff / features_price) * 100 if features_price > 0 else 0
                
                if price_diff_pct > 0.5:
                    logger.warning(
                        f"⚠️  Price discrepancy for {symbol}: "
                        f"Features ${features_price:.2f} vs Real-time ${realtime_price:.2f} "
                        f"({price_diff_pct:.2f}% difference) - Using real-time price"
                    )
                else:
                    logger.info(
                        f"✓ Price verified for {symbol}: ${realtime_price:.2f} "
                        f"(features: ${features_price:.2f}, diff: {price_diff_pct:.2f}%)"
                    )
            else:
                # Fallback to features price if real-time API fails
                price = features_price
                logger.warning(
                    f"⚠️  Using features price for {symbol}: ${price:.2f} "
                    f"(real-time price unavailable)"
                )
            atr = features['atr']
            
            stop_price = calculate_atr_stop(price, atr, self.stop_mult, signal)
            target_price = calculate_atr_target(price, atr, self.target_mult, signal)
            
            # CRITICAL FIX: Account for slippage in bracket calculations
            # Market orders can slip 0.1-0.3%, so we need wider brackets
            slippage_buffer = 0.003  # 0.3% slippage buffer
            
            # Adjust entry price for expected slippage
            if signal == 'buy':
                expected_fill_price = price * (1 + slippage_buffer)  # Expect to buy higher
            else:
                expected_fill_price = price * (1 - slippage_buffer)  # Expect to sell lower
            
            # Recalculate brackets from expected fill price
            stop_price = calculate_atr_stop(expected_fill_price, atr, self.stop_mult, signal)
            target_price = calculate_atr_target(expected_fill_price, atr, self.target_mult, signal)
            
            logger.info(
                f"💰 Slippage-adjusted brackets for {symbol}: "
                f"Signal ${price:.2f} → Expected ${expected_fill_price:.2f} "
                f"(+{slippage_buffer*100:.1f}% buffer)"
            )
            
            # Enforce minimum stop distance - ADAPTIVE based on volatility
            # Use ATR/Price ratio to determine volatility
            atr_pct = (atr / expected_fill_price) * 100  # ATR as % of price
            
            # Dynamic minimum stop based on volatility:
            # Low volatility (ATR < 1%): 1.5% min stop (not 1.0% - TDG was 0.11%!)
            # Medium volatility (ATR 1-2%): 2.0% min stop  
            # High volatility (ATR 2-3%): 2.5% min stop
            # Very high volatility (ATR > 3%): 3.0% min stop
            if atr_pct < 1.0:
                min_stop_pct = 0.015  # 1.5% (CRITICAL: was 1.0%, caused TDG bug)
            elif atr_pct < 2.0:
                min_stop_pct = 0.020  # 2.0%
            elif atr_pct < 3.0:
                min_stop_pct = 0.025  # 2.5%
            else:
                min_stop_pct = 0.030  # 3.0%
            
            stop_distance = abs(expected_fill_price - stop_price)
            min_stop_distance = expected_fill_price * min_stop_pct
            
            if stop_distance < min_stop_distance:
                logger.warning(
                    f"Stop distance too small for {symbol}: ${stop_distance:.2f} < ${min_stop_distance:.2f} "
                    f"(min {min_stop_pct*100:.1f}% for {atr_pct:.1f}% ATR). Adjusting..."
                )
                # Adjust stop to meet minimum distance
                if signal == 'buy':
                    stop_price = expected_fill_price - min_stop_distance
                else:  # sell/short
                    stop_price = expected_fill_price + min_stop_distance
                
                logger.info(f"Adjusted stop for {symbol}: ${stop_price:.2f} (entry: ${expected_fill_price:.2f}, volatility: {atr_pct:.1f}% ATR, min: {min_stop_pct*100:.1f}%)")
            
            # CRITICAL: Ensure minimum R/R ratio of 2:1 for profitability
            risk = abs(expected_fill_price - stop_price)
            reward = abs(target_price - expected_fill_price)
            rr_ratio = reward / risk if risk > 0 else 0
            
            if rr_ratio < 2.0:
                # Adjust target to achieve 2:1 R/R minimum
                if signal == 'buy':
                    target_price = expected_fill_price + (risk * 2.0)
                else:
                    target_price = expected_fill_price - (risk * 2.0)
                
                logger.info(
                    f"Adjusted target for {symbol} to achieve 2:1 R/R: "
                    f"${target_price:.2f} (risk ${risk:.2f}, reward ${reward:.2f})"
                )
            
            # Dynamic risk based on confidence score
            signal_info = features.get('_signal_info', {})
            confidence = signal_info.get('confidence', 50.0)
            
            # Scale risk based on confidence - OPTIMIZED FOR QUALITY TRADES
            # With higher quality threshold (70%+), we can size more aggressively
            # Confidence 70-75: 1.0% risk (good quality)
            # Confidence 75-80: 1.2% risk (high quality)
            # Confidence 80-85: 1.5% risk (very high quality)
            # Confidence 85-90: 1.8% risk (excellent quality)
            # Confidence 90-100: 2.0% risk (exceptional quality)
            base_risk = settings.risk_per_trade_pct
            
            if confidence >= 90:
                risk_multiplier = 2.0  # Exceptional - max size
            elif confidence >= 85:
                risk_multiplier = 1.8  # Excellent
            elif confidence >= 80:
                risk_multiplier = 1.5  # Very high quality
            elif confidence >= 75:
                risk_multiplier = 1.2  # High quality
            elif confidence >= 70:
                risk_multiplier = 1.0  # Good quality (minimum threshold)
            else:
                # Below 70% shouldn't reach here due to earlier filter
                risk_multiplier = 0.8
            
            adjusted_risk = base_risk * risk_multiplier
            adjusted_risk = max(0.01, min(adjusted_risk, 0.02))  # Cap at 1.0-2.0%
            
            logger.info(
                f"💰 Position sizing for {symbol}: Confidence {confidence:.1f}/100 → "
                f"Risk {adjusted_risk*100:.2f}% (base {base_risk*100:.1f}% × {risk_multiplier:.1f}x) | "
                f"Quality-adjusted sizing enabled"
            )
            
            # Apply time-of-day position sizing multiplier
            time_passed, time_session = self._is_optimal_trading_time()
            time_multiplier = 1.0
            
            if time_session == "morning_session":
                time_multiplier = 1.0  # Full size (9:30-11:00 AM)
            elif time_session == "midday_session":
                time_multiplier = 0.7  # 70% size (11:00 AM-2:00 PM)
            elif time_session == "closing_session":
                time_multiplier = 0.5  # 50% size (2:00-3:30 PM)
            
            adjusted_risk_with_time = adjusted_risk * time_multiplier
            
            logger.info(
                f"⏰ Time-based sizing for {symbol}: {time_session} → "
                f"{time_multiplier*100:.0f}% size (risk {adjusted_risk_with_time*100:.2f}%)"
            )
            
            # Calculate actual stop distance for position sizing
            actual_stop_distance = abs(price - stop_price)
            
            # Use dynamic position sizer that considers all constraints
            qty, sizing_reason = self.position_sizer.calculate_optimal_size(
                symbol=symbol,
                price=price,
                stop_distance=actual_stop_distance,
                confidence=confidence,
                base_risk_pct=adjusted_risk_with_time,
                max_position_pct=settings.max_position_pct
            )
            
            logger.info(f"Dynamic position sizing for {symbol}: {sizing_reason}")
            
            if qty <= 0:
                logger.warning(f"Position size too small for {symbol}")
                return False
            
            # Cap position size at max position value AND available buying power
            max_position_value = equity * settings.max_position_pct
            position_value = qty * price
            
            # Final check: ensure we don't exceed max position size
            max_position_value = equity * settings.max_position_pct
            position_value = qty * price
            
            if position_value > max_position_value:
                # Reduce quantity to fit within max position size
                original_qty = qty
                qty = int(max_position_value / price)
                logger.warning(
                    f"Position size capped by equity limit: {original_qty} shares → {qty} shares "
                    f"(${position_value:,.2f} → ${qty * price:,.2f}, max {settings.max_position_pct*100}% of equity)"
                )
                
                if qty <= 0:
                    logger.warning(f"Position size too small after capping for {symbol}")
                    return False
            
            # Submit order with enhanced reason
            signal_info = features.get('_signal_info', {})
            confirmations = signal_info.get('confirmations', [])
            confirmation_str = ', '.join(confirmations) if confirmations else 'none'
            
            reason = (
                f"EMA({self.ema_short}/{self.ema_long}) {signal.upper()} | "
                f"Confidence: {confidence:.0f}/100 | "
                f"Confirmed: {confirmation_str}"
            )
            
            # ML Shadow Mode: Make prediction before order submission
            if self.ml_shadow_mode:
                try:
                    import asyncio
                    ml_prediction = asyncio.create_task(
                        self.ml_shadow_mode.get_prediction(
                            symbol=symbol,
                            signal_data={
                                'signal_type': signal,
                                'price': price,
                                'stop_price': stop_price,
                                'target_price': target_price,
                                'confidence': confidence,
                                'confirmations': confirmations,
                                'indicators': {
                                    'rsi': signal_info.get('rsi'),
                                    'macd': signal_info.get('macd'),
                                    'adx': signal_info.get('adx'),
                                    'volume_ratio': signal_info.get('volume_ratio'),
                                },
                            },
                            existing_confidence=confidence
                        )
                    )
                    logger.debug(f"🤖 ML prediction queued for {symbol}")
                except Exception as e:
                    logger.warning(f"ML prediction failed for {symbol}: {e}")
            
            order = self.order_manager.submit_order(
                symbol=symbol,
                side=signal,
                qty=qty,
                reason=reason,
                price=price,
                take_profit_price=target_price,
                stop_loss_price=stop_price,
            )
            
            if order:
                # Update cooldown timestamp to prevent duplicate orders
                from datetime import datetime
                self.last_order_times[symbol] = datetime.now()
                
                logger.info(
                    f"✓ Order submitted: {signal.upper()} {qty} {symbol} @ ~${price:.2f} | "
                    f"Stop: ${stop_price:.2f} | Target: ${target_price:.2f} | "
                    f"Confidence: {confidence:.0f}/100 | Risk: {adjusted_risk*100:.2f}%"
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to execute signal for {symbol}: {e}")
            return False
    
    def check_exit(self, symbol: str, features: Dict) -> Optional[str]:
        """
        Check if we should exit a position.
        Returns 'stop_loss', 'take_profit', or None
        """
        position = trading_state.get_position(symbol)
        if not position:
            return None
        
        current_price = features['price']
        
        # Check stop loss
        if position.side == 'buy':
            if current_price <= position.stop_loss:
                return 'stop_loss'
            if current_price >= position.take_profit:
                return 'take_profit'
        else:  # sell/short
            if current_price >= position.stop_loss:
                return 'stop_loss'
            if current_price <= position.take_profit:
                return 'take_profit'
        
        return None
    
    def execute_exit(self, symbol: str, reason: str) -> bool:
        """Execute exit order."""
        try:
            position = trading_state.get_position(symbol)
            if not position:
                return False
            
            # Determine exit side (opposite of entry)
            exit_side = 'sell' if position.side == 'buy' else 'buy'
            
            order = self.order_manager.submit_order(
                symbol=symbol,
                side=exit_side,
                qty=position.qty,
                reason=reason
            )
            
            if order:
                logger.info(f"Exit order submitted: {symbol} ({reason})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to execute exit for {symbol}: {e}")
            return False
    
    def _is_optimal_trading_time(self) -> Tuple[bool, str]:
        """
        Check if current time is optimal for trading.
        
        ENHANCED: Full day trading with adaptive position sizing
        - 9:30-11:00 AM: Morning session (100% position size)
        - 11:00 AM-2:00 PM: Midday session (70% position size)
        - 2:00-3:30 PM: Closing session (50% position size)
        
        Returns:
            (is_optimal, reason_if_not)
        """
        try:
            now = datetime.now(tz=pytz.timezone('US/Eastern'))
            hour = now.hour
            minute = now.minute
            current_minutes = hour * 60 + minute
            
            # Morning session: 9:30-11:00 AM (100% size)
            start_h1, start_m1 = settings.optimal_hours_start_1
            end_h1, end_m1 = settings.optimal_hours_end_1
            morning_start = start_h1 * 60 + start_m1
            morning_end = end_h1 * 60 + end_m1
            
            if morning_start <= current_minutes < morning_end:
                return True, "morning_session"
            
            # Midday session: 11:00 AM-2:00 PM (70% size)
            start_h2, start_m2 = settings.optimal_hours_start_2
            end_h2, end_m2 = settings.optimal_hours_end_2
            midday_start = start_h2 * 60 + start_m2
            midday_end = end_h2 * 60 + end_m2
            
            if midday_start <= current_minutes < midday_end:
                return True, "midday_session"
            
            # Closing session: 2:00-3:30 PM (50% size)
            start_h3, start_m3 = settings.optimal_hours_start_3
            end_h3, end_m3 = settings.optimal_hours_end_3
            closing_start = start_h3 * 60 + start_m3
            closing_end = end_h3 * 60 + end_m3
            
            if closing_start <= current_minutes < closing_end:
                return True, "closing_session"
            
            # Outside trading hours
            return False, "Outside trading hours (9:30 AM - 3:30 PM)"
            
        except Exception as e:
            logger.warning(f"Time-of-day filter error: {e}")
            return True, "morning_session"  # Default to morning session if error
    
    def _check_daily_trend(self, symbol: str, signal: str) -> Tuple[bool, str]:
        """
        Check 200-EMA daily trend alignment.
        
        Sprint 7: 200-EMA daily trend filter
        - Only long when daily price > 200-EMA
        - Only short when daily price < 200-EMA
        
        Args:
            symbol: Stock symbol
            signal: 'buy' or 'sell'
            
        Returns:
            (is_aligned, reason_if_not)
        """
        try:
            daily_cache = get_daily_cache()
            daily_data = daily_cache.get_daily_data(symbol)
            
            if not daily_data:
                logger.debug(f"No daily data for {symbol}, allowing trade")
                return True, ""  # Allow if no data
            
            daily_price = daily_data['price']
            daily_200_ema = daily_data['ema_200']
            
            # Only long when price > 200-EMA (with-trend)
            if signal == 'buy' and daily_price < daily_200_ema:
                return False, f"Counter-trend long (daily ${daily_price:.2f} < 200-EMA ${daily_200_ema:.2f})"
            
            # Only short when price < 200-EMA (with-trend)
            if signal == 'sell' and daily_price > daily_200_ema:
                return False, f"Counter-trend short (daily ${daily_price:.2f} > 200-EMA ${daily_200_ema:.2f})"
            
            return True, ""
            
        except Exception as e:
            logger.warning(f"Daily trend filter error for {symbol}: {e}")
            return True, ""  # Allow if error
    
    def _check_timeframe_alignment(self, symbol: str, signal: str) -> Tuple[bool, str]:
        """
        Check multi-timeframe alignment.
        
        Sprint 7: Multi-timeframe alignment filter
        - Only long when daily EMA trend is bullish
        - Only short when daily EMA trend is bearish
        
        Args:
            symbol: Stock symbol
            signal: 'buy' or 'sell'
            
        Returns:
            (is_aligned, reason_if_not)
        """
        try:
            daily_cache = get_daily_cache()
            daily_data = daily_cache.get_daily_data(symbol)
            
            if not daily_data:
                logger.debug(f"No daily data for {symbol}, allowing trade")
                return True, ""  # Allow if no data
            
            daily_trend = daily_data['trend']
            
            # Only long when daily trend is bullish
            if signal == 'buy' and daily_trend != 'bullish':
                return False, f"Daily trend {daily_trend}, not bullish"
            
            # Only short when daily trend is bearish
            if signal == 'sell' and daily_trend != 'bearish':
                return False, f"Daily trend {daily_trend}, not bearish"
            
            return True, ""
            
        except Exception as e:
            logger.warning(f"Timeframe alignment filter error for {symbol}: {e}")
            return True, ""  # Allow if error
