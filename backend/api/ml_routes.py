"""
ML Monitoring API Routes
Endpoints for ML shadow mode monitoring and management
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

from core.supabase_client import get_client as get_supabase_client
from ml.shadow_mode import MLShadowMode

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ml", tags=["ml"])

# Global ML shadow mode instance (will be initialized by trading engine)
ml_shadow_mode: Optional[MLShadowMode] = None


def set_ml_shadow_mode(shadow_mode: MLShadowMode):
    """Set global ML shadow mode instance"""
    global ml_shadow_mode
    ml_shadow_mode = shadow_mode


@router.get("/shadow/status")
async def get_shadow_mode_status():
    """
    Get ML shadow mode status
    
    Returns:
        Shadow mode statistics and configuration
    """
    try:
        if not ml_shadow_mode:
            return {
                'status': 'not_initialized',
                'message': 'ML shadow mode not initialized'
            }
        
        stats = ml_shadow_mode.get_statistics()
        
        return {
            'status': 'active',
            'statistics': stats
        }
        
    except Exception as e:
        logger.error(f"Error getting shadow mode status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shadow/accuracy")
async def get_shadow_mode_accuracy(days: int = Query(30, ge=1, le=90)):
    """
    Get ML prediction accuracy metrics
    
    Args:
        days: Number of days to analyze (1-90)
        
    Returns:
        Accuracy metrics
    """
    try:
        if not ml_shadow_mode:
            raise HTTPException(status_code=400, detail="ML shadow mode not initialized")
        
        metrics = await ml_shadow_mode.get_accuracy_metrics(days=days)
        
        return {
            'status': 'success',
            'metrics': metrics
        }
        
    except Exception as e:
        logger.error(f"Error getting accuracy metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shadow/predictions")
async def get_recent_predictions(limit: int = Query(50, ge=1, le=200)):
    """
    Get recent ML predictions
    
    Args:
        limit: Number of predictions to return (1-200)
        
    Returns:
        Recent predictions
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.table('ml_predictions').select('*').order(
            'created_at', desc=True
        ).limit(limit).execute()
        
        predictions = result.data if result.data else []
        
        return {
            'status': 'success',
            'predictions': predictions,
            'count': len(predictions)
        }
        
    except Exception as e:
        logger.error(f"Error getting predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/shadow/weight")
async def update_ml_weight(new_weight: float):
    """
    Update ML weight
    
    Args:
        new_weight: New ML weight (0.0-1.0)
        
    Returns:
        Update confirmation
    """
    try:
        if not ml_shadow_mode:
            raise HTTPException(status_code=400, detail="ML shadow mode not initialized")
        
        if not 0.0 <= new_weight <= 1.0:
            raise HTTPException(status_code=400, detail="Weight must be between 0.0 and 1.0")
        
        old_weight = ml_shadow_mode.ml_weight
        ml_shadow_mode.set_ml_weight(new_weight)
        
        return {
            'status': 'success',
            'old_weight': old_weight,
            'new_weight': new_weight,
            'message': f'ML weight updated from {old_weight} to {new_weight}'
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating ML weight: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
async def get_ml_performance():
    """
    Get ML performance summary
    
    Returns:
        Performance summary with accuracy, latency, and impact
    """
    try:
        if not ml_shadow_mode:
            raise HTTPException(status_code=400, detail="ML shadow mode not initialized")
        
        # Get statistics
        stats = ml_shadow_mode.get_statistics()
        
        # Get accuracy metrics
        accuracy_30d = await ml_shadow_mode.get_accuracy_metrics(days=30)
        accuracy_7d = await ml_shadow_mode.get_accuracy_metrics(days=7)
        
        return {
            'status': 'success',
            'statistics': stats,
            'accuracy_30_days': accuracy_30d,
            'accuracy_7_days': accuracy_7d
        }
        
    except Exception as e:
        logger.error(f"Error getting ML performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predictions/{symbol}")
async def get_symbol_predictions(symbol: str, limit: int = Query(20, ge=1, le=100)):
    """
    Get predictions for specific symbol
    
    Args:
        symbol: Stock symbol
        limit: Number of predictions to return
        
    Returns:
        Symbol predictions
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.table('ml_predictions').select('*').eq(
            'symbol', symbol.upper()
        ).order('created_at', desc=True).limit(limit).execute()
        
        predictions = result.data if result.data else []
        
        # Calculate symbol-specific accuracy
        completed = [p for p in predictions if p.get('actual_outcome')]
        accuracy = 0
        if completed:
            correct = sum(1 for p in completed if p.get('was_correct'))
            accuracy = (correct / len(completed)) * 100
        
        return {
            'status': 'success',
            'symbol': symbol.upper(),
            'predictions': predictions,
            'total_predictions': len(predictions),
            'completed_predictions': len(completed),
            'accuracy': round(accuracy, 1)
        }
        
    except Exception as e:
        logger.error(f"Error getting symbol predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
