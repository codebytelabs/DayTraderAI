import asyncio
import math
import re
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from config import settings
from copilot.config import CopilotConfig
from core.alpaca_client import AlpacaClient
from core.state import trading_state
from core.supabase_client import SupabaseClient
from data.market_data import MarketDataManager
from news.news_client import NewsClient
from trading.risk_manager import RiskManager
from utils.logger import setup_logger

logger = setup_logger(__name__)

SYMBOL_PATTERN = re.compile(r"\b[A-Z]{1,6}\b")


@dataclass(slots=True)
class ContextResult:
    """Container returned by the context builder."""

    context: Dict[str, Any]
    summary: str
    highlights: List[str]


class CopilotContextBuilder:
    """Aggregates trading, market, and news context for copilot queries."""

    def __init__(
        self,
        alpaca_client: AlpacaClient,
        supabase_client: SupabaseClient,
        market_data_manager: MarketDataManager,
        news_client: NewsClient,
        risk_manager: RiskManager,
        config: CopilotConfig,
    ):
        self._alpaca = alpaca_client
        self._supabase = supabase_client
        self._market = market_data_manager
        self._news = news_client
        self._risk = risk_manager
        self._config = config

        self._cache: Dict[str, Tuple[datetime, Any]] = {}
        self._cache_lock = Lock()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def build_context(
        self,
        query: str,
        *,
        symbols: Optional[Sequence[str]] = None,
    ) -> ContextResult:
        """Build a comprehensive context payload for the given query."""

        if not self._config.context_enabled:
            logger.debug("Copilot context disabled; returning minimal payload.")
            minimal = self._minimal_context(query)
            return ContextResult(context=minimal, summary="", highlights=[])

        normalized_query = query.strip()
        detected_symbols = list({s for s in (symbols or []) if s})
        if not detected_symbols:
            detected_symbols = self.extract_symbols(normalized_query)

        account = self._aggregate_account_state()
        positions = self._aggregate_positions(account)
        history, performance = await self._aggregate_trade_history()
        market = await self._aggregate_market_context(detected_symbols or None)
        news_items = await self._aggregate_news(detected_symbols or None)
        risk = self._aggregate_risk(account, positions, performance)

        context = {
            "query": normalized_query,
            "timestamp": datetime.utcnow().isoformat(),
            "symbols": detected_symbols,
            "account": account,
            "positions": positions,
            "history": history,
            "performance": performance,
            "market": market,
            "news": news_items,
            "risk": risk,
        }

        highlights = self._build_highlights(context)
        summary = self._render_summary(context, highlights)
        context["summary"] = summary
        context["highlights"] = highlights

        return ContextResult(context=context, summary=summary, highlights=highlights)

    def extract_symbols(self, text: str) -> List[str]:
        """Extract potential ticker symbols from free-form text."""
        if not text:
            return []
        candidates = SYMBOL_PATTERN.findall(text.upper())
        watchlist = set(settings.watchlist_symbols)
        return [symbol for symbol in candidates if symbol in watchlist]

    # ------------------------------------------------------------------
    # Aggregators
    # ------------------------------------------------------------------

    def _aggregate_account_state(self) -> Dict[str, Any]:
        metrics = trading_state.get_metrics()
        account_snapshot = {
            "equity": metrics.equity,
            "cash": metrics.cash,
            "buying_power": metrics.buying_power,
            "daily_pl": metrics.daily_pl,
            "daily_pl_pct": metrics.daily_pl_pct,
            "total_pl": metrics.total_pl,
            "win_rate": metrics.win_rate,
            "profit_factor": metrics.profit_factor,
            "wins": metrics.wins,
            "losses": metrics.losses,
            "total_trades": metrics.total_trades,
            "open_positions": metrics.open_positions,
            "max_positions": metrics.max_positions,
            "circuit_breaker_triggered": metrics.circuit_breaker_triggered,
            "trading_enabled": trading_state.is_trading_allowed(),
            "last_update": trading_state.last_update.isoformat(),
        }
        return account_snapshot

    def _aggregate_positions(self, account: Dict[str, Any]) -> List[Dict[str, Any]]:
        equity = account.get("equity") or 0
        positions = []
        for position in trading_state.get_all_positions():
            exposure_pct = 0.0
            try:
                exposure_pct = (position.market_value / equity) * 100 if equity else 0.0
            except ZeroDivisionError:
                exposure_pct = 0.0

            positions.append(
                {
                    "symbol": position.symbol,
                    "qty": position.qty,
                    "side": position.side,
                    "avg_entry_price": position.avg_entry_price,
                    "current_price": position.current_price,
                    "unrealized_pl": position.unrealized_pl,
                    "unrealized_pl_pct": position.unrealized_pl_pct,
                    "market_value": position.market_value,
                    "stop_loss": position.stop_loss,
                    "take_profit": position.take_profit,
                    "exposure_pct": exposure_pct,
                    "entry_time": position.entry_time.isoformat(),
                }
            )
        positions.sort(key=lambda p: abs(p.get("market_value", 0)), reverse=True)
        return positions

    async def _aggregate_trade_history(self) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        cache_key = "trade_history"
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        def fetch() -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
            trades = self._supabase.get_trades(limit=self._config.max_history_trades)
            if not trades:
                return [], {
                    "win_rate": 0.0,
                    "profit_factor": 0.0,
                    "avg_win": 0.0,
                    "avg_loss": 0.0,
                    "sharpe_ratio": 0.0,
                    "total_trades": 0,
                }

            processed: List[Dict[str, Any]] = []
            wins: List[float] = []
            losses: List[float] = []
            returns_pct: List[float] = []

            for trade in trades:
                pnl = float(trade.get("pnl", 0) or 0)
                pnl_pct = float(trade.get("pnl_pct", 0) or 0)
                processed.append(
                    {
                        "symbol": trade.get("symbol"),
                        "side": trade.get("side"),
                        "qty": trade.get("qty"),
                        "entry_price": float(trade.get("entry_price", 0) or 0),
                        "exit_price": float(trade.get("exit_price", 0) or 0),
                        "pnl": pnl,
                        "pnl_pct": pnl_pct,
                        "entry_time": trade.get("entry_time"),
                        "exit_time": trade.get("exit_time"),
                        "reason": trade.get("reason"),
                    }
                )
                returns_pct.append(pnl_pct)
                if pnl > 0:
                    wins.append(pnl)
                elif pnl < 0:
                    losses.append(abs(pnl))

            win_rate = (len(wins) / len(processed)) if processed else 0.0
            avg_win = statistics.mean(wins) if wins else 0.0
            avg_loss = statistics.mean(losses) if losses else 0.0
            profit_factor = (sum(wins) / sum(losses)) if wins and losses and sum(losses) else 0.0
            sharpe = self._calculate_sharpe_ratio(returns_pct)

            metrics = {
                "win_rate": win_rate,
                "profit_factor": profit_factor,
                "avg_win": avg_win,
                "avg_loss": avg_loss,
                "sharpe_ratio": sharpe,
                "total_trades": len(processed),
            }
            return processed, metrics

        history, performance = await asyncio.to_thread(fetch)
        self._cache_set(cache_key, (history, performance))
        return history, performance

    async def _aggregate_market_context(self, focus_symbols: Optional[Sequence[str]]) -> Dict[str, Any]:
        cache_key = f"market:{','.join(focus_symbols) if focus_symbols else 'all'}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        symbols = list(settings.watchlist_symbols)
        focus = set(focus_symbols or [])

        def classify_symbol(symbol: str, features: Dict[str, Any]) -> str:
            try:
                ema_short = float(features.get("ema_short", 0))
                ema_long = float(features.get("ema_long", 0))
                macd = float(features.get("macd", ema_short - ema_long))
            except (TypeError, ValueError):
                return "unknown"

            if ema_short >= ema_long and macd >= 0:
                return "bullish"
            if ema_short <= ema_long and macd <= 0:
                return "bearish"
            return "neutral"

        def fetch() -> Dict[str, Any]:
            market_snapshot: Dict[str, Any] = {"symbols": []}
            latest_bars = self._alpaca.get_latest_bars(symbols)

            for symbol in symbols:
                features = self._market.get_latest_features(symbol) or {}
                latest_bar = latest_bars.get(symbol) if latest_bars else None
                indicator = classify_symbol(symbol, features)

                market_snapshot["symbols"].append(
                    {
                        "symbol": symbol,
                        "price": float(features.get("price") or latest_bar.close if latest_bar else 0),
                        "atr": float(features.get("atr", 0) or 0),
                        "ema_short": float(features.get("ema_short", 0) or 0),
                        "ema_long": float(features.get("ema_long", 0) or 0),
                        "rsi": float(features.get("rsi", 0) or 0),
                        "signal": indicator,
                        "focus": symbol in focus,
                        "timestamp": features.get("timestamp"),
                    }
                )

            spy_features = self._market.get_latest_features("SPY") or {}
            vix_features = self._market.get_latest_features("VIX") or {}

            market_snapshot["macro"] = {
                "spy_trend": classify_symbol("SPY", spy_features) if spy_features else "unknown",
                "spy_price": float(spy_features.get("price", 0) or 0),
                "vix_level": float(vix_features.get("price", 0) or 0),
                "vix_trend": classify_symbol("VIX", vix_features) if vix_features else "unknown",
            }

            return market_snapshot

        market_context = await asyncio.to_thread(fetch)
        self._cache_set(cache_key, market_context)
        return market_context

    async def _aggregate_news(self, focus_symbols: Optional[Sequence[str]]) -> List[Dict[str, Any]]:
        if not self._config.include_news or self._news is None:
            return []

        cache_key = f"news:{','.join(focus_symbols) if focus_symbols else 'all'}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        def fetch() -> List[Dict[str, Any]]:
            symbols = list(focus_symbols or [])
            if not symbols:
                symbols = [pos["symbol"] for pos in self._aggregate_positions(self._aggregate_account_state())[:5]]
            articles = self._news.get_news(
                symbols=symbols or None,
                start=datetime.utcnow() - timedelta(hours=self._config.news_lookback_hours),
                limit=self._config.max_news_items,
            )

            enriched: List[Dict[str, Any]] = []
            for article in articles[: self._config.max_news_items]:
                sentiment = self._news.analyze_sentiment(article)
                enriched.append(
                    {
                        "headline": article.get("headline"),
                        "summary": article.get("summary"),
                        "url": article.get("url"),
                        "created_at": article.get("created_at"),
                        "symbols": article.get("symbols", []),
                        "source": article.get("source"),
                        "sentiment": sentiment.get("sentiment"),
                        "sentiment_score": sentiment.get("score"),
                        "sentiment_confidence": sentiment.get("confidence"),
                    }
                )
            return enriched

        news_items = await asyncio.to_thread(fetch)
        self._cache_set(cache_key, news_items)
        return news_items

    def _aggregate_risk(
        self,
        account: Dict[str, Any],
        positions: List[Dict[str, Any]],
        performance: Dict[str, Any],
    ) -> Dict[str, Any]:
        max_positions = getattr(self._risk, "max_positions", account.get("max_positions", 0))
        risk_per_trade_pct = getattr(self._risk, "risk_per_trade_pct", settings.risk_per_trade_pct)

        total_exposure = sum(abs(pos.get("market_value", 0) or 0) for pos in positions)
        equity = account.get("equity") or 0

        return {
            "open_positions": len(positions),
            "max_positions": max_positions,
            "position_utilisation": (len(positions) / max_positions) if max_positions else 0.0,
            "gross_exposure": total_exposure,
            "equity_utilisation": (total_exposure / equity) if equity else 0.0,
            "risk_per_trade_pct": risk_per_trade_pct,
            "circuit_breaker_triggered": account.get("circuit_breaker_triggered", False),
            "win_rate": performance.get("win_rate", 0.0),
            "profit_factor": performance.get("profit_factor", 0.0),
        }

    # ------------------------------------------------------------------
    # Summaries / formatting
    # ------------------------------------------------------------------

    def _build_highlights(self, context: Dict[str, Any]) -> List[str]:
        highlights: List[str] = []
        account = context.get("account", {})
        performance = context.get("performance", {})
        risk = context.get("risk", {})

        equity = account.get("equity", 0)
        daily_pl = account.get("daily_pl", 0)
        daily_pl_pct = account.get("daily_pl_pct", 0)
        highlights.append(
            f"Equity ${equity:,.2f} | Daily P/L {self._format_signed(daily_pl)} "
            f"({daily_pl_pct:+.2f}%)"
        )

        win_rate = performance.get("win_rate", 0.0) * 100 if performance.get("win_rate") <= 1 else performance.get("win_rate", 0.0)
        highlights.append(
            f"Win rate {win_rate:.1f}% | Profit factor {performance.get('profit_factor', 0.0):.2f}"
        )

        if context.get("positions"):
            top = context["positions"][0]
            highlights.append(
                f"Largest position {top['symbol']} {top['side'].upper()} "
                f"{top['qty']} @ {top['avg_entry_price']:.2f} "
                f"(P/L {self._format_signed(top['unrealized_pl'])})"
            )

        if risk.get("circuit_breaker_triggered"):
            highlights.append("⚠️ Circuit breaker active — trading disabled.")

        return highlights

    def _render_summary(self, context: Dict[str, Any], highlights: Iterable[str]) -> str:
        lines: List[str] = ["Trading Snapshot:"]
        lines.extend(f"- {line}" for line in highlights)

        if context.get("symbols"):
            lines.append(f"Focus symbols: {', '.join(context['symbols'])}")

        market = context.get("market", {})
        macro = market.get("macro", {})
        if macro:
            lines.append(
                f"Market: SPY trend {macro.get('spy_trend', 'unknown')}, "
                f"VIX {macro.get('vix_trend', 'unknown')} @ {macro.get('vix_level', 0):.2f}"
            )

        news = context.get("news") or []
        if news:
            latest = news[0]
            lines.append(
                f"Latest news: {latest.get('headline')} "
                f"({latest.get('sentiment', 'neutral')})"
            )

        lines.append(f"Generated at {context.get('timestamp')}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _format_signed(value: float) -> str:
        prefix = "+" if value >= 0 else "-"
        return f"{prefix}${abs(value):,.2f}"

    @staticmethod
    def _calculate_sharpe_ratio(returns_pct: Sequence[float]) -> float:
        if not returns_pct:
            return 0.0

        returns = [r / 100 for r in returns_pct if isinstance(r, (int, float))]
        if len(returns) < 2:
            return 0.0

        avg = statistics.mean(returns)
        stddev = statistics.stdev(returns)
        if stddev == 0:
            return 0.0
        # Assume 252 trading days
        return (avg / stddev) * math.sqrt(252)

    def _cache_get(self, key: str):
        with self._cache_lock:
            entry = self._cache.get(key)
            if not entry:
                return None
            timestamp, payload = entry
            if datetime.utcnow() - timestamp > timedelta(seconds=self._config.cache_ttl_seconds):
                del self._cache[key]
                return None
            return payload

    def _cache_set(self, key: str, value: Any):
        with self._cache_lock:
            self._cache[key] = (datetime.utcnow(), value)

    @staticmethod
    def _minimal_context(query: str) -> Dict[str, Any]:
        return {
            "query": query,
            "timestamp": datetime.utcnow().isoformat(),
            "summary": "",
            "highlights": [],
        }
