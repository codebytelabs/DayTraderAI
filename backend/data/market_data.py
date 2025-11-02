import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from alpaca.data.timeframe import TimeFrame
from core.alpaca_client import AlpacaClient
from core.supabase_client import SupabaseClient
from core.state import trading_state
from data.features import FeatureEngine
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


class MarketDataManager:
    """
    Manages market data ingestion and feature computation.
    """
    
    def __init__(
        self,
        alpaca_client: AlpacaClient,
        supabase_client: SupabaseClient
    ):
        self.alpaca = alpaca_client
        self.supabase = supabase_client
        self.feature_engine = FeatureEngine()
    
    def fetch_historical_bars(
        self,
        symbols: List[str],
        days: int = 30
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical bars for symbols.
        Used for initial feature computation.
        """
        try:
            start = datetime.now() - timedelta(days=days)
            end = datetime.now()
            
            bars = self.alpaca.get_bars(
                symbols=symbols,
                timeframe=TimeFrame.Minute,
                start=start,
                end=end
            )
            
            if bars is None or bars.empty:
                logger.warning("No historical bars fetched")
                return {}
            
            # Group by symbol
            result = {}
            for symbol in symbols:
                try:
                    symbol_bars = bars.loc[symbol] if symbol in bars.index.get_level_values(0) else pd.DataFrame()
                    if not symbol_bars.empty:
                        result[symbol] = symbol_bars
                        logger.info(f"Fetched {len(symbol_bars)} bars for {symbol}")
                except Exception as e:
                    logger.error(f"Error processing bars for {symbol}: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to fetch historical bars: {e}")
            return {}
    
    def fetch_latest_bars(self, symbols: List[str]) -> Dict:
        """
        Fetch latest bar for each symbol.
        Used for real-time updates.
        """
        try:
            latest_bars = self.alpaca.get_latest_bars(symbols)
            
            if not latest_bars:
                return {}
            
            result = {}
            for symbol, bar in latest_bars.items():
                result[symbol] = {
                    'timestamp': bar.timestamp,
                    'open': float(bar.open),
                    'high': float(bar.high),
                    'low': float(bar.low),
                    'close': float(bar.close),
                    'volume': int(bar.volume)
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to fetch latest bars: {e}")
            return {}
    
    def compute_features(
        self,
        symbol: str,
        bars_df: pd.DataFrame
    ) -> Optional[Dict]:
        """
        Compute features for a symbol.
        """
        try:
            features = self.feature_engine.calculate_features(
                bars_df,
                ema_short=settings.ema_short,
                ema_long=settings.ema_long
            )
            
            if features:
                features['symbol'] = symbol
                features['timestamp'] = datetime.utcnow().isoformat()
                
                # Store in state
                trading_state.update_features(symbol, features)
                
                # Store in database
                self.supabase.upsert_features(features)
                
                logger.debug(f"Computed features for {symbol}: EMA_short={features['ema_short']:.2f}, EMA_long={features['ema_long']:.2f}")
                
                return features
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to compute features for {symbol}: {e}")
            return None
    
    def update_all_features(self, symbols: List[str]):
        """
        Update features for all symbols.
        Fetches latest bars and computes indicators.
        """
        try:
            # Fetch historical data for feature computation
            historical_bars = self.fetch_historical_bars(symbols, days=1)
            
            for symbol in symbols:
                if symbol in historical_bars:
                    bars_df = historical_bars[symbol]
                    self.compute_features(symbol, bars_df)
            
            logger.info(f"Updated features for {len(symbols)} symbols")
            
        except Exception as e:
            logger.error(f"Failed to update features: {e}")
    
    def store_bars_to_db(self, symbol: str, bars: List[Dict]):
        """
        Store market data bars to database.
        """
        try:
            bars_data = []
            for bar in bars:
                bars_data.append({
                    'symbol': symbol,
                    'timestamp': bar['timestamp'].isoformat() if isinstance(bar['timestamp'], datetime) else bar['timestamp'],
                    'open': bar['open'],
                    'high': bar['high'],
                    'low': bar['low'],
                    'close': bar['close'],
                    'volume': bar['volume'],
                    'timeframe': '1min'
                })
            
            if bars_data:
                count = self.supabase.insert_bars(bars_data)
                logger.debug(f"Stored {count} bars for {symbol}")
            
        except Exception as e:
            logger.error(f"Failed to store bars for {symbol}: {e}")
    
    def get_latest_features(self, symbol: str) -> Optional[Dict]:
        """
        Get latest computed features for a symbol.
        """
        # Try state first (fastest)
        features = trading_state.get_features(symbol)
        if features:
            return features
        
        # Fall back to database
        try:
            features = self.supabase.get_features(symbol)
            if features:
                trading_state.update_features(symbol, features)
            return features
        except Exception as e:
            logger.error(f"Failed to get features for {symbol}: {e}")
            return None

    def apply_stream_price(self, symbol: str, price: float, timestamp: Optional[datetime] = None):
        """
        Lightweight feature update when a streaming price arrives.
        Keeps features in sync for copilot/context consumers without heavy recomputation.
        """
        if price <= 0:
            return

        features = trading_state.get_features(symbol) or {"symbol": symbol}
        features["price"] = price
        features["last_update"] = (timestamp or datetime.utcnow()).isoformat()

        trading_state.update_features(symbol, features)
        try:
            self.supabase.upsert_features(features)
        except Exception as exc:
            logger.debug(f"Non-fatal: failed to upsert streaming feature for {symbol}: {exc}")

    def apply_stream_bar(self, symbol: str, bar: Dict[str, float], timestamp: Optional[datetime] = None):
        """
        Update stored bar data and cached features based on a streaming bar update.
        """
        price = float(bar.get("close") or 0)
        if price:
            self.apply_stream_price(symbol, price, timestamp or datetime.utcnow())

        try:
            self.supabase.insert_bars(
                [
                    {
                        "symbol": symbol,
                        "timestamp": (timestamp or datetime.utcnow()).isoformat(),
                        "open": bar.get("open"),
                        "high": bar.get("high"),
                        "low": bar.get("low"),
                        "close": bar.get("close"),
                        "volume": bar.get("volume"),
                        "timeframe": "stream",
                    }
                ]
            )
        except Exception as exc:
            logger.debug(f"Non-fatal: failed to store streaming bar for {symbol}: {exc}")
