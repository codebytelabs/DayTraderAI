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
    risk_per_trade_pct: float = 0.015  # Increased from 1% to 1.5% for better capital utilization
    max_position_pct: float = 0.15  # Increased from 10% to 15% per position (deploy more capital)
    max_position_pct_scaled: float = 0.20  # Increased from 15% to 20% for high-confidence trades
    # ============ OPTIMAL STOP LOSS SETTINGS (Research-Based) ============
    # Based on: Van Tharp, prop trading firms, quantitative research
    min_stop_distance_pct: float = 0.008  # 0.8% minimum (prevents noise exits)
    max_stop_distance_pct: float = 0.020  # 2.0% maximum (caps risk)
    circuit_breaker_pct: float = 0.03  # 3% daily max loss (was 5% - too loose)
    ema_short: int = 9
    ema_long: int = 21
    
    # ATR-Based Stop Loss (optimal for day trading)
    stop_loss_atr_mult: float = 1.5  # 1.5x ATR (day trading sweet spot, was 2.5)
    stop_loss_atr_period: int = 10  # 10-period ATR (faster for intraday)
    take_profit_atr_mult: float = 3.0  # 3x ATR for 1:2 R/R minimum (was 5.0)
    bracket_orders_enabled: bool = True
    default_take_profit_pct: float = 3.0  # 3% target (2:1 R/R with 1.5% stop)
    default_stop_loss_pct: float = 1.5  # 1.5% stop (research optimal)
    
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
    scanner_min_score: float = 65.0  # Balanced threshold (was 80.0 - too restrictive, 60.0 - too permissive)
    scanner_watchlist_size: int = 21  # Number of stocks in dynamic watchlist
    
    # Momentum Wave Rider Scanner (Alternative to AI Discovery)
    USE_MOMENTUM_SCANNER: bool = True  # ENABLED - Real-time momentum scanning (32 property tests passing)
    MOMENTUM_SCAN_INTERVAL: int = 300  # 5 minutes default scan interval
    FIRST_HOUR_SCAN_INTERVAL: int = 120  # 2 minutes in first hour (9:30-10:30 AM)
    MOMENTUM_MIN_SCORE: float = 60.0  # Minimum momentum score to consider
    MOMENTUM_HIGH_CONFIDENCE_THRESHOLD: float = 85.0  # Score for high-confidence alerts
    
    # Confidence-Based Position Sizing Tiers
    CONFIDENCE_TIER_ULTRA_HIGH: float = 90.0  # 15% max position
    CONFIDENCE_TIER_HIGH: float = 80.0  # 12% max position
    CONFIDENCE_TIER_MEDIUM: float = 70.0  # 10% max position
    CONFIDENCE_TIER_LOW: float = 60.0  # 8% max position
    
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
    trade_cooldown_minutes: int = 15  # Reduced from 30 - better for day trading momentum
    min_hold_time_minutes: int = 15  # Minimum time to hold position before manual exit (stops still work)
    
    # ============ OPTIMAL TRAILING STOP SETTINGS (Research-Based) ============
    # Based on: Professional prop firms, Van Tharp R-multiple methodology
    trailing_stops_enabled: bool = True  # ENABLED - Protect profits automatically
    
    # Breakeven Protection (The "Free Trade")
    breakeven_trigger_r: float = 1.0  # Move to breakeven at 1R profit
    breakeven_buffer_pct: float = 0.001  # 0.1% above entry (slippage protection)
    
    # Trailing Stop Activation
    trailing_stops_activation_r: float = 1.5  # Start trailing at 1.5R (was 2.0)
    trailing_stops_activation_threshold: float = 1.5  # ALIAS for backward compatibility
    trailing_stops_distance_pct: float = 0.01  # 1.0% trailing distance (was 0.5%)
    trailing_stops_distance_r: float = 0.5  # ALIAS for backward compatibility
    trailing_stops_min_distance_pct: float = 0.005  # ALIAS for backward compatibility
    trailing_stops_atr_multiplier: float = 1.0  # 1x ATR for trailing (tighter than initial)
    trailing_stops_use_atr: bool = True  # Use ATR for dynamic trailing
    trailing_stops_update_seconds: int = 30  # Update every 30 seconds
    max_trailing_stop_positions: int = 999  # Unlimited
    
    # ============ PARTIAL PROFIT TAKING (Scale Out) ============
    # "Half Off at 1R" Strategy - proven by prop trading firms
    partial_profits_enabled: bool = True  # ENABLED - Lock in profits early
    
    # Scale Out Levels
    partial_profits_1r_percent: float = 0.50  # Sell 50% at 1R
    partial_profits_2r_percent: float = 0.25  # Sell 25% more at 2R
    partial_profits_3r_percent: float = 0.25  # Trail remaining 25% at 3R+
    
    # After partial profit, tighten trailing
    partial_profits_tight_trail_atr: float = 0.75  # 0.75x ATR after 3R
    
    # BACKWARD COMPATIBILITY ALIASES
    partial_profits_first_target_r: float = 1.0  # Alias
    partial_profits_percentage: float = 0.5  # Alias
    partial_profits_second_target_r: float = 2.0  # Alias
    partial_profits_use_trailing: bool = True  # Alias
    max_partial_profit_positions: int = 999  # Alias

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
    SMART_EXECUTOR_MAX_SLIPPAGE_PCT: float = 0.002  # 0.20% max slippage (increased for paper trading)
    SMART_EXECUTOR_LIMIT_BUFFER_REGULAR: float = 0.001  # 0.10% buffer for regular hours
    SMART_EXECUTOR_LIMIT_BUFFER_EXTENDED: float = 0.0005  # 0.05% buffer for extended hours
    SMART_EXECUTOR_FILL_TIMEOUT: int = 120  # 120 seconds to wait for fill (increased for reliability)
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
    
    # EOD Risk Management (Sprint 8) - CRITICAL FOR DAY TRADING
    # Overnight gaps can destroy profits (e.g., COIN -$1,098 overnight gap)
    force_eod_exit: bool = True  # Force close all positions before market close
    eod_exit_time: str = "15:57"  # 3 minutes before market close (ET) - NO EXCEPTIONS
    eod_close_all: bool = True  # True = close ALL positions, False = only close losers
    eod_loss_threshold: float = 2.0  # If eod_close_all=False, close positions with >X% loss
    
    # Entry Cutoff - No new positions near market close
    entry_cutoff_time: str = "15:30"  # No new entries after 3:30 PM ET (30 min before close)
    entry_cutoff_enabled: bool = True  # Enforce entry cutoff strictly
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env
    
    @property
    def watchlist_symbols(self) -> List[str]:
        return [s.strip().upper() for s in self.watchlist.split(",") if s.strip()]


settings = Settings()
