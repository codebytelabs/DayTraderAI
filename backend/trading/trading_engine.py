import asyncio
from datetime import datetime
from typing import Callable, Dict, Optional
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
from config import settings
from utils.logger import setup_logger

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
        
        # Initialize options strategy if enabled
        self.options_strategy = None
        if options_client and settings.options_enabled:
            self.options_strategy = OptionsStrategy(options_client)
            logger.info("Options strategy initialized and enabled")
        
        self.is_running = False
        self.watchlist = settings.watchlist_symbols
    
    async def start(self):
        """Start all trading loops."""
        if self.is_running:
            logger.warning("Trading engine already running")
            return
        
        self.is_running = True
        logger.info("🚀 Starting Trading Engine...")
        logger.info(f"Watchlist: {', '.join(self.watchlist)}")
        logger.info(f"Max Positions: {settings.max_positions}")
        logger.info(f"Risk Per Trade: {settings.risk_per_trade_pct * 100}%")
        
        # Initial sync
        await self.sync_account()

        if self.streaming_enabled:
            await self._start_streaming()

        # Start all loops concurrently
        await asyncio.gather(
            self.market_data_loop(),
            self.strategy_loop(),
            self.position_monitor_loop(),
            self.metrics_loop(),
            return_exceptions=True
        )
    
    async def stop(self):
        """Stop all trading loops."""
        logger.info("🛑 Stopping Trading Engine...")
        self.is_running = False
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
                logger.info(f"🔍 Evaluating {len(self.watchlist)} symbols: {', '.join(self.watchlist)}")
                
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
                            
                            # Execute stock signal
                            success = self.strategy.execute_signal(symbol, signal, features)
                            
                            if success:
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
        """
        logger.info("👁️  Position monitor loop started")
        
        while self.is_running:
            try:
                if not self.alpaca.is_market_open():
                    await asyncio.sleep(30)
                    continue
                
                # Update position prices
                self.position_manager.update_position_prices()
                
                # Check stops and targets
                symbols_to_close = self.position_manager.check_stops_and_targets()
                
                for symbol, reason in symbols_to_close:
                    logger.info(f"🎯 Closing {symbol}: {reason}")
                    self.position_manager.close_position(symbol, reason)
                
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


# Global engine instance
trading_engine: Optional[TradingEngine] = None


def get_trading_engine() -> Optional[TradingEngine]:
    """Get the global trading engine instance."""
    return trading_engine


def set_trading_engine(engine: TradingEngine):
    """Set the global trading engine instance."""
    global trading_engine
    trading_engine = engine
