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
    
    # OpenRouter Configuration
    openrouter_api_key: str = ""
    openrouter_api_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_primary_model: str = "google/gemini-2.5-flash-preview-09-2025"
    openrouter_secondary_model: str = "google/gemini-2.5-flash-lite-preview-09-2025"
    openrouter_backup_model: str = "minimax/minimax-m2:free"
    openrouter_temperature: float = 0.7
    
    # Perplexity Configuration
    perplexity_api_key: str = ""
    perplexity_api_base_url: str = "https://api.perplexity.ai"
    perplexity_default_model: str = "sonar-pro"
    
    # Strategy
    watchlist: str = "SPY,QQQ,AAPL,MSFT,NVDA"
    max_positions: int = 5
    risk_per_trade_pct: float = 0.01
    circuit_breaker_pct: float = 0.05
    ema_short: int = 9
    ema_long: int = 21
    stop_loss_atr_mult: float = 2.0
    take_profit_atr_mult: float = 4.0
    
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
