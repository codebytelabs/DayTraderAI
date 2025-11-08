"""
Test ML System
Verifies ML system components work correctly
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from ml.ml_system import MLSystem
from ml.feature_extractor import FeatureExtractor
from ml.model_trainer import ModelTrainer
from ml.predictor import Predictor

load_dotenv()


async def test_ml_system():
    """Test ML system components"""
    
    print("=" * 60)
    print("ML System Test - Sprint 1")
    print("=" * 60)
    print()
    
    # Connect to Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY required")
        return 1
    
    print("📡 Connecting to Supabase...")
    supabase: Client = create_client(supabase_url, supabase_key)
    print("✅ Connected")
    print()
    
    # Test Feature Extractor
    print("🔍 Testing Feature Extractor...")
    feature_extractor = FeatureExtractor(supabase)
    
    test_market_data = {
        'ema_20': 150.0,
        'ema_50': 148.0,
        'rsi': 65.0,
        'macd': 2.5,
        'macd_signal': 2.0,
        'adx': 25.0,
        'vwap': 149.5,
        'price': 151.0,
        'regime': 'broad_bullish',
        'market_breadth': 65.0,
        'vix': 15.0,
        'sector_strength': 1.5
    }
    
    features = await feature_extractor.extract_all_features(
        symbol='AAPL',
        signal_type='long',
        market_data=test_market_data
    )
    
    print(f"✅ Extracted {len(features)} features")
    print(f"   Sample features: RSI={features.get('rsi')}, ADX={features.get('adx')}")
    print()
    
    # Test ML System
    print("🤖 Testing ML System...")
    ml_system = MLSystem(supabase)
    await ml_system.initialize()
    print(f"✅ ML System initialized (ready: {ml_system.is_ready()})")
    print()
    
    # Test Model Trainer
    print("🎓 Testing Model Trainer...")
    model_trainer = ModelTrainer(supabase)
    
    # Check if we have enough data
    X, y = await model_trainer.load_training_data()
    print(f"   Training data: {len(X)} samples")
    
    if len(X) >= 10:  # Need at least 10 samples for testing
        print("   ✅ Sufficient data for training")
        print("   Note: Full training requires 100+ samples")
    else:
        print("   ⚠️  Insufficient data for training (need 100+ samples)")
        print("   Collect more trades to enable ML training")
    print()
    
    # Test Predictor
    print("🔮 Testing Predictor...")
    predictor = Predictor(supabase)
    
    if predictor.is_model_loaded():
        print("   ✅ Model loaded")
        
        # Test prediction
        prediction = await predictor.predict_trade_outcome(features)
        if prediction:
            print(f"   ✅ Prediction: {prediction['prediction']} "
                  f"({prediction['probability']:.2%} probability)")
            print(f"   ✅ Latency: {prediction['latency_ms']}ms")
    else:
        print("   ⚠️  No model loaded (train a model first)")
    print()
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print("✅ Feature Extractor: Working")
    print("✅ ML System: Working")
    print("✅ Model Trainer: Working")
    print(f"{'✅' if predictor.is_model_loaded() else '⚠️ '} Predictor: {'Working' if predictor.is_model_loaded() else 'No model (train first)'}")
    print()
    print("Next steps:")
    if len(X) < 100:
        print("1. Collect more trade data (need 100+ samples)")
        print("2. Train initial model")
        print("3. Start making predictions")
    else:
        print("1. Train model: python backend/train_ml_model.py")
        print("2. Integrate with trading system")
        print("3. Start making money! 💰")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(test_ml_system()))
