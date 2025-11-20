#!/usr/bin/env python3
"""
Analyze ML Shadow Mode Performance
Comprehensive analysis of ML predictions and learning progress
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from core.supabase_client import SupabaseClient


def analyze_ml_shadow_mode():
    """Comprehensive ML shadow mode analysis"""
    
    print("=" * 80)
    print("🤖 ML SHADOW MODE ANALYSIS")
    print("=" * 80)
    print()
    
    supabase_client = SupabaseClient()
    supabase = supabase_client.client
    
    # 1. Get all predictions
    print("📊 Fetching ML predictions...")
    result = supabase.table('ml_predictions').select('*').order('created_at', desc=True).execute()
    
    if not result.data:
        print("❌ No ML predictions found in database")
        print()
        print("Possible reasons:")
        print("  1. ML shadow mode not enabled")
        print("  2. No trades executed yet")
        print("  3. Database table not created")
        return
    
    predictions = result.data
    total_predictions = len(predictions)
    
    print(f"✅ Found {total_predictions} ML predictions")
    print()
    
    # 2. Separate completed vs pending
    completed = [p for p in predictions if p.get('actual_outcome') is not None]
    pending = [p for p in predictions if p.get('actual_outcome') is None]
    
    print("=" * 80)
    print("📈 PREDICTION STATUS")
    print("=" * 80)
    print(f"Total Predictions:     {total_predictions}")
    print(f"Completed (with outcome): {len(completed)}")
    print(f"Pending (trade active):   {len(pending)}")
    print()
    
    # 3. Analyze completed predictions
    if completed:
        print("=" * 80)
        print("🎯 ACCURACY ANALYSIS (Completed Predictions)")
        print("=" * 80)
        
        correct = sum(1 for p in completed if p.get('was_correct'))
        accuracy = (correct / len(completed)) * 100
        
        print(f"Total Completed:   {len(completed)}")
        print(f"Correct:           {correct}")
        print(f"Incorrect:         {len(completed) - correct}")
        print(f"Accuracy:          {accuracy:.1f}%")
        print()
        
        # By outcome type
        wins = [p for p in completed if p.get('actual_outcome') == 'WIN']
        losses = [p for p in completed if p.get('actual_outcome') == 'LOSS']
        breakeven = [p for p in completed if p.get('actual_outcome') == 'BREAKEVEN']
        
        print("By Outcome Type:")
        print(f"  Wins:      {len(wins)}")
        print(f"  Losses:    {len(losses)}")
        print(f"  Breakeven: {len(breakeven)}")
        print()
        
        # Accuracy by prediction type
        if wins:
            win_correct = sum(1 for p in wins if p.get('was_correct'))
            win_accuracy = (win_correct / len(wins)) * 100
            print(f"Win Prediction Accuracy:  {win_accuracy:.1f}% ({win_correct}/{len(wins)})")
        
        if losses:
            loss_correct = sum(1 for p in losses if p.get('was_correct'))
            loss_accuracy = (loss_correct / len(losses)) * 100
            print(f"Loss Prediction Accuracy: {loss_accuracy:.1f}% ({loss_correct}/{len(losses)})")
        print()
        
        # Confidence analysis
        avg_ml_conf = sum(p.get('ml_confidence', 0) for p in completed) / len(completed)
        avg_existing_conf = sum(p.get('existing_confidence', 0) for p in completed) / len(completed)
        
        print("Confidence Levels:")
        print(f"  Avg ML Confidence:       {avg_ml_conf:.1f}%")
        print(f"  Avg Strategy Confidence: {avg_existing_conf:.1f}%")
        print()
        
        # Performance metrics
        avg_latency = sum(p.get('latency_ms', 0) for p in completed) / len(completed)
        max_latency = max(p.get('latency_ms', 0) for p in completed)
        
        print("Performance:")
        print(f"  Avg Latency: {avg_latency:.1f}ms")
        print(f"  Max Latency: {max_latency:.1f}ms")
        print()
    
    # 4. Analyze pending predictions
    if pending:
        print("=" * 80)
        print("⏳ PENDING PREDICTIONS (Active Trades)")
        print("=" * 80)
        
        for p in pending[:5]:  # Show first 5
            symbol = p.get('symbol')
            ml_pred = p.get('ml_prediction')
            ml_conf = p.get('ml_confidence', 0)
            created = p.get('created_at', '')[:19]
            
            print(f"  {symbol:6} | ML: {ml_pred:4} ({ml_conf:.0f}%) | Created: {created}")
        
        if len(pending) > 5:
            print(f"  ... and {len(pending) - 5} more")
        print()
    
    # 5. Recent predictions (last 24 hours)
    now = datetime.now()
    last_24h = now - timedelta(hours=24)
    recent = [p for p in predictions if datetime.fromisoformat(p.get('created_at', '').replace('Z', '+00:00')) > last_24h]
    
    if recent:
        print("=" * 80)
        print("🕐 LAST 24 HOURS")
        print("=" * 80)
        print(f"Predictions Made: {len(recent)}")
        
        recent_completed = [p for p in recent if p.get('actual_outcome') is not None]
        if recent_completed:
            recent_correct = sum(1 for p in recent_completed if p.get('was_correct'))
            recent_accuracy = (recent_correct / len(recent_completed)) * 100
            print(f"Completed:        {len(recent_completed)}")
            print(f"Accuracy:         {recent_accuracy:.1f}%")
        else:
            print("Completed:        0 (all trades still active)")
        print()
    
    # 6. Symbol breakdown
    if completed:
        print("=" * 80)
        print("📊 BY SYMBOL")
        print("=" * 80)
        
        symbols = {}
        for p in completed:
            symbol = p.get('symbol')
            if symbol not in symbols:
                symbols[symbol] = {'total': 0, 'correct': 0}
            symbols[symbol]['total'] += 1
            if p.get('was_correct'):
                symbols[symbol]['correct'] += 1
        
        # Sort by total predictions
        sorted_symbols = sorted(symbols.items(), key=lambda x: x[1]['total'], reverse=True)
        
        for symbol, stats in sorted_symbols[:10]:  # Top 10
            accuracy = (stats['correct'] / stats['total']) * 100
            print(f"  {symbol:6} | {stats['correct']:2}/{stats['total']:2} correct | {accuracy:5.1f}% accuracy")
        
        if len(sorted_symbols) > 10:
            print(f"  ... and {len(sorted_symbols) - 10} more symbols")
        print()
    
    # 7. Learning progress over time
    if len(completed) >= 10:
        print("=" * 80)
        print("📈 LEARNING PROGRESS")
        print("=" * 80)
        
        # Split into early vs recent
        mid_point = len(completed) // 2
        early = completed[mid_point:]  # Older predictions
        recent = completed[:mid_point]  # Newer predictions
        
        early_correct = sum(1 for p in early if p.get('was_correct'))
        early_accuracy = (early_correct / len(early)) * 100
        
        recent_correct = sum(1 for p in recent if p.get('was_correct'))
        recent_accuracy = (recent_correct / len(recent)) * 100
        
        improvement = recent_accuracy - early_accuracy
        
        print(f"Early Predictions (first {len(early)}):  {early_accuracy:.1f}% accuracy")
        print(f"Recent Predictions (last {len(recent)}): {recent_accuracy:.1f}% accuracy")
        print()
        
        if improvement > 0:
            print(f"✅ Improvement: +{improvement:.1f} percentage points")
            print("   ML is learning and getting better!")
        elif improvement < 0:
            print(f"⚠️  Decline: {improvement:.1f} percentage points")
            print("   ML may need retraining or more data")
        else:
            print("➡️  No change in accuracy")
            print("   ML is stable but not improving yet")
        print()
    
    # 8. Recommendations
    print("=" * 80)
    print("💡 RECOMMENDATIONS")
    print("=" * 80)
    
    if not completed:
        print("⏳ Not enough data yet")
        print("   - ML is making predictions but no trades have completed")
        print("   - Wait for trades to close to see accuracy")
        print("   - Check back in a few hours")
    elif len(completed) < 20:
        print("📊 Early Stage (need more data)")
        print(f"   - Only {len(completed)} completed predictions")
        print("   - Need 50-100 predictions for reliable metrics")
        print("   - Keep ML weight at 0.0 (shadow mode)")
        print("   - Continue collecting data")
    elif accuracy < 50:
        print("❌ Poor Performance")
        print(f"   - Accuracy: {accuracy:.1f}% (below random)")
        print("   - ML needs retraining with better features")
        print("   - Keep ML weight at 0.0")
        print("   - Review feature engineering")
    elif accuracy < 55:
        print("⚠️  Below Target")
        print(f"   - Accuracy: {accuracy:.1f}% (below strategy)")
        print("   - ML not adding value yet")
        print("   - Keep ML weight at 0.0")
        print("   - Continue monitoring")
    elif accuracy < 65:
        print("✅ Promising Results")
        print(f"   - Accuracy: {accuracy:.1f}% (competitive)")
        print("   - ML showing potential")
        print("   - Consider pilot mode: ML weight 0.1-0.2")
        print("   - Monitor closely for 1-2 weeks")
    else:
        print("🎯 Excellent Performance!")
        print(f"   - Accuracy: {accuracy:.1f}% (strong)")
        print("   - ML is adding significant value")
        print("   - Ready for pilot mode: ML weight 0.2-0.3")
        print("   - Gradually increase weight if performance holds")
    
    print()
    print("=" * 80)
    print("Analysis complete!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        analyze_ml_shadow_mode()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
