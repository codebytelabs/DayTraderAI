from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv

# Force load .env to override any stale shell environment variables
load_dotenv(override=True)



class Settings(BaseSettings):
    # Alpaca
    alpaca_api_key: str
    alpaca_secret_key: str
    alpaca_base_url: str = "https://paper-api.alpaca.markets"
    
    # Supabase
    supabase_url: str
    supabase_key: str
    supabase_service_key: str
    
    # AI Provider Configuration
    ai_primary_provider: str = "perplexity"  # perplexity or openrouter
    ai_secondary_provider: str = "openrouter"  # perplexity or openrouter
    
    # OpenRouter Configuration
    openrouter_api_key: str = ""
    openrouter_api_base_url: str = "https://openrouter.ai/api/v1"
    
    # Default models to use (loaded from .env - DO NOT HARDCODE)
    # These are fallback defaults only - actual values come from .env
    # COST OPTIMIZED 2025-12-01: Grok models are FREE and high quality!
    openrouter_primary_model: str = "x-ai/grok-4.1-fast:free"  # FREE, 100% JSON, Score 85
    openrouter_secondary_model: str = "x-ai/grok-4-fast"  # $0.70/M, fast, reliable
    openrouter_tertiary_model: str = "openai/gpt-oss-120b"  # $0.24/M, best value
    openrouter_backup_model: str = "google/gemini-2.5-flash-lite"  # Fast, cheap fallback
    openrouter_temperature: float = 0.3  # Lower temp for more consistent trading analysis
    
    # Perplexity Configuration
    perplexity_api_key: str = ""
    perplexity_api_base_url: str = "https://api.perplexity.ai"
    perplexity_default_model: str = "sonar-pro"
    
    # OpenRouter Perplexity Fallback (when native Perplexity API fails)
    openrouter_perplexity_model: str = "perplexity/sonar-pro"
    
    # Twelve Data Configuration (Sprint 7 - Daily Cache)
    twelvedata_api_key: str = ""
    twelvedata_secondary_api_key: str = ""
    
    # Strategy
    watchlist: str = "SPY,QQQ,AAPL,MSFT,NVDA"
    max_positions: int = 25  # Increased from 20 (Phase 2a: Conservative rollout) ✅
    risk_per_trade_pct: float = 0.01
    max_position_pct: float = 0.20  # Increased to 20% (Hedge Fund Tweak) to unlock 2% risk sizing 🚀
    min_stop_distance_pct: float = 0.015  # Min 1.5% stop distance (was 1.0% - caused TDG bug!)
    circuit_breaker_pct: float = 0.05
    ema_short: int = 9
    ema_long: int = 21
    stop_loss_atr_mult: float = 2.5  # Wider stops (was 2.0 - too tight)
    take_profit_atr_mult: float = 5.0  # Wider targets for better R/R (was 4.0)
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
    use_dynamic_watchlist: bool = True  # Enable dynamic watchlist - FIXED: was False
    scanner_interval_hours: int = 1  # Scan every hour
    scanner_min_score: float = 80.0  # Minimum A- grade (was 60.0 - too permissive)
    scanner_watchlist_size: int = 20  # Number of stocks in dynamic watchlist
    
    # Trading Mode Configuration
    long_only_mode: bool = False  # Allow both long and short positions
    
    # Trailing Stops Configuration (already implemented below)
    # trailing_stops_enabled: bool = True  # Enable trailing stops for profitable positions
    # trailing_stops_activation_threshold: float = 2.0  # Activate at +2R profit
    # trailing_stops_distance_r: float = 0.5  # Trail by 0.5R (0.5% for 1% risk positions)
    
    # Trade Frequency Limits (Quality over Quantity)
    # Research: 17 trades/day with 8 on META = churning = losses
    # Hedge fund approach: fewer, higher-quality trades
    max_trades_per_day: int = 15  # Reduced from 30 - quality over quantity
    max_trades_per_symbol_per_day: int = 2  # Max 2 entries per symbol per day
    trade_cooldown_minutes: int = 30  # Increased from 15 - prevent rapid re-entry churning
    min_hold_time_minutes: int = 15  # Minimum time to hold position before manual exit (stops still work)
    
    # Sprint 5: Trailing Stops Configuration
    trailing_stops_enabled: bool = True  # ENABLED - Protect profits automatically
    trailing_stops_activation_threshold: float = 2.0  # Activate after +2R profit
    trailing_stops_distance_r: float = 0.5  # Trail by 0.5R
    trailing_stops_min_distance_pct: float = 0.005  # Minimum 0.5% trailing distance
    trailing_stops_use_atr: bool = True  # Use ATR for dynamic trailing distance
    trailing_stops_atr_multiplier: float = 1.5  # 1.5x ATR for trailing distance
    max_trailing_stop_positions: int = 999  # Limit for gradual rollout (999 = unlimited)
    
    # Sprint 6: Partial Profit Taking Configuration
    partial_profits_enabled: bool = True  # ENABLED - Lock in profits early
    partial_profits_first_target_r: float = 1.0  # Take partial profits at +1R
    partial_profits_percentage: float = 0.5  # Sell 50% of position
    partial_profits_second_target_r: float = 2.0  # Let remaining run to +2R
    partial_profits_use_trailing: bool = True  # Use trailing stops on remaining position
    max_partial_profit_positions: int = 999  # Limit for gradual rollout

    # Copilot configuration
    copilot_context_enabled: bool = True
    copilot_hybrid_routing: bool = True
    copilot_trade_execution: bool = False

    copilot_context_timeout_ms: int = 800
    copilot_ai_timeout_ms: int = 30_000  # Increased from 15s - free models can be slow
    copilot_cache_ttl_seconds: int = 60

    copilot_include_account: bool = True
    copilot_include_positions: bool = True
    copilot_include_history: bool = True
    copilot_include_market: bool = True
    copilot_include_news: bool = True
    copilot_include_risk: bool = True
    
    # AI Enhancement Configuration (Phase 1: High-Risk Trade Validation)
    ENABLE_AI_VALIDATION: bool = True  # ENABLED - Fixed prompt to understand day trading leverage
    AI_VALIDATION_TIMEOUT: float = 3.5  # Max time to wait for AI response (seconds)
    
    # Smart Order Executor Configuration (Industry-Standard Order Execution)
    USE_SMART_EXECUTOR: bool = True  # Enable smart order execution with slippage protection
    SMART_EXECUTOR_MAX_SLIPPAGE_PCT: float = 0.001  # 0.10% max slippage
    SMART_EXECUTOR_LIMIT_BUFFER_REGULAR: float = 0.0005  # 0.05% buffer for regular hours
    SMART_EXECUTOR_LIMIT_BUFFER_EXTENDED: float = 0.0002  # 0.02% buffer for extended hours
    SMART_EXECUTOR_FILL_TIMEOUT: int = 60  # 60 seconds to wait for fill
    SMART_EXECUTOR_MIN_RR_RATIO: float = 2.0  # Minimum 1:2 risk/reward ratio
    SMART_EXECUTOR_ENABLE_EXTENDED_HOURS: bool = False  # Disable extended hours trading

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
    
    # Sprint 7: Win Rate Optimization Filters
    enable_time_of_day_filter: bool = True
    enable_200_ema_filter: bool = False  # Disabled - too strict for day trading
    enable_multitime_frame_filter: bool = False  # Disabled - blocking valid opportunities
    
    # Time-of-day settings - EXPANDED FOR DAY TRADING
    # Phase 1: Full trading day with adaptive position sizing
    optimal_hours_start_1: tuple = (9, 30)   # 9:30 AM - Market open
    optimal_hours_end_1: tuple = (11, 0)     # 11:00 AM - Morning session (100% size)
    optimal_hours_start_2: tuple = (11, 0)   # 11:00 AM - Midday session (70% size)
    optimal_hours_end_2: tuple = (14, 0)     # 2:00 PM - Midday session
    optimal_hours_start_3: tuple = (14, 0)   # 2:00 PM - Closing session (50% size)
    optimal_hours_end_3: tuple = (15, 30)    # 3:30 PM - Closing session
    avoid_lunch_hour: bool = False  # Disabled - we trade all day with adaptive sizing
    
    # Adaptive position sizing multipliers by time of day
    morning_session_multiplier: float = 1.0   # 100% size (9:30-11:00 AM)
    midday_session_multiplier: float = 0.7    # 70% size (11:00 AM-2:00 PM)
    closing_session_multiplier: float = 0.5   # 50% size (2:00-3:30 PM)
    
    # Daily trend settings
    daily_trend_ema_period: int = 200
    cache_refresh_time: str = "09:30"  # Market open
    
    # EOD Risk Management (Sprint 8)
    force_eod_exit: bool = True  # Force close all positions before market close
    eod_exit_time: str = "15:58"  # 2 minutes before market close (ET)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env
    
    @property
    def watchlist_symbols(self) -> List[str]:
        return [s.strip().upper() for s in self.watchlist.split(",") if s.strip()]


settings = Settings()
