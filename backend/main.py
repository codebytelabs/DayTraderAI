from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from pydantic import BaseModel

from config import settings
from copilot.config import CopilotConfig, build_copilot_config
from copilot.context_builder import CopilotContextBuilder, ContextResult
from copilot.query_router import QueryRoute, QueryRouter
from copilot.action_classifier import ActionClassifier, ActionIntent
from copilot.action_executor import ActionExecutor, ExecutionResult
from copilot.response_formatter import ResponseFormatter, CopilotResponse
from copilot.command_handler import CommandHandler
from copilot.prompts import get_system_prompt, get_perplexity_prompt
from advisory.openrouter import OpenRouterClient
from advisory.perplexity import PerplexityClient
from core.alpaca_client import AlpacaClient
from core.supabase_client import SupabaseClient
from core.state import trading_state, Position as StatePosition
from trading.risk_manager import RiskManager
from trading.order_manager import OrderManager
from trading.position_manager import PositionManager
from trading.strategy import EMAStrategy
from trading.trading_engine import TradingEngine, set_trading_engine, get_trading_engine
from data.features import FeatureEngine
from data.market_data import MarketDataManager
from news.news_client import NewsClient
from options.options_client import OptionsClient
from streaming import stream_manager, StreamingBroadcaster
from utils.logger import setup_logger
from ml.shadow_mode import MLShadowMode

logger = setup_logger(__name__)

# Global clients
alpaca_client: Optional[AlpacaClient] = None
supabase_client: Optional[SupabaseClient] = None
risk_manager: Optional[RiskManager] = None
order_manager: Optional[OrderManager] = None
position_manager: Optional[PositionManager] = None
strategy: Optional[EMAStrategy] = None
market_data_manager: Optional[MarketDataManager] = None
news_client: Optional[NewsClient] = None
copilot_config: Optional[CopilotConfig] = None
copilot_context_builder: Optional[CopilotContextBuilder] = None
copilot_router: Optional[QueryRouter] = None
action_classifier: Optional[ActionClassifier] = None
action_executor: Optional[ActionExecutor] = None
response_formatter: Optional[ResponseFormatter] = None
openrouter_client: Optional[OpenRouterClient] = None
perplexity_client: Optional[PerplexityClient] = None
streaming_broadcaster: Optional[StreamingBroadcaster] = None
command_handler: Optional[CommandHandler] = None
ml_shadow_mode: Optional[Any] = None  # ML shadow mode for learning


def _serialize_positions() -> List[Dict[str, Any]]:
    positions = trading_state.get_all_positions()
    return [
        {
            "symbol": p.symbol,
            "qty": p.qty,
            "side": p.side,
            "avg_entry_price": p.avg_entry_price,
            "current_price": p.current_price,
            "unrealized_pl": p.unrealized_pl,
            "unrealized_pl_pct": p.unrealized_pl_pct,
            "market_value": p.market_value,
            "stop_loss": p.stop_loss,
            "take_profit": p.take_profit,
        }
        for p in positions
    ]


def _serialize_orders() -> List[Dict[str, Any]]:
    orders = trading_state.get_all_orders()
    return [
        {
            "order_id": o.order_id,
            "symbol": o.symbol,
            "qty": o.qty,
            "side": o.side,
            "type": o.type,
            "status": o.status,
            "filled_qty": o.filled_qty,
            "filled_avg_price": o.filled_avg_price,
            "submitted_at": o.submitted_at.isoformat() if o.submitted_at else None,
        }
        for o in orders
    ]


def _serialize_logs(limit: int = 100) -> List[Dict[str, Any]]:
    logs = trading_state.get_logs(limit=limit)
    return [
        {
            "id": idx,
            "timestamp": log.timestamp.isoformat(),
            "level": log.level,
            "message": log.message,
            "source": log.source,
        }
        for idx, log in enumerate(logs)
    ]


def _serialize_advisories(limit: int = 20) -> List[Dict[str, Any]]:
    if not supabase_client:
        return []
    advisories = supabase_client.get_advisories(limit=limit)
    return [
        {
            "id": adv.get("id"),
            "timestamp": adv.get("timestamp"),
            "type": adv.get("type", "analysis"),
            "symbol": adv.get("symbol"),
            "content": adv.get("content"),
            "model": adv.get("model"),
            "confidence": adv.get("confidence", 0.5),
        }
        for adv in advisories
    ]


def build_streaming_snapshot() -> Dict[str, Any]:
    metrics = trading_state.get_metrics()
    snapshot = {
        "metrics": {
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
            "circuit_breaker_triggered": metrics.circuit_breaker_triggered,
        },
        "positions": _serialize_positions(),
        "orders": _serialize_orders(),
        "logs": _serialize_logs(limit=50),
        "advisories": _serialize_advisories(limit=20),
        "feature_flags": {
            "streaming": settings.streaming_enabled,
            "bracket_orders": getattr(settings, "bracket_orders_enabled", True),
            "options": getattr(settings, "options_enabled", False),
            "news": getattr(settings, "news_enabled", True),
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
    return snapshot


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize clients and start trading engine on startup."""
    global alpaca_client, supabase_client, risk_manager, order_manager, position_manager, strategy, market_data_manager, news_client, copilot_config, copilot_context_builder, copilot_router, action_classifier, action_executor, response_formatter, openrouter_client, perplexity_client, streaming_broadcaster, command_handler, ml_shadow_mode
    
    logger.info("🚀 Starting DayTraderAI Backend...")
    
    try:
        # Initialize clients
        alpaca_client = AlpacaClient()
        supabase_client = SupabaseClient()
        
        # Set up Supabase logging handler
        from core.supabase_log_handler import SupabaseLogHandler
        import logging
        supabase_handler = SupabaseLogHandler(supabase_client, source="backend")
        logging.getLogger().addHandler(supabase_handler)
        logger.info("✓ Supabase log handler initialized")
        
        # Initialize AI opportunity finder and sentiment aggregator first
        from scanner.ai_opportunity_finder import get_ai_opportunity_finder
        from indicators.sentiment_aggregator import get_sentiment_aggregator
        
        ai_finder = get_ai_opportunity_finder()
        sentiment_aggregator = get_sentiment_aggregator(alpaca_client, ai_finder)
        logger.info("✓ Sentiment aggregator initialized with dual-source validation")
        
        # Initialize risk manager with sentiment aggregator
        risk_manager = RiskManager(alpaca_client, sentiment_aggregator=sentiment_aggregator)
        order_manager = OrderManager(alpaca_client, supabase_client, risk_manager)
        position_manager = PositionManager(alpaca_client, supabase_client)
        market_data_manager = MarketDataManager(alpaca_client, supabase_client)
        
        # Initialize ML shadow mode first (before strategy)
        ml_shadow_mode = MLShadowMode(supabase_client, ml_weight=0.0)
        logger.info("🤖 ML Shadow Mode initialized (weight: 0.0 - learning only)")
        
        # Initialize strategy with ML shadow mode
        strategy = EMAStrategy(order_manager, ml_shadow_mode=ml_shadow_mode)
        
        # Try to initialize news client, but don't fail if not configured
        try:
            news_client = NewsClient()
            logger.info("✓ News client initialized")
        except Exception as e:
            logger.warning(f"⚠️  News client not available: {e}")
            news_client = None
        
        options_client = OptionsClient(alpaca_client) if settings.options_enabled else None
        copilot_config = build_copilot_config(settings)
        copilot_context_builder = CopilotContextBuilder(
            alpaca_client=alpaca_client,
            supabase_client=supabase_client,
            market_data_manager=market_data_manager,
            news_client=news_client,
            risk_manager=risk_manager,
            config=copilot_config,
        )
        copilot_router = QueryRouter(copilot_config)
        action_classifier = ActionClassifier()
        action_executor = ActionExecutor(
            alpaca_client=alpaca_client,
            trading_engine=None,  # Will be set after engine is created
            position_manager=position_manager,
            risk_manager=risk_manager,
            market_data_manager=market_data_manager,
            news_client=news_client,
        )
        response_formatter = ResponseFormatter()
        openrouter_client = OpenRouterClient()
        perplexity_client = PerplexityClient()
        command_handler = CommandHandler(alpaca_client)
        streaming_broadcaster = StreamingBroadcaster()
        await streaming_broadcaster.start(snapshot_builder=build_streaming_snapshot)
        
        # Attach WebSocket log handler
        from utils.websocket_logger import WebSocketLogHandler
        ws_log_handler = WebSocketLogHandler(streaming_broadcaster)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ws_log_handler.setFormatter(formatter)
        logging.getLogger().addHandler(ws_log_handler)
        logger.info("✓ WebSocket log handler attached")
        
        # Set global ML shadow mode for API routes
        from api.ml_routes import set_ml_shadow_mode
        set_ml_shadow_mode(ml_shadow_mode)
        
        # Initialize trading engine
        engine = TradingEngine(
            alpaca_client=alpaca_client,
            supabase_client=supabase_client,
            risk_manager=risk_manager,
            order_manager=order_manager,
            position_manager=position_manager,
            strategy=strategy,
            market_data_manager=market_data_manager,
            options_client=options_client,
            stream_manager=stream_manager,
            streaming_broadcaster=streaming_broadcaster,
            snapshot_builder=build_streaming_snapshot,
            ml_shadow_mode=ml_shadow_mode,
        )
        set_trading_engine(engine)
        
        # Inject cooldown manager into position manager (Sprint 6)
        position_manager.cooldown_manager = engine.cooldown_manager
        
        # Set trading engine reference in action executor
        if action_executor:
            action_executor._engine = engine
        
        # Sync initial state
        await sync_state()
        if streaming_broadcaster:
            await streaming_broadcaster.enqueue({"type": "snapshot", "payload": build_streaming_snapshot()})
        
        # Start trading engine in background
        asyncio.create_task(engine.start())
        
        logger.info("✅ Backend initialized successfully")
        logger.info("✅ Trading engine started")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize backend: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down...")
    engine = get_trading_engine()
    if engine:
        await engine.stop()
    if streaming_broadcaster:
        await streaming_broadcaster.stop()


app = FastAPI(
    title="DayTraderAI Backend",
    description="Production trading bot backend",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:5174", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from api.report_routes import router as report_router
from api.adaptive_routes import router as adaptive_router
from api.ml_routes import router as ml_router
app.include_router(report_router)
app.include_router(adaptive_router)
app.include_router(ml_router)

@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    if not streaming_broadcaster or not settings.streaming_enabled:
        await websocket.accept()
        await websocket.send_json(
            {
                "type": "error",
                "message": "Streaming disabled",
            }
        )
        await websocket.close()
        return

    await streaming_broadcaster.connect(websocket)
    await streaming_broadcaster.listen(websocket)


async def sync_state():
    """Sync state from Alpaca and Supabase."""
    try:
        # Get account info
        account = alpaca_client.get_account()
        equity = float(account.equity)
        cash = float(account.cash)
        buying_power = float(account.buying_power)
        
        # Get positions from Alpaca
        alpaca_positions = alpaca_client.get_positions()
        
        # Update state
        for pos in alpaca_positions:
            position = StatePosition(
                symbol=pos.symbol,
                qty=int(pos.qty),
                side='buy' if int(pos.qty) > 0 else 'sell',
                avg_entry_price=float(pos.avg_entry_price),
                current_price=float(pos.current_price),
                unrealized_pl=float(pos.unrealized_pl),
                unrealized_pl_pct=float(pos.unrealized_plpc) * 100,
                market_value=float(pos.market_value),
                stop_loss=0,  # TODO: Load from DB
                take_profit=0,  # TODO: Load from DB
                entry_time=datetime.utcnow()
            )
            trading_state.update_position(position)
        
        # Update metrics
        trading_state.update_metrics(
            equity=equity,
            cash=cash,
            buying_power=buying_power,
            open_positions=len(alpaca_positions)
        )
        
        logger.info(f"State synced: {len(alpaca_positions)} positions, ${equity:.2f} equity")
        
    except Exception as e:
        logger.error(f"Failed to sync state: {e}")


# API Routes


class ChatMessagePayload(BaseModel):
    role: str
    content: str


class ChatRequestPayload(BaseModel):
    message: str
    history: List[ChatMessagePayload] = []
    trace_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


def _history_to_messages(history: List[ChatMessagePayload]) -> List[Dict[str, str]]:
    messages: List[Dict[str, str]] = []
    for item in history[-6:]:
        if item.role in {"user", "assistant"} and item.content:
            messages.append({"role": item.role, "content": item.content})
    return messages


def _format_context_for_ai(context: Dict[str, Any], *, include_news: bool = True) -> str:
    lines: List[str] = []
    account = context.get("account", {})
    lines.append(
        f"ACCOUNT | Equity ${account.get('equity', 0):,.2f} | Cash ${account.get('cash', 0):,.2f} | "
        f"Buying power ${account.get('buying_power', 0):,.2f} | Daily P/L {account.get('daily_pl', 0):+.2f} "
        f"({account.get('daily_pl_pct', 0):+.2f}%)"
    )
    performance = context.get("performance", {})
    if performance:
        lines.append(
            f"PERFORMANCE | Win rate {performance.get('win_rate', 0)*100:.1f}% | Profit factor "
            f"{performance.get('profit_factor', 0):.2f} | Sharpe {performance.get('sharpe_ratio', 0):.2f}"
        )

    positions = context.get("positions", []) or []
    if positions:
        lines.append("POSITIONS (top 6 by exposure):")
        for position in positions[:6]:
            lines.append(
                f"- {position['symbol']} {position['side'].upper()} {position['qty']} @ {position['avg_entry_price']:.2f} | "
                f"Px {position['current_price']:.2f} | P/L {position['unrealized_pl']:+.2f} "
                f"({position['unrealized_pl_pct']:+.2f}%) | SL {position['stop_loss']:.2f} | TP {position['take_profit']:.2f}"
            )
    else:
        lines.append("POSITIONS | No open positions.")

    market = context.get("market", {})
    macro = market.get("macro", {})
    if macro:
        lines.append(
            f"MARKET | SPY trend {macro.get('spy_trend', 'unknown')} @ {macro.get('spy_price', 0):.2f} | "
            f"VIX {macro.get('vix_trend', 'unknown')} @ {macro.get('vix_level', 0):.2f}"
        )

    if market.get("symbols"):
        focus_symbols = [sym for sym in market["symbols"] if sym.get("focus")]
        if focus_symbols:
            lines.append("FOCUS TECHNICALS:")
            for symbol_info in focus_symbols[:5]:
                lines.append(
                    f"- {symbol_info['symbol']}: price {symbol_info['price']:.2f}, "
                    f"EMA9 {symbol_info['ema_short']:.2f}, EMA21 {symbol_info['ema_long']:.2f}, "
                    f"RSI {symbol_info['rsi']:.1f}, signal {symbol_info['signal']}"
                )

    if include_news and context.get("news"):
        lines.append("NEWS (last 24h):")
        for article in context["news"][:5]:
            lines.append(
                f"- {article.get('headline')} [{article.get('sentiment')}] ({article.get('source')})"
            )

    risk = context.get("risk", {})
    if risk:
        lines.append(
            f"RISK | Open positions: {risk.get('open_positions', 0)}/{risk.get('max_positions', 0)} | "
            f"Equity utilisation {risk.get('equity_utilisation', 0)*100:.1f}% | "
            f"Risk per trade {risk.get('risk_per_trade_pct', 0)*100:.2f}% | "
            f"Circuit breaker {'ACTIVE' if risk.get('circuit_breaker_triggered') else 'clear'}"
        )

    return "\n".join(lines)


def _serialize_route(route: QueryRoute) -> Dict[str, Any]:
    return {
        "category": route.category,
        "targets": route.targets,
        "confidence": route.confidence,
        "symbols": route.symbols,
        "notes": route.notes,
    }


def _detect_query_type(message: str) -> str:
    """Detect the type of query for better prompt selection."""
    message_lower = message.lower()
    
    # Portfolio/performance queries
    if any(kw in message_lower for kw in ["portfolio", "performance", "how am i doing", "how is my", "last month", "last week", "returns", "p/l", "pnl"]):
        if any(kw in message_lower for kw in ["month", "week", "history", "historical"]):
            return "historical_performance"
        return "portfolio_analysis"
    
    # Status queries
    if any(kw in message_lower for kw in ["status", "summary", "account", "balance", "equity"]):
        return "status"
    
    # Opportunities queries
    if any(kw in message_lower for kw in ["opportunities", "opportunity", "ideas", "signals", "setups", "trades", "what to buy", "what should i"]):
        return "opportunities"
    
    # Trade analysis
    if any(kw in message_lower for kw in ["should i buy", "should i sell", "analyze", "analysis", "entry", "exit"]):
        return "trade_analysis"
    
    # Quick queries (short questions)
    if len(message.split()) < 10:
        return "quick_query"
    
    return "default"


def _format_account_summary(context: Dict[str, Any]) -> str:
    """Format a clean account summary response."""
    account = context.get("account", {})
    positions = context.get("positions", [])
    performance = context.get("performance", {})
    risk = context.get("risk", {})
    
    equity = account.get("equity", 0)
    cash = account.get("cash", 0)
    buying_power = account.get("buying_power", 0)
    daily_pl = account.get("daily_pl", 0)
    daily_pl_pct = account.get("daily_pl_pct", 0)
    
    pl_emoji = "📈" if daily_pl >= 0 else "📉"
    pl_sign = "+" if daily_pl >= 0 else ""
    
    lines = [
        f"{pl_emoji} **Account Summary**",
        f"- Equity: ${equity:,.2f}",
        f"- Cash: ${cash:,.2f}",
        f"- Buying Power: ${buying_power:,.2f}",
        f"- Daily P/L: {pl_sign}${daily_pl:,.2f} ({pl_sign}{daily_pl_pct:.2f}%)",
        f"- Open Positions: {len(positions)}/{risk.get('max_positions', 20)}",
        f"- Win Rate: {performance.get('win_rate', 0)*100:.1f}%",
        f"- Profit Factor: {performance.get('profit_factor', 0):.2f}",
        f"- Circuit Breaker: {'⚠️ ACTIVE' if risk.get('circuit_breaker_triggered') else '✓ Clear'}",
    ]
    
    # Add top positions
    if positions:
        winners = [p for p in positions if p.get("unrealized_pl", 0) > 0]
        losers = [p for p in positions if p.get("unrealized_pl", 0) < 0]
        
        if winners:
            winners.sort(key=lambda x: x.get("unrealized_pl", 0), reverse=True)
            lines.append("\n📈 **Top Winners**")
            for p in winners[:3]:
                pl = p.get("unrealized_pl", 0)
                lines.append(f"- {p['symbol']}: +${pl:,.2f} (+{p.get('unrealized_pl_pct', 0):.1f}%)")
        
        if losers:
            losers.sort(key=lambda x: x.get("unrealized_pl", 0))
            lines.append("\n📉 **Underperformers**")
            for p in losers[:3]:
                pl = p.get("unrealized_pl", 0)
                lines.append(f"- {p['symbol']}: ${pl:,.2f} ({p.get('unrealized_pl_pct', 0):.1f}%)")
    
    return "\n".join(lines)


def _clean_ai_response(response: str) -> str:
    """Clean up AI response to remove verbose disclaimers and limitations."""
    # Remove common verbose patterns
    patterns_to_remove = [
        r"I appreciate the detailed request.*?limitations.*?\n\n",
        r"## Current Data Limitations.*?(?=##|\Z)",
        r"I need to be transparent about.*?\n\n",
        r"The search results provided contain.*?\n\n",
        r"Based on the available data.*?(?=\n\n|\Z)",
        r"Would you like me to.*?\Z",
        r"For the level of analysis.*?\Z",
    ]
    
    import re
    cleaned = response
    for pattern in patterns_to_remove:
        cleaned = re.sub(pattern, "", cleaned, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove excessive newlines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    
    return cleaned.strip()


def _build_perplexity_prompt(context: Dict[str, Any], message: str, route: Optional[QueryRoute] = None) -> str:
    summary = context.get("summary", "")
    highlights = context.get("highlights", [])
    focus_symbols = context.get("symbols", [])
    
    # Check query type
    message_lower = message.lower()
    is_opportunities = any(kw in message_lower for kw in ["opportunities", "opportunity", "ideas", "signals", "setups", "trades"])
    is_deep_analysis = route and route.category == "deep_analysis"

    if is_deep_analysis and route and route.symbols:
        # Deep analysis prompt for specific symbols
        symbols_str = ", ".join(route.symbols)
        
        prompt_lines = [
            f"Conduct COMPREHENSIVE DEEP-DIVE ANALYSIS for: {symbols_str}",
            "",
            "For EACH symbol, provide:",
            "",
            "1. TECHNICAL ANALYSIS:",
            "   - Current price, 52-week range, % from highs/lows",
            "   - Key support and resistance levels",
            "   - RSI, MACD, moving averages (20/50/200 day)",
            "   - Volume analysis (vs average)",
            "   - Chart patterns (if any)",
            "   - Bollinger Bands position",
            "   - Momentum assessment (short/medium/long term)",
            "",
            "2. FUNDAMENTAL ANALYSIS:",
            "   - Latest financials (revenue, net income, margins)",
            "   - Valuation metrics (P/E, P/B, PEG, P/S, EV/EBITDA)",
            "   - Growth rates (revenue, EPS, FCF)",
            "   - Balance sheet health (debt/equity, current ratio, cash)",
            "   - Profitability (ROE, ROA, profit margins)",
            "   - Fair value assessment",
            "",
            "3. SENTIMENT & NEWS:",
            "   - Recent news headlines (last 7 days) with dates",
            "   - Overall news sentiment (positive/negative/neutral)",
            "   - Analyst ratings breakdown",
            "   - Average price target and upside/downside",
            "   - Social media sentiment (Reddit, Twitter, StockTwits)",
            "",
            "4. OPTIONS ANALYSIS:",
            "   - Unusual options activity (if any)",
            "   - Put/call ratio",
            "   - Implied volatility and IV rank",
            "   - Notable large trades (calls/puts)",
            "",
            "5. INSIDER & INSTITUTIONAL:",
            "   - Recent insider transactions (last 3 months)",
            "   - Net insider buying/selling",
            "   - Institutional ownership %",
            "   - Recent institutional changes",
            "   - Top institutional holders",
            "",
            "6. EARNINGS:",
            "   - Next earnings date",
            "   - EPS estimate and whisper number",
            "   - Recent earnings surprises",
            "   - Earnings trend",
            "",
            "7. COMPETITIVE LANDSCAPE:",
            "   - Main competitors",
            "   - Market share",
            "   - Competitive advantages",
            "   - Industry trends",
            "",
            "8. RISK FACTORS:",
            "   - Beta and volatility",
            "   - Max drawdown (1 year)",
            "   - Key risks (regulatory, competitive, market)",
            "",
            "9. TRADE SETUP:",
            "   - Bullish entry zone",
            "   - Stop loss level",
            "   - Target prices (T1, T2)",
            "   - Risk/reward ratio",
            "   - Time horizon",
            "",
            "10. BOTTOM LINE:",
            "   - Overall rating (Strong Buy/Buy/Hold/Sell/Strong Sell)",
            "   - Confidence level",
            "   - Key catalyst to watch",
            "   - Next action recommendation",
            "",
            "Provide SPECIFIC NUMBERS, DATES, and SOURCES for all data.",
            "Use real-time market data.",
            "Be comprehensive but concise.",
        ]
        
        if len(route.symbols) > 1:
            prompt_lines.extend([
                "",
                "MULTI-SYMBOL ANALYSIS:",
                "- Compare all symbols side-by-side",
                "- Rank by attractiveness",
                "- Show correlation between symbols",
                "- Suggest portfolio allocation",
            ])
        
        return "\n".join(prompt_lines)
    
    elif is_opportunities:
        # Specialized prompt for opportunities research
        account = context.get("account", {})
        cash = account.get("cash", 0)
        equity = account.get("equity", 0)
        positions = context.get("positions", [])
        
        # Get current sector exposure
        sectors = {}
        for pos in positions:
            symbol = pos.get("symbol")
            value = abs(pos.get("market_value", 0))
            # Simple sector mapping (you can enhance this)
            if symbol in ["AAPL", "MSFT", "GOOGL", "META", "AMZN"]:
                sectors["Tech"] = sectors.get("Tech", 0) + value
            elif symbol in ["TSLA"]:
                sectors["EV/Auto"] = sectors.get("EV/Auto", 0) + value
            elif symbol in ["NVDA", "AMD"]:
                sectors["Semiconductors"] = sectors.get("Semiconductors", 0) + value
        
        prompt_lines = [
            "You are a market research analyst finding the BEST trading opportunities RIGHT NOW.",
            "",
            "RESEARCH MISSION:",
            "Find the top 5-7 trading opportunities across different categories:",
            "1. High-momentum stocks (strong uptrend, breaking out)",
            "2. Undervalued stocks (oversold, potential reversal)",
            "3. Sector leaders (strongest in their sector)",
            "4. Dividend/value plays (stable, defensive)",
            "5. Options opportunities (high IV, earnings plays)",
            "",
            "CURRENT PORTFOLIO CONTEXT:",
            f"- Available cash: ${cash:,.0f}",
            f"- Total equity: ${equity:,.0f}",
            f"- Open positions: {len(positions)}",
        ]
        
        if sectors:
            prompt_lines.append("- Current sector exposure:")
            for sector, value in sectors.items():
                pct = (value / equity * 100) if equity > 0 else 0
                prompt_lines.append(f"  • {sector}: ${value:,.0f} ({pct:.1f}%)")
        
        prompt_lines.extend([
            "",
            "RESEARCH REQUIREMENTS:",
            "For each opportunity, provide:",
            "- Symbol and company name",
            "- Current price and recent price action",
            "- Why it's a good opportunity RIGHT NOW (catalyst, technical setup, fundamentals)",
            "- Suggested entry price range",
            "- Suggested stop loss level",
            "- Suggested take profit target",
            "- Risk/reward ratio",
            "- Position size recommendation (% of portfolio)",
            "- Time horizon (day trade, swing, position)",
            "- Asset class (stock, ETF, option strategy)",
            "",
            "DIVERSIFICATION FOCUS:",
            "- Suggest opportunities in sectors NOT currently overweight",
            "- Include at least one defensive/hedge position",
            "- Consider market cap diversity (large, mid, small cap)",
            "- Include at least one options strategy if appropriate",
            "",
            "Use real-time market data, recent news, earnings calendars, and technical analysis.",
            "Cite your sources for each recommendation.",
        ])
        
        return "\n".join(prompt_lines)
    
    else:
        # Original news-focused prompt
        prompt_lines = [
            "You are the DayTraderAI market intelligence analyst. Use the structured data below to gather the most recent, factual news.",
            "",
            "Trading system highlights:",
        ]
        prompt_lines.extend(f"- {item}" for item in highlights[:5])

        if focus_symbols:
            prompt_lines.append(f"Focus symbols: {', '.join(focus_symbols)}")

        prompt_lines.append("")
        prompt_lines.append("System summary:")
        prompt_lines.append(summary or "(summary unavailable)")

        prompt_lines.append("")
        prompt_lines.append("User query:")
        prompt_lines.append(message.strip())

        prompt_lines.append("")
        prompt_lines.append(
            "Respond with a concise market intelligence briefing. Include bullet points with key takeaways, "
            "note major catalysts, and provide source citations."
        )
        return "\n".join(prompt_lines)

@app.get("/")
async def root():
    return {
        "service": "DayTraderAI Backend",
        "status": "running",
        "version": "1.0.0",
        "trading_enabled": trading_state.is_trading_allowed()
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    try:
        # Check Alpaca connection
        account = alpaca_client.get_account()
        alpaca_ok = account is not None
        
        # Check market status
        market_open = alpaca_client.is_market_open()
        
        return {
            "status": "healthy",
            "alpaca": "connected" if alpaca_ok else "disconnected",
            "market": "open" if market_open else "closed",
            "trading_enabled": trading_state.is_trading_allowed(),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/market/status")
async def get_market_status():
    """Get detailed market status with countdown timers."""
    try:
        from datetime import timezone
        import pytz
        
        # Get current time
        now_utc = datetime.now(timezone.utc)
        
        # Market timezone (Eastern Time)
        market_tz = pytz.timezone('America/New_York')
        now_market = now_utc.astimezone(market_tz)
        
        # Check if market is open
        is_open = alpaca_client.is_market_open()
        
        # Get market clock from Alpaca
        clock = alpaca_client.get_clock()
        
        # Calculate next open/close times
        next_open = clock.next_open
        next_close = clock.next_close
        
        # Calculate seconds until next event
        if is_open:
            closes_in = int((next_close - now_utc).total_seconds())
            opens_in = None
        else:
            opens_in = int((next_open - now_utc).total_seconds())
            closes_in = None
        
        return {
            "isOpen": is_open,
            "opensIn": opens_in,
            "closesIn": closes_in,
            "nextOpen": next_open.isoformat() if next_open else None,
            "nextClose": next_close.isoformat() if next_close else None,
            "currentTime": now_utc.isoformat(),
            "marketTime": now_market.isoformat(),
            "timezone": "America/New_York"
        }
    except Exception as e:
        logger.error(f"Failed to get market status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/account")
async def get_account():
    """Get account information."""
    try:
        account = alpaca_client.get_account()
        return {
            "equity": float(account.equity),
            "cash": float(account.cash),
            "buying_power": float(account.buying_power),
            "portfolio_value": float(account.portfolio_value),
            "last_equity": float(account.last_equity),
            "currency": account.currency
        }
    except Exception as e:
        logger.error(f"Failed to get account: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/positions")
async def get_positions():
    """Get all positions."""
    positions = trading_state.get_all_positions()
    return [
        {
            "symbol": p.symbol,
            "qty": p.qty,
            "side": p.side,
            "avg_entry_price": p.avg_entry_price,
            "current_price": p.current_price,
            "unrealized_pl": p.unrealized_pl,
            "unrealized_pl_pct": p.unrealized_pl_pct,
            "market_value": p.market_value,
            "stop_loss": p.stop_loss,
            "take_profit": p.take_profit
        }
        for p in positions
    ]


@app.get("/orders")
async def get_orders():
    """Get all orders."""
    orders = trading_state.get_all_orders()
    return [
        {
            "order_id": o.order_id,
            "symbol": o.symbol,
            "qty": o.qty,
            "side": o.side,
            "type": o.type,
            "status": o.status,
            "filled_qty": o.filled_qty,
            "filled_avg_price": o.filled_avg_price,
            "submitted_at": o.submitted_at.isoformat()
        }
        for o in orders
    ]


@app.get("/metrics")
async def get_metrics():
    """Get trading metrics."""
    metrics = trading_state.get_metrics()
    return {
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
        "circuit_breaker_triggered": metrics.circuit_breaker_triggered
    }


@app.post("/orders/submit")
async def submit_order(
    symbol: str,
    side: str,
    qty: int,
    reason: str = "",
    price: Optional[float] = None,
    take_profit: Optional[float] = None,
    stop_loss: Optional[float] = None,
):
    """Submit a new order."""
    try:
        order = order_manager.submit_order(
            symbol,
            side,
            qty,
            reason,
            price=price,
            take_profit_price=take_profit,
            stop_loss_price=stop_loss,
        )
        if order:
            return {
                "success": True,
                "order_id": order.order_id,
                "message": f"Order submitted: {side} {qty} {symbol}"
            }
        else:
            return {
                "success": False,
                "message": "Order rejected by risk manager"
            }
    except Exception as e:
        logger.error(f"Failed to submit order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/orders/{order_id}/cancel")
async def cancel_order(order_id: str):
    """Cancel an order."""
    try:
        success = order_manager.cancel_order(order_id)
        return {
            "success": success,
            "message": "Order canceled" if success else "Failed to cancel order"
        }
    except Exception as e:
        logger.error(f"Failed to cancel order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/positions/{symbol}/close")
async def close_position(symbol: str):
    """Close a position."""
    try:
        success = alpaca_client.close_position(symbol)
        if success:
            trading_state.remove_position(symbol)
        return {
            "success": success,
            "message": f"Position closed: {symbol}" if success else "Failed to close position"
        }
    except Exception as e:
        logger.error(f"Failed to close position: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/emergency/stop")
async def emergency_stop():
    """Emergency stop: disable trading and close all positions."""
    try:
        risk_manager.emergency_stop()
        return {
            "success": True,
            "message": "Emergency stop executed"
        }
    except Exception as e:
        logger.error(f"Emergency stop failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/trading/enable")
async def enable_trading():
    """Enable trading."""
    trading_state.enable_trading()
    return {"success": True, "message": "Trading enabled"}


@app.post("/trading/disable")
async def disable_trading():
    """Disable trading."""
    trading_state.disable_trading()
    return {"success": True, "message": "Trading disabled"}


@app.post("/sync")
async def sync():
    """Manually sync state from Alpaca."""
    try:
        await sync_state()
        return {"success": True, "message": "State synced"}
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/logs")
async def get_logs(limit: int = 100):
    """Get recent system logs from Supabase."""
    try:
        if supabase_client:
            logs = supabase_client.get_logs(limit=limit)
            return logs
        else:
            # Fallback to in-memory logs
            logs = trading_state.get_logs(limit=limit)
            return [
                {
                    "id": i,
                    "timestamp": log.timestamp.isoformat(),
                    "level": log.level,
                    "message": log.message,
                    "source": log.source
                }
            for i, log in enumerate(logs)
        ]
    except Exception as e:
        logger.error(f"Failed to get logs: {e}")
        return []


@app.get("/advisories")
async def get_advisories(limit: int = 50):
    """Get recent AI advisories."""
    try:
        advisories = supabase_client.get_advisories(limit=limit)
        return [
            {
                "id": adv.get("id"),
                "timestamp": adv.get("timestamp"),
                "type": adv.get("type", "analysis"),
                "symbol": adv.get("symbol"),
                "content": adv.get("content"),
                "model": adv.get("model"),
                "confidence": adv.get("confidence", 0.5)
            }
            for adv in advisories
        ]
    except Exception as e:
        logger.error(f"Failed to get advisories: {e}")
        return []


@app.get("/analyses")
async def get_analyses(limit: int = 50):
    """Get recent trade analyses."""
    try:
        # Get recent trades with analysis
        trades = supabase_client.get_trades(limit=limit)
        analyses = []
        
        for trade in trades:
            if trade.get("reason"):  # Has analysis
                analyses.append({
                    "id": trade.get("id"),
                    "timestamp": trade.get("timestamp"),
                    "symbol": trade.get("symbol"),
                    "side": trade.get("side"),
                    "action": "entry" if trade.get("entry_time") else "exit",
                    "analysis": trade.get("reason"),
                    "pnl": trade.get("pnl", 0),
                    "pnl_pct": trade.get("pnl_pct", 0)
                })
        
        return analyses
    except Exception as e:
        logger.error(f"Failed to get analyses: {e}")
        return []


@app.post("/chat")
async def chat(request: ChatRequestPayload):
    """Chat with the intelligent copilot assistant."""
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    if not copilot_context_builder or not copilot_router:
        raise HTTPException(status_code=503, detail="Copilot not initialized.")

    # Build context from backend
    context_result: ContextResult = await copilot_context_builder.build_context(request.message)
    
    # Merge frontend-provided context if available (for real-time data)
    if request.context:
        frontend_ctx = request.context
        if frontend_ctx.get("account"):
            context_result.context.setdefault("account", {}).update(frontend_ctx["account"])
        if frontend_ctx.get("positions"):
            context_result.context["positions"] = frontend_ctx["positions"]
        if frontend_ctx.get("market_status"):
            context_result.context.setdefault("market", {})["status"] = frontend_ctx["market_status"]
        if frontend_ctx.get("opportunities"):
            context_result.context["opportunities"] = frontend_ctx["opportunities"]
    
    # NEW: Classify action intent (if enabled)
    if (
        copilot_config
        and copilot_config.action_execution_enabled
        and action_classifier
        and action_executor
        and response_formatter
    ):
        intent: ActionIntent = action_classifier.classify(request.message, context_result.context)
        
        # Route based on intent type
        if intent.intent_type == "execute" and intent.confidence >= copilot_config.action_confidence_threshold:
            # Check for ambiguities
            if intent.ambiguities:
                return {
                    "success": False,
                    "content": "I need clarification:\n" + "\n".join(f"- {amb}" for amb in intent.ambiguities),
                    "provider": "Action Classifier",
                    "confidence": intent.confidence,
                    "requires_clarification": True,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            
            # Execute action
            result: ExecutionResult = await action_executor.execute(intent, context_result.context)
            copilot_response: CopilotResponse = response_formatter.format_execution(result)
            
            # Persist advisory if successful
            if result.success and supabase_client:
                try:
                    supabase_client.insert_advisory({
                        "source": "ActionExecutor",
                        "content": copilot_response.content,
                        "model": "ActionExecutor",
                        "type": "execution",
                        "confidence": 1.0,
                        "symbol": intent.parameters.get("symbol"),
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                except Exception as e:
                    logger.debug(f"Failed to persist advisory: {e}")
            
            return {
                "success": result.success,
                "content": copilot_response.content,
                "provider": "Action Executor",
                "response_type": copilot_response.response_type,
                "details": copilot_response.details,
                "confidence": copilot_response.confidence,
                "metadata": copilot_response.metadata,
                "timestamp": datetime.utcnow().isoformat(),
                "trace_id": request.trace_id,
            }
        
        elif intent.intent_type == "info" and intent.confidence >= copilot_config.action_confidence_threshold:
            # Execute info query
            result: ExecutionResult = await action_executor.execute(intent, context_result.context)
            copilot_response: CopilotResponse = response_formatter.format_execution(result)
            
            return {
                "success": result.success,
                "content": copilot_response.content,
                "provider": "Info Retrieval",
                "response_type": copilot_response.response_type,
                "details": copilot_response.details,
                "confidence": copilot_response.confidence,
                "metadata": copilot_response.metadata,
                "timestamp": datetime.utcnow().isoformat(),
                "trace_id": request.trace_id,
            }
    
    # Fall through to existing LLM routing for advice queries or low confidence
    route: QueryRoute = copilot_router.route(
        request.message, context_result.context, context_result.context.get("symbols", [])
    )

    context_text = _format_context_for_ai(context_result.context)
    history_messages = _history_to_messages(request.history)

    sections: List[Dict[str, str]] = []
    provider_labels: List[str] = []
    notes: List[str] = list(route.notes)
    citations: List[Dict[str, Any]] = []
    success_boost = 0.0

    ai_timeout = (copilot_config.ai_timeout_ms / 1000) if copilot_config else 15.0
    
    # Perplexity needs more time for comprehensive research
    perplexity_timeout = 45.0  # 45 seconds for deep research queries

    # Optional Perplexity pass for news/research
    if "perplexity" in route.targets:
        if perplexity_client and settings.perplexity_api_key:
            perplexity_prompt = _build_perplexity_prompt(context_result.context, request.message, route)
            try:
                perplexity_task = asyncio.wait_for(
                    perplexity_client.search(perplexity_prompt),
                    timeout=perplexity_timeout,
                )
                perplexity_result = await perplexity_task
                if perplexity_result and perplexity_result.get("content"):
                    provider_labels.append(f"Perplexity ({settings.perplexity_default_model})")
                    sections.append(
                        {
                            "title": "Market Intelligence",
                            "content": perplexity_result["content"].strip(),
                        }
                    )
                    citations = perplexity_result.get("citations") or []
                    success_boost += 0.1
                else:
                    notes.append("Perplexity returned no content.")
            except Exception as err:
                import traceback
                error_details = traceback.format_exc()
                logger.error(f"Perplexity query failed: {err}")
                logger.error(f"Perplexity error details: {error_details}")
                notes.append(f"Perplexity query failed: {str(err) or 'Unknown error'}; continuing without news.")
        else:
            notes.append("Perplexity API key missing; skipping news routing.")

    # Detect query type for better prompt selection
    query_type = _detect_query_type(request.message)
    
    # Handle simple status/portfolio queries directly without AI
    if query_type == "status" and not "perplexity" in route.targets:
        # Return formatted account summary directly
        summary_content = _format_account_summary(context_result.context)
        return {
            "success": True,
            "content": summary_content,
            "provider": "Local Context",
            "route": _serialize_route(route),
            "context_summary": context_result.summary,
            "highlights": context_result.highlights,
            "citations": [],
            "notes": ["Direct status query - no AI needed"],
            "confidence": 0.95,
            "symbols": route.symbols,
            "timestamp": datetime.utcnow().isoformat(),
            "trace_id": request.trace_id,
        }

    # Primary OpenRouter analysis
    openrouter_reply = None
    if "openrouter" in route.targets:
        if openrouter_client and settings.openrouter_api_key:
            # Check query type
            message_lower = request.message.lower()
            is_opportunities = any(kw in message_lower for kw in ["opportunities", "opportunity", "ideas", "signals", "setups", "trades"])
            is_deep_analysis = route.category == "deep_analysis"
            
            if is_deep_analysis and sections:
                # Enhanced prompt for deep analysis
                symbols_str = ", ".join(route.symbols) if route.symbols else "symbol(s)"
                system_prompt = get_system_prompt("trade_analysis")
            elif is_opportunities and sections:
                # Enhanced prompt for opportunities with market research
                system_prompt = get_system_prompt("opportunities")
            elif query_type == "portfolio_analysis":
                system_prompt = get_system_prompt("portfolio_analysis")
            elif query_type == "historical_performance":
                system_prompt = get_system_prompt("historical_performance")
            elif query_type == "quick_query":
                system_prompt = get_system_prompt("quick_query")
            else:
                # Default prompt
                system_prompt = get_system_prompt("default")

            user_prompt = (
                f"User question:\n{request.message.strip()}\n\n"
                "<system_context>\n"
                f"{context_text}\n"
                "</system_context>\n"
            )

            if sections:
                latest_news = sections[-1]["content"]
                user_prompt += (
                    "\n<market_intel>\n"
                    f"{latest_news}\n"
                    "</market_intel>\n"
                )

            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(history_messages)
            messages.append({"role": "user", "content": user_prompt})

            try:
                # Use secondary model for copilot (faster) unless deep analysis
                copilot_model = settings.openrouter_secondary_model if not is_deep_analysis else settings.openrouter_primary_model
                openrouter_task = asyncio.wait_for(
                    openrouter_client.chat_completion(
                        messages=messages,
                        model=copilot_model,
                        temperature=settings.openrouter_temperature,
                    ),
                    timeout=ai_timeout,
                )
                openrouter_reply = await openrouter_task
                if openrouter_reply:
                    provider_labels.append(f"OpenRouter ({copilot_model})")
                    sections.append(
                        {
                            "title": "Strategy Guidance",
                            "content": openrouter_reply.strip(),
                        }
                    )
                    success_boost += 0.15
                else:
                    notes.append("OpenRouter returned no content.")
            except Exception as err:
                logger.error(f"OpenRouter analysis failed: {err}")
                notes.append("OpenRouter analysis failed; using fallback summary.")
        else:
            notes.append("OpenRouter API key missing; skipping analysis routing.")

    if not sections:
        sections.append(
            {
                "title": "System Summary",
                "content": context_result.summary or "Unable to generate AI response at this time.",
            }
        )
        provider_labels.append("Local summary")

    confidence = min(0.95, max(0.35, route.confidence + success_boost))
    
    # Format content with markdown
    formatted_sections = []
    for section in sections:
        # Clean up verbose AI responses
        cleaned_content = _clean_ai_response(section['content'])
        formatted_sections.append(f"**{section['title']}**\n\n{cleaned_content}")
    
    content = "\n\n".join(formatted_sections)
    provider_display = ", ".join(provider_labels)

    response_payload = {
        "success": True,
        "content": content,
        "provider": provider_display,
        "route": _serialize_route(route),
        "context_summary": context_result.summary,
        "highlights": context_result.highlights,
        "citations": citations,
        "notes": notes,
        "confidence": confidence,
        "symbols": route.symbols,
        "timestamp": datetime.utcnow().isoformat(),
        "trace_id": request.trace_id,
    }

    # Persist advisory snapshot for audit trail
    try:
        if provider_labels and supabase_client:
            supabase_client.insert_advisory(
                {
                    "source": provider_display,
                    "content": content,
                    "model": provider_display,
                    "type": route.category,
                    "confidence": confidence,
                    "symbol": route.symbols[0] if route.symbols else None,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
    except Exception as err:
        logger.debug(f"Failed to persist advisory: {err}")

    return response_payload


@app.get("/engine/status")
async def get_engine_status():
    """Get trading engine status."""
    engine = get_trading_engine()
    if not engine:
        return {"running": False, "message": "Engine not initialized"}
    
    return {
        "running": engine.is_running,
        "watchlist": engine.watchlist,
        "trading_enabled": trading_state.is_trading_allowed(),
        "market_open": alpaca_client.is_market_open() if alpaca_client else False
    }


@app.post("/engine/start")
async def start_engine(background_tasks: BackgroundTasks):
    """Start the trading engine."""
    engine = get_trading_engine()
    if not engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    
    if engine.is_running:
        return {"success": False, "message": "Engine already running"}
    
    background_tasks.add_task(engine.start)
    return {"success": True, "message": "Engine starting"}


@app.post("/engine/stop")
async def stop_engine():
    """Stop the trading engine."""
    engine = get_trading_engine()
    if not engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    
    if not engine.is_running:
        return {"success": False, "message": "Engine not running"}
    
    await engine.stop()
    return {"success": True, "message": "Engine stopped"}


@app.get("/config")
async def get_config():
    """Get frontend configuration defaults (no secrets)."""
    return {
        "alpaca_base_url": settings.alpaca_base_url,
        "supabase_url": settings.supabase_url,
        "watchlist": command_handler.get_watchlist() if command_handler else settings.watchlist_symbols,
        "max_positions": settings.max_positions,
        "risk_per_trade_pct": settings.risk_per_trade_pct,
        "backend_url": f"http://localhost:{settings.backend_port}",
        "streaming_enabled": settings.streaming_enabled,
        "stream_reconnect_delay": settings.stream_reconnect_delay,
        "bracket_orders_enabled": settings.bracket_orders_enabled,
        "default_take_profit_pct": settings.default_take_profit_pct,
        "default_stop_loss_pct": settings.default_stop_loss_pct,
        "options_enabled": settings.options_enabled,
        "max_options_positions": settings.max_options_positions,
        "options_risk_per_trade_pct": settings.options_risk_per_trade_pct,
    }


@app.get("/regime/status")
async def get_regime_status():
    """Get current market regime status with momentum confirmation."""
    try:
        from trading.regime_manager import RegimeManager
        
        regime_manager = RegimeManager()
        await regime_manager.update_regime()
        
        # Get basic regime summary
        summary = regime_manager.get_regime_summary()
        
        # Try to get momentum-confirmed data
        momentum_manager = regime_manager.get_momentum_confirmed_manager()
        if momentum_manager:
            # Use neutral momentum for summary (actual momentum calculated per-trade)
            momentum_summary = momentum_manager.get_summary(momentum_strength=0.5)
            summary["momentum_confirmed"] = momentum_summary
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting regime status: {e}")
        return {
            "regime": "neutral",
            "index_value": 50,
            "error": str(e)
        }


@app.get("/watchlist")
async def get_watchlist():
    """Get current watchlist."""
    if not command_handler:
        raise HTTPException(status_code=503, detail="Command handler not initialized")
    
    # Build context for position info
    context = {"position_details": _serialize_positions()}
    result = command_handler.view_watchlist(context)
    
    return result


@app.post("/watchlist/add")
async def add_to_watchlist(symbols: List[str]):
    """Add symbols to watchlist."""
    if not command_handler:
        raise HTTPException(status_code=503, detail="Command handler not initialized")
    
    result = command_handler.add_to_watchlist(symbols)
    
    # Update trading engine watchlist
    engine = get_trading_engine()
    if engine:
        engine.watchlist = command_handler.get_watchlist()
    
    return result


@app.post("/watchlist/remove")
async def remove_from_watchlist(symbols: List[str]):
    """Remove symbols from watchlist."""
    if not command_handler:
        raise HTTPException(status_code=503, detail="Command handler not initialized")
    
    # Build context for position info
    context = {"position_details": _serialize_positions()}
    result = command_handler.remove_from_watchlist(symbols, context)
    
    # Update trading engine watchlist
    engine = get_trading_engine()
    if engine:
        engine.watchlist = command_handler.get_watchlist()
    
    return result


@app.post("/watchlist/reset")
async def reset_watchlist():
    """Reset watchlist to default."""
    if not command_handler:
        raise HTTPException(status_code=503, detail="Command handler not initialized")
    
    result = command_handler.reset_watchlist()
    
    # Update trading engine watchlist
    engine = get_trading_engine()
    if engine:
        engine.watchlist = command_handler.get_watchlist()
    
    return result


# Phase 2: Scanner Routes
@app.get("/scanner/opportunities")
async def get_scanner_opportunities(min_score: float = 60.0, limit: int = 20):
    """Get current opportunities from scanner."""
    from api.scanner_routes import get_opportunities
    return await get_opportunities(min_score=min_score, limit=limit)


@app.get("/scanner/watchlist")
async def get_scanner_watchlist():
    """Get dynamic watchlist."""
    from api.scanner_routes import get_dynamic_watchlist
    return await get_dynamic_watchlist()


@app.get("/scanner/summary")
async def get_scanner_summary_endpoint():
    """Get scanner summary."""
    from api.scanner_routes import get_scanner_summary
    return await get_scanner_summary()


@app.post("/scanner/scan")
async def trigger_scanner_scan(symbols: List[str] = None, min_score: float = 60.0):
    """Trigger manual scan."""
    from api.scanner_routes import trigger_scan
    return await trigger_scan(symbols=symbols, min_score=min_score)


@app.get("/scanner/universe")
async def get_scanner_universe():
    """Get stock universe."""
    from api.scanner_routes import get_stock_universe
    return await get_stock_universe()


@app.get("/scanner/universe/{sector}")
async def get_scanner_sector(sector: str):
    """Get stocks by sector."""
    from api.scanner_routes import get_sector_stocks
    return await get_sector_stocks(sector=sector)


@app.get("/health/services")
async def get_services_health():
    """Get health status of all external services."""
    try:
        # Test Alpaca
        alpaca_healthy = False
        try:
            if alpaca_client:
                account = alpaca_client.get_account()
                alpaca_healthy = bool(account)
        except Exception as e:
            logger.debug(f"Alpaca health check failed: {e}")
            pass

        # Test Supabase
        supabase_healthy = False
        try:
            if supabase_client:
                # Try to fetch latest metrics as health check
                metrics = supabase_client.get_latest_metrics()
                supabase_healthy = True
        except Exception as e:
            logger.debug(f"Supabase health check failed: {e}")
            pass

        # OpenRouter - assume healthy if we have the key
        openrouter_healthy = bool(settings.openrouter_api_key)

        # Perplexity - assume healthy if we have the key
        perplexity_healthy = bool(settings.perplexity_api_key)

        return {
            "alpaca": "connected" if alpaca_healthy else "disconnected",
            "supabase": "connected" if supabase_healthy else "disconnected",
            "openrouter": "connected" if openrouter_healthy else "disconnected",
            "perplexity": "connected" if perplexity_healthy else "disconnected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "alpaca": "error",
            "supabase": "error",
            "openrouter": "error",
            "perplexity": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@app.get("/performance")
async def get_performance_history(timeframe: str = "1D", limit: int = 500):
    """Get performance history for charts - simplified to just return Alpaca data."""
    try:
        # Fetch portfolio history from Alpaca
        portfolio_history = alpaca_client.get_portfolio_history(timeframe=timeframe)
        
        if not portfolio_history or len(portfolio_history) == 0:
            logger.warning("No portfolio history available from Alpaca")
            return []
        
        # Return data directly - just add the fields the frontend expects
        result = []
        for point in portfolio_history[-limit:]:  # Limit to last N points
            equity = point['equity']
            result.append({
                "timestamp": point['timestamp'],
                "equity": equity,
                "open": equity,
                "high": equity * 1.001,  # Approximate
                "low": equity * 0.999,   # Approximate
                "close": equity,
                "pnl": 0,
                "winRate": 0,
                "profitFactor": 0,
                "wins": 0,
                "losses": 0
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get performance history: {e}")
        return []


@app.get("/performance/summary")
async def get_performance_summary(period: str = "1M"):
    """Get performance summary for a specific period (1D, 1W, 1M, 3M, YTD, 1Y)."""
    try:
        # Map period to Alpaca timeframe
        period_map = {
            "1D": ("1D", "5Min"),
            "1W": ("1W", "1H"),
            "1M": ("1M", "1D"),
            "3M": ("3M", "1D"),
            "YTD": ("1A", "1D"),
            "1Y": ("1A", "1D"),
        }
        
        alpaca_period, timeframe = period_map.get(period, ("1M", "1D"))
        
        # Get portfolio history
        history = alpaca_client.get_portfolio_history(period=alpaca_period, timeframe=timeframe)
        
        if not history or len(history) < 2:
            return {
                "period": period,
                "start_equity": 0,
                "end_equity": 0,
                "total_return": 0,
                "total_return_pct": 0,
                "high": 0,
                "low": 0,
                "max_drawdown": 0,
                "data_points": 0,
            }
        
        start_equity = history[0].get("equity", 0)
        end_equity = history[-1].get("equity", 0)
        total_return = end_equity - start_equity
        total_return_pct = (total_return / start_equity * 100) if start_equity > 0 else 0
        
        equities = [h.get("equity", 0) for h in history]
        high = max(equities)
        low = min(equities)
        
        # Calculate max drawdown
        peak = equities[0]
        max_drawdown = 0
        for eq in equities:
            if eq > peak:
                peak = eq
            drawdown = (peak - eq) / peak * 100 if peak > 0 else 0
            max_drawdown = max(max_drawdown, drawdown)
        
        # Get trade statistics from Supabase
        trades = []
        if supabase_client:
            try:
                trades = supabase_client.get_trades(limit=500)
            except:
                pass
        
        wins = [t for t in trades if float(t.get("pnl", 0) or 0) > 0]
        losses = [t for t in trades if float(t.get("pnl", 0) or 0) < 0]
        
        win_rate = len(wins) / len(trades) * 100 if trades else 0
        avg_win = sum(float(t.get("pnl", 0) or 0) for t in wins) / len(wins) if wins else 0
        avg_loss = abs(sum(float(t.get("pnl", 0) or 0) for t in losses) / len(losses)) if losses else 0
        profit_factor = (sum(float(t.get("pnl", 0) or 0) for t in wins) / 
                        abs(sum(float(t.get("pnl", 0) or 0) for t in losses))) if losses and sum(float(t.get("pnl", 0) or 0) for t in losses) != 0 else 0
        
        return {
            "period": period,
            "start_equity": start_equity,
            "end_equity": end_equity,
            "total_return": total_return,
            "total_return_pct": total_return_pct,
            "high": high,
            "low": low,
            "max_drawdown": max_drawdown,
            "data_points": len(history),
            "total_trades": len(trades),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": win_rate,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor,
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance summary: {e}")
        return {
            "period": period,
            "error": str(e),
        }


def transform_portfolio_to_ohlc(
    portfolio_data: List[Dict],
    current_metrics: Dict,
    limit: int = 100
) -> List[Dict]:
    """
    Transform Alpaca portfolio history to OHLC candlestick format.
    
    For each time period:
    - open: equity at period start
    - high: max equity during period (approximated as equity * 1.001)
    - low: min equity during period (approximated as equity * 0.999)
    - close: equity at period end
    """
    result = []
    
    # Limit data points
    data_to_process = portfolio_data[-limit:] if len(portfolio_data) > limit else portfolio_data
    
    for point in data_to_process:
        equity = point['equity']
        profit_loss = point.get('profit_loss', 0)
        profit_loss_pct = point.get('profit_loss_pct', 0)
        
        # For OHLC, we approximate high/low since Alpaca gives us point values
        # In reality, these would be the actual high/low during the period
        # Add small variance to create candlestick effect
        high = equity * 1.001
        low = equity * 0.999
        
        result.append({
            "timestamp": point['timestamp'].isoformat() if hasattr(point['timestamp'], 'isoformat') else point['timestamp'],
            "equity": equity,
            "open": equity,
            "high": high,
            "low": low,
            "close": equity,
            "daily_pl": profit_loss,
            "daily_pl_pct": profit_loss_pct,
            "win_rate": current_metrics.win_rate,
            "profit_factor": current_metrics.profit_factor,
            "wins": current_metrics.wins,
            "losses": current_metrics.losses
        })
    
    return result


# API v1 Routes (for frontend compatibility)
@app.get("/api/v1/portfolio")
async def get_portfolio_v1():
    """Get portfolio/account information (v1 API)."""
    try:
        account = alpaca_client.get_account()
        positions = trading_state.get_all_positions()
        metrics = trading_state.get_metrics()
        
        return {
            "account": {
                "equity": float(account.equity),
                "cash": float(account.cash),
                "buying_power": float(account.buying_power),
                "portfolio_value": float(account.portfolio_value),
                "last_equity": float(account.last_equity),
                "currency": account.currency
            },
            "metrics": {
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
                "max_positions": metrics.max_positions
            },
            "positions": [
                {
                    "symbol": p.symbol,
                    "qty": p.qty,
                    "side": p.side,
                    "avg_entry_price": p.avg_entry_price,
                    "current_price": p.current_price,
                    "unrealized_pl": p.unrealized_pl,
                    "unrealized_pl_pct": p.unrealized_pl_pct,
                    "market_value": p.market_value,
                    "stop_loss": p.stop_loss,
                    "take_profit": p.take_profit
                }
                for p in positions
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/positions")
async def get_positions_v1():
    """Get all positions (v1 API)."""
    positions = trading_state.get_all_positions()
    return [
        {
            "symbol": p.symbol,
            "qty": p.qty,
            "side": p.side,
            "avg_entry_price": p.avg_entry_price,
            "current_price": p.current_price,
            "unrealized_pl": p.unrealized_pl,
            "unrealized_pl_pct": p.unrealized_pl_pct,
            "market_value": p.market_value,
            "stop_loss": p.stop_loss,
            "take_profit": p.take_profit
        }
        for p in positions
    ]


@app.get("/api/v1/orders")
async def get_orders_v1():
    """Get all orders (v1 API)."""
    orders = trading_state.get_all_orders()
    return [
        {
            "order_id": o.order_id,
            "symbol": o.symbol,
            "qty": o.qty,
            "side": o.side,
            "type": o.type,
            "status": o.status,
            "filled_qty": o.filled_qty,
            "filled_avg_price": o.filled_avg_price,
            "submitted_at": o.submitted_at.isoformat() if o.submitted_at else None
        }
        for o in orders
    ]


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.backend_port,
        reload=False,  # Disable reload for production
        log_level=settings.log_level.lower()
    )
