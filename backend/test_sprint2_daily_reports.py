"""
Sprint 2 Daily Reports Test
Tests the daily report generation system
"""

import asyncio
import logging
from datetime import date, timedelta
from core.supabase_client import get_client as get_supabase_client
from analysis.daily_report import DailyReportGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_daily_report_generation():
    """Test daily report generation"""
    logger.info("=" * 60)
    logger.info("SPRINT 2: DAILY REPORT GENERATION TEST")
    logger.info("=" * 60)
    
    try:
        # Initialize
        supabase = get_supabase_client()
        report_generator = DailyReportGenerator(supabase)
        
        # Generate report for yesterday
        yesterday = date.today() - timedelta(days=1)
        logger.info(f"\n📊 Generating daily report for {yesterday}...")
        
        report = await report_generator.generate_daily_report(yesterday)
        
        # Display report
        logger.info("\n" + "=" * 60)
        logger.info("DAILY REPORT GENERATED")
        logger.info("=" * 60)
        
        if 'error' in report:
            logger.error(f"❌ Error: {report['error']}")
            return
        
        # Executive Summary
        exec_summary = report.get('sections', {}).get('executive_summary', {})
        logger.info("\n📈 EXECUTIVE SUMMARY")
        logger.info(f"  Grade: {exec_summary.get('grade', 'N/A')}")
        logger.info(f"  Total Trades: {exec_summary.get('total_trades', 0)}")
        logger.info(f"  Win Rate: {exec_summary.get('win_rate', 0)}%")
        logger.info(f"  Total P/L: ${exec_summary.get('total_pnl', 0):.2f}")
        logger.info(f"  Profit Factor: {exec_summary.get('profit_factor', 0):.2f}")
        logger.info(f"  Early Exits: {exec_summary.get('early_exits', 0)}")
        logger.info(f"  ML Accuracy: {exec_summary.get('ml_accuracy', 0)}%")
        
        # Trade Analysis
        trade_analysis = report.get('sections', {}).get('trade_analysis', {})
        logger.info(f"\n🔍 TRADE ANALYSIS")
        logger.info(f"  Trades Analyzed: {trade_analysis.get('total_analyzed', 0)}")
        insights = trade_analysis.get('insights', {})
        if isinstance(insights, dict):
            logger.info(f"  Key Insights: {insights.get('key_insights', [])}")
        
        # Pattern Analysis
        pattern_analysis = report.get('sections', {}).get('pattern_analysis', {})
        logger.info(f"\n📊 PATTERN ANALYSIS")
        logger.info(f"  Summary: {pattern_analysis.get('summary', 'N/A')}")
        
        streak = pattern_analysis.get('streak_patterns', {})
        if streak:
            logger.info(f"  Current Streak: {streak.get('current_streak', 0)} {streak.get('type', 'none')}")
        
        # Performance Metrics
        perf_metrics = report.get('sections', {}).get('performance_metrics', {})
        logger.info(f"\n📈 PERFORMANCE METRICS")
        trading_metrics = perf_metrics.get('trading_metrics', {})
        if trading_metrics:
            logger.info(f"  Win Rate: {trading_metrics.get('win_rate', 0)}%")
            logger.info(f"  Total P/L: ${trading_metrics.get('total_pnl', 0):.2f}")
        
        # Risk Analysis
        risk_analysis = report.get('sections', {}).get('risk_analysis', {})
        logger.info(f"\n⚠️ RISK ANALYSIS")
        logger.info(f"  Risk Level: {risk_analysis.get('risk_level', 'UNKNOWN')}")
        logger.info(f"  Max Drawdown: ${risk_analysis.get('max_drawdown', 0):.2f}")
        logger.info(f"  Max Loss: ${risk_analysis.get('max_loss', 0):.2f}")
        
        # Recommendations
        recommendations = report.get('sections', {}).get('recommendations', {})
        logger.info(f"\n💡 RECOMMENDATIONS")
        priority_actions = recommendations.get('priority_actions', [])
        for action in priority_actions:
            logger.info(f"  {action}")
        
        # Position Sizing
        pos_sizing = recommendations.get('position_sizing', {})
        if pos_sizing:
            logger.info(f"\n  Position Sizing: {pos_sizing.get('recommendation', 'N/A')}")
            logger.info(f"    Reason: {pos_sizing.get('reason', 'N/A')}")
            logger.info(f"    Confidence: {pos_sizing.get('confidence', 0):.1%}")
        
        # Next Day Outlook
        outlook = report.get('sections', {}).get('next_day_outlook', {})
        logger.info(f"\n🔮 NEXT DAY OUTLOOK")
        logger.info(f"  Market Conditions: {outlook.get('market_conditions', 'NORMAL')}")
        logger.info(f"  Recommended Position Size: {outlook.get('recommended_position_size', 'NORMAL')}")
        
        focus_areas = outlook.get('focus_areas', [])
        if focus_areas:
            logger.info(f"  Focus Areas:")
            for area in focus_areas:
                logger.info(f"    - {area}")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ DAILY REPORT TEST COMPLETE")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)


async def test_trade_analyzer():
    """Test individual trade analysis"""
    logger.info("\n" + "=" * 60)
    logger.info("TRADE ANALYZER TEST")
    logger.info("=" * 60)
    
    try:
        from analysis.trade_analyzer import TradeAnalyzer
        
        supabase = get_supabase_client()
        analyzer = TradeAnalyzer(supabase)
        
        # Get recent trades
        result = supabase.table('trades').select('*').order('entry_time', desc=True).limit(5).execute()
        
        if not result.data:
            logger.info("No trades found to analyze")
            return
        
        logger.info(f"\n🔍 Analyzing {len(result.data)} recent trades...\n")
        
        for trade in result.data:
            analysis = await analyzer.analyze_trade(trade)
            
            logger.info(f"Trade: {trade.get('symbol')} | P/L: ${trade.get('pnl', 0):.2f}")
            logger.info(f"  Grade: {analysis.get('grade', 'N/A')}")
            logger.info(f"  Entry Quality: {analysis.get('entry_analysis', {}).get('quality', 'UNKNOWN')}")
            logger.info(f"  Exit Type: {analysis.get('exit_analysis', {}).get('type', 'NORMAL')}")
            logger.info(f"  Risk Level: {analysis.get('risk_analysis', {}).get('risk_level', 'UNKNOWN')}")
            
            lessons = analysis.get('lessons', [])
            if lessons:
                logger.info(f"  Lessons:")
                for lesson in lessons[:2]:  # Show first 2 lessons
                    logger.info(f"    - {lesson}")
            logger.info("")
        
        logger.info("✅ Trade analyzer test complete")
        
    except Exception as e:
        logger.error(f"❌ Trade analyzer test failed: {e}", exc_info=True)


async def test_pattern_detector():
    """Test pattern detection"""
    logger.info("\n" + "=" * 60)
    logger.info("PATTERN DETECTOR TEST")
    logger.info("=" * 60)
    
    try:
        from analysis.pattern_detector import PatternDetector
        
        supabase = get_supabase_client()
        detector = PatternDetector(supabase)
        
        # Get recent trades
        yesterday = date.today() - timedelta(days=1)
        result = supabase.table('trades').select('*').gte(
            'entry_time', yesterday.isoformat()
        ).execute()
        
        if not result.data:
            logger.info("No trades found for pattern detection")
            return
        
        logger.info(f"\n🔍 Detecting patterns in {len(result.data)} trades...\n")
        
        patterns = await detector.detect_patterns(result.data, yesterday)
        
        # Display patterns
        logger.info("📊 DETECTED PATTERNS:")
        logger.info(f"  Summary: {patterns.get('summary', 'N/A')}")
        
        # Streak patterns
        streak = patterns.get('streak_patterns', {})
        if streak:
            logger.info(f"\n  Streak: {streak.get('current_streak', 0)} {streak.get('type', 'none')}")
            logger.info(f"    Recommendation: {streak.get('recommendation', 'N/A')}")
        
        # Time patterns
        time_patterns = patterns.get('time_patterns', {})
        if time_patterns.get('best_hour'):
            logger.info(f"\n  Best Trading Hour: {time_patterns['best_hour']}:00")
            logger.info(f"  Worst Trading Hour: {time_patterns.get('worst_hour', 'N/A')}:00")
        
        # Symbol patterns
        symbol_patterns = patterns.get('symbol_patterns', {})
        best_performers = symbol_patterns.get('best_performers', [])
        if best_performers:
            logger.info(f"\n  Best Performing Symbols:")
            for symbol, data in best_performers[:3]:
                logger.info(f"    {symbol}: ${data['pnl']:.2f} ({data['win_rate']:.1f}% win rate)")
        
        logger.info("\n✅ Pattern detector test complete")
        
    except Exception as e:
        logger.error(f"❌ Pattern detector test failed: {e}", exc_info=True)


async def test_recommendation_engine():
    """Test recommendation engine"""
    logger.info("\n" + "=" * 60)
    logger.info("RECOMMENDATION ENGINE TEST")
    logger.info("=" * 60)
    
    try:
        from analysis.recommendation_engine import RecommendationEngine
        
        supabase = get_supabase_client()
        engine = RecommendationEngine(supabase)
        
        # Get recent data
        yesterday = date.today() - timedelta(days=1)
        
        trades_result = supabase.table('trades').select('*').gte(
            'entry_time', yesterday.isoformat()
        ).execute()
        
        positions_result = supabase.table('position_exits').select('*').gte(
            'created_at', yesterday.isoformat()
        ).execute()
        
        ml_result = supabase.table('ml_predictions').select('*').gte(
            'created_at', yesterday.isoformat()
        ).execute()
        
        trades_data = trades_result.data if trades_result.data else []
        positions_data = positions_result.data if positions_result.data else []
        ml_data = ml_result.data if ml_result.data else []
        
        logger.info(f"\n🔍 Generating recommendations from:")
        logger.info(f"  Trades: {len(trades_data)}")
        logger.info(f"  Position Exits: {len(positions_data)}")
        logger.info(f"  ML Predictions: {len(ml_data)}")
        
        recommendations = await engine.generate_recommendations(trades_data, positions_data, ml_data)
        
        # Display recommendations
        logger.info("\n💡 RECOMMENDATIONS:")
        
        priority_actions = recommendations.get('priority_actions', [])
        logger.info(f"\n  Priority Actions:")
        for action in priority_actions:
            logger.info(f"    {action}")
        
        # Position sizing
        pos_sizing = recommendations.get('position_sizing', {})
        logger.info(f"\n  Position Sizing: {pos_sizing.get('recommendation', 'N/A')}")
        logger.info(f"    {pos_sizing.get('reason', 'N/A')}")
        logger.info(f"    Confidence: {pos_sizing.get('confidence', 0):.1%}")
        
        # Stop loss
        stop_loss = recommendations.get('stop_loss', {})
        logger.info(f"\n  Stop Loss: {stop_loss.get('recommendation', 'N/A')}")
        logger.info(f"    {stop_loss.get('reason', 'N/A')}")
        
        # Entry criteria
        entry = recommendations.get('entry_criteria', {})
        logger.info(f"\n  Entry Criteria: {entry.get('recommendation', 'N/A')}")
        logger.info(f"    {entry.get('reason', 'N/A')}")
        
        logger.info("\n✅ Recommendation engine test complete")
        
    except Exception as e:
        logger.error(f"❌ Recommendation engine test failed: {e}", exc_info=True)


async def main():
    """Run all Sprint 2 tests"""
    logger.info("\n" + "=" * 60)
    logger.info("🚀 SPRINT 2: DAILY REPORTS SYSTEM TEST")
    logger.info("=" * 60)
    
    # Run all tests
    await test_daily_report_generation()
    await test_trade_analyzer()
    await test_pattern_detector()
    await test_recommendation_engine()
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ ALL SPRINT 2 TESTS COMPLETE!")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
