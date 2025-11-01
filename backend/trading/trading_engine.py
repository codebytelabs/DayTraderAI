import asyncio
from datetime import datetime
from typing import Optional
from core.alpaca_client import AlpacaClient
from core.supabase_client import SupabaseClient
from core.state import trading_state
from trading.risk_manager import RiskManager
from trading.order_manager import OrderManager
from trading.position_manager import PositionManager
from trading.strategy import EMAStrategy
from data.market_data import MarketDataManager
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
        market_data_manager: MarketDataManager
    ):
        self.alpaca = alpaca_client
        self.supabase = supabase_client
        self.risk_manager = risk_manager
        self.order_manager = order_manager
        self.position_manager = position_manager
        self.strategy = strategy
        self.market_data = market_data_manager
        
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
                for symbol in self.watchlist:
                    try:
                        features = self.market_data.get_latest_features(symbol)
                        if not features:
                            continue
                        
                        # Check for signal
                        signal = self.strategy.evaluate(symbol, features)
                        
                        if signal:
                            logger.info(f"📈 Signal detected: {signal.upper()} {symbol}")
                            
                            # Execute signal
                            success = self.strategy.execute_signal(symbol, signal, features)
                            
                            if success:
                                logger.info(f"✅ Order submitted for {symbol}")
                            else:
                                logger.warning(f"❌ Order rejected for {symbol}")
                        
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
