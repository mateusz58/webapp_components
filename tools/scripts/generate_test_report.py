#!/usr/bin/env python3
"""
🧪 Automated Test Report Generator for Component Management System

This script automatically runs all tests and generates comprehensive reports
for QA tracking and development progress monitoring.
"""

import subprocess
import json
import time
import os
import sys
from datetime import datetime
from pathlib import Path

class TestReportGenerator:
    def __init__(self):
        self.start_time = time.time()
        self.report_data = {
            'timestamp': datetime.now().isoformat(),
            'session_id': f"test_session_{int(time.time())}",
            'categories': {},
            'summary': {},
            'issues': [],
            'performance': {},
            'recommendations': []
        }
        
        # Create reports directory
        self.reports_dir = Path('tests/reports')
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        print("🧪 AUTOMATED TEST REPORT GENERATOR")
        print("=" * 50)
    
    def run_unit_tests(self):
        """Run unit tests and collect results"""
        print("\n🔬 Running Unit Tests...")
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "tests/unit/", 
                "-v", "--tb=short", 
                "--json-report", f"--json-report-file={self.reports_dir}/unit_tests.json"
            ], capture_output=True, text=True, timeout=120)
            
            # Parse results
            unit_data = {
                'status': 'passed' if result.returncode == 0 else 'failed',
                'return_code': result.returncode,
                'execution_time': 0,
                'test_count': 0,
                'passed': 0,
                'failed': 0,
                'output': result.stdout[-1000:] if result.stdout else "",  # Last 1000 chars
                'errors': result.stderr[-500:] if result.stderr else ""   # Last 500 chars
            }
            
            # Try to parse JSON report if available
            json_report_path = self.reports_dir / 'unit_tests.json'
            if json_report_path.exists():
                try:
                    with open(json_report_path, 'r') as f:
                        json_data = json.load(f)
                        unit_data['test_count'] = json_data.get('summary', {}).get('total', 0)
                        unit_data['passed'] = json_data.get('summary', {}).get('passed', 0)
                        unit_data['failed'] = json_data.get('summary', {}).get('failed', 0)
                        unit_data['execution_time'] = json_data.get('duration', 0)
                except:
                    pass
            
            # Extract basic info from stdout if JSON parsing failed
            if unit_data['test_count'] == 0 and result.stdout:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'passed' in line and ('failed' in line or 'error' in line):
                        # Look for pattern like "37 passed in 0.69s"
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part.isdigit() and i + 1 < len(parts) and 'passed' in parts[i + 1]:
                                unit_data['test_count'] = int(part)
                                unit_data['passed'] = int(part)
                                break
            
            self.report_data['categories']['unit'] = unit_data
            
            status_emoji = "✅" if unit_data['status'] == 'passed' else "❌"
            print(f"{status_emoji} Unit Tests: {unit_data['passed']} passed, {unit_data['failed']} failed")
            
        except subprocess.TimeoutExpired:
            print("⏱️ Unit tests timed out")
            self.report_data['categories']['unit'] = {
                'status': 'timeout',
                'error': 'Tests timed out after 120 seconds'
            }
        except Exception as e:
            print(f"❌ Unit test execution failed: {e}")
            self.report_data['categories']['unit'] = {
                'status': 'error',
                'error': str(e)
            }
    
    def run_api_tests(self):
        """Run API tests and collect results"""
        print("\n🌐 Running API Tests...")
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "tests/api/", 
                "-v", "--tb=short",
                "--json-report", f"--json-report-file={self.reports_dir}/api_tests.json"
            ], capture_output=True, text=True, timeout=180)
            
            api_data = {
                'status': 'passed' if result.returncode == 0 else 'failed',
                'return_code': result.returncode,
                'execution_time': 0,
                'test_count': 0,
                'passed': 0,
                'failed': 0,
                'output': result.stdout[-1000:] if result.stdout else "",
                'errors': result.stderr[-500:] if result.stderr else ""
            }
            
            # Try to parse JSON report
            json_report_path = self.reports_dir / 'api_tests.json'
            if json_report_path.exists():
                try:
                    with open(json_report_path, 'r') as f:
                        json_data = json.load(f)
                        api_data['test_count'] = json_data.get('summary', {}).get('total', 0)
                        api_data['passed'] = json_data.get('summary', {}).get('passed', 0)
                        api_data['failed'] = json_data.get('summary', {}).get('failed', 0)
                        api_data['execution_time'] = json_data.get('duration', 0)
                except:
                    pass
            
            # Extract from stdout if needed
            if api_data['test_count'] == 0 and result.stdout:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'passed' in line:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part.isdigit() and i + 1 < len(parts) and 'passed' in parts[i + 1]:
                                api_data['passed'] = int(part)
                                break
                    if 'failed' in line:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part.isdigit() and i + 1 < len(parts) and 'failed' in parts[i + 1]:
                                api_data['failed'] = int(part)
                                break
                
                api_data['test_count'] = api_data['passed'] + api_data['failed']
            
            self.report_data['categories']['api'] = api_data
            
            status_emoji = "✅" if api_data['status'] == 'passed' else "❌"
            print(f"{status_emoji} API Tests: {api_data['passed']} passed, {api_data['failed']} failed")
            
        except subprocess.TimeoutExpired:
            print("⏱️ API tests timed out")
            self.report_data['categories']['api'] = {
                'status': 'timeout',
                'error': 'Tests timed out after 180 seconds'
            }
        except Exception as e:
            print(f"❌ API test execution failed: {e}")
            self.report_data['categories']['api'] = {
                'status': 'error',
                'error': str(e)
            }
    
    def check_application_status(self):
        """Check if the application is running"""
        print("\n🔍 Checking Application Status...")
        
        try:
            import requests
            response = requests.get("http://localhost:6002", timeout=5)
            if response.status_code == 200:
                print("✅ Application is running")
                self.report_data['application_status'] = 'running'
                return True
            else:
                print(f"⚠️ Application responded with status {response.status_code}")
                self.report_data['application_status'] = f'error_{response.status_code}'
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Application is not running: {e}")
            self.report_data['application_status'] = 'not_running'
            return False
    
    def run_selenium_smoke_test(self):
        """Run a quick Selenium smoke test"""
        if not self.check_application_status():
            print("⚠️ Skipping Selenium tests - application not running")
            self.report_data['categories']['selenium'] = {
                'status': 'skipped',
                'reason': 'application_not_running'
            }
            return
        
        print("\n🎬 Running Selenium Smoke Test...")
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "tests/selenium/test_simple_visual_demo.py::TestSimpleVisualDemo::test_visual_navigation_demo",
                "-v", "--tb=short"
            ], capture_output=True, text=True, timeout=120)
            
            selenium_data = {
                'status': 'passed' if result.returncode == 0 else 'failed',
                'return_code': result.returncode,
                'execution_time': 0,
                'test_count': 1,
                'passed': 1 if result.returncode == 0 else 0,
                'failed': 0 if result.returncode == 0 else 1,
                'output': result.stdout[-1000:] if result.stdout else "",
                'errors': result.stderr[-500:] if result.stderr else ""
            }
            
            self.report_data['categories']['selenium'] = selenium_data
            
            status_emoji = "✅" if selenium_data['status'] == 'passed' else "❌"
            print(f"{status_emoji} Selenium Smoke Test: {selenium_data['status']}")
            
        except subprocess.TimeoutExpired:
            print("⏱️ Selenium test timed out")
            self.report_data['categories']['selenium'] = {
                'status': 'timeout',
                'error': 'Test timed out after 120 seconds'
            }
        except Exception as e:
            print(f"❌ Selenium test execution failed: {e}")
            self.report_data['categories']['selenium'] = {
                'status': 'error',
                'error': str(e)
            }
    
    def generate_summary(self):
        """Generate test summary and analysis"""
        print("\n📊 Generating Test Summary...")
        
        categories = self.report_data['categories']
        
        # Calculate totals
        total_tests = 0
        total_passed = 0
        total_failed = 0
        categories_passed = 0
        total_categories = len(categories)
        
        for category, data in categories.items():
            if data.get('status') == 'passed':
                categories_passed += 1
            
            total_tests += data.get('test_count', 0)
            total_passed += data.get('passed', 0)
            total_failed += data.get('failed', 0)
        
        # Calculate percentages
        pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        category_success_rate = (categories_passed / total_categories * 100) if total_categories > 0 else 0
        
        execution_time = time.time() - self.start_time
        
        summary = {
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'pass_rate_percentage': round(pass_rate, 1),
            'categories_passed': categories_passed,
            'total_categories': total_categories,
            'category_success_rate': round(category_success_rate, 1),
            'execution_time_seconds': round(execution_time, 2),
            'overall_status': 'EXCELLENT' if pass_rate >= 95 else 'GOOD' if pass_rate >= 85 else 'NEEDS_IMPROVEMENT'
        }
        
        self.report_data['summary'] = summary
        
        # Generate recommendations
        recommendations = []
        
        if total_failed > 0:
            recommendations.append(f"🔧 Fix {total_failed} failing tests before proceeding")
        
        if pass_rate < 90:
            recommendations.append("📈 Increase test coverage to 90%+ target")
        
        if category_success_rate < 100:
            failed_categories = [cat for cat, data in categories.items() if data.get('status') != 'passed']
            recommendations.append(f"⚠️ Address issues in: {', '.join(failed_categories)}")
        
        if execution_time > 120:
            recommendations.append("⚡ Consider optimizing test execution time")
        
        if not recommendations:
            recommendations.append("🎉 All tests passing - excellent work!")
        
        self.report_data['recommendations'] = recommendations
    
    def save_reports(self):
        """Save all generated reports"""
        print("\n💾 Saving Test Reports...")
        
        # Save JSON report
        json_report_path = self.reports_dir / 'latest_test_report.json'
        with open(json_report_path, 'w') as f:
            json.dump(self.report_data, f, indent=2)
        
        # Generate markdown summary
        self.generate_markdown_report()
        
        print(f"✅ Reports saved:")
        print(f"   📄 JSON Report: {json_report_path}")
        print(f"   📋 Markdown Summary: {self.reports_dir}/test_summary.md")
    
    def generate_markdown_report(self):
        """Generate a markdown summary report"""
        summary = self.report_data['summary']
        categories = self.report_data['categories']
        
        markdown_content = f"""# 🧪 Automated Test Report Summary

**Generated**: {self.report_data['timestamp']}  
**Session ID**: {self.report_data['session_id']}

## 📊 Executive Summary

| Metric | Value | Status |
|--------|-------|--------|
| **Total Tests** | {summary['total_tests']} | - |
| **Tests Passed** | {summary['total_passed']} | {'✅' if summary['total_passed'] > 0 else '⚠️'} |
| **Tests Failed** | {summary['total_failed']} | {'❌' if summary['total_failed'] > 0 else '✅'} |
| **Pass Rate** | {summary['pass_rate_percentage']}% | {'✅' if summary['pass_rate_percentage'] >= 90 else '⚠️'} |
| **Categories Passed** | {summary['categories_passed']}/{summary['total_categories']} | {'✅' if summary['category_success_rate'] == 100 else '⚠️'} |
| **Execution Time** | {summary['execution_time_seconds']}s | {'✅' if summary['execution_time_seconds'] < 60 else '⚠️'} |
| **Overall Status** | {summary['overall_status']} | {'✅' if summary['overall_status'] == 'EXCELLENT' else '⚠️'} |

## 🎯 Test Category Results

"""
        
        for category, data in categories.items():
            status_emoji = "✅" if data.get('status') == 'passed' else "❌" if data.get('status') == 'failed' else "⚠️"
            markdown_content += f"""### {status_emoji} {category.title()} Tests
- **Status**: {data.get('status', 'unknown')}
- **Tests**: {data.get('passed', 0)} passed, {data.get('failed', 0)} failed
- **Execution Time**: {data.get('execution_time', 0)}s

"""
        
        if self.report_data['recommendations']:
            markdown_content += "## 🎯 Recommendations\n\n"
            for rec in self.report_data['recommendations']:
                markdown_content += f"- {rec}\n"
            markdown_content += "\n"
        
        markdown_content += f"""## 📈 Performance Metrics

- **Test Execution Speed**: {summary['execution_time_seconds']}s for {summary['total_tests']} tests
- **Average Test Time**: {round(summary['execution_time_seconds'] / max(summary['total_tests'], 1), 3)}s per test
- **System Health**: {summary['overall_status']}

## 🔍 Next Steps

"""
        
        if summary['total_failed'] > 0:
            markdown_content += "1. **Priority**: Fix failing tests before proceeding\n"
        
        markdown_content += """2. **Maintain**: Keep test coverage above 90%
3. **Monitor**: Regular test execution during development
4. **Document**: Update test_report.md with findings

---
*Report generated by Automated Test Report Generator*
"""
        
        # Save markdown report
        markdown_path = self.reports_dir / 'test_summary.md'
        with open(markdown_path, 'w') as f:
            f.write(markdown_content)
    
    def print_final_summary(self):
        """Print final test summary to console"""
        summary = self.report_data['summary']
        
        print("\n" + "=" * 60)
        print("🎯 FINAL TEST SUMMARY")
        print("=" * 60)
        
        print(f"📊 Tests: {summary['total_passed']}/{summary['total_tests']} passed ({summary['pass_rate_percentage']}%)")
        print(f"⏱️  Time: {summary['execution_time_seconds']}s")
        print(f"🏆 Status: {summary['overall_status']}")
        
        if self.report_data['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in self.report_data['recommendations']:
                print(f"   {rec}")
        
        print(f"\n📁 Reports saved in: tests/reports/")
        print("=" * 60)
    
    def run_full_report(self):
        """Run complete test report generation"""
        try:
            # Run all test categories
            self.run_unit_tests()
            self.run_api_tests()
            self.run_selenium_smoke_test()
            
            # Generate analysis
            self.generate_summary()
            
            # Save reports
            self.save_reports()
            
            # Print summary
            self.print_final_summary()
            
            return True
            
        except KeyboardInterrupt:
            print("\n⏹️  Test report generation interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Test report generation failed: {e}")
            return False


def main():
    """Main entry point"""
    generator = TestReportGenerator()
    success = generator.run_full_report()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()