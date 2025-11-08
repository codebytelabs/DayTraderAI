from typing import Optional, Dict
from config import settings
from core.state import trading_state
from data.features import FeatureEngine
from trading.order_manager import OrderManager
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
        self.order_cooldown_seconds = 300  # 5 minutes between orders for same symbol
        
        # Dynamic position sizer
        self.alpaca = order_manager.alpaca  # Get alpaca client from order manager
        self.position_sizer = DynamicPositionSizer(self.alpaca)
        
        # Initialize sentiment aggregator once (reuse for all checks)
        try:
            from indicators.sentiment_aggregator import SentimentAggregator
            self.sentiment_aggregator = SentimentAggregator(self.alpaca)
            logger.info("✅ Sentiment aggregator initialized for short filtering")
        except Exception as e:
            logger.warning(f"⚠️  Could not initialize sentiment aggregator: {e}")
            self.sentiment_aggregator = None
    
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
        
        # CRITICAL: Filter shorts in bullish markets
        if signal == 'sell':
            # Get market sentiment to avoid shorting in uptrends
            if self.sentiment_aggregator:
                try:
                    sentiment_data = self.sentiment_aggregator.get_sentiment()
                    market_score = sentiment_data['score']
                    
                    # Don't short when market is bullish (score > 55)
                    if market_score > 55:
                        logger.info(
                            f"⛔ Short signal rejected for {symbol}: Market too bullish "
                            f"(sentiment: {market_score}/100)"
                        )
                        return None
                    
                    # Require HIGHER confidence for shorts (75% vs 70% for longs)
                    if confidence < 75.0:
                        logger.info(
                            f"⛔ Short signal rejected for {symbol}: Insufficient confidence "
                            f"for short ({confidence:.1f}/100, need 75+)"
                        )
                        return None
                except Exception as e:
                    logger.warning(f"Could not check market sentiment for short filter: {e}")
                    # If we can't check sentiment, require even higher confidence
                    if confidence < 80.0:
                        logger.info(
                            f"⛔ Short signal rejected for {symbol}: Cannot verify market direction, "
                            f"require 80+ confidence (have {confidence:.1f})"
                        )
                        return None
            else:
                # No sentiment aggregator available, require higher confidence
                if confidence < 80.0:
                    logger.info(
                        f"⛔ Short signal rejected for {symbol}: Cannot verify market direction, "
                        f"require 80+ confidence (have {confidence:.1f})"
                    )
                    return None
        
        # Require HIGH confidence score (70/100) - quality over quantity
        if confidence < 70.0:
            logger.debug(
                f"Signal rejected for {symbol}: Low confidence {confidence:.1f}/100 "
                f"(need 70+)"
            )
            return None
        
        # Require at least 3 confirmations - strong signal validation
        if confirmation_count < 3:
            logger.debug(
                f"Signal rejected for {symbol}: Insufficient confirmations {confirmation_count}/4 "
                f"(need 3+)"
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
            price = features['price']
            atr = features['atr']
            
            stop_price = calculate_atr_stop(price, atr, self.stop_mult, signal)
            target_price = calculate_atr_target(price, atr, self.target_mult, signal)
            
            # Enforce minimum stop distance
            stop_distance = abs(price - stop_price)
            min_stop_distance = price * settings.min_stop_distance_pct
            
            if stop_distance < min_stop_distance:
                logger.warning(
                    f"Stop distance too small for {symbol}: ${stop_distance:.2f} < ${min_stop_distance:.2f} "
                    f"(min {settings.min_stop_distance_pct*100}%). Adjusting..."
                )
                # Adjust stop to meet minimum distance
                if signal == 'buy':
                    stop_price = price - min_stop_distance
                else:
                    stop_price = price + min_stop_distance
            
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
            
            # Use dynamic position sizer that considers all constraints
            qty, sizing_reason = self.position_sizer.calculate_optimal_size(
                symbol=symbol,
                price=price,
                confidence=confidence,
                base_risk_pct=adjusted_risk,
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
