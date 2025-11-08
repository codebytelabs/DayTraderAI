"""
Daily Report API Routes
Endpoints for accessing daily trading reports
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import date, timedelta
from typing import Optional
import logging

from core.supabase_client import get_client as get_supabase_client
from analysis.daily_report import DailyReportGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/daily")
async def get_daily_report(report_date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format")):
    """
    Get daily trading report
    
    Args:
        report_date: Date to get report for (defaults to yesterday)
        
    Returns:
        Complete daily report with all sections
    """
    try:
        # Parse date
        if report_date:
            target_date = date.fromisoformat(report_date)
        else:
            target_date = date.today() - timedelta(days=1)
        
        # Generate report
        supabase = get_supabase_client()
        report_generator = DailyReportGenerator(supabase)
        
        report = await report_generator.generate_daily_report(target_date)
        
        if 'error' in report:
            raise HTTPException(status_code=500, detail=report['error'])
        
        return report
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        logger.error(f"Error getting daily report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/daily/summary")
async def get_daily_summary(report_date: Optional[str] = Query(None)):
    """
    Get executive summary only
    
    Args:
        report_date: Date to get summary for (defaults to yesterday)
        
    Returns:
        Executive summary section
    """
    try:
        if report_date:
            target_date = date.fromisoformat(report_date)
        else:
            target_date = date.today() - timedelta(days=1)
        
        supabase = get_supabase_client()
        report_generator = DailyReportGenerator(supabase)
        
        report = await report_generator.generate_daily_report(target_date)
        
        if 'error' in report:
            raise HTTPException(status_code=500, detail=report['error'])
        
        return report.get('sections', {}).get('executive_summary', {})
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        logger.error(f"Error getting daily summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/daily/recommendations")
async def get_recommendations(report_date: Optional[str] = Query(None)):
    """
    Get recommendations only
    
    Args:
        report_date: Date to get recommendations for (defaults to yesterday)
        
    Returns:
        Recommendations section
    """
    try:
        if report_date:
            target_date = date.fromisoformat(report_date)
        else:
            target_date = date.today() - timedelta(days=1)
        
        supabase = get_supabase_client()
        report_generator = DailyReportGenerator(supabase)
        
        report = await report_generator.generate_daily_report(target_date)
        
        if 'error' in report:
            raise HTTPException(status_code=500, detail=report['error'])
        
        return report.get('sections', {}).get('recommendations', {})
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/daily/patterns")
async def get_patterns(report_date: Optional[str] = Query(None)):
    """
    Get pattern analysis only
    
    Args:
        report_date: Date to get patterns for (defaults to yesterday)
        
    Returns:
        Pattern analysis section
    """
    try:
        if report_date:
            target_date = date.fromisoformat(report_date)
        else:
            target_date = date.today() - timedelta(days=1)
        
        supabase = get_supabase_client()
        report_generator = DailyReportGenerator(supabase)
        
        report = await report_generator.generate_daily_report(target_date)
        
        if 'error' in report:
            raise HTTPException(status_code=500, detail=report['error'])
        
        return report.get('sections', {}).get('pattern_analysis', {})
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        logger.error(f"Error getting patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weekly")
async def get_weekly_report(end_date: Optional[str] = Query(None)):
    """
    Get weekly trading report (aggregated from daily reports)
    
    Args:
        end_date: End date for week (defaults to yesterday)
        
    Returns:
        Weekly aggregated report
    """
    try:
        if end_date:
            target_date = date.fromisoformat(end_date)
        else:
            target_date = date.today() - timedelta(days=1)
        
        # Get last 7 days of data
        start_date = target_date - timedelta(days=6)
        
        supabase = get_supabase_client()
        
        # Get all trades for the week
        trades_result = supabase.table('trades').select('*').gte(
            'entry_time', start_date.isoformat()
        ).lte(
            'entry_time', (target_date + timedelta(days=1)).isoformat()
        ).execute()
        
        trades_data = trades_result.data if trades_result.data else []
        
        # Calculate weekly metrics
        total_trades = len(trades_data)
        winning_trades = sum(1 for t in trades_data if t.get('pnl', 0) > 0)
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        total_pnl = sum(t.get('pnl', 0) for t in trades_data)
        
        # Group by day
        daily_pnl = {}
        for trade in trades_data:
            if trade.get('entry_time'):
                trade_date = trade['entry_time'][:10]  # Get YYYY-MM-DD
                if trade_date not in daily_pnl:
                    daily_pnl[trade_date] = 0
                daily_pnl[trade_date] += trade.get('pnl', 0)
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': target_date.isoformat()
            },
            'summary': {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'win_rate': round(win_rate, 1),
                'total_pnl': round(total_pnl, 2),
                'avg_daily_pnl': round(total_pnl / 7, 2),
                'trading_days': len(daily_pnl)
            },
            'daily_breakdown': daily_pnl
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        logger.error(f"Error getting weekly report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/grade")
async def get_performance_grade(report_date: Optional[str] = Query(None)):
    """
    Get just the performance grade for a day
    
    Args:
        report_date: Date to get grade for (defaults to yesterday)
        
    Returns:
        Performance grade (A-F)
    """
    try:
        if report_date:
            target_date = date.fromisoformat(report_date)
        else:
            target_date = date.today() - timedelta(days=1)
        
        supabase = get_supabase_client()
        report_generator = DailyReportGenerator(supabase)
        
        report = await report_generator.generate_daily_report(target_date)
        
        if 'error' in report:
            raise HTTPException(status_code=500, detail=report['error'])
        
        exec_summary = report.get('sections', {}).get('executive_summary', {})
        
        return {
            'date': target_date.isoformat(),
            'grade': exec_summary.get('grade', 'N/A'),
            'summary': exec_summary.get('summary', '')
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        logger.error(f"Error getting performance grade: {e}")
        raise HTTPException(status_code=500, detail=str(e))
