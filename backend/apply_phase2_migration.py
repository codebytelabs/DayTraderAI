#!/usr/bin/env python3
"""Apply Phase 2 database migration."""

import sys
from core.supabase_client import supabase_client
from utils.logger import setup_logger

logger = setup_logger(__name__)


def check_opportunities_table():
    """Check if opportunities table exists."""
    try:
        result = supabase_client.client.table("opportunities").select("*").limit(1).execute()
        return True
    except Exception as e:
        if "relation" in str(e).lower() and "does not exist" in str(e).lower():
            return False
        logger.error(f"Error checking table: {e}")
        return False


def apply_migration():
    """Apply Phase 2 migration."""
    try:
        logger.info("Applying Phase 2 migration...")
        
        # Read migration file
        with open('supabase_migration_phase2_opportunities.sql', 'r') as f:
            sql = f.read()
        
        # Execute migration
        # Note: Supabase client doesn't support raw SQL execution
        # User needs to apply this manually via Supabase dashboard
        
        logger.warning("⚠️  Please apply migration manually:")
        logger.warning("   1. Go to Supabase Dashboard → SQL Editor")
        logger.warning("   2. Copy contents of: backend/supabase_migration_phase2_opportunities.sql")
        logger.warning("   3. Run the migration")
        
        return False
        
    except Exception as e:
        logger.error(f"Error applying migration: {e}")
        return False


def main():
    """Main function."""
    logger.info("=" * 60)
    logger.info("PHASE 2: DATABASE MIGRATION CHECK")
    logger.info("=" * 60)
    
    # Check if table exists
    logger.info("\nChecking if opportunities table exists...")
    
    if check_opportunities_table():
        logger.info("✓ Opportunities table already exists!")
        logger.info("✓ Phase 2 migration already applied")
        return True
    else:
        logger.warning("✗ Opportunities table does not exist")
        logger.warning("\n📋 MANUAL MIGRATION REQUIRED:")
        logger.warning("   File: backend/supabase_migration_phase2_opportunities.sql")
        logger.warning("\n   Steps:")
        logger.warning("   1. Open Supabase Dashboard")
        logger.warning("   2. Go to SQL Editor")
        logger.warning("   3. Copy/paste the migration file")
        logger.warning("   4. Click 'Run'")
        logger.warning("   5. Restart this script")
        return False


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Migration check failed: {e}", exc_info=True)
        sys.exit(1)
