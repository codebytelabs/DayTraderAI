from dataclasses import dataclass
from config import Settings, settings


@dataclass(slots=True)
class CopilotConfig:
    """Runtime configuration for the copilot system."""

    context_enabled: bool = True
    hybrid_routing: bool = True
    trade_execution: bool = False

    context_timeout_ms: int = 800
    ai_timeout_ms: int = 15_000
    cache_ttl_seconds: int = 60

    include_account: bool = True
    include_positions: bool = True
    include_history: bool = True
    include_market: bool = True
    include_news: bool = True
    include_risk: bool = True

    max_history_trades: int = 20
    news_lookback_hours: int = 24
    max_news_items: int = 12

    # Action execution settings
    action_execution_enabled: bool = True
    action_confidence_threshold: float = 0.7
    require_confirmation_above_value: float = 1000.0  # USD
    max_bulk_operations: int = 10
    action_timeout_seconds: float = 5.0

    def copy(self) -> "CopilotConfig":
        return CopilotConfig(
            context_enabled=self.context_enabled,
            hybrid_routing=self.hybrid_routing,
            trade_execution=self.trade_execution,
            context_timeout_ms=self.context_timeout_ms,
            ai_timeout_ms=self.ai_timeout_ms,
            cache_ttl_seconds=self.cache_ttl_seconds,
            include_account=self.include_account,
            include_positions=self.include_positions,
            include_history=self.include_history,
            include_market=self.include_market,
            include_news=self.include_news,
            include_risk=self.include_risk,
            max_history_trades=self.max_history_trades,
            news_lookback_hours=self.news_lookback_hours,
            max_news_items=self.max_news_items,
            action_execution_enabled=self.action_execution_enabled,
            action_confidence_threshold=self.action_confidence_threshold,
            require_confirmation_above_value=self.require_confirmation_above_value,
            max_bulk_operations=self.max_bulk_operations,
            action_timeout_seconds=self.action_timeout_seconds,
        )


def build_copilot_config(app_settings: Settings = settings) -> CopilotConfig:
    """Create a CopilotConfig instance from global settings."""
    return CopilotConfig(
        context_enabled=app_settings.copilot_context_enabled,
        hybrid_routing=app_settings.copilot_hybrid_routing,
        trade_execution=app_settings.copilot_trade_execution,
        context_timeout_ms=app_settings.copilot_context_timeout_ms,
        ai_timeout_ms=app_settings.copilot_ai_timeout_ms,
        cache_ttl_seconds=app_settings.copilot_cache_ttl_seconds,
        include_account=app_settings.copilot_include_account,
        include_positions=app_settings.copilot_include_positions,
        include_history=app_settings.copilot_include_history,
        include_market=app_settings.copilot_include_market,
        include_news=app_settings.copilot_include_news,
        include_risk=app_settings.copilot_include_risk,
        max_history_trades=app_settings.copilot_history_trades,
        news_lookback_hours=app_settings.copilot_news_lookback_hours,
        max_news_items=app_settings.copilot_news_max_items,
        action_execution_enabled=app_settings.copilot_action_execution_enabled,
        action_confidence_threshold=app_settings.copilot_action_confidence_threshold,
        require_confirmation_above_value=app_settings.copilot_require_confirmation_above_value,
        max_bulk_operations=app_settings.copilot_max_bulk_operations,
        action_timeout_seconds=app_settings.copilot_action_timeout_seconds,
    )
