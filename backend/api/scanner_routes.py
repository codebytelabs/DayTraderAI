"""API routes for opportunity scanner (Phase 2)."""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from trading.trading_engine import get_trading_engine
from scanner.stock_universe import StockUniverse
from utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/scanner", tags=["scanner"])


@router.get("/opportunities")
async def get_opportunities(
    min_score: float = Query(60.0, description="Minimum score threshold"),
    limit: int = Query(20, description="Maximum number of results")
):
    """Get current opportunities from last scan."""
    try:
        engine = get_trading_engine()
        if not engine or not engine.scanner:
            raise HTTPException(status_code=503, detail="Scanner not available")
        
        opportunities = engine.scanner.get_top_opportunities(n=limit)
        
        # Filter by min score
        filtered = [opp for opp in opportunities if opp['score'] >= min_score]
        
        return {
            "success": True,
            "count": len(filtered),
            "opportunities": filtered,
            "last_scan": engine.scanner.last_scan_time.isoformat() if engine.scanner.last_scan_time else None
        }
        
    except Exception as e:
        logger.error(f"Error getting opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/watchlist")
async def get_dynamic_watchlist():
    """Get current dynamic watchlist."""
    try:
        engine = get_trading_engine()
        if not engine:
            raise HTTPException(status_code=503, detail="Trading engine not available")
        
        return {
            "success": True,
            "watchlist": engine.watchlist,
            "dynamic_mode": engine.use_dynamic_watchlist,
            "count": len(engine.watchlist)
        }
        
    except Exception as e:
        logger.error(f"Error getting watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_scanner_summary():
    """Get scanner summary statistics."""
    try:
        engine = get_trading_engine()
        if not engine or not engine.scanner:
            raise HTTPException(status_code=503, detail="Scanner not available")
        
        summary = engine.scanner.get_opportunity_summary()
        
        return {
            "success": True,
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan")
async def trigger_scan(
    symbols: Optional[List[str]] = None,
    min_score: float = Query(60.0, description="Minimum score threshold")
):
    """Manually trigger an opportunity scan."""
    try:
        engine = get_trading_engine()
        if not engine or not engine.scanner:
            raise HTTPException(status_code=503, detail="Scanner not available")
        
        logger.info(f"Manual scan triggered (symbols: {symbols or 'high priority'})")
        
        # Run scan
        opportunities = await engine.scanner.scan_universe(
            symbols=symbols,
            min_score=min_score
        )
        
        return {
            "success": True,
            "count": len(opportunities),
            "opportunities": opportunities[:20],  # Return top 20
            "scanned_at": engine.scanner.last_scan_time.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error triggering scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-discover")
async def trigger_ai_discovery(
    min_score: float = Query(60.0, description="Minimum score threshold")
):
    """Manually trigger AI opportunity discovery (bypasses 1-hour cooldown)."""
    try:
        engine = get_trading_engine()
        if not engine:
            raise HTTPException(status_code=503, detail="Trading engine not available")
        
        logger.info("🤖 Manual AI discovery triggered")
        
        # Force AI discovery
        await engine._run_scanner_loop(force=True)
        
        return {
            "success": True,
            "watchlist": engine.watchlist,
            "count": len(engine.watchlist),
            "message": "AI discovery completed and watchlist updated"
        }
        
    except Exception as e:
        logger.error(f"Error triggering AI discovery: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/universe")
async def get_stock_universe():
    """Get stock universe information."""
    try:
        stats = StockUniverse.get_stats()
        full_universe = StockUniverse.get_full_universe()
        high_priority = StockUniverse.get_high_priority()
        
        return {
            "success": True,
            "stats": stats,
            "full_universe": full_universe,
            "high_priority": high_priority
        }
        
    except Exception as e:
        logger.error(f"Error getting universe: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/universe/{sector}")
async def get_sector_stocks(sector: str):
    """Get stocks by sector."""
    try:
        stocks = StockUniverse.get_by_sector(sector)
        
        if not stocks:
            raise HTTPException(status_code=404, detail=f"Sector '{sector}' not found")
        
        return {
            "success": True,
            "sector": sector,
            "count": len(stocks),
            "stocks": stocks
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sector stocks: {e}")
        raise HTTPException(status_code=500, detail=str(e))
