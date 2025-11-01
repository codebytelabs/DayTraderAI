from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import asyncio
from datetime import datetime
from typing import Optional

from config import settings
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
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Global clients
alpaca_client: Optional[AlpacaClient] = None
supabase_client: Optional[SupabaseClient] = None
risk_manager: Optional[RiskManager] = None
order_manager: Optional[OrderManager] = None
position_manager: Optional[PositionManager] = None
strategy: Optional[EMAStrategy] = None
market_data_manager: Optional[MarketDataManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize clients and start trading engine on startup."""
    global alpaca_client, supabase_client, risk_manager, order_manager, position_manager, strategy, market_data_manager
    
    logger.info("🚀 Starting DayTraderAI Backend...")
    
    try:
        # Initialize clients
        alpaca_client = AlpacaClient()
        supabase_client = SupabaseClient()
        risk_manager = RiskManager(alpaca_client)
        order_manager = OrderManager(alpaca_client, supabase_client, risk_manager)
        position_manager = PositionManager(alpaca_client, supabase_client)
        strategy = EMAStrategy(order_manager)
        market_data_manager = MarketDataManager(alpaca_client, supabase_client)
        
        # Initialize trading engine
        engine = TradingEngine(
            alpaca_client=alpaca_client,
            supabase_client=supabase_client,
            risk_manager=risk_manager,
            order_manager=order_manager,
            position_manager=position_manager,
            strategy=strategy,
            market_data_manager=market_data_manager
        )
        set_trading_engine(engine)
        
        # Sync initial state
        await sync_state()
        
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


app = FastAPI(
    title="DayTraderAI Backend",
    description="Production trading bot backend",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
async def submit_order(symbol: str, side: str, qty: int, reason: str = ""):
    """Submit a new order."""
    try:
        order = order_manager.submit_order(symbol, side, qty, reason)
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


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.backend_port,
        reload=False,  # Disable reload for production
        log_level=settings.log_level.lower()
    )
