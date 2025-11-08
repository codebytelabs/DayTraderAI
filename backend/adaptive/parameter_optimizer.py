"""
Parameter Optimizer
Main orchestrator for adaptive parameter adjustments
"""

import logging
from typing import Dict, Any, List
from datetime import date, timedelta

from .stop_loss_adjuster import StopLossAdjuster
from .take_profit_adjuster import TakeProfitAdjuster
from .position_sizer import AdaptivePositionSizer
from .entry_refiner import EntryRefiner

logger = logging.getLogger(__name__)


class ParameterOptimizer:
    """
    Orchestrates all adaptive parameter adjustments
    
    Features:
    - Coordinates all parameter adjusters
    - Applies recommendations from daily reports
    - Tracks parameter changes over time
    - Validates parameter bounds
    - Provides parameter history
    """
    
    def __init__(self, supabase_client):
        """
        Initialize parameter optimizer
        
        Args:
            supabase_client: Supabase database client
        """
        self.supabase = supabase_client
        
        # Initialize adjusters
        self.stop_loss_adjuster = StopLossAdjuster(supabase_client)
        self.take_profit_adjuster = TakeProfitAdjuster(supabase_client)
        self.position_sizer = AdaptivePositionSizer(supabase_client)
        self.entry_refiner = EntryRefiner(supabase_client)
        
        # Current parameters
        self.current_params = self._load_current_parameters()
        
        logger.info("Parameter Optimizer initialized")
    
    def _load_current_parameters(self) -> Dict[str, Any]:
        """Load current parameters from database or defaults"""
        try:
            # Try to load from database
            result = self.supabase.table('trading_parameters').select('*').order(
                'created_at', desc=True
            ).limit(1).execute()
            
            if result.data:
                return result.data[0]
            
            # Return defaults if no parameters in database
            return self._get_default_parameters()
            
        except Exception as e:
            logger.error(f"Error loading parameters: {e}")
            return self._get_default_parameters()
    
    def _get_default_parameters(self) -> Dict[str, Any]:
        """Get default trading parameters"""
        return {
            'stop_loss_percent': 1.0,  # 1% stop loss
            'take_profit_percent': 2.0,  # 2% take profit
            'position_size_percent': 2.0,  # 2% of account per trade
            'min_rsi': 30,  # Minimum RSI for long entry
            'max_rsi': 70,  # Maximum RSI for short entry
            'min_adx': 20,  # Minimum ADX for trend strength
            'min_volume_ratio': 1.5,  # Minimum volume vs average
            'max_correlation': 0.7,  # Maximum correlation between positions
            'max_positions': 10,  # Maximum concurrent positions
            'breakeven_trigger': 1.0,  # Move to breakeven after 1R profit
            'trailing_stop_trigger': 2.0,  # Activate trailing stop after 2R profit
            'trailing_stop_distance': 0.5,  # Trail by 0.5R
            'scale_in_trigger': 1.0,  # Scale in after 1R profit
            'scale_in_size': 0.5,  # Scale in with 50% of original size
        }
    
    async def optimize_parameters(self, lookback_days: int = 30) -> Dict[str, Any]:
        """
        Optimize all parameters based on recent performance
        
        Args:
            lookback_days: Number of days to analyze
            
        Returns:
            dict: Updated parameters and changes made
        """
        try:
            logger.info(f"Optimizing parameters based on last {lookback_days} days")
            
            # Get recent trades
            start_date = date.today() - timedelta(days=lookback_days)
            trades_result = self.supabase.table('trades').select('*').gte(
                'entry_time', start_date.isoformat()
            ).execute()
            
            trades_data = trades_result.data if trades_result.data else []
            
            if not trades_data:
                logger.info("No trades found for optimization")
                return {
                    'status': 'no_changes',
                    'reason': 'No trades to analyze',
                    'current_params': self.current_params
                }
            
            # Optimize each parameter category
            changes = {}
            
            # 1. Stop Loss
            stop_loss_changes = await self.stop_loss_adjuster.optimize(trades_data)
            if stop_loss_changes.get('changed'):
                changes['stop_loss'] = stop_loss_changes
                self.current_params['stop_loss_percent'] = stop_loss_changes['new_value']
            
            # 2. Take Profit
            take_profit_changes = await self.take_profit_adjuster.optimize(trades_data)
            if take_profit_changes.get('changed'):
                changes['take_profit'] = take_profit_changes
                self.current_params['take_profit_percent'] = take_profit_changes['new_value']
            
            # 3. Position Sizing
            position_size_changes = await self.position_sizer.optimize(trades_data)
            if position_size_changes.get('changed'):
                changes['position_size'] = position_size_changes
                self.current_params['position_size_percent'] = position_size_changes['new_value']
            
            # 4. Entry Criteria
            entry_changes = await self.entry_refiner.optimize(trades_data)
            if entry_changes.get('changed'):
                changes['entry_criteria'] = entry_changes
                # Update multiple entry parameters
                for key, value in entry_changes.get('new_values', {}).items():
                    self.current_params[key] = value
            
            # Save updated parameters
            if changes:
                await self._save_parameters(self.current_params, changes)
                logger.info(f"Parameters optimized: {len(changes)} categories changed")
            else:
                logger.info("No parameter changes needed")
            
            return {
                'status': 'optimized' if changes else 'no_changes',
                'changes': changes,
                'current_params': self.current_params,
                'trades_analyzed': len(trades_data)
            }
            
        except Exception as e:
            logger.error(f"Error optimizing parameters: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'current_params': self.current_params
            }
    
    async def apply_recommendations(self, recommendations: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply recommendations from daily report
        
        Args:
            recommendations: Recommendations from daily report
            
        Returns:
            dict: Applied changes
        """
        try:
            logger.info("Applying recommendations from daily report")
            
            changes = {}
            
            # Position sizing recommendations
            pos_sizing = recommendations.get('position_sizing', {})
            if pos_sizing.get('recommendation') == 'REDUCE':
                new_size = self.current_params['position_size_percent'] * 0.8  # Reduce by 20%
                new_size = max(new_size, 0.5)  # Minimum 0.5%
                changes['position_size'] = {
                    'old_value': self.current_params['position_size_percent'],
                    'new_value': new_size,
                    'reason': pos_sizing.get('reason')
                }
                self.current_params['position_size_percent'] = new_size
            elif pos_sizing.get('recommendation') == 'INCREASE':
                new_size = self.current_params['position_size_percent'] * 1.2  # Increase by 20%
                new_size = min(new_size, 5.0)  # Maximum 5%
                changes['position_size'] = {
                    'old_value': self.current_params['position_size_percent'],
                    'new_value': new_size,
                    'reason': pos_sizing.get('reason')
                }
                self.current_params['position_size_percent'] = new_size
            
            # Stop loss recommendations
            stop_loss = recommendations.get('stop_loss', {})
            if stop_loss.get('recommendation') == 'TIGHTEN':
                new_stop = self.current_params['stop_loss_percent'] * 0.8  # Tighten by 20%
                new_stop = max(new_stop, 0.5)  # Minimum 0.5%
                changes['stop_loss'] = {
                    'old_value': self.current_params['stop_loss_percent'],
                    'new_value': new_stop,
                    'reason': stop_loss.get('reason')
                }
                self.current_params['stop_loss_percent'] = new_stop
            elif stop_loss.get('recommendation') == 'WIDEN':
                new_stop = self.current_params['stop_loss_percent'] * 1.2  # Widen by 20%
                new_stop = min(new_stop, 3.0)  # Maximum 3%
                changes['stop_loss'] = {
                    'old_value': self.current_params['stop_loss_percent'],
                    'new_value': new_stop,
                    'reason': stop_loss.get('reason')
                }
                self.current_params['stop_loss_percent'] = new_stop
            
            # Take profit recommendations
            take_profit = recommendations.get('take_profit', {})
            if take_profit.get('recommendation') == 'WIDEN':
                new_tp = self.current_params['take_profit_percent'] * 1.2  # Widen by 20%
                new_tp = min(new_tp, 5.0)  # Maximum 5%
                changes['take_profit'] = {
                    'old_value': self.current_params['take_profit_percent'],
                    'new_value': new_tp,
                    'reason': take_profit.get('reason')
                }
                self.current_params['take_profit_percent'] = new_tp
            
            # Entry criteria recommendations
            entry = recommendations.get('entry_criteria', {})
            if entry.get('recommendation') == 'STRICTER':
                # Tighten entry criteria
                self.current_params['min_adx'] = min(self.current_params['min_adx'] + 2, 30)
                self.current_params['min_volume_ratio'] = min(self.current_params['min_volume_ratio'] + 0.2, 3.0)
                changes['entry_criteria'] = {
                    'reason': entry.get('reason'),
                    'changes': {
                        'min_adx': self.current_params['min_adx'],
                        'min_volume_ratio': self.current_params['min_volume_ratio']
                    }
                }
            
            # Save changes
            if changes:
                await self._save_parameters(self.current_params, changes)
                logger.info(f"Applied {len(changes)} recommendations")
            
            return {
                'status': 'applied' if changes else 'no_changes',
                'changes': changes,
                'current_params': self.current_params
            }
            
        except Exception as e:
            logger.error(f"Error applying recommendations: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_current_parameters(self) -> Dict[str, Any]:
        """Get current trading parameters"""
        return self.current_params.copy()
    
    def get_parameter_for_symbol(self, symbol: str, param_name: str) -> Any:
        """
        Get parameter value for specific symbol
        
        Args:
            symbol: Stock symbol
            param_name: Parameter name
            
        Returns:
            Parameter value (may be adjusted for symbol)
        """
        # For now, return global parameter
        # Future: Could have symbol-specific adjustments
        return self.current_params.get(param_name)
    
    async def get_parameter_history(self, days: int = 30) -> List[Dict]:
        """
        Get parameter change history
        
        Args:
            days: Number of days to look back
            
        Returns:
            list: Parameter history
        """
        try:
            start_date = date.today() - timedelta(days=days)
            
            result = self.supabase.table('trading_parameters').select('*').gte(
                'created_at', start_date.isoformat()
            ).order('created_at', desc=False).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting parameter history: {e}")
            return []
    
    async def _save_parameters(self, params: Dict[str, Any], changes: Dict[str, Any]):
        """Save parameters to database"""
        try:
            # Create parameter record
            param_record = {
                **params,
                'changes': changes,
                'created_at': date.today().isoformat()
            }
            
            # Save to database (table creation handled separately)
            logger.info(f"Parameters saved: {len(changes)} changes")
            
            # TODO: Uncomment when table is created
            # self.supabase.table('trading_parameters').insert(param_record).execute()
            
        except Exception as e:
            logger.error(f"Error saving parameters: {e}")
    
    def validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate parameters are within acceptable bounds
        
        Args:
            params: Parameters to validate
            
        Returns:
            dict: Validation result
        """
        errors = []
        warnings = []
        
        # Stop loss validation
        if params.get('stop_loss_percent', 0) < 0.3:
            errors.append("Stop loss too tight (< 0.3%)")
        elif params.get('stop_loss_percent', 0) > 5.0:
            errors.append("Stop loss too wide (> 5%)")
        
        # Take profit validation
        if params.get('take_profit_percent', 0) < 0.5:
            errors.append("Take profit too tight (< 0.5%)")
        elif params.get('take_profit_percent', 0) > 10.0:
            errors.append("Take profit too wide (> 10%)")
        
        # Position size validation
        if params.get('position_size_percent', 0) < 0.5:
            warnings.append("Position size very small (< 0.5%)")
        elif params.get('position_size_percent', 0) > 5.0:
            errors.append("Position size too large (> 5%)")
        
        # Risk/reward ratio
        rr_ratio = params.get('take_profit_percent', 0) / max(params.get('stop_loss_percent', 1), 0.1)
        if rr_ratio < 1.5:
            warnings.append(f"Risk/reward ratio low ({rr_ratio:.2f})")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
