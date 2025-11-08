"""
Sprint 1 Integration Script
Integrates ML system and position management into the trading system
"""

import asyncio
import logging
from typing import Optional

from core.alpaca_client import AlpacaClient
from core.supabase_client import SupabaseClient
from data.market_data import MarketDataManager
from ml.ml_system import MLSystem
from trading.exit_monitor import ExitMonitor
from trading.breakeven_manager import BreakevenStopManager

logger = logging.getLogger(__name__)


class Sprint1Integration:
    """
    Integrates Sprint 1 features:
    - ML System (feature collection, training, prediction)
    - Exit Monitor (early exits based on volume, time, momentum)
    - Breakeven Stop Manager (profit protection)
    """
    
    def __init__(
        self,
        alpaca_client: AlpacaClient,
        supabase_client: SupabaseClient,
        market_data_manager: MarketDataManager
    ):
        """
        Initialize Sprint 1 integration
        
        Args:
            alpaca_client: Alpaca API client
            supabase_client: Supabase database client
            market_data_manager: Market data manager
        """
        self.alpaca = alpaca_client
        self.supabase = supabase_client
        self.market_data = market_data_manager
        
        # Initialize ML system
        self.ml_system = MLSystem(supabase_client)
        
        # Initialize position management
        self.exit_monitor = ExitMonitor(
            alpaca_client,
            supabase_client,
            market_data_manager
        )
        
        self.breakeven_manager = BreakevenStopManager(
            alpaca_client,
            supabase_client
        )
        
        self.monitoring_tasks = []
        logger.info("Sprint 1 Integration initialized")
    
    async def initialize(self):
        """Initialize all Sprint 1 components"""
        try:
            # Initialize ML system (load model if available)
            await self.ml_system.initialize()
            logger.info("✅ ML System initialized")
            
            # Start position monitoring
            await self.start_monitoring()
            logger.info("✅ Position monitoring started")
            
            logger.info("🚀 Sprint 1 features active!")
            
        except Exception as e:
            logger.error(f"Error initializing Sprint 1: {e}")
    
    async def start_monitoring(self):
        """Start background monitoring tasks"""
        # Start exit monitor
        exit_task = asyncio.create_task(self.exit_monitor.start_monitoring())
        self.monitoring_tasks.append(exit_task)
        
        # Start breakeven manager
        breakeven_task = asyncio.create_task(self.breakeven_manager.start_monitoring())
        self.monitoring_tasks.append(breakeven_task)
        
        logger.info("Position monitoring tasks started")
    
    async def stop_monitoring(self):
        """Stop background monitoring tasks"""
        self.exit_monitor.stop_monitoring()
        self.breakeven_manager.stop_monitoring()
        
        # Cancel tasks
        for task in self.monitoring_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        
        logger.info("Position monitoring stopped")
    
    async def on_trade_signal(self, signal_data: dict) -> dict:
        """
        Called when a trade signal is generated
        Collects features and optionally makes ML prediction
        
        Args:
            signal_data: Trade signal data
            
        Returns:
            dict: Enhanced signal data with ML prediction (if available)
        """
        try:
            # Collect features for ML
            await self.ml_system.collect_trade_data(signal_data)
            
            # Make prediction if model is ready
            if self.ml_system.is_ready():
                features = signal_data.get('features', {})
                prediction = await self.ml_system.predict(features)
                
                if prediction:
                    signal_data['ml_prediction'] = prediction
                    logger.info(f"ML Prediction: {prediction['prediction']} "
                              f"({prediction['probability']:.2%})")
            
            return signal_data
            
        except Exception as e:
            logger.error(f"Error in on_trade_signal: {e}")
            return signal_data
    
    async def on_trade_complete(self, trade_id: int, outcome: str, pnl_percent: float):
        """
        Called when a trade completes
        Updates ML system with outcome
        
        Args:
            trade_id: Trade ID
            outcome: 'WIN', 'LOSS', or 'BREAKEVEN'
            pnl_percent: P/L percentage
        """
        try:
            await self.ml_system.update_trade_outcome(trade_id, outcome, pnl_percent)
            logger.info(f"Updated trade {trade_id} outcome: {outcome}")
        except Exception as e:
            logger.error(f"Error in on_trade_complete: {e}")
    
    async def get_ml_metrics(self) -> dict:
        """Get current ML system metrics"""
        try:
            return await self.ml_system.get_performance_metrics()
        except Exception as e:
            logger.error(f"Error getting ML metrics: {e}")
            return {}
    
    async def train_model(self, min_samples: int = 100) -> Optional[dict]:
        """
        Train ML model
        
        Args:
            min_samples: Minimum samples required
            
        Returns:
            dict: Training results
        """
        try:
            logger.info("Starting model training...")
            results = await self.ml_system.train_model(min_samples)
            
            if results:
                logger.info(f"✅ Model trained: {results['accuracy']:.2%} accuracy")
            else:
                logger.warning("❌ Model training failed")
            
            return results
        except Exception as e:
            logger.error(f"Error training model: {e}")
            return None


# Global instance
sprint1_integration: Optional[Sprint1Integration] = None


def get_sprint1_integration() -> Optional[Sprint1Integration]:
    """Get Sprint 1 integration instance"""
    return sprint1_integration


def set_sprint1_integration(integration: Sprint1Integration):
    """Set Sprint 1 integration instance"""
    global sprint1_integration
    sprint1_integration = integration
    logger.info("Sprint 1 integration set")
