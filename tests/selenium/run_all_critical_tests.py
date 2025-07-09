#!/usr/bin/env python3
"""
Run all critical Selenium tests
This script runs the most important tests to ensure system functionality
"""
import unittest
import sys
import os
from component_deletion.test_bulk_deletion_working import BulkDeletionWorkingTest
from component_deletion.test_component_deletion_api_integration import ComponentDeletionAPIIntegrationTestCase

class CriticalTestSuite:
    """Run all critical tests"""
    
    def run_all_tests(self):
        """Run all critical tests and report results"""
        # Create test suite
        suite = unittest.TestSuite()
        
        # Add critical tests
        suite.addTest(unittest.makeSuite(BulkDeletionWorkingTest))
        suite.addTest(unittest.makeSuite(ComponentDeletionAPIIntegrationTestCase))
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Report results
        if result.wasSuccessful():
            print("\n✅ ALL CRITICAL TESTS PASSED!")
            return True
        else:
            print(f"\n❌ {len(result.failures)} FAILURES, {len(result.errors)} ERRORS")
            for test, error in result.failures + result.errors:
                print(f"FAILED: {test}")
                print(f"ERROR: {error}")
            return False

if __name__ == '__main__':
    suite = CriticalTestSuite()
    success = suite.run_all_tests()
    sys.exit(0 if success else 1)