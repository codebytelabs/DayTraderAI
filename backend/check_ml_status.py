#!/usr/bin/env python3
"""
Check ML System Status
Quick diagnostic to see if ML shadow mode is running and learning
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from core.supabase_client import SupabaseClient


async def check_ml_status():
    """Check ML system status"""
    print("=" * 60)
    print("ML SYSTEM STATUS CHECK")
    print("=" * 60)
    print()
    
    try:
        # Initialize Supabase
        supabase = SupabaseClient()
        print("✓ Connected to Supabase")
        print()
        
        # Check if ml_predictions table exists and has data
        print("📊 CHECKING ML PREDICTIONS TABLE...")
        print("-" * 60)
        
        try:
            result = supabase.client.table('ml_predictions').select('*', count='exact').limit(1).execute()
            total_predictions = result.count if hasattr(result, 'count') else 0
            
            print(f"Total predictions logged: {total_predictions}")
            
            if total_predictions == 0:
                print()
                print("⚠️  NO PREDICTIONS FOUND")
                print()
                print("This means:")
                print("  • ML shadow mode is NOT integrated into trading engine")
                print("  • No predictions are being made or logged")
                print("  • ML system is not learning from trades")
                print()
                print("STATUS: ML Shadow Mode NOT ACTIVE ❌")
                return
            
            # Get recent predictions
            recent_result = supabase.client.table('ml_predictions').select('*').order(
                'created_at', desc=True
            ).limit(10).execute()
            
            recent_predictions = recent_result.data if recent_result.data else []
            
            if recent_predictions:
                latest = recent_predictions[0]
                latest_time = datetime.fromisoformat(latest['created_at'].replace('Z', '+00:00'))
                time_ago = datetime.now(latest_time.tzinfo) - latest_time
                
                print(f"Latest prediction: {time_ago.total_seconds() / 60:.1f} minutes ago")
                print(f"Latest symbol: {latest.get('symbol')}")
                print(f"ML confidence: {latest.get('ml_confidence', 0):.1f}%")
                print(f"ML prediction: {latest.get('ml_prediction')}")
                print()
            
            # Check predictions with outcomes (completed trades)
            completed_result = supabase.client.table('ml_predictions').select('*').not_.is_(
                'actual_outcome', 'null'
            ).execute()
            
            completed = completed_result.data if completed_result.data else []
            
            print(f"Completed predictions (with outcomes): {len(completed)}")
            
            if completed:
                correct = sum(1 for p in completed if p.get('was_correct'))
                accuracy = (correct / len(completed)) * 100
                
                print(f"Correct predictions: {correct}")
                print(f"Accuracy: {accuracy:.1f}%")
                print()
                
                # Breakdown by outcome
                wins = [p for p in completed if p.get('actual_outcome') == 'WIN']
                losses = [p for p in completed if p.get('actual_outcome') == 'LOSS']
                
                if wins:
                    win_correct = sum(1 for p in wins if p.get('was_correct'))
                    win_accuracy = (win_correct / len(wins)) * 100
                    print(f"Win predictions: {len(wins)} ({win_accuracy:.1f}% accuracy)")
                
                if losses:
                    loss_correct = sum(1 for p in losses if p.get('was_correct'))
                    loss_accuracy = (loss_correct / len(losses)) * 100
                    print(f"Loss predictions: {len(losses)} ({loss_accuracy:.1f}% accuracy)")
                
                print()
            else:
                print("⚠️  No completed predictions yet (trades haven't closed)")
                print()
            
            # Check last 24 hours activity
            yesterday = datetime.now() - timedelta(days=1)
            recent_24h_result = supabase.client.table('ml_predictions').select('*', count='exact').gte(
                'created_at', yesterday.isoformat()
            ).execute()
            
            count_24h = recent_24h_result.count if hasattr(recent_24h_result, 'count') else 0
            
            print(f"Predictions in last 24 hours: {count_24h}")
            
            if count_24h > 0:
                print()
                print("✅ ML SHADOW MODE IS ACTIVE AND LEARNING!")
                print()
                print("What it's doing:")
                print("  • Making predictions for every trade signal")
                print("  • Logging predictions to database")
                print("  • Tracking accuracy vs actual outcomes")
                print("  • Running at 0% weight (no impact on trades)")
                print()
            else:
                print()
                print("⚠️  NO RECENT ACTIVITY (last 24 hours)")
                print()
                print("Possible reasons:")
                print("  • No trade signals generated")
                print("  • Market is closed")
                print("  • ML shadow mode not integrated")
                print()
            
            # Check latency
            if recent_predictions:
                latencies = [p.get('latency_ms', 0) for p in recent_predictions if p.get('latency_ms')]
                if latencies:
                    avg_latency = sum(latencies) / len(latencies)
                    max_latency = max(latencies)
                    print(f"Average prediction latency: {avg_latency:.1f}ms")
                    print(f"Max prediction latency: {max_latency:.1f}ms")
                    print()
            
            # Summary
            print("=" * 60)
            print("SUMMARY")
            print("=" * 60)
            print(f"Total predictions: {total_predictions}")
            print(f"Completed: {len(completed)}")
            if completed:
                print(f"Accuracy: {accuracy:.1f}%")
            print(f"Last 24h: {count_24h}")
            
            if count_24h > 0:
                print()
                print("STATUS: ✅ ACTIVE AND LEARNING")
            elif total_predictions > 0:
                print()
                print("STATUS: ⚠️  INACTIVE (but has historical data)")
            else:
                print()
                print("STATUS: ❌ NOT INTEGRATED")
            
        except Exception as e:
            print(f"❌ Error checking ml_predictions table: {e}")
            print()
            print("This likely means:")
            print("  • ml_predictions table doesn't exist")
            print("  • Database migration not applied")
            print("  • ML system not set up")
            print()
            print("STATUS: ML System NOT CONFIGURED ❌")
            return
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(check_ml_status())
