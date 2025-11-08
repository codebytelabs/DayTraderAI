from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Alpaca
    alpaca_api_key: str
    alpaca_secret_key: str
    alpaca_base_url: str = "https://paper-api.alpaca.markets"
    
    # Supabase
    supabase_url: str
    supabase_key: str
    supabase_service_key: str
    
    # OpenRouter Configuration (Models tested and optimized for quality + speed)
    openrouter_api_key: str = ""
    openrouter_api_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_primary_model: str = "openai/gpt-oss-safeguard-20b"  # Best: 408 score, 1.4s
    openrouter_secondary_model: str = "google/gemini-2.5-flash-preview-09-2025"  # Fast: 322 score, 1.7s
    openrouter_tertiary_model: str = "openai/gpt-oss-120b"  # Balanced: 221 score, 3.4s
    openrouter_backup_model: str = "minimax/minimax-m2:free"
    openrouter_temperature: float = 0.7
    
    # Perplexity Configuration
    perplexity_api_key: str = ""
    perplexity_api_base_url: str = "https://api.perplexity.ai"
    perplexity_default_model: str = "sonar-pro"
    
    # Strategy
    watchlist: str = "SPY,QQQ,AAPL,MSFT,NVDA"
    max_positions: int = 20
    risk_per_trade_pct: float = 0.01
    max_position_pct: float = 0.10  # Max 10% of equity per position
    min_stop_distance_pct: float = 0.01  # Min 1% stop distance from entry
    circuit_breaker_pct: float = 0.05
    ema_short: int = 9
    ema_long: int = 21
    stop_loss_atr_mult: float = 2.0
    take_profit_atr_mult: float = 4.0
    bracket_orders_enabled: bool = True
    default_take_profit_pct: float = 2.0
    default_stop_loss_pct: float = 1.0
    
    # Options
    options_enabled: bool = False
    max_options_positions: int = 5
    options_risk_per_trade_pct: float = 0.02
    
    # Streaming
    streaming_enabled: bool = True
    stream_reconnect_delay: int = 5
    
    # Phase 2: Opportunity Scanner
    use_dynamic_watchlist: bool = False  # Enable dynamic watchlist
    scanner_interval_hours: int = 1  # Scan every hour
    scanner_min_score: float = 80.0  # Minimum A- grade (was 60.0 - too permissive)
    scanner_watchlist_size: int = 20  # Number of stocks in dynamic watchlist
    
    # Trade Frequency Limits (Quality over Quantity)
    max_trades_per_day: int = 30  # Cap daily trades to prevent over-trading
    max_trades_per_symbol_per_day: int = 2  # Max 2 entries per symbol per day
    trade_cooldown_minutes: int = 15  # Minimum 15 minutes between trades in same symbol

    # Copilot configuration
    copilot_context_enabled: bool = True
    copilot_hybrid_routing: bool = True
    copilot_trade_execution: bool = False

    copilot_context_timeout_ms: int = 800
    copilot_ai_timeout_ms: int = 15_000
    copilot_cache_ttl_seconds: int = 60

    copilot_include_account: bool = True
    copilot_include_positions: bool = True
    copilot_include_history: bool = True
    copilot_include_market: bool = True
    copilot_include_news: bool = True
    copilot_include_risk: bool = True

    copilot_history_trades: int = 20
    copilot_news_lookback_hours: int = 24
    copilot_news_max_items: int = 12

    # Copilot action execution settings
    copilot_action_execution_enabled: bool = True
    copilot_action_confidence_threshold: float = 0.7
    copilot_require_confirmation_above_value: float = 1000.0
    copilot_max_bulk_operations: int = 10
    copilot_action_timeout_seconds: float = 5.0
    
    # Server
    backend_port: int = 8000
    frontend_url: str = "http://localhost:5173"
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def watchlist_symbols(self) -> List[str]:
        return [s.strip().upper() for s in self.watchlist.split(",") if s.strip()]


settings = Settings()
