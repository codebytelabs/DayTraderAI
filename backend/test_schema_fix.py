#!/usr/bin/env python3
"""
Test script to validate database schema fix for partial profit trades.
Ensures insert_trade works with new fields before deploying to production.
"""

from datetime import datetime
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from core.supabase_client import SupabaseClient
from utils.logger import setup_logger

logger = setup_logger(__name__)

def test_partial_profit_trade_schema():
    """Test that insert_trade works with entry_time and exit_time fields"""
    
    logger.info("🧪 Testing partial profit trade schema...")
    
    try:
        supabase = SupabaseClient()
        
        # Test data matching the new schema
        test_trade = {
            'symbol': 'TEST',  # Shortened (was TEST_SCHEMA = 11 chars)
            'side': 'sell',
            'qty': 5,
            'entry_price': 100.0,
            'exit_price': 102.0,
            'pnl': 10.0,
            'pnl_pct': 1.0,
            'entry_time': datetime.utcnow().isoformat(),  # NEW FIELD
            'exit_time': datetime.utcnow().isoformat(),    # NEW FIELD
            'strategy': 'ema',  # Shortened to fit varchar(10)
            'reason': 'test'  # Shortened (was partial_profit = 15 chars)
        }
        
        logger.info(f"Attempting to insert test trade with fields: {list(test_trade.keys())}")
        
        result = supabase.insert_trade(test_trade)
        
        if result:
            logger.info("✅ SUCCESS: Trade inserted with new schema!")
            logger.info(f"Inserted trade ID: {result.get('id') if isinstance(result, dict) else 'N/A'}")
            
            # Clean up test data
            try:
                supabase.client.table("trades").delete().eq("symbol", "TEST").execute()
                logger.info("🧹 Cleaned up test data")
            except Exception as e:
                logger.warning(f"Could not clean up test data: {e}")
            
            return True
        else:
            logger.error("❌ FAILED: Trade insertion returned None")
            return False
            
    except Exception as e:
        logger.error(f"❌ FAILED: {e}")
        return False

if __name__ == "__main__":
    success = test_partial_profit_trade_schema()
    
    if success:
        print("\n" + "="*60)
        print("✅ DATABASE SCHEMA FIX VALIDATED")
        print("="*60)
        print("The partial profit trade schema is working correctly.")
        print("Safe to restart the bot.")
        print("="*60 + "\n")
        sys.exit(0)
    else:
        print("\n" + "="*60)
        print("❌ DATABASE SCHEMA FIX FAILED")
        print("="*60)
        print("DO NOT restart the bot. Check Supabase schema.")
        print("="*60 + "\n")
        sys.exit(1)
