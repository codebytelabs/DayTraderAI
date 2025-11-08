"""
Adaptive Parameters API Routes
Endpoints for parameter optimization and management
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

from core.supabase_client import get_client as get_supabase_client
from adaptive.parameter_optimizer import ParameterOptimizer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/adaptive", tags=["adaptive"])


@router.get("/parameters")
async def get_current_parameters():
    """
    Get current trading parameters
    
    Returns:
        Current parameter values
    """
    try:
        supabase = get_supabase_client()
        optimizer = ParameterOptimizer(supabase)
        
        params = optimizer.get_current_parameters()
        
        return {
            'status': 'success',
            'parameters': params
        }
        
    except Exception as e:
        logger.error(f"Error getting parameters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize")
async def optimize_parameters(lookback_days: int = Query(30, ge=7, le=90)):
    """
    Optimize parameters based on recent performance
    
    Args:
        lookback_days: Number of days to analyze (7-90)
        
    Returns:
        Optimization results and changes made
    """
    try:
        supabase = get_supabase_client()
        optimizer = ParameterOptimizer(supabase)
        
        result = await optimizer.optimize_parameters(lookback_days=lookback_days)
        
        return result
        
    except Exception as e:
        logger.error(f"Error optimizing parameters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/apply-recommendations")
async def apply_recommendations(recommendations: dict):
    """
    Apply recommendations from daily report
    
    Args:
        recommendations: Recommendations dictionary
        
    Returns:
        Applied changes
    """
    try:
        supabase = get_supabase_client()
        optimizer = ParameterOptimizer(supabase)
        
        result = await optimizer.apply_recommendations(recommendations)
        
        return result
        
    except Exception as e:
        logger.error(f"Error applying recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/parameters/history")
async def get_parameter_history(days: int = Query(30, ge=7, le=90)):
    """
    Get parameter change history
    
    Args:
        days: Number of days to look back (7-90)
        
    Returns:
        Parameter history
    """
    try:
        supabase = get_supabase_client()
        optimizer = ParameterOptimizer(supabase)
        
        history = await optimizer.get_parameter_history(days=days)
        
        return {
            'status': 'success',
            'history': history,
            'count': len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting parameter history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/parameters/validate")
async def validate_parameters():
    """
    Validate current parameters
    
    Returns:
        Validation results
    """
    try:
        supabase = get_supabase_client()
        optimizer = ParameterOptimizer(supabase)
        
        params = optimizer.get_current_parameters()
        validation = optimizer.validate_parameters(params)
        
        return {
            'status': 'success',
            'validation': validation,
            'parameters': params
        }
        
    except Exception as e:
        logger.error(f"Error validating parameters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/parameters/{symbol}")
async def get_symbol_parameters(symbol: str):
    """
    Get parameters for specific symbol
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Symbol-specific parameters
    """
    try:
        supabase = get_supabase_client()
        optimizer = ParameterOptimizer(supabase)
        
        params = optimizer.get_current_parameters()
        
        # For now, return global parameters
        # Future: Could have symbol-specific adjustments
        return {
            'status': 'success',
            'symbol': symbol,
            'parameters': params
        }
        
    except Exception as e:
        logger.error(f"Error getting symbol parameters: {e}")
        raise HTTPException(status_code=500, detail=str(e))
