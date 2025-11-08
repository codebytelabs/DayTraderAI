"""
Apply ML Database Migration
Applies the ML tables migration to Supabase database
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def apply_ml_migration():
    """Apply ML database migration"""
    
    print("=" * 60)
    print("ML Database Migration - Sprint 1")
    print("=" * 60)
    print()
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        print("   Please check your .env file")
        return 1
    
    print(f"📡 Connecting to Supabase...")
    print(f"   URL: {supabase_url}")
    print()
    
    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Read migration file
        migration_file = Path(__file__).parent / "supabase_migration_ml_tables.sql"
        
        if not migration_file.exists():
            print(f"❌ Error: Migration file not found: {migration_file}")
            return 1
        
        print(f"📄 Reading migration file...")
        with open(migration_file, 'r') as f:
            sql = f.read()
        
        print(f"   File: {migration_file.name}")
        print(f"   Size: {len(sql)} characters")
        print()
        
        # Execute migration
        print("🚀 Applying migration...")
        print()
        
        # Split SQL into individual statements
        statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
        
        success_count = 0
        error_count = 0
        
        for i, statement in enumerate(statements, 1):
            # Skip comments and empty statements
            if not statement or statement.startswith('--'):
                continue
            
            # Skip DO blocks (they're informational)
            if 'DO $$' in statement:
                continue
            
            try:
                # Execute statement
                supabase.rpc('exec_sql', {'sql': statement}).execute()
                success_count += 1
                
                # Print progress for important statements
                if 'CREATE TABLE' in statement:
                    table_name = statement.split('CREATE TABLE')[1].split('(')[0].strip().split()[0]
                    print(f"   ✅ Created table: {table_name}")
                elif 'CREATE INDEX' in statement:
                    index_name = statement.split('CREATE INDEX')[1].split('ON')[0].strip().split()[0]
                    print(f"   ✅ Created index: {index_name}")
                elif 'CREATE VIEW' in statement or 'CREATE OR REPLACE VIEW' in statement:
                    view_name = statement.split('VIEW')[1].split('AS')[0].strip()
                    print(f"   ✅ Created view: {view_name}")
                    
            except Exception as e:
                error_count += 1
                print(f"   ⚠️  Statement {i} warning: {str(e)[:100]}")
                # Continue with other statements
        
        print()
        print("=" * 60)
        print("Migration Summary")
        print("=" * 60)
        print(f"✅ Successful statements: {success_count}")
        if error_count > 0:
            print(f"⚠️  Warnings: {error_count}")
        print()
        
        # Verify tables were created
        print("🔍 Verifying tables...")
        print()
        
        tables_to_check = [
            'ml_trade_features',
            'ml_models',
            'ml_predictions',
            'ml_performance',
            'position_exits'
        ]
        
        verified_count = 0
        for table in tables_to_check:
            try:
                # Try to query the table
                result = supabase.table(table).select('id').limit(1).execute()
                print(f"   ✅ Table verified: {table}")
                verified_count += 1
            except Exception as e:
                print(f"   ❌ Table not found: {table}")
        
        print()
        print("=" * 60)
        
        if verified_count == len(tables_to_check):
            print("✅ All ML tables created successfully!")
            print()
            print("Next steps:")
            print("1. Set up ML module structure (Task 3)")
            print("2. Begin feature engineering (Tasks 4-8)")
            print("3. Start building the money printer! 🚀")
            return 0
        else:
            print(f"⚠️  Only {verified_count}/{len(tables_to_check)} tables verified")
            print("   Some tables may not have been created correctly")
            return 1
            
    except Exception as e:
        print(f"❌ Error applying migration: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(apply_ml_migration())
