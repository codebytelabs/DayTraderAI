"""
Sprint 3 Adaptive Parameters Test
Tests the adaptive parameter optimization system
"""

import asyncio
import logging
from datetime import date, timedelta
from core.supabase_client import get_client as get_supabase_client
from adaptive.parameter_optimizer import ParameterOptimizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_parameter_optimizer():
    """Test parameter optimization"""
    logger.info("=" * 60)
    logger.info("SPRINT 3: PARAMETER OPTIMIZER TEST")
    logger.info("=" * 60)
    
    try:
        # Initialize
        supabase = get_supabase_client()
        optimizer = ParameterOptimizer(supabase)
        
        # Get current parameters
        logger.info("\n📊 Current Parameters:")
        current_params = optimizer.get_current_parameters()
        for key, value in current_params.items():
            logger.info(f"  {key}: {value}")
        
        # Optimize parameters
        logger.info("\n🔧 Optimizing parameters based on last 30 days...")
        result = await optimizer.optimize_parameters(lookback_days=30)
        
        logger.info(f"\nOptimization Status: {result['status']}")
        logger.info(f"Trades Analyzed: {result.get('trades_analyzed', 0)}")
        
        if result['status'] == 'optimized':
            logger.info("\n✅ Parameters Optimized:")
            for category, changes in result['changes'].items():
                logger.info(f"\n  {category.upper()}:")
                logger.info(f"    Old Value: {changes.get('old_value')}")
                logger.info(f"    New Value: {changes.get('new_value')}")
                logger.info(f"    Reason: {changes.get('reason')}")
                
                if 'metrics' in changes:
                    logger.info(f"    Metrics: {changes['metrics']}")
        else:
            logger.info(f"\n  {result.get('reason', 'No changes needed')}")
        
        # Validate parameters
        logger.info("\n🔍 Validating Parameters...")
        validation = optimizer.validate_parameters(optimizer.get_current_parameters())
        
        if validation['valid']:
            logger.info("  ✅ All parameters valid")
        else:
            logger.info("  ❌ Validation errors:")
            for error in validation['errors']:
                logger.info(f"    - {error}")
        
        if validation['warnings']:
            logger.info("  ⚠️  Warnings:")
            for warning in validation['warnings']:
                logger.info(f"    - {warning}")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ PARAMETER OPTIMIZER TEST COMPLETE")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)


async def test_apply_recommendations():
    """Test applying recommendations from daily report"""
    logger.info("\n" + "=" * 60)
    logger.info("APPLY RECOMMENDATIONS TEST")
    logger.info("=" * 60)
    
    try:
        supabase = get_supabase_client()
        optimizer = ParameterOptimizer(supabase)
        
        # Mock recommendations (would come from daily report)
        mock_recommendations = {
            'position_sizing': {
                'recommendation': 'REDUCE',
                'reason': 'High drawdown detected',
                'confidence': 0.9
            },
            'stop_loss': {
                'recommendation': 'TIGHTEN',
                'reason': 'Too many large losses',
                'confidence': 0.85
            },
            'take_profit': {
                'recommendation': 'WIDEN',
                'reason': 'Many small wins - capture more profit',
                'confidence': 0.75
            },
            'entry_criteria': {
                'recommendation': 'STRICTER',
                'reason': 'Low win rate - tighten entry criteria',
                'confidence': 0.8
            }
        }
        
        logger.info("\n📋 Applying Mock Recommendations:")
        for category, rec in mock_recommendations.items():
            logger.info(f"  {category}: {rec['recommendation']} ({rec['confidence']:.0%} confidence)")
            logger.info(f"    Reason: {rec['reason']}")
        
        # Apply recommendations
        result = await optimizer.apply_recommendations(mock_recommendations)
        
        logger.info(f"\nApplication Status: {result['status']}")
        
        if result['status'] == 'applied':
            logger.info("\n✅ Changes Applied:")
            for category, changes in result['changes'].items():
                logger.info(f"\n  {category.upper()}:")
                if 'old_value' in changes:
                    logger.info(f"    Old Value: {changes['old_value']}")
                    logger.info(f"    New Value: {changes['new_value']}")
                logger.info(f"    Reason: {changes.get('reason')}")
        
        logger.info("\n✅ Apply recommendations test complete")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)


async def test_individual_adjusters():
    """Test individual parameter adjusters"""
    logger.info("\n" + "=" * 60)
    logger.info("INDIVIDUAL ADJUSTERS TEST")
    logger.info("=" * 60)
    
    try:
        from adaptive.stop_loss_adjuster import StopLossAdjuster
        from adaptive.take_profit_adjuster import TakeProfitAdjuster
        from adaptive.position_sizer import AdaptivePositionSizer
        from adaptive.entry_refiner import EntryRefiner
        
        supabase = get_supabase_client()
        
        # Get recent trades
        yesterday = date.today() - timedelta(days=1)
        result = supabase.table('trades').select('*').gte(
            'entry_time', yesterday.isoformat()
        ).execute()
        
        trades_data = result.data if result.data else []
        
        if not trades_data:
            logger.info("No trades found for testing")
            return
        
        logger.info(f"\n🔍 Testing with {len(trades_data)} trades...\n")
        
        # Test Stop Loss Adjuster
        logger.info("1. Stop Loss Adjuster:")
        stop_loss_adjuster = StopLossAdjuster(supabase)
        sl_result = await stop_loss_adjuster.optimize(trades_data)
        logger.info(f"   Changed: {sl_result.get('changed')}")
        if sl_result.get('changed'):
            logger.info(f"   {sl_result.get('old_value')}% → {sl_result.get('new_value')}%")
            logger.info(f"   Reason: {sl_result.get('reason')}")
        
        # Test Take Profit Adjuster
        logger.info("\n2. Take Profit Adjuster:")
        tp_adjuster = TakeProfitAdjuster(supabase)
        tp_result = await tp_adjuster.optimize(trades_data)
        logger.info(f"   Changed: {tp_result.get('changed')}")
        if tp_result.get('changed'):
            logger.info(f"   {tp_result.get('old_value')}% → {tp_result.get('new_value')}%")
            logger.info(f"   Reason: {tp_result.get('reason')}")
        
        # Test Position Sizer
        logger.info("\n3. Position Sizer:")
        position_sizer = AdaptivePositionSizer(supabase)
        ps_result = await position_sizer.optimize(trades_data)
        logger.info(f"   Changed: {ps_result.get('changed')}")
        if ps_result.get('changed'):
            logger.info(f"   {ps_result.get('old_value')}% → {ps_result.get('new_value')}%")
            logger.info(f"   Reason: {ps_result.get('reason')}")
        
        # Test Entry Refiner
        logger.info("\n4. Entry Refiner:")
        entry_refiner = EntryRefiner(supabase)
        er_result = await entry_refiner.optimize(trades_data)
        logger.info(f"   Changed: {er_result.get('changed')}")
        if er_result.get('changed'):
            logger.info(f"   Reason: {er_result.get('reason')}")
            logger.info(f"   New Criteria: {er_result.get('new_values')}")
        
        logger.info("\n✅ Individual adjusters test complete")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)


async def test_parameter_history():
    """Test parameter history tracking"""
    logger.info("\n" + "=" * 60)
    logger.info("PARAMETER HISTORY TEST")
    logger.info("=" * 60)
    
    try:
        supabase = get_supabase_client()
        optimizer = ParameterOptimizer(supabase)
        
        logger.info("\n📊 Getting parameter history (last 30 days)...")
        history = await optimizer.get_parameter_history(days=30)
        
        if history:
            logger.info(f"\nFound {len(history)} parameter changes:")
            for record in history[-5:]:  # Show last 5
                logger.info(f"\n  Date: {record.get('created_at')}")
                logger.info(f"  Stop Loss: {record.get('stop_loss_percent')}%")
                logger.info(f"  Take Profit: {record.get('take_profit_percent')}%")
                logger.info(f"  Position Size: {record.get('position_size_percent')}%")
        else:
            logger.info("  No parameter history found")
        
        logger.info("\n✅ Parameter history test complete")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)


async def main():
    """Run all Sprint 3 tests"""
    logger.info("\n" + "=" * 60)
    logger.info("🚀 SPRINT 3: ADAPTIVE PARAMETERS SYSTEM TEST")
    logger.info("=" * 60)
    
    # Run all tests
    await test_parameter_optimizer()
    await test_apply_recommendations()
    await test_individual_adjusters()
    await test_parameter_history()
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ ALL SPRINT 3 TESTS COMPLETE!")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
