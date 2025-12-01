import asyncio
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from core.alpaca_client import AlpacaClient
from core.supabase_client import SupabaseClient
from core.state import trading_state
from trading.risk_manager import RiskManager
from trading.order_manager import OrderManager
from trading.position_manager import PositionManager
from trading.strategy import EMAStrategy
from trading.options_strategy import OptionsStrategy
from data.market_data import MarketDataManager
from streaming import StreamManager, StreamingBroadcaster
from options.options_client import OptionsClient
from scanner.opportunity_scanner import OpportunityScanner
from config import settings
from utils.logger import setup_logger

# Momentum Wave Rider imports
try:
    from scanner.momentum_scanner import MomentumScanner
    from scanner.momentum_scorer import MomentumScorer
    from utils.confidence_sizer import ConfidenceBasedSizer
    from trading.wave_entry import WaveEntryEngine
    MOMENTUM_SCANNER_AVAILABLE = True
except ImportError as e:
    MOMENTUM_SCANNER_AVAILABLE = False
    logger.warning(f"Momentum scanner not available: {e}")

logger = setup_logger(__name__)


class TradingEngine:
    """
    Main trading engine that orchestrates all components.
    Runs automation loops for data, strategy, and position monitoring.
    """
    
    def __init__(
        self,
        alpaca_client: AlpacaClient,
        supabase_client: SupabaseClient,
        risk_manager: RiskManager,
        order_manager: OrderManager,
        position_manager: PositionManager,
        strategy: EMAStrategy,
        market_data_manager: MarketDataManager,
        options_client: Optional[OptionsClient] = None,
        stream_manager: Optional[StreamManager] = None,
        streaming_broadcaster: Optional[StreamingBroadcaster] = None,
        snapshot_builder: Optional[Callable[[], Dict]] = None,
        ml_shadow_mode: Optional[Any] = None,
    ):
        self.alpaca = alpaca_client
        self.supabase = supabase_client
        self.risk_manager = risk_manager
        self.order_manager = order_manager
        self.position_manager = position_manager
        self.strategy = strategy
        self.market_data = market_data_manager
        self.stream_manager = stream_manager
        self.streaming_broadcaster = streaming_broadcaster
        self.snapshot_builder = snapshot_builder
        self.streaming_enabled = settings.streaming_enabled
        self.stream_reconnect_delay = settings.stream_reconnect_delay
        self._streaming_active = False
        self.ml_shadow_mode = ml_shadow_mode
        
        # Initialize options strategy if enabled
        self.options_strategy = None
        if options_client and settings.options_enabled:
            self.options_strategy = OptionsStrategy(options_client)
            logger.info("Options strategy initialized and enabled")
        
        # Initialize AI opportunity finder first
        from scanner.ai_opportunity_finder import get_ai_opportunity_finder
        self.ai_finder = get_ai_opportunity_finder()
        
        # Initialize sentiment aggregator with dual-source validation
        from indicators.sentiment_aggregator import get_sentiment_aggregator
        self.sentiment_aggregator = get_sentiment_aggregator(alpaca_client, self.ai_finder)
        
        # Initialize opportunity scanner (Phase 2) with sentiment
        self.scanner = OpportunityScanner(market_data_manager, sentiment_analyzer=self.sentiment_aggregator)
        self.use_dynamic_watchlist = getattr(settings, 'use_dynamic_watchlist', False)
        self.scanner_interval_hours = getattr(settings, 'scanner_interval_hours', 1)
        logger.info(f"Opportunity scanner initialized (dynamic watchlist: {self.use_dynamic_watchlist})")
        
        # Initialize symbol cooldown manager (Sprint 6 - prevents overtrading)
        from trading.symbol_cooldown import SymbolCooldownManager
        self.cooldown_manager = SymbolCooldownManager(supabase_client)
        logger.info("✓ Symbol cooldown manager initialized")
        
        # Initialize momentum-based bracket adjustment system
        from momentum import MomentumConfig, BracketAdjustmentEngine
        self.momentum_config = MomentumConfig.default_conservative()
        self.momentum_config.enabled = True  # Auto-enable on startup
        self.momentum_engine = BracketAdjustmentEngine(
            alpaca_client=alpaca_client,
            config=self.momentum_config
        )
        logger.info("✅ Momentum bracket adjustment system initialized and ENABLED (conservative mode)")
        self.momentum_config.log_config()
        
        # Initialize Stop Loss Protection Manager (Critical - runs every 5 seconds)
        from trading.stop_loss_protection import get_protection_manager
        self.protection_manager = get_protection_manager(alpaca_client)
        logger.info("✅ Stop Loss Protection Manager initialized (5-second checks)")
        
        # Initialize Intelligent Profit Protection System (R-multiple based)
        # This provides: Dynamic trailing stops, systematic profit taking at 2R/3R/4R
        from trading.profit_protection import get_profit_protection_manager
        self.profit_protection = get_profit_protection_manager(alpaca_client)
        logger.info("✅ Intelligent Profit Protection initialized (R-multiple tracking, 2R/3R/4R profit taking)")
        
        self.is_running = False
        self.watchlist = settings.watchlist_symbols
        
        # Initialize Regime Manager (Sprint 2 - Regime Adaptive Strategy)
        from trading.regime_manager import RegimeManager
        self.regime_manager = RegimeManager()
        logger.info("✅ Regime Manager initialized")
        
        # Pass regime manager to strategy if it supports it
        if hasattr(self.strategy, 'set_regime_manager'):
            self.strategy.set_regime_manager(self.regime_manager)
            
        # Pass regime manager to position manager (Sprint 2)
        if hasattr(self.position_manager, 'set_regime_manager'):
            self.position_manager.set_regime_manager(self.regime_manager)
        
        # ==================== MOMENTUM WAVE RIDER SYSTEM ====================
        # Initialize momentum scanner as alternative to AI discovery
        self.use_momentum_scanner = getattr(settings, 'USE_MOMENTUM_SCANNER', False)
        self.momentum_scan_interval = getattr(settings, 'MOMENTUM_SCAN_INTERVAL', 300)  # 5 min default
        self.first_hour_scan_interval = getattr(settings, 'FIRST_HOUR_SCAN_INTERVAL', 120)  # 2 min in first hour
        
        self.momentum_scanner = None
        self.momentum_scorer = None
        self.confidence_sizer = None
        self.wave_entry_engine = None
        
        if MOMENTUM_SCANNER_AVAILABLE and self.use_momentum_scanner:
            try:
                self.momentum_scanner = MomentumScanner(alpaca_client, market_data_manager)
                self.momentum_scorer = MomentumScorer()
                self.confidence_sizer = ConfidenceBasedSizer()
                self.wave_entry_engine = WaveEntryEngine()
                logger.info("✅ Momentum Wave Rider system initialized")
                logger.info(f"   • Scan interval: {self.momentum_scan_interval}s (first hour: {self.first_hour_scan_interval}s)")
                logger.info("   • Confidence-based position sizing enabled")
                logger.info("   • Wave entry timing enabled")
            except Exception as e:
                logger.error(f"Failed to initialize momentum scanner: {e}")
                self.use_momentum_scanner = False
        elif self.use_momentum_scanner:
            logger.warning("⚠️ Momentum scanner requested but not available - using AI discovery")
            self.use_momentum_scanner = False
        self.daily_trade_count = 0
        self.symbol_trade_counts = {}  # {symbol: count}
        self.last_reset_date = None
        logger.info(f"📊 Trade limits: {settings.max_trades_per_day}/day, {settings.max_trades_per_symbol_per_day}/symbol/day")
        
        # EOD Force Close State
        self.eod_triggered = False
        self.last_eod_date = None
    
    async def start(self):
        """Start all trading loops."""
        if self.is_running:
            logger.warning("Trading engine already running")
            return
        
        self.is_running = True
        logger.info("🚀 Starting Trading Engine...")
        logger.info(f"Watchlist: {', '.join(self.watchlist)}")
        logger.info(f"Max Positions: {settings.max_positions}")
        
        # Log ML shadow mode status
        if self.ml_shadow_mode:
            logger.info(f"🤖 ML Shadow Mode: ACTIVE (weight: {self.ml_shadow_mode.ml_weight:.1%})")
            logger.info("   • Making predictions for all trade signals")
            logger.info("   • Logging predictions to database")
            logger.info("   • Tracking accuracy vs actual outcomes")
            logger.info("   • Zero impact on trading decisions (learning only)")
        else:
            logger.info("🤖 ML Shadow Mode: DISABLED")
        logger.info(f"Risk Per Trade: {settings.risk_per_trade_pct * 100}%")
        
        # Initial sync
        await self.sync_account()
        
        # CRITICAL: Verify and fix bracket orders immediately on startup
        logger.info("🔍 Verifying bracket orders for existing positions...")
        self.position_manager.verify_position_protection()
        logger.info("✅ Bracket order verification complete")
        
        # Start Intelligent Profit Protection System
        # Syncs existing positions and starts R-multiple tracking
        logger.info("🚀 Starting Intelligent Profit Protection...")
        self.profit_protection.sync_existing_positions()
        self.profit_protection.start()
        logger.info("✅ Profit protection active - R-multiple tracking, 2R/3R/4R profit taking enabled")
        
        # Sprint 7: Refresh daily cache for new filters
        # NOW ENABLED with Twelve Data API (free tier)
        logger.info("🔄 Initializing Sprint 7 daily cache...")
        try:
            from data.daily_cache import get_daily_cache
            daily_cache = get_daily_cache()
            daily_cache.refresh_cache(symbols=self.watchlist)
            logger.info("✅ Daily cache ready for Sprint 7 filters")
        except Exception as e:
            logger.warning(f"⚠️ Failed to refresh daily cache: {e}")
            logger.warning("Sprint 7 filters will operate without daily data")

        if self.streaming_enabled:
            await self._start_streaming()

        # CRITICAL: Run initial scan BEFORE any trading begins
        # If momentum scanner is enabled, use it instead of AI discovery
        if self.use_momentum_scanner and self.momentum_scanner:
            logger.info("🌊 Running initial MOMENTUM scan BEFORE trading starts...")
            try:
                await self._run_momentum_scan()
                logger.info(f"✅ Momentum watchlist ready: {len(self.watchlist)} symbols")
            except Exception as e:
                logger.warning(f"⚠️ Initial momentum scan failed: {e} - using static watchlist")
        elif self.use_dynamic_watchlist:
            logger.info("🔍 Running initial AI scan BEFORE trading starts...")
            try:
                await self._run_scanner_with_ai()
                logger.info(f"✅ AI watchlist ready: {len(self.watchlist)} symbols - {', '.join(self.watchlist[:5])}...")
            except Exception as e:
                logger.warning(f"⚠️ Initial AI scan failed: {e} - using static watchlist")

        # Start all loops concurrently
        loops = [
            self.market_data_loop(),
            self.strategy_loop(),
            self.position_monitor_loop(),
            self.metrics_loop(),
            self.regime_update_loop(),  # New regime update loop
        ]
        
        # Add scanner loop - momentum scanner takes priority over AI discovery
        if self.use_momentum_scanner and self.momentum_scanner:
            loops.append(self.momentum_scanner_loop())
            logger.info("🌊 Momentum Wave Rider scanner loop started (replaces AI discovery)")
        elif self.use_dynamic_watchlist:
            loops.append(self.scanner_loop())
            logger.info("🔍 Dynamic watchlist enabled - AI scanner loop started (30-min refresh)")
        
        await asyncio.gather(*loops, return_exceptions=True)
    
    async def stop(self):
        """Stop all trading loops."""
        logger.info("🛑 Stopping Trading Engine...")
        self.is_running = False
        
        # Stop profit protection monitoring
        if hasattr(self, 'profit_protection') and self.profit_protection:
            self.profit_protection.stop()
            logger.info("⏹️  Profit protection stopped")
        
        if self.streaming_enabled:
            await self._stop_streaming()
        await asyncio.sleep(2)  # Allow loops to finish
        logger.info("Trading Engine stopped")
    
    async def sync_account(self):
        """Sync account state from Alpaca."""
        try:
            logger.info("Syncing account state...")
            
            # Get account info
            account = self.alpaca.get_account()
            equity = float(account.equity)
            cash = float(account.cash)
            buying_power = float(account.buying_power)
            
            # Update metrics
            trading_state.update_metrics(
                equity=equity,
                cash=cash,
                buying_power=buying_power
            )
            
            # Sync positions
            self.position_manager.sync_positions()
            
            logger.info(f"Account synced: ${equity:.2f} equity, {len(trading_state.get_all_positions())} positions")
            
        except Exception as e:
            logger.error(f"Failed to sync account: {e}")
    
    async def market_data_loop(self):
        """
        Market data ingestion loop.
        Fetches latest bars and computes features every 60 seconds.
        """
        logger.info("📊 Market data loop started")
        
        while self.is_running:
            try:
                if not self.alpaca.is_market_open():
                    logger.debug("Market closed, skipping data update")
                    await asyncio.sleep(60)
                    continue
                
                # Update features for all watchlist symbols
                self.market_data.update_all_features(self.watchlist)
                
                # Update position prices
                self.position_manager.update_position_prices()
                
                await asyncio.sleep(60)  # Update every minute
                
            except Exception as e:
                logger.error(f"Error in market data loop: {e}")
                await asyncio.sleep(60)
    
    async def strategy_loop(self):
        """
        Strategy evaluation loop.
        Checks for signals and submits orders every 60 seconds.
        """
        logger.info("🎯 Strategy loop started")
        
        while self.is_running:
            try:
                if not trading_state.is_trading_allowed():
                    logger.debug("Trading disabled, skipping strategy evaluation")
                    await asyncio.sleep(60)
                    continue
                
                if not self.alpaca.is_market_open():
                    logger.debug("Market closed, skipping strategy evaluation")
                    await asyncio.sleep(60)
                    continue
                
                # Check circuit breaker
                if self.risk_manager.check_circuit_breaker():
                    logger.error("Circuit breaker triggered, halting strategy")
                    await asyncio.sleep(300)  # Wait 5 minutes
                    continue
                
                # Evaluate strategy for each symbol
                logger.debug(f"🔍 Evaluating {len(self.watchlist)} symbols: {', '.join(self.watchlist)}")
                
                for symbol in self.watchlist:
                    try:
                        features = self.market_data.get_latest_features(symbol)
                        if not features:
                            logger.warning(f"⚠️  No features available for {symbol}")
                            continue
                        
                        # Log feature values for debugging
                        logger.debug(f"📊 {symbol}: price=${features.get('price', 0):.2f}, EMA9=${features.get('ema_short', 0):.2f}, EMA21=${features.get('ema_long', 0):.2f}")
                        
                        # Check for signal
                        signal = self.strategy.evaluate(symbol, features)
                        
                        if signal:
                            logger.info(f"📈 Signal detected: {signal.upper()} {symbol}")
                            
                            # Long-only mode filter
                            if getattr(settings, 'long_only_mode', False) and signal.upper() == 'SELL':
                                logger.warning(f"⚠️  {symbol} SELL signal rejected: Long-only mode enabled")
                                continue
                            
                            # Check symbol cooldown FIRST (prevents overtrading after losses)
                            is_allowed, cooldown_reason = self.cooldown_manager.is_symbol_allowed(symbol)
                            if not is_allowed:
                                logger.warning(f"🚫 {symbol} blocked: {cooldown_reason}")
                                continue
                            
                            # Check trade frequency limits BEFORE executing
                            if not self._check_trade_limits(symbol):
                                logger.warning(f"⛔ Trade limit reached for {symbol}, skipping")
                                continue
                            
                            # Execute stock signal
                            success = self.strategy.execute_signal(symbol, signal, features)
                            
                            if success:
                                # Increment trade counters after successful order
                                self._increment_trade_count(symbol)
                                logger.info(f"✅ Stock order submitted for {symbol}")
                            else:
                                logger.warning(f"❌ Stock order rejected for {symbol}")
                            
                            # Check if we should also trade options
                            if self.options_strategy and settings.options_enabled:
                                try:
                                    account = self.alpaca.get_account()
                                    equity = float(account.equity)
                                    current_price = features.get('close', 0)
                                    
                                    # Count current options positions
                                    positions = self.position_manager.get_all_positions()
                                    options_positions = sum(
                                        1 for p in positions 
                                        if len(p.get('symbol', '')) > 10  # Options symbols are longer
                                    )
                                    
                                    # Generate options signal
                                    options_signal = self.options_strategy.generate_options_signal(
                                        symbol=symbol,
                                        signal=signal,
                                        current_price=current_price,
                                        account_equity=equity,
                                        current_options_positions=options_positions
                                    )
                                    
                                    if options_signal:
                                        logger.info(
                                            f"📊 Options signal: {options_signal['option_type'].upper()} "
                                            f"{options_signal['contracts']} contracts of {symbol}"
                                        )
                                        
                                        # Execute options order
                                        options_order = self.order_manager.submit_options_order(
                                            option_symbol=options_signal['option_symbol'],
                                            contracts=options_signal['contracts'],
                                            premium=options_signal['entry_premium'],
                                            option_type=options_signal['option_type'],
                                            underlying_symbol=symbol,
                                            reason=f"options_{options_signal['signal']}"
                                        )
                                        
                                        if options_order:
                                            logger.info(f"✅ Options order submitted: {options_order.order_id}")
                                        else:
                                            logger.warning(f"❌ Options order rejected for {symbol}")
                                        
                                except Exception as e:
                                    logger.error(f"Error generating options signal for {symbol}: {e}")
                        else:
                            logger.debug(f"➖ No signal for {symbol}")
                        
                    except Exception as e:
                        logger.error(f"Error evaluating {symbol}: {e}")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in strategy loop: {e}")
                await asyncio.sleep(60)
    
    async def position_monitor_loop(self):
        """
        Position monitoring loop.
        Checks stops/targets and closes positions every 10 seconds.
        Syncs positions every 60 seconds to catch bracket order closes.
        Checks momentum for bracket adjustment every 30 seconds.
        CRITICAL: Runs stop loss protection manager every 5 seconds.
        """
        logger.info("👁️  Position monitor loop started")
        
        sync_counter = 0
        momentum_counter = 0
        protection_counter = 0
        trailing_stop_counter = 0  # Aggressive trailing stops every 60 seconds
        
        # Parse EOD time
        try:
            eod_hour, eod_minute = map(int, settings.eod_exit_time.split(':'))
        except ValueError:
            logger.error(f"Invalid EOD exit time format: {settings.eod_exit_time}, defaulting to 15:58")
            eod_hour, eod_minute = 15, 58
        
        while self.is_running:
            try:
                # Check for EOD Force Close
                if settings.force_eod_exit:
                    clock = self.alpaca.get_clock()
                    now = clock.timestamp
                    
                    # Reset trigger if it's a new day
                    if self.last_eod_date != now.date():
                        self.eod_triggered = False
                        self.last_eod_date = now.date()
                    
                    # Check if it's time to close
                    # Convert to ET time components for comparison
                    # Actually, let's rely on the clock object if possible or just simple hour/minute check from timestamp
                    # Alpaca clock timestamp is UTC. We need to be careful.
                    # Let's use the simple approach: Get current time in ET
                    import pytz
                    ny_tz = pytz.timezone('America/New_York')
                    now_ny = datetime.now(ny_tz)
                    
                    if (now_ny.hour > eod_hour or (now_ny.hour == eod_hour and now_ny.minute >= eod_minute)) and \
                       now_ny.hour <= 16 and \
                       not self.eod_triggered:
                        
                        # Check if we should close ALL positions or just losers
                        eod_close_all = getattr(settings, 'eod_close_all', True)
                        
                        if eod_close_all:
                            # TRUE DAY TRADING: Close ALL positions before market close
                            # Prevents overnight gap risk (e.g., COIN -$1,098 overnight)
                            logger.warning(f"⏰ EOD FORCE CLOSE ALL at {now_ny.strftime('%H:%M:%S')} - closing ALL positions")
                            await self._close_all_positions_eod()
                            self.eod_triggered = True
                            logger.info("🌙 EOD complete - ALL positions closed, starting fresh tomorrow")
                        else:
                            # SELECTIVE: Only close losing positions (>X% loss)
                            loss_threshold = getattr(settings, 'eod_loss_threshold', 2.0)
                            logger.warning(f"⏰ EOD SELECTIVE CLOSE at {now_ny.strftime('%H:%M:%S')} - closing losers only")
                            await self._close_losing_positions_eod(loss_threshold=loss_threshold)
                            self.eod_triggered = True
                            logger.info("🌙 EOD complete - winners held overnight, losers closed")
                        
                if not self.alpaca.is_market_open():
                    await asyncio.sleep(30)
                    continue
                
                # CRITICAL: Run stop loss protection manager every 5 seconds (every other iteration)
                # This is the PRIMARY protection mechanism - runs independently of bracket orders
                protection_counter += 1
                if protection_counter >= 1:  # Every iteration (10 seconds, but fast enough)
                    try:
                        results = self.protection_manager.verify_all_positions()
                        # Log only if action was taken
                        created = sum(1 for s in results.values() if s == 'created')
                        if created > 0:
                            logger.info(f"🛡️  Protection manager created {created} stop losses")
                    except Exception as e:
                        logger.error(f"Protection manager error: {e}")
                    protection_counter = 0
                
                # Sync positions every 60 seconds (6 iterations) to catch bracket order closes
                sync_counter += 1
                if sync_counter >= 6:
                    self.position_manager.sync_positions()
                    sync_counter = 0
                    
                    # Check for HELD orders and fix them (every 60 seconds)
                    self.position_manager.check_and_fix_held_orders()
                    
                    # Verify all positions have stop loss protection (legacy check)
                    # self.position_manager.verify_position_protection()
                
                # Update position prices
                self.position_manager.update_position_prices()
                
                # Check momentum for bracket adjustment every 30 seconds (3 iterations)
                momentum_counter += 1
                if momentum_counter >= 3 and self.momentum_config.enabled:
                    await self._check_momentum_adjustments()
                    momentum_counter = 0
                
                # PROFESSIONAL TRAILING STOPS - every 60 seconds (6 iterations)
                # Trails stops at 2.5% below current price for profitable positions (2%+ profit)
                trailing_stop_counter += 1
                if trailing_stop_counter >= 6:
                    await self._update_aggressive_trailing_stops()
                    trailing_stop_counter = 0
                
                # Check stops and targets (only for positions without bracket orders)
                symbols_to_close = self.position_manager.check_stops_and_targets()
                
                for symbol, reason in symbols_to_close:
                    logger.info(f"🎯 Closing {symbol}: {reason}")
                    self.position_manager.close_position(symbol, reason)
                    
                    # Clean up momentum tracking when position closes
                    self.momentum_engine.remove_position_tracking(symbol)
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in position monitor loop: {e}")
                await asyncio.sleep(10)

    async def _start_streaming(self):
        if not self.stream_manager:
            logger.warning("Stream manager not configured; skipping streaming start")
            return

        try:
            self.stream_manager.register_quote_handler(self._handle_quote)
            self.stream_manager.register_trade_handler(self._handle_trade)
            self.stream_manager.register_bar_handler(self._handle_bar)
            await self.stream_manager.start(self.watchlist)
            self._streaming_active = True
            logger.info("🔌 Streaming manager connected for watchlist symbols")
        except Exception as exc:
            self._streaming_active = False
            self.streaming_enabled = False
            logger.error("Streaming start failed (%s); reverting to polling", exc)

    async def _stop_streaming(self):
        if self.stream_manager and self._streaming_active:
            await self.stream_manager.stop()
            self._streaming_active = False

    async def _handle_quote(self, quote):
        try:
            symbol = getattr(quote, "symbol", None)
            if not symbol:
                return

            bid = float(getattr(quote, "bid_price", 0) or 0)
            ask = float(getattr(quote, "ask_price", 0) or 0)
            midpoint = (bid + ask) / 2 if bid and ask else bid or ask
            if midpoint:
                self._update_position_price_from_stream(symbol, midpoint)

            payload = {
                "type": "quote",
                "symbol": symbol,
                "bid": bid,
                "ask": ask,
                "bid_size": float(getattr(quote, "bid_size", 0) or 0),
                "ask_size": float(getattr(quote, "ask_size", 0) or 0),
                "timestamp": getattr(quote, "timestamp", None),
            }
            await self._publish_stream_message(payload)
        except Exception as exc:
            logger.error("Quote handler error: %s", exc)

    async def _handle_trade(self, trade):
        try:
            symbol = getattr(trade, "symbol", None)
            if not symbol:
                return

            price = float(getattr(trade, "price", 0) or 0)
            if price:
                self._update_position_price_from_stream(symbol, price)

            payload = {
                "type": "trade",
                "symbol": symbol,
                "price": price,
                "size": float(getattr(trade, "size", 0) or 0),
                "timestamp": getattr(trade, "timestamp", None),
            }
            await self._publish_stream_message(payload)
        except Exception as exc:
            logger.error("Trade handler error: %s", exc)

    async def _handle_bar(self, bar):
        try:
            symbol = getattr(bar, "symbol", None)
            if not symbol:
                return

            payload = {
                "type": "bar",
                "symbol": symbol,
                "open": float(getattr(bar, "open", 0) or 0),
                "high": float(getattr(bar, "high", 0) or 0),
                "low": float(getattr(bar, "low", 0) or 0),
                "close": float(getattr(bar, "close", 0) or 0),
                "volume": float(getattr(bar, "volume", 0) or 0),
                "timestamp": getattr(bar, "timestamp", None),
            }
            if payload["close"]:
                self.market_data.apply_stream_price(symbol, payload["close"], payload["timestamp"])
                self.market_data.apply_stream_bar(symbol, payload, payload["timestamp"])
            await self._publish_stream_message(payload)
        except Exception as exc:
            logger.error("Bar handler error: %s", exc)

    async def _publish_stream_message(self, payload: Dict):
        if not self.streaming_enabled or not self.streaming_broadcaster:
            return
        await self.streaming_broadcaster.enqueue(payload)

    def _update_position_price_from_stream(self, symbol: str, price: float):
        if price <= 0:
            return

        position = trading_state.get_position(symbol)
        if not position:
            return

        qty = position.qty or 0
        if qty <= 0:
            return

        if position.side == "buy":
            unrealized_pl = (price - position.avg_entry_price) * qty
            market_value = price * qty
        else:
            unrealized_pl = (position.avg_entry_price - price) * qty
            market_value = -price * qty

        cost_basis = position.avg_entry_price * qty
        if cost_basis:
            unrealized_pct = (unrealized_pl / cost_basis) * 100
        else:
            unrealized_pct = position.unrealized_pl_pct

        position.current_price = price
        position.unrealized_pl = unrealized_pl
        position.unrealized_pl_pct = unrealized_pct
        position.market_value = market_value
        trading_state.update_position(position)
    
    async def metrics_loop(self):
        """
        Metrics calculation loop.
        Updates performance metrics every 5 minutes.
        """
        logger.info("📈 Metrics loop started")
        
        while self.is_running:
            try:
                # Calculate metrics
                metrics = trading_state.get_metrics()
                
                # Calculate win rate and profit factor
                total_trades = metrics.wins + metrics.losses
                if total_trades > 0:
                    win_rate = metrics.wins / total_trades
                    trading_state.update_metrics(win_rate=win_rate)
                
                # Store metrics snapshot
                self.supabase.insert_metrics({
                    'equity': metrics.equity,
                    'cash': metrics.cash,
                    'buying_power': metrics.buying_power,
                    'daily_pl': metrics.daily_pl,
                    'daily_pl_pct': metrics.daily_pl_pct,
                    'total_pl': metrics.total_pl,
                    'win_rate': metrics.win_rate,
                    'profit_factor': metrics.profit_factor,
                    'wins': metrics.wins,
                    'losses': metrics.losses,
                    'total_trades': metrics.total_trades,
                    'open_positions': metrics.open_positions,
                    'circuit_breaker_triggered': metrics.circuit_breaker_triggered
                })
                
                logger.debug(f"Metrics: Equity=${metrics.equity:.2f}, P/L=${metrics.daily_pl:.2f}, Win Rate={metrics.win_rate*100:.1f}%")

                if self.streaming_enabled and self.streaming_broadcaster:
                    await self.streaming_broadcaster.enqueue(
                        {
                            "type": "metrics",
                            "payload": {
                                "equity": metrics.equity,
                                "cash": metrics.cash,
                                "buying_power": metrics.buying_power,
                                "daily_pl": metrics.daily_pl,
                                "daily_pl_pct": metrics.daily_pl_pct,
                                "total_pl": metrics.total_pl,
                                "win_rate": metrics.win_rate,
                                "profit_factor": metrics.profit_factor,
                                "wins": metrics.wins,
                                "losses": metrics.losses,
                                "total_trades": metrics.total_trades,
                                "open_positions": metrics.open_positions,
                                "circuit_breaker_triggered": metrics.circuit_breaker_triggered,
                            },
                        }
                    )
                
                await asyncio.sleep(300)  # Update every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in metrics loop: {e}")
                await asyncio.sleep(300)

    async def regime_update_loop(self):
        """
        Regime update loop.
        Updates market regime every hour (or as configured in RegimeManager).
        """
        logger.info("🌍 Regime update loop started")
        
        # Initial update
        await self.regime_manager.update_regime()
        
        while self.is_running:
            try:
                # Update regime
                regime = await self.regime_manager.update_regime()
                
                # Log current regime
                params = self.regime_manager.get_params()
                logger.info(f"🌍 Current Regime: {regime.value.upper()} | Target: {params['profit_target_r']}R | Size: {params['position_size_mult']}x")
                
                # Wait for next update (15 minutes check, manager handles caching)
                await asyncio.sleep(900)
                
            except Exception as e:
                logger.error(f"Error in regime update loop: {e}")
                await asyncio.sleep(300)
    
    async def scanner_loop(self):
        """
        Market-aware opportunity scanner loop.
        - Scans every 15 minutes during market hours (9:30 AM - 4:00 PM ET)
        - Scans 15 minutes before market open (9:15 AM ET)
        - Pauses after market close until next trading day
        """
        logger.info("🔍 Market-aware scanner loop started")
        
        # Initial scan
        await self._run_scanner_with_ai()
        
        while self.is_running:
            try:
                # Check if market is open or about to open
                clock = self.alpaca.get_clock()
                is_open = clock.is_open
                
                if is_open:
                    # Market is open - scan every 30 minutes to avoid repetitive analysis
                    scan_interval = 30 * 60  # 30 minutes in seconds
                    logger.debug("📊 Market open - scanning every 30 minutes")
                else:
                    # Market closed - check when it opens next
                    next_open = clock.next_open
                    next_close = clock.next_close
                    now = clock.timestamp
                    
                    # Calculate time until 15 minutes before market open
                    time_until_premarket = (next_open - now).total_seconds() - (15 * 60)
                    
                    if time_until_premarket > 0:
                        # Wait until 15 min before market open
                        logger.info(f"💤 Market closed - next scan in {time_until_premarket/3600:.1f} hours (15 min before open)")
                        await asyncio.sleep(time_until_premarket)
                        continue
                    else:
                        # We're in the 15-min pre-market window or market is about to open
                        scan_interval = 10 * 60  # Check every 10 minutes until open
                        logger.info("🌅 Pre-market window - scanning every 10 minutes")
                
                # Wait for next scan
                await asyncio.sleep(scan_interval)
                
                # Run scan
                logger.info("🔍 Running scheduled opportunity scan...")
                await self._run_scanner_with_ai()
                
            except Exception as e:
                logger.error(f"Error in scanner loop: {e}")
                await asyncio.sleep(300)  # Wait 5 min on error
    
    async def momentum_scanner_loop(self):
        """
        Momentum Wave Rider scanner loop.
        - Scans every 5 minutes during market hours
        - Scans every 2 minutes in the first hour (9:30-10:30 AM ET)
        - Alerts on high-confidence opportunities (score 85+)
        
        **Requirements: 1.5, 7.1, 7.2, 7.3, 7.4**
        """
        logger.info("🌊 Momentum scanner loop started")
        
        import pytz
        ny_tz = pytz.timezone('America/New_York')
        
        while self.is_running:
            try:
                if not self.alpaca.is_market_open():
                    logger.debug("Market closed, momentum scanner sleeping")
                    await asyncio.sleep(60)
                    continue
                
                # Determine scan interval based on time of day
                now_ny = datetime.now(ny_tz)
                
                # First hour (9:30-10:30 AM) - scan more frequently
                if now_ny.hour == 9 and now_ny.minute >= 30:
                    scan_interval = self.first_hour_scan_interval
                elif now_ny.hour == 10 and now_ny.minute < 30:
                    scan_interval = self.first_hour_scan_interval
                else:
                    scan_interval = self.momentum_scan_interval
                
                # Run momentum scan
                await self._run_momentum_scan()
                
                await asyncio.sleep(scan_interval)
                
            except Exception as e:
                logger.error(f"Error in momentum scanner loop: {e}")
                await asyncio.sleep(60)
    
    async def _run_momentum_scan(self):
        """
        Run momentum scanner and process results.
        
        **Requirements: 1.1, 1.2, 1.3, 1.4**
        """
        if not self.momentum_scanner:
            return
        
        try:
            logger.info("🌊 Running momentum wave scan...")
            
            # Scan for momentum waves
            candidates = await self.momentum_scanner.scan_momentum_waves()
            
            if not candidates:
                logger.debug("No momentum candidates found")
                return
            
            # Score and filter candidates
            scored_candidates = []
            for candidate in candidates:
                features = {
                    'volume_ratio': candidate.get('volume_ratio', 1.0),
                    'adx': candidate.get('adx', 0),
                    'rsi': candidate.get('rsi', 50),
                    'ema_diff': candidate.get('ema_diff', 0),
                    'price': candidate.get('price', 0),
                    'resistance': candidate.get('resistance', 0),
                    'support': candidate.get('support', 0),
                    'vwap_distance': candidate.get('vwap_distance', 0),
                    'multi_tf_aligned': candidate.get('multi_tf_aligned', False)
                }
                
                score = self.momentum_scorer.calculate_score(features)
                candidate['momentum_score'] = score.total_score
                candidate['score_breakdown'] = score
                scored_candidates.append(candidate)
            
            # Sort by score
            scored_candidates.sort(key=lambda x: x['momentum_score'], reverse=True)
            
            # Log top candidates
            logger.info(f"🌊 Top Momentum Candidates ({len(scored_candidates)} found):")
            for i, c in enumerate(scored_candidates[:5], 1):
                alert = "🔥" if c['momentum_score'] >= 85 else "📈"
                logger.info(
                    f"  {alert} {i}. {c['symbol']}: Score {c['momentum_score']:.0f} | "
                    f"Vol: {c.get('volume_ratio', 0):.1f}x | "
                    f"ADX: {c.get('adx', 0):.0f} | "
                    f"RSI: {c.get('rsi', 0):.0f}"
                )
                
                # High-confidence alert (score 85+)
                if c['momentum_score'] >= 85:
                    logger.warning(
                        f"🔥 HIGH CONFIDENCE ALERT: {c['symbol']} "
                        f"Score {c['momentum_score']:.0f} - Consider immediate entry!"
                    )
            
            # Update watchlist with top momentum candidates
            if self.use_momentum_scanner:
                top_symbols = [c['symbol'] for c in scored_candidates[:settings.max_positions]]
                if top_symbols:
                    old_watchlist = self.watchlist.copy()
                    self.watchlist = top_symbols
                    
                    added = set(top_symbols) - set(old_watchlist)
                    removed = set(old_watchlist) - set(top_symbols)
                    
                    if added or removed:
                        logger.info(f"🌊 Momentum watchlist updated: {len(top_symbols)} symbols")
                        if added:
                            logger.info(f"  ➕ Added: {', '.join(sorted(added))}")
                        if removed:
                            logger.info(f"  ➖ Removed: {', '.join(sorted(removed))}")
            
        except Exception as e:
            logger.error(f"Error in momentum scan: {e}", exc_info=True)
    
    async def _run_scanner_async(self):
        """Run AI-powered opportunity scan and update watchlist."""
        try:
            logger.info("🔍 Running AI-powered opportunity scan...")
            
            # Scan universe with AI discovery
            opportunities = await self.scanner.scan_universe_async(
                symbols=None,  # Let AI discover opportunities
                min_score=60.0  # Minimum B- grade
            )
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error in async scanner: {e}")
            return []
    
    def _run_scanner(self):
        """Run opportunity scan and update watchlist (sync wrapper)."""
        try:
            logger.info("🔍 Running opportunity scan...")
            
            # Try async AI scan first
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Schedule async scan
                    asyncio.create_task(self._run_scanner_with_ai())
                    return
                else:
                    opportunities = loop.run_until_complete(self._run_scanner_async())
            except Exception as e:
                logger.warning(f"AI scan failed, using fallback: {e}")
                # Fallback to sync scan
                opportunities = self.scanner.scan_universe(
                    symbols=None,
                    min_score=60.0
                )
            
            self._process_scan_results(opportunities)
            
        except Exception as e:
            logger.error(f"Error in scanner: {e}")
    
    async def _run_scanner_with_ai(self):
        """Run scanner with AI and process results."""
        try:
            opportunities = await self._run_scanner_async()
            self._process_scan_results(opportunities)
        except Exception as e:
            logger.error(f"Error in AI scanner: {e}")
    
    def _process_scan_results(self, opportunities: List[Dict]):
        """Process scan results and update watchlist."""
        try:
            if not opportunities:
                logger.warning("No opportunities found in scan")
                return
            
            # Log top opportunities
            top_5 = opportunities[:5]
            logger.info(f"📊 Top 5 AI-Discovered Opportunities:")
            for i, opp in enumerate(top_5, 1):
                ai_tag = "🤖 " if opp.get('ai_discovered') else ""
                logger.info(
                    f"  {ai_tag}{i}. {opp['symbol']}: {opp['score']:.1f} ({opp['grade']}) - "
                    f"${opp['price']:.2f} | RSI: {opp['rsi']:.1f} | "
                    f"ADX: {opp['adx']:.1f} | Vol: {opp['volume_ratio']:.2f}x"
                )
            
            # Update watchlist if dynamic mode enabled
            if self.use_dynamic_watchlist:
                new_watchlist = self.scanner.get_watchlist_symbols(
                    n=settings.max_positions,  # Match max positions
                    min_score=60.0
                )
                
                if new_watchlist and new_watchlist != self.watchlist:
                    old_watchlist = self.watchlist.copy()
                    self.watchlist = new_watchlist
                    
                    # Update streaming if enabled
                    # Note: Streaming update would need to be async, skip for now
                    # if self.streaming_enabled and self.stream_manager:
                    #     await self.stream_manager.update_subscriptions(new_watchlist)
                    
                    avg_score = sum(o['score'] for o in opportunities[:len(new_watchlist)]) / len(new_watchlist)
                    logger.info(f"✓ Watchlist updated: {len(new_watchlist)} AI-discovered symbols (avg score: {avg_score:.1f})")
                    
                    # Log market cap breakdown of new watchlist
                    self._log_watchlist_breakdown(new_watchlist, opportunities[:len(new_watchlist)])
                    
                    # Log changes
                    added = set(new_watchlist) - set(old_watchlist)
                    removed = set(old_watchlist) - set(new_watchlist)
                    if added:
                        logger.info(f"  ➕ Added: {', '.join(sorted(added))}")
                    if removed:
                        logger.info(f"  ➖ Removed: {', '.join(sorted(removed))}")
            
            # Save opportunities to database
            self.scanner.save_opportunities_to_db(opportunities, self.supabase)
            
            # Get summary
            summary = self.scanner.get_opportunity_summary()
            logger.info(
                f"✓ Scan complete: {summary['total_opportunities']} opportunities | "
                f"Avg score: {summary['avg_score']} | "
                f"Top: {summary['top_symbol']} ({summary['top_score']:.1f})"
            )
            
        except Exception as e:
            logger.error(f"Error running scanner: {e}", exc_info=True)
    
    def _log_watchlist_breakdown(self, watchlist: List[str], opportunities: List[Dict]) -> None:
        """Log detailed breakdown of watchlist by market cap and scores."""
        
        # Market cap classifications
        large_cap = {
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'META', 'TSLA', 
            'BAC', 'XOM', 'ORCL', 'CRM', 'AMD', 'NFLX', 'ADBE', 'DIS', 'TMO',
            'SPY', 'QQQ', 'IWM', 'VTI', 'VOO', 'PFE', 'JNJ', 'WMT', 'HD'
        }
        
        mid_cap = {
            'PLTR', 'COIN', 'SOFI', 'RIVN', 'SNOW', 'DKNG', 'CRWD', 'ZS', 'RBLX',
            'MDB', 'TEAM', 'WDAY', 'VEEV', 'TTD', 'TRADE', 'OPEN', 'RKT', 'HOOD'
        }
        
        small_cap = {
            'MARA', 'RIOT', 'AMC', 'GME', 'ENPH', 'SEDG', 'RUN', 'FSLY',
            'BRTX', 'SOUN', 'IONQ', 'RGTI', 'QUBT', 'AIMD', 'SMCI'
        }
        
        # Classify watchlist symbols
        large_found = [s for s in watchlist if s in large_cap]
        mid_found = [s for s in watchlist if s in mid_cap]
        small_found = [s for s in watchlist if s in small_cap]
        unknown = [s for s in watchlist if s not in large_cap and s not in mid_cap and s not in small_cap]
        
        logger.info("📊 Watchlist Market Cap Breakdown:")
        logger.info(f"  🏢 Large-Cap ({len(large_found)}): {', '.join(large_found) if large_found else 'None'}")
        logger.info(f"  🏭 Mid-Cap ({len(mid_found)}): {', '.join(mid_found) if mid_found else 'None'}")
        logger.info(f"  🏪 Small-Cap ({len(small_found)}): {', '.join(small_found) if small_found else 'None'}")
        if unknown:
            logger.info(f"  ❓ Other ({len(unknown)}): {', '.join(unknown)}")
        
        # Show top opportunities with scores
        logger.info("🎯 Top Opportunities:")
        for i, opp in enumerate(opportunities[:5], 1):
            symbol = opp['symbol']
            score = opp['score']
            grade = self._score_to_grade(score)
            logger.info(f"  {i}. {symbol:6} | Score: {score:5.1f} ({grade})")
    
    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B+"
        elif score >= 60:
            return "B"
        elif score >= 50:
            return "C"
        else:
            return "D"
    
    def _check_trade_limits(self, symbol: str) -> bool:
        """
        Check if we can place another trade based on frequency limits.
        Returns True if trade is allowed, False if limit reached.
        """
        from datetime import date
        
        # Reset counters at start of new trading day
        today = date.today()
        if self.last_reset_date != today:
            self.daily_trade_count = 0
            self.symbol_trade_counts = {}
            self.last_reset_date = today
            logger.info(f"📅 New trading day: {today} - Trade counters reset")
        
        # Check daily trade limit
        if self.daily_trade_count >= settings.max_trades_per_day:
            logger.warning(
                f"⛔ Daily trade limit reached: {self.daily_trade_count}/{settings.max_trades_per_day}"
            )
            return False
        
        # Check per-symbol trade limit
        symbol_count = self.symbol_trade_counts.get(symbol, 0)
        if symbol_count >= settings.max_trades_per_symbol_per_day:
            logger.warning(
                f"⛔ Symbol trade limit reached for {symbol}: "
                f"{symbol_count}/{settings.max_trades_per_symbol_per_day}"
            )
            return False
        
        return True
    
    def _increment_trade_count(self, symbol: str):
        """Increment trade counters after successful order submission."""
        self.daily_trade_count += 1
        self.symbol_trade_counts[symbol] = self.symbol_trade_counts.get(symbol, 0) + 1
        
        logger.info(
            f"📊 Trade count updated: {self.daily_trade_count}/{settings.max_trades_per_day} daily, "
            f"{self.symbol_trade_counts[symbol]}/{settings.max_trades_per_symbol_per_day} for {symbol}"
        )
    
    async def _check_momentum_adjustments(self):
        """Check positions for momentum-based bracket adjustments"""
        try:
            positions = trading_state.get_all_positions()
            if not positions:
                return
            
            for position in positions:
                # Skip if already adjusted
                if self.momentum_engine.is_position_adjusted(position.symbol):
                    continue
                
                # Calculate current profit in R
                risk = abs(position.avg_entry_price - position.stop_loss)
                if risk == 0:
                    continue
                
                profit = position.current_price - position.avg_entry_price
                profit_r = profit / risk
                
                # Only evaluate if at +0.75R or better
                if profit_r < self.momentum_config.evaluation_profit_r:
                    continue
                
                logger.info(f"📊 Evaluating momentum for {position.symbol} at +{profit_r:.2f}R")
                
                # Get market data
                market_data = self._fetch_market_data_for_momentum(position.symbol)
                if not market_data:
                    continue
                
                # Evaluate and adjust if momentum is strong
                signal = self.momentum_engine.evaluate_and_adjust(
                    symbol=position.symbol,
                    entry_price=position.avg_entry_price,
                    current_price=position.current_price,
                    stop_loss=position.stop_loss,
                    take_profit=position.take_profit,
                    quantity=position.qty,
                    side='long' if position.side == 'buy' else 'short',
                    market_data=market_data
                )
                
                if signal:
                    if signal.extend:
                        logger.info(f"🎯 Extended target for {position.symbol}!")
                    else:
                        logger.debug(f"⏹️ Keeping standard target for {position.symbol}: {signal.reason}")
        
        except Exception as e:
            logger.error(f"Error checking momentum adjustments: {e}")
    
    async def _update_aggressive_trailing_stops(self):
        """
        PROFESSIONAL TRAILING STOPS - Lock in profits for BOTH long and short positions.
        
        Based on hedge fund research:
        - Day traders use 2-5% trailing stops (not 1.5%)
        - Only trail after meaningful profit (2%+)
        - Prevents "death by thousand cuts" from too-tight stops
        
        Logic:
        - For positions with 2%+ unrealized profit
        - LONG: Trail stop at 2.5% below current price (raise stop as price rises)
        - SHORT: Trail stop at 2.5% above current price (lower stop as price falls)
        - Never move stop in wrong direction
        - Ensures we lock in gains as price moves in our favor
        """
        try:
            from alpaca.trading.requests import GetOrdersRequest, ReplaceOrderRequest
            from alpaca.trading.enums import QueryOrderStatus
            
            # PROFESSIONAL SETTINGS (based on hedge fund research)
            TRAIL_PERCENT = 2.5  # Trail 2.5% from current price (was 1.5% - too tight!)
            MIN_PROFIT_TO_TRAIL = 2.0  # Only trail if 2%+ in profit (was 1%)
            
            # Get positions directly from Alpaca for accurate current prices
            positions = self.alpaca.get_positions()
            if not positions:
                return
            
            # Get open stop orders
            orders = self.alpaca.trading_client.get_orders(
                filter=GetOrdersRequest(status=QueryOrderStatus.OPEN)
            )
            
            # Build stop order map by symbol (for BUY orders = short covers)
            stop_orders = {}
            for order in orders:
                order_type = str(order.order_type).upper()
                if 'STOP' in order_type and 'LIMIT' not in order_type:
                    stop_orders[order.symbol] = order
            
            updated_count = 0
            
            for pos in positions:
                symbol = pos.symbol
                entry = float(pos.avg_entry_price)
                current = float(pos.current_price)
                qty = int(float(pos.qty))
                pnl_pct = float(pos.unrealized_plpc) * 100
                
                # Skip if not enough profit
                if pnl_pct < MIN_PROFIT_TO_TRAIL:
                    continue
                
                stop_order = stop_orders.get(symbol)
                if not stop_order:
                    continue
                
                current_stop = float(stop_order.stop_price)
                is_long = qty > 0
                abs_qty = abs(qty)
                
                if is_long:
                    # LONG position: trail stop BELOW current price, raise as price rises
                    new_stop = round(current * (1 - TRAIL_PERCENT / 100), 2)
                    
                    # Ensure we're locking in profit (stop above entry)
                    if new_stop <= entry:
                        new_stop = round(entry * 1.005, 2)  # At minimum, 0.5% above entry
                    
                    # Only update if new stop is HIGHER than current (tightening)
                    if new_stop <= current_stop:
                        continue
                    
                    locked_pct = ((new_stop - entry) / entry) * 100
                    direction = "raised"
                else:
                    # SHORT position: trail stop ABOVE current price, lower as price falls
                    new_stop = round(current * (1 + TRAIL_PERCENT / 100), 2)
                    
                    # Ensure we're locking in profit (stop below entry for shorts)
                    if new_stop >= entry:
                        new_stop = round(entry * 0.995, 2)  # At minimum, 0.5% below entry
                    
                    # Only update if new stop is LOWER than current (tightening for shorts)
                    if new_stop >= current_stop:
                        continue
                    
                    locked_pct = ((entry - new_stop) / entry) * 100
                    direction = "lowered"
                
                try:
                    replace_request = ReplaceOrderRequest(
                        qty=abs_qty,
                        stop_price=new_stop
                    )
                    self.alpaca.trading_client.replace_order_by_id(stop_order.id, replace_request)
                    updated_count += 1
                    pos_type = "LONG" if is_long else "SHORT"
                    logger.info(
                        f"📈 {symbol} ({pos_type}): Trailing stop {direction} ${current_stop:.2f} → ${new_stop:.2f} "
                        f"(locks {locked_pct:+.1f}% profit, P/L: {pnl_pct:+.1f}%)"
                    )
                except Exception as e:
                    logger.warning(f"Failed to update trailing stop for {symbol}: {e}")
            
            if updated_count > 0:
                logger.info(f"🎯 Updated {updated_count} aggressive trailing stops")
                
        except Exception as e:
            logger.error(f"Error updating aggressive trailing stops: {e}")
    
    def _fetch_market_data_for_momentum(self, symbol: str, bars: int = 60) -> Optional[Dict]:
        """Fetch market data for momentum evaluation - FIXED DataFrame handling"""
        try:
            from alpaca.data.timeframe import TimeFrame
            from datetime import datetime, timedelta, timezone
            import pandas as pd
            
            # Fetch bars from Alpaca
            barset = self.alpaca.get_bars(
                symbols=[symbol],
                timeframe=TimeFrame.Minute,
                start=datetime.now(timezone.utc) - timedelta(hours=5),
                limit=bars
            )
            
            # FIXED: Proper empty check
            if barset is None:
                logger.warning(f"No bars response for {symbol}")
                return None
            
            # FIXED: Handle multi-indexed DataFrame
            if isinstance(barset, pd.DataFrame):
                # Check if multi-indexed (symbol, timestamp)
                if isinstance(barset.index, pd.MultiIndex):
                    # Extract data for this symbol
                    if symbol in barset.index.get_level_values(0):
                        symbol_bars = barset.loc[symbol]
                        logger.debug(f"Extracted {len(symbol_bars)} bars from multi-index for {symbol}")
                    else:
                        logger.warning(f"Symbol {symbol} not found in bars response")
                        return None
                else:
                    # Single-indexed, use directly
                    symbol_bars = barset
                    logger.debug(f"Using {len(symbol_bars)} bars from single-index for {symbol}")
                
                # Check if we have enough data
                if len(symbol_bars) < 50:
                    logger.warning(f"Insufficient bars for {symbol}: {len(symbol_bars)}/50 required")
                    return None
                
                # Extract OHLCV data
                market_data = {
                    'high': symbol_bars['high'].tolist(),
                    'low': symbol_bars['low'].tolist(),
                    'close': symbol_bars['close'].tolist(),
                    'volume': symbol_bars['volume'].tolist(),
                    'timestamp': datetime.now()
                }
                
                logger.info(f"✅ Fetched {len(symbol_bars)} bars for {symbol} momentum analysis")
                return market_data
            else:
                logger.error(f"Unexpected bars response type: {type(barset)}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {e}", exc_info=True)
            return None
    
    def enable_momentum_system(self, aggressive: bool = False):
        """Enable the momentum-based bracket adjustment system"""
        from momentum import MomentumConfig
        
        if aggressive:
            self.momentum_config = MomentumConfig.default_aggressive()
        else:
            self.momentum_config = MomentumConfig.default_conservative()
        
        self.momentum_config.enabled = True
        self.momentum_engine.update_config(self.momentum_config)
        
        logger.info(f"✅ Momentum system ENABLED ({'aggressive' if aggressive else 'conservative'})")
        self.momentum_config.log_config()
    
    def disable_momentum_system(self):
        """Disable the momentum-based bracket adjustment system"""
        self.momentum_config.enabled = False
        self.momentum_engine.update_config(self.momentum_config)
        logger.info("⏹️ Momentum system DISABLED")
    
    def get_momentum_stats(self) -> Dict:
        """Get statistics about momentum adjustments"""
        adjusted = self.momentum_engine.get_adjusted_positions()
        
        return {
            'enabled': self.momentum_config.enabled,
            'total_adjusted': len(adjusted),
            'adjusted_symbols': list(adjusted.keys()),
            'config': self.momentum_config.to_dict()
        }
    
    async def _close_all_positions_eod(self):
        """
        TRUE DAY TRADING: Close ALL positions before market close.
        Prevents overnight gap risk which can destroy profits.
        
        Example: COIN dropped -$1,098 (-3.90%) overnight - no stop loss can protect against gaps!
        """
        try:
            positions = self.alpaca.get_positions()
            if not positions:
                logger.info("🌙 No positions to close for EOD")
                return
            
            total_pnl = 0.0
            closed_count = 0
            failed_count = 0
            
            logger.info(f"🔴 EOD FORCE CLOSE: Closing {len(positions)} positions...")
            
            for position in positions:
                try:
                    symbol = position.symbol
                    qty = float(position.qty)
                    avg_entry = float(position.avg_entry_price)
                    current_price = float(position.current_price)
                    unrealized_pnl = float(position.unrealized_pl)
                    pnl_pct = float(position.unrealized_plpc) * 100
                    
                    total_pnl += unrealized_pnl
                    
                    status = "🟢" if unrealized_pnl >= 0 else "🔴"
                    logger.info(f"{status} Closing {symbol}: {qty} shares @ ${current_price:.2f} | P/L: ${unrealized_pnl:+.2f} ({pnl_pct:+.1f}%)")
                    
                    # Cancel any existing orders first
                    try:
                        orders = self.alpaca.get_orders(symbol=symbol, status='open')
                        for order in orders:
                            self.alpaca.cancel_order(order.id)
                            logger.debug(f"   Cancelled order {order.id} for {symbol}")
                    except Exception as e:
                        logger.warning(f"   Could not cancel orders for {symbol}: {e}")
                    
                    # Close the position
                    try:
                        self.alpaca.close_position(symbol)
                        closed_count += 1
                        
                        # Log to database
                        if self.supabase:
                            self.supabase.insert_trade({
                                'symbol': symbol,
                                'side': 'sell' if qty > 0 else 'buy',
                                'qty': abs(qty),
                                'price': current_price,
                                'reason': 'eod_force_close',
                                'pnl': unrealized_pnl
                            })
                            
                        # Clean up momentum tracking
                        self.momentum_engine.remove_position_tracking(symbol)
                        
                    except Exception as e:
                        logger.error(f"   Failed to close {symbol}: {e}")
                        failed_count += 1
                        
                except Exception as e:
                    logger.error(f"Error closing {position.symbol}: {e}")
                    failed_count += 1
            
            # Summary
            status_emoji = "🟢" if total_pnl >= 0 else "🔴"
            logger.info(f"")
            logger.info(f"{'='*60}")
            logger.info(f"📊 EOD CLOSE SUMMARY")
            logger.info(f"{'='*60}")
            logger.info(f"   Positions Closed: {closed_count}")
            logger.info(f"   Failed to Close: {failed_count}")
            logger.info(f"   {status_emoji} Day's P/L: ${total_pnl:+.2f}")
            logger.info(f"{'='*60}")
            logger.info(f"🌙 Starting fresh tomorrow - no overnight risk!")
            
        except Exception as e:
            logger.error(f"Error in EOD force close all: {e}")
    
    async def _close_losing_positions_eod(self, loss_threshold: float = 2.0):
        """
        Selective EOD Close: Only close positions with losses > threshold.
        Keep winners overnight to capture gap-up potential.
        
        Args:
            loss_threshold: Close positions with loss greater than this % (default 2%)
        """
        try:
            positions = self.alpaca.get_positions()
            if not positions:
                logger.info("🌙 No positions to evaluate for EOD close")
                return
            
            closed_count = 0
            kept_count = 0
            
            for position in positions:
                try:
                    symbol = position.symbol
                    qty = float(position.qty)
                    avg_entry = float(position.avg_entry_price)
                    current_price = float(position.current_price)
                    unrealized_pnl = float(position.unrealized_pl)
                    
                    # Calculate P&L percentage
                    if qty > 0:  # Long position
                        pnl_pct = ((current_price - avg_entry) / avg_entry) * 100
                    else:  # Short position
                        pnl_pct = ((avg_entry - current_price) / avg_entry) * 100
                    
                    # Close if loss exceeds threshold
                    if pnl_pct < -loss_threshold:
                        logger.warning(f"🔴 EOD CLOSE: {symbol} at {pnl_pct:.1f}% loss (${unrealized_pnl:.2f})")
                        
                        # Cancel any existing orders first
                        try:
                            orders = self.alpaca.get_orders(symbol=symbol, status='open')
                            for order in orders:
                                self.alpaca.cancel_order(order.id)
                                logger.info(f"   Cancelled order {order.id} for {symbol}")
                        except Exception as e:
                            logger.warning(f"   Could not cancel orders for {symbol}: {e}")
                        
                        # Close the position
                        try:
                            self.alpaca.close_position(symbol)
                            logger.info(f"   ✅ Position closed: {symbol}")
                            closed_count += 1
                            
                            # Log to database
                            if self.supabase:
                                self.supabase.insert_trade({
                                    'symbol': symbol,
                                    'side': 'sell' if qty > 0 else 'buy',
                                    'qty': abs(qty),
                                    'price': current_price,
                                    'reason': 'eod_loss_cut',
                                    'pnl': unrealized_pnl
                                })
                        except Exception as e:
                            logger.error(f"   Failed to close {symbol}: {e}")
                    else:
                        status = "🟢 WINNER" if pnl_pct > 0 else "🟡 SMALL LOSS"
                        logger.info(f"{status} EOD KEEP: {symbol} at {pnl_pct:+.1f}% (${unrealized_pnl:+.2f}) - holding overnight")
                        kept_count += 1
                        
                except Exception as e:
                    logger.error(f"Error evaluating {position.symbol} for EOD close: {e}")
            
            # Summary
            logger.info(f"📊 EOD Summary: Closed {closed_count} losers (>{loss_threshold}% loss), kept {kept_count} positions overnight")
            
            if kept_count > 0:
                logger.info(f"💡 Overnight strategy: {kept_count} positions held to capture gap-up potential")
                    
        except Exception as e:
            logger.error(f"Error in EOD selective close: {e}")


# Global engine instance
trading_engine: Optional[TradingEngine] = None


def get_trading_engine() -> Optional[TradingEngine]:
    """Get the global trading engine instance."""
    return trading_engine


def set_trading_engine(engine: TradingEngine):
    """Set the global trading engine instance."""
    global trading_engine
    trading_engine = engine
