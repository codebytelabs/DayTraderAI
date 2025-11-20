"""
Example integration of momentum-based bracket adjustment system.
This shows how to integrate the momentum system into your trading engine.
"""

import logging
from typing import Dict, List
from datetime import datetime

from momentum import MomentumConfig, BracketAdjustmentEngine
from core.alpaca_client import AlpacaClient
from core.state import trading_state

logger = logging.getLogger(__name__)


class MomentumIntegrationExample:
    """
    Example showing how to integrate momentum system into trading engine.
    """
    
    def __init__(self, alpaca_client: AlpacaClient):
        self.alpaca = alpaca_client
        
        # Initialize momentum system (disabled by default)
        self.momentum_config = MomentumConfig.default_conservative()
        self.momentum_engine = BracketAdjustmentEngine(
            alpaca_client=alpaca_client,
            config=self.momentum_config
        )
        
        logger.info("✅ Momentum system initialized (disabled)")
    
    def enable_momentum_system(self, aggressive: bool = False):
        """Enable the momentum system"""
        if aggressive:
            self.momentum_config = MomentumConfig.default_aggressive()
        else:
            self.momentum_config = MomentumConfig.default_conservative()
        
        self.momentum_config.enabled = True
        self.momentum_engine.update_config(self.momentum_config)
        
        logger.info(f"✅ Momentum system ENABLED ({'aggressive' if aggressive else 'conservative'})")
    
    def check_positions_for_momentum(self):
        """
        Check all positions for momentum adjustment opportunities.
        Call this periodically (e.g., every 5 minutes) during market hours.
        """
        try:
            if not self.momentum_config.enabled:
                return
            
            positions = trading_state.get_all_positions()
            if not positions:
                return
            
            logger.info(f"🔍 Checking {len(positions)} positions for momentum adjustment")
            
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
                
                logger.info(f"📊 Evaluating {position.symbol} at +{profit_r:.2f}R")
                
                # Get market data
                market_data = self._fetch_market_data(position.symbol)
                if not market_data:
                    logger.warning(f"No market data for {position.symbol}")
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
                        logger.info(f"⏹️ Keeping standard target for {position.symbol}: {signal.reason}")
        
        except Exception as e:
            logger.error(f"Error checking positions for momentum: {e}")
    
    def _fetch_market_data(self, symbol: str, bars: int = 60) -> Dict:
        """
        Fetch market data for momentum evaluation.
        
        Args:
            symbol: Stock symbol
            bars: Number of bars to fetch (need 50+ for indicators)
            
        Returns:
            Dict with 'high', 'low', 'close', 'volume' lists
        """
        try:
            # Fetch bars from Alpaca
            barset = self.alpaca.get_bars(
                symbol=symbol,
                timeframe='5Min',  # 5-minute bars
                limit=bars
            )
            
            if not barset or len(barset) < 50:
                logger.warning(f"Insufficient bars for {symbol}: {len(barset) if barset else 0}")
                return None
            
            # Extract OHLCV data
            market_data = {
                'high': [float(bar.high) for bar in barset],
                'low': [float(bar.low) for bar in barset],
                'close': [float(bar.close) for bar in barset],
                'volume': [float(bar.volume) for bar in barset],
                'timestamp': datetime.now()
            }
            
            return market_data
            
        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {e}")
            return None
    
    def on_position_closed(self, symbol: str):
        """
        Call this when a position is closed to clean up tracking.
        
        Args:
            symbol: Symbol that was closed
        """
        self.momentum_engine.remove_position_tracking(symbol)
        logger.info(f"Removed {symbol} from momentum tracking")
    
    def get_momentum_stats(self) -> Dict:
        """Get statistics about momentum adjustments"""
        adjusted = self.momentum_engine.get_adjusted_positions()
        
        return {
            'enabled': self.momentum_config.enabled,
            'total_adjusted': len(adjusted),
            'adjusted_symbols': list(adjusted.keys()),
            'config': self.momentum_config.to_dict()
        }


# Example usage in your trading engine
def integrate_into_trading_engine():
    """
    Example of how to integrate into your main trading engine.
    """
    
    # In your TradingEngine.__init__():
    # self.momentum_integration = MomentumIntegrationExample(self.alpaca)
    
    # In your main trading loop (every 5 minutes):
    # self.momentum_integration.check_positions_for_momentum()
    
    # When closing a position:
    # self.momentum_integration.on_position_closed(symbol)
    
    # To enable the system:
    # self.momentum_integration.enable_momentum_system(aggressive=False)
    
    pass


# Shadow mode example - log decisions without executing
class ShadowModeMomentum(MomentumIntegrationExample):
    """
    Shadow mode version that logs decisions without executing adjustments.
    Use this for testing before going live.
    """
    
    def __init__(self, alpaca_client: AlpacaClient):
        super().__init__(alpaca_client)
        self.shadow_decisions = []
    
    def check_positions_for_momentum(self):
        """Override to run in shadow mode"""
        try:
            if not self.momentum_config.enabled:
                return
            
            positions = trading_state.get_all_positions()
            if not positions:
                return
            
            for position in positions:
                if self.momentum_engine.is_position_adjusted(position.symbol):
                    continue
                
                risk = abs(position.avg_entry_price - position.stop_loss)
                if risk == 0:
                    continue
                
                profit = position.current_price - position.avg_entry_price
                profit_r = profit / risk
                
                if profit_r < self.momentum_config.evaluation_profit_r:
                    continue
                
                market_data = self._fetch_market_data(position.symbol)
                if not market_data:
                    continue
                
                # Validate momentum WITHOUT adjusting brackets
                signal = self.momentum_engine.validator.validate_momentum(
                    symbol=position.symbol,
                    high=market_data['high'],
                    low=market_data['low'],
                    close=market_data['close'],
                    volume=market_data['volume'],
                    current_profit_r=profit_r
                )
                
                # Log the decision
                decision = {
                    'timestamp': datetime.now(),
                    'symbol': position.symbol,
                    'profit_r': profit_r,
                    'would_extend': signal.extend,
                    'signal': signal.to_dict()
                }
                
                self.shadow_decisions.append(decision)
                
                logger.info(f"🔍 SHADOW MODE - {position.symbol}: {'WOULD EXTEND' if signal.extend else 'WOULD KEEP'}")
                logger.info(f"   ADX: {signal.adx:.1f}, Vol: {signal.volume_ratio:.2f}x, Trend: {signal.trend_strength:.2f}")
        
        except Exception as e:
            logger.error(f"Error in shadow mode: {e}")
    
    def get_shadow_stats(self) -> Dict:
        """Get statistics from shadow mode"""
        if not self.shadow_decisions:
            return {'total': 0, 'would_extend': 0, 'extension_rate': 0.0}
        
        would_extend = sum(1 for d in self.shadow_decisions if d['would_extend'])
        
        return {
            'total': len(self.shadow_decisions),
            'would_extend': would_extend,
            'extension_rate': would_extend / len(self.shadow_decisions),
            'decisions': self.shadow_decisions
        }


if __name__ == '__main__':
    # Example test
    print("Momentum Integration Example")
    print("=" * 50)
    print()
    print("To integrate into your trading engine:")
    print("1. Add MomentumIntegrationExample to your TradingEngine")
    print("2. Call check_positions_for_momentum() every 5 minutes")
    print("3. Call on_position_closed() when positions close")
    print("4. Enable with enable_momentum_system()")
    print()
    print("For testing:")
    print("1. Use ShadowModeMomentum to log decisions without executing")
    print("2. Review shadow_decisions to validate behavior")
    print("3. Check extension rate is 20-40%")
    print("4. Then enable for real")
