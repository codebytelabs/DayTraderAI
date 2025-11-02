"""
Options Strategy Module

Implements options trading strategies for bullish and bearish signals.
Integrates with the main EMA strategy to provide options-based trades.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from alpaca.trading.enums import OrderSide

from options.options_client import OptionsClient
from config import settings

logger = logging.getLogger(__name__)


class OptionsStrategy:
    """
    Options trading strategy that complements the main EMA strategy.
    
    - Bullish signals: Buy call options
    - Bearish signals: Buy put options
    """
    
    def __init__(self, options_client: OptionsClient):
        self.options_client = options_client
        self.enabled = settings.options_enabled
        self.max_positions = settings.max_options_positions
        self.risk_per_trade_pct = settings.options_risk_per_trade_pct
        
        logger.info(
            "OptionsStrategy initialized: enabled=%s, max_positions=%d, risk_pct=%.2f%%",
            self.enabled,
            self.max_positions,
            self.risk_per_trade_pct * 100
        )
    
    def should_trade_options(self, symbol: str, signal: str, current_positions: int) -> bool:
        """
        Determine if we should trade options for this signal.
        
        Args:
            symbol: Stock symbol
            signal: 'bullish' or 'bearish'
            current_positions: Number of current options positions
            
        Returns:
            True if we should trade options
        """
        if not self.enabled:
            logger.debug("Options trading disabled")
            return False
        
        if current_positions >= self.max_positions:
            logger.debug(
                "Max options positions reached: %d/%d",
                current_positions,
                self.max_positions
            )
            return False
        
        if signal not in ['bullish', 'bearish']:
            logger.debug("Invalid signal for options: %s", signal)
            return False
        
        return True
    
    def find_optimal_option(
        self,
        symbol: str,
        signal: str,
        current_price: float,
        account_equity: float
    ) -> Optional[Dict[str, Any]]:
        """
        Find the optimal option contract for the given signal.
        
        Args:
            symbol: Stock symbol
            signal: 'bullish' or 'bearish'
            current_price: Current stock price
            account_equity: Account equity for position sizing
            
        Returns:
            Dict with option details or None if no suitable option found
        """
        try:
            # Determine option type
            option_type = 'call' if signal == 'bullish' else 'put'
            
            # Get expiration date (30-45 days out for optimal theta decay)
            expiration_date = datetime.now() + timedelta(days=35)
            expiration_str = expiration_date.strftime('%Y-%m-%d')
            
            # Fetch options chain
            chain = self.options_client.get_options_chain(
                symbol=symbol,
                expiration_date=expiration_str
            )
            
            if not chain:
                logger.warning("No options chain available for %s", symbol)
                return None
            
            # Filter by option type
            options = [opt for opt in chain if opt.get('type') == option_type]
            
            if not options:
                logger.warning("No %s options available for %s", option_type, symbol)
                return None
            
            # Find ATM or slightly OTM strike
            # For calls: strike slightly above current price (1-3%)
            # For puts: strike slightly below current price (1-3%)
            target_strike = current_price * 1.02 if option_type == 'call' else current_price * 0.98
            
            # Find closest strike to target
            best_option = min(
                options,
                key=lambda opt: abs(opt.get('strike', 0) - target_strike)
            )
            
            # Get quote for the option
            option_symbol = best_option.get('symbol')
            quote = self.options_client.get_option_quote(option_symbol)
            
            if not quote:
                logger.warning("No quote available for option %s", option_symbol)
                return None
            
            # Calculate position size based on risk
            max_risk = account_equity * self.risk_per_trade_pct
            premium = quote.get('ask', 0)
            
            if premium <= 0:
                logger.warning("Invalid premium for option %s: %s", option_symbol, premium)
                return None
            
            # Each option contract = 100 shares
            # Max contracts = max_risk / (premium * 100)
            max_contracts = int(max_risk / (premium * 100))
            
            if max_contracts < 1:
                logger.warning(
                    "Insufficient capital for options trade: max_risk=%s, premium=%s",
                    max_risk,
                    premium
                )
                return None
            
            # Limit to reasonable number of contracts
            contracts = min(max_contracts, 10)
            
            return {
                'symbol': option_symbol,
                'underlying': symbol,
                'type': option_type,
                'strike': best_option.get('strike'),
                'expiration': best_option.get('expiration'),
                'premium': premium,
                'contracts': contracts,
                'total_cost': premium * contracts * 100,
                'max_loss': premium * contracts * 100,  # Premium paid
                'breakeven': best_option.get('strike') + premium if option_type == 'call' else best_option.get('strike') - premium,
            }
            
        except Exception as e:
            logger.error("Error finding optimal option for %s: %s", symbol, e, exc_info=True)
            return None
    
    def calculate_option_exit_prices(
        self,
        option_details: Dict[str, Any],
        entry_premium: float
    ) -> Dict[str, float]:
        """
        Calculate take-profit and stop-loss prices for options.
        
        Args:
            option_details: Option contract details
            entry_premium: Entry premium price
            
        Returns:
            Dict with take_profit and stop_loss prices
        """
        # For options, we use percentage-based exits on the premium
        # Take profit: 50-100% gain on premium
        # Stop loss: 50% loss on premium (cut losses quickly)
        
        take_profit_pct = 0.75  # 75% gain
        stop_loss_pct = 0.50    # 50% loss
        
        take_profit = entry_premium * (1 + take_profit_pct)
        stop_loss = entry_premium * (1 - stop_loss_pct)
        
        return {
            'take_profit': round(take_profit, 2),
            'stop_loss': round(stop_loss, 2),
        }
    
    def generate_options_signal(
        self,
        symbol: str,
        signal: str,
        current_price: float,
        account_equity: float,
        current_options_positions: int
    ) -> Optional[Dict[str, Any]]:
        """
        Generate an options trading signal.
        
        Args:
            symbol: Stock symbol
            signal: 'bullish' or 'bearish'
            current_price: Current stock price
            account_equity: Account equity
            current_options_positions: Number of current options positions
            
        Returns:
            Dict with options trade signal or None
        """
        if not self.should_trade_options(symbol, signal, current_options_positions):
            return None
        
        option_details = self.find_optimal_option(
            symbol=symbol,
            signal=signal,
            current_price=current_price,
            account_equity=account_equity
        )
        
        if not option_details:
            return None
        
        exit_prices = self.calculate_option_exit_prices(
            option_details=option_details,
            entry_premium=option_details['premium']
        )
        
        return {
            'action': 'buy_option',
            'option_symbol': option_details['symbol'],
            'underlying_symbol': symbol,
            'option_type': option_details['type'],
            'strike': option_details['strike'],
            'expiration': option_details['expiration'],
            'contracts': option_details['contracts'],
            'entry_premium': option_details['premium'],
            'take_profit': exit_prices['take_profit'],
            'stop_loss': exit_prices['stop_loss'],
            'total_cost': option_details['total_cost'],
            'max_loss': option_details['max_loss'],
            'breakeven': option_details['breakeven'],
            'signal': signal,
            'timestamp': datetime.now().isoformat(),
        }
