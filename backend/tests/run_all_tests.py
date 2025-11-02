#!/usr/bin/env python3
"""
Master Test Runner
Executes all comprehensive tests and generates final report
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('master_test_results.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def run_api_tests():
    """Run API tests"""
    logger.info("\n" + "="*80)
    logger.info("PHASE 1: API TESTING")
    logger.info("="*80 + "\n")
    
    try:
        from test_real_apis import RealAPITester
        tester = RealAPITester()
        await tester.run_all_tests()
        return tester.results
    except Exception as e:
        logger.error(f"API tests failed: {e}")
        return None

async def main():
    """Main test execution"""
    logger.info("\n" + "="*100)
    logger.info("🚀 DAYTRADERAI COMPREHENSIVE TEST SUITE")
    logger.info("="*100 + "\n")
    
    start_time = datetime.now()
    
    # Run all test phases
    api_results = await run_api_tests()
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    # Generate final report
    logger.info("\n" + "="*100)
    logger.info("📊 FINAL TEST REPORT")
    logger.info("="*100)
    logger.info(f"Total Duration: {duration.total_seconds():.1f} seconds")
    logger.info(f"Completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Calculate overall statistics
    if api_results:
        total_tests = sum(len(data['tests']) for data in api_results.values())
        passed_tests = sum(
            sum(1 for test in data['tests'] if test['success'])
            for data in api_results.values()
        )
        failed_tests = total_tests - passed_tests
        
        logger.info(f"\n📈 OVERALL STATISTICS:")
        logger.info(f"   Total Tests: {total_tests}")
        logger.info(f"   Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
        logger.info(f"   Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
        
        if failed_tests == 0:
            logger.info("\n🎉 ALL TESTS PASSED! System is ready for production.")
        elif failed_tests < total_tests * 0.1:
            logger.info("\n✅ EXCELLENT! Minor issues to address.")
        elif failed_tests < total_tests * 0.2:
            logger.info("\n⚠️  GOOD! Some issues to address.")
        else:
            logger.error("\n❌ ATTENTION NEEDED! Review failed tests.")
    
    logger.info("="*100 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
