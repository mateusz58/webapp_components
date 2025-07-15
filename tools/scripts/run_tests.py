#!/usr/bin/env python3
"""
Comprehensive Test Runner for Component Management System
MANDATORY: ALL tests must pass before proceeding with any development work

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --unit             # Run only unit tests
    python run_tests.py --integration      # Run only integration tests
    python run_tests.py --api              # Run only API tests
    python run_tests.py --selenium         # Run only Selenium tests
    python run_tests.py --fast             # Run fast tests only (unit + integration)
    python run_tests.py --coverage         # Run with coverage report
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ FAILED: {description}")
        print(f"Exit code: {e.returncode}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Comprehensive Test Runner")
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--api', action='store_true', help='Run API tests only')
    parser.add_argument('--selenium', action='store_true', help='Run Selenium tests only')
    parser.add_argument('--fast', action='store_true', help='Run fast tests (unit + integration)')
    parser.add_argument('--coverage', action='store_true', help='Run with coverage report')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Change to project directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("🚀 Component Management System - Test Runner")
    print("=" * 60)
    print("CRITICAL: All tests MUST pass before proceeding with development!")
    print("=" * 60)
    
    # Base pytest command
    base_cmd = ['python', '-m', 'pytest']
    
    if args.verbose:
        base_cmd.append('-v')
    
    # Determine which tests to run
    test_paths = []
    test_descriptions = []
    
    if args.unit:
        test_paths.append('tests/unit/')
        test_descriptions.append("Unit Tests")
    elif args.integration:
        test_paths.append('tests/integration/')
        test_descriptions.append("Integration Tests")
    elif args.api:
        test_paths.append('tests/api/')
        test_descriptions.append("API Tests")
    elif args.selenium:
        test_paths.append('tests/selenium/')
        test_descriptions.append("Selenium E2E Tests")
    elif args.fast:
        test_paths.extend(['tests/unit/', 'tests/integration/'])
        test_descriptions.append("Fast Tests (Unit + Integration)")
    else:
        # Run all tests
        test_paths.extend(['tests/unit/', 'tests/integration/', 'tests/api/', 'tests/selenium/'])
        test_descriptions.append("All Tests")
    
    # Add coverage if requested
    if args.coverage:
        base_cmd.extend(['--cov=app', '--cov-report=html', '--cov-report=term'])
    
    all_passed = True
    
    # Run tests for each category
    for i, test_path in enumerate(test_paths):
        if os.path.exists(test_path):
            cmd = base_cmd + [test_path]
            description = test_descriptions[0] if len(test_descriptions) == 1 else f"Testing {test_path}"
            
            success = run_command(cmd, description)
            if not success:
                all_passed = False
                if not args.verbose:
                    print("❌ STOPPING: Tests failed. Fix failures before proceeding!")
                    break
        else:
            print(f"⚠️  Warning: Test directory {test_path} does not exist")
    
    # Final results
    print(f"\n{'='*60}")
    if all_passed:
        print("✅ ALL TESTS PASSED! ✅")
        print("✅ Safe to proceed with development work.")
        print(f"{'='*60}")
        sys.exit(0)
    else:
        print("❌ TESTS FAILED! ❌")
        print("❌ DO NOT PROCEED until all tests pass!")
        print("❌ Fix failing tests before continuing development.")
        print(f"{'='*60}")
        sys.exit(1)

if __name__ == '__main__':
    main()