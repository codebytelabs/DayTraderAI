"""
Options trading client for fetching options chains, pricing, and execution.
Supports calls, puts, and various spread strategies.
"""

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOptionContractsRequest, MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, AssetClass
from alpaca.data.historical import OptionHistoricalDataClient
from alpaca.data.requests import OptionBarsRequest, OptionLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


class OptionsClient:
    """Client for options trading and data."""
    
    def __init__(self):
        self.trading_client = TradingClient(
            api_key=settings.alpaca_api_key,
            secret_key=settings.alpaca_secret_key,
            paper=True
        )
        self.data_client = OptionHistoricalDataClient(
            api_key=settings.alpaca_api_key,
            secret_key=settings.alpaca_secret_key
        )
        logger.info("Options client initialized")
    
    def get_options_chain(
        self,
        underlying_symbol: str,
        expiration_date: Optional[datetime] = None,
        strike_price_gte: Optional[float] = None,
        strike_price_lte: Optional[float] = None
    ) -> List[Dict]:
        """
        Fetch options chain for an underlying symbol.
        
        Args:
            underlying_symbol: Stock symbol (e.g., 'AAPL')
            expiration_date: Filter by expiration date
            strike_price_gte: Minimum strike price
            strike_price_lte: Maximum strike price
            
        Returns:
            List of option contracts
        """
        try:
            request = GetOptionContractsRequest(
                underlying_symbols=[underlying_symbol],
                expiration_date=expiration_date,
                strike_price_gte=strike_price_gte,
                strike_price_lte=strike_price_lte
            )
            
            contracts = self.trading_client.get_option_contracts(request)
            
            logger.info(f"Fetched {len(contracts)} option contracts for {underlying_symbol}")
            
            return [
                {
                    "symbol": c.symbol,
                    "underlying_symbol": c.underlying_symbol,
                    "strike_price": float(c.strike_price),
                    "expiration_date": c.expiration_date,
                    "type": c.type,  # 'call' or 'put'
                    "style": c.style,  # 'american' or 'european'
                }
                for c in contracts
            ]
            
        except Exception as e:
            logger.error(f"Failed to fetch options chain: {e}")
            return []
    
    def get_option_quote(self, option_symbol: str) -> Optional[Dict]:
        """
        Get latest quote for an option contract.
        
        Args:
            option_symbol: Option symbol (e.g., 'AAPL250117C00150000')
            
        Returns:
            Quote data with bid, ask, last price
        """
        try:
            request = OptionLatestQuoteRequest(symbol_or_symbols=[option_symbol])
            quotes = self.data_client.get_option_latest_quote(request)
            
            if option_symbol in quotes:
                quote = quotes[option_symbol]
                return {
                    "symbol": option_symbol,
                    "bid": float(quote.bid_price),
                    "ask": float(quote.ask_price),
                    "bid_size": quote.bid_size,
                    "ask_size": quote.ask_size,
                    "timestamp": quote.timestamp
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get option quote: {e}")
            return None
    
    def buy_call(
        self,
        option_symbol: str,
        qty: int,
        limit_price: Optional[float] = None
    ):
        """
        Buy call option (bullish strategy).
        
        Args:
            option_symbol: Option symbol
            qty: Number of contracts
            limit_price: Optional limit price (market order if None)
            
        Returns:
            Order object
        """
        try:
            order = MarketOrderRequest(
                symbol=option_symbol,
                qty=qty,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )
            
            result = self.trading_client.submit_order(order)
            logger.info(f"Bought {qty} call contracts: {option_symbol}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to buy call: {e}")
            raise
    
    def buy_put(
        self,
        option_symbol: str,
        qty: int,
        limit_price: Optional[float] = None
    ):
        """
        Buy put option (bearish strategy).
        
        Args:
            option_symbol: Option symbol
            qty: Number of contracts
            limit_price: Optional limit price (market order if None)
            
        Returns:
            Order object
        """
        try:
            order = MarketOrderRequest(
                symbol=option_symbol,
                qty=qty,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )
            
            result = self.trading_client.submit_order(order)
            logger.info(f"Bought {qty} put contracts: {option_symbol}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to buy put: {e}")
            raise
    
    def find_atm_options(
        self,
        underlying_symbol: str,
        current_price: float,
        expiration_days: int = 30
    ) -> Dict[str, Optional[Dict]]:
        """
        Find at-the-money (ATM) call and put options.
        
        Args:
            underlying_symbol: Stock symbol
            current_price: Current stock price
            expiration_days: Days until expiration (default 30)
            
        Returns:
            Dict with 'call' and 'put' ATM options
        """
        try:
            # Calculate target expiration date
            target_date = datetime.now() + timedelta(days=expiration_days)
            
            # Fetch options chain
            chain = self.get_options_chain(
                underlying_symbol=underlying_symbol,
                strike_price_gte=current_price * 0.95,
                strike_price_lte=current_price * 1.05
            )
            
            # Find ATM options
            atm_call = None
            atm_put = None
            min_call_diff = float('inf')
            min_put_diff = float('inf')
            
            for option in chain:
                strike_diff = abs(option['strike_price'] - current_price)
                
                if option['type'] == 'call' and strike_diff < min_call_diff:
                    min_call_diff = strike_diff
                    atm_call = option
                
                elif option['type'] == 'put' and strike_diff < min_put_diff:
                    min_put_diff = strike_diff
                    atm_put = option
            
            return {
                "call": atm_call,
                "put": atm_put
            }
            
        except Exception as e:
            logger.error(f"Failed to find ATM options: {e}")
            return {"call": None, "put": None}
    
    def get_options_positions(self) -> List[Dict]:
        """Get all open options positions."""
        try:
            positions = self.trading_client.get_all_positions()
            
            options_positions = [
                {
                    "symbol": p.symbol,
                    "qty": float(p.qty),
                    "avg_entry_price": float(p.avg_entry_price),
                    "current_price": float(p.current_price),
                    "market_value": float(p.market_value),
                    "unrealized_pl": float(p.unrealized_pl),
                    "unrealized_pl_pct": float(p.unrealized_plpc) * 100,
                }
                for p in positions
                if p.asset_class == AssetClass.US_OPTION
            ]
            
            return options_positions
            
        except Exception as e:
            logger.error(f"Failed to get options positions: {e}")
            return []
