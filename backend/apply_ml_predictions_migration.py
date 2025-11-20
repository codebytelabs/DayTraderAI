#!/usr/bin/env python3
"""
Apply ML Predictions Table Migration
Creates the ml_predictions table in Supabase
"""

import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from core.supabase_client import SupabaseClient


def apply_migration():
    """Apply ML predictions table migration"""
    
    print("=" * 80)
    print("🔧 APPLYING ML PREDICTIONS TABLE MIGRATION")
    print("=" * 80)
    print()
    
    # Read SQL file
    sql_file = os.path.join(os.path.dirname(__file__), 'create_ml_predictions_table.sql')
    
    with open(sql_file, 'r') as f:
        sql = f.read()
    
    print("📄 SQL Migration:")
    print("-" * 80)
    print(sql[:500] + "..." if len(sql) > 500 else sql)
    print("-" * 80)
    print()
    
    # Connect to Supabase
    print("🔌 Connecting to Supabase...")
    client = SupabaseClient()
    print("✅ Connected")
    print()
    
    # Execute migration
    print("⚙️  Executing migration...")
    try:
        # Note: Supabase Python client doesn't support raw SQL execution
        # You need to run this SQL in the Supabase SQL Editor
        print()
        print("⚠️  MANUAL STEP REQUIRED:")
        print()
        print("The Supabase Python client doesn't support raw SQL execution.")
        print("Please follow these steps:")
        print()
        print("1. Go to your Supabase dashboard: https://supabase.com/dashboard")
        print("2. Select your project")
        print("3. Click 'SQL Editor' in the left sidebar")
        print("4. Click 'New Query'")
        print("5. Copy and paste the SQL from: backend/create_ml_predictions_table.sql")
        print("6. Click 'Run' to execute")
        print()
        print("Alternatively, you can copy this SQL:")
        print()
        print("=" * 80)
        print(sql)
        print("=" * 80)
        print()
        
        # Test if table exists
        print("🔍 Testing if table exists...")
        try:
            result = client.client.table('ml_predictions').select('*').limit(1).execute()
            print("✅ Table 'ml_predictions' exists!")
            print(f"   Records found: {len(result.data)}")
            return True
        except Exception as e:
            print(f"❌ Table 'ml_predictions' does not exist yet")
            print(f"   Error: {e}")
            print()
            print("Please create the table using the SQL above.")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = apply_migration()
    
    if success:
        print()
        print("=" * 80)
        print("✅ MIGRATION COMPLETE!")
        print("=" * 80)
        print()
        print("Next steps:")
        print("1. Restart your backend: python main.py")
        print("2. ML Shadow Mode will now log predictions")
        print("3. Check predictions: python analyze_ml_shadow_mode.py")
    else:
        print()
        print("=" * 80)
        print("⚠️  MIGRATION INCOMPLETE")
        print("=" * 80)
        print()
        print("Please create the table manually in Supabase SQL Editor")
        sys.exit(1)
