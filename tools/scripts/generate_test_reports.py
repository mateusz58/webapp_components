#!/usr/bin/env python3
import sys
import os
import subprocess
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class TestReportGenerator:
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.reports_dir = self.project_root / "docs" / "test_reports_generated"
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def setup_reports_directory(self):
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
    def run_unit_tests(self):
        print("🧪 Running unit tests...")
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "tests/unit/",
                "-v", "--tb=short",
                f"--junitxml={self.reports_dir}/unit_tests_{self.timestamp}.xml",
                "--json-report", f"--json-report-file={self.reports_dir}/unit_tests_{self.timestamp}.json"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            return {
                "type": "unit",
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "passed": result.returncode == 0
            }
        except Exception as e:
            return {
                "type": "unit", 
                "exit_code": -1,
                "error": str(e),
                "passed": False
            }
    
    def run_integration_tests(self):
        print("🔗 Running integration tests...")
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                "tests/integration/", 
                "-v", "--tb=short",
                f"--junitxml={self.reports_dir}/integration_tests_{self.timestamp}.xml",
                "--json-report", f"--json-report-file={self.reports_dir}/integration_tests_{self.timestamp}.json"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            return {
                "type": "integration",
                "exit_code": result.returncode, 
                "stdout": result.stdout,
                "stderr": result.stderr,
                "passed": result.returncode == 0
            }
        except Exception as e:
            return {
                "type": "integration",
                "exit_code": -1, 
                "error": str(e),
                "passed": False
            }
    
    def run_selenium_tests(self):
        print("🌐 Running Selenium tests...")
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                "tests/selenium/",
                "-v", "--tb=short", 
                f"--junitxml={self.reports_dir}/selenium_tests_{self.timestamp}.xml",
                "--json-report", f"--json-report-file={self.reports_dir}/selenium_tests_{self.timestamp}.json"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            return {
                "type": "selenium",
                "exit_code": result.returncode,
                "stdout": result.stdout, 
                "stderr": result.stderr,
                "passed": result.returncode == 0
            }
        except Exception as e:
            return {
                "type": "selenium",
                "exit_code": -1,
                "error": str(e), 
                "passed": False
            }
    
    def generate_summary_report(self, test_results):
        summary = {
            "timestamp": datetime.now().isoformat(),
            "project": "Component Management System",
            "test_suites": len(test_results),
            "overall_status": all(r["passed"] for r in test_results),
            "results": test_results
        }
        
        summary_file = self.reports_dir / f"test_summary_{self.timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        markdown_report = self.generate_markdown_summary(summary)
        markdown_file = self.reports_dir / f"test_summary_{self.timestamp}.md"
        with open(markdown_file, 'w') as f:
            f.write(markdown_report)
            
        return summary_file, markdown_file
    
    def generate_markdown_summary(self, summary):
        status_icon = "✅" if summary["overall_status"] else "❌"
        
        md_content = f"""# Test Report Summary
        
**Timestamp**: {summary["timestamp"]}  
**Project**: {summary["project"]}  
**Overall Status**: {status_icon} {"PASSED" if summary["overall_status"] else "FAILED"}

## Test Suite Results

"""
        
        for result in summary["results"]:
            test_type = result["type"].title()
            test_status = "✅ PASSED" if result["passed"] else "❌ FAILED"
            
            md_content += f"### {test_type} Tests\n"
            md_content += f"**Status**: {test_status}  \n"
            md_content += f"**Exit Code**: {result['exit_code']}  \n"
            
            if "error" in result:
                md_content += f"**Error**: {result['error']}  \n"
            
            md_content += "\n"
        
        return md_content
    
    def update_main_test_reports(self, summary_file, markdown_file):
        test_reports_file = self.project_root / "docs" / "test_reports.md"
        
        if test_reports_file.exists():
            with open(test_reports_file, 'r') as f:
                existing_content = f.read()
        else:
            existing_content = """# Test Reports

This file contains chronological test execution reports for the Component Management System.

## Test Report History
"""
        
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        summary_path = summary_file.relative_to(self.project_root)
        markdown_path = markdown_file.relative_to(self.project_root)
        
        new_entry = f"""
### {timestamp_str}
- **Summary JSON**: `{summary_path}`
- **Summary Markdown**: `{markdown_path}`
- **Generated**: {timestamp_str}

"""
        
        lines = existing_content.split('\n')
        insert_index = -1
        for i, line in enumerate(lines):
            if line.strip() == "## Test Report History":
                insert_index = i + 1
                break
        
        if insert_index > -1:
            lines.insert(insert_index, new_entry)
            updated_content = '\n'.join(lines)
        else:
            updated_content = existing_content + new_entry
        
        with open(test_reports_file, 'w') as f:
            f.write(updated_content)
    
    def cleanup_old_reports(self, keep_last=10):
        json_reports = sorted(
            self.reports_dir.glob("test_summary_*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        for old_report in json_reports[keep_last:]:
            timestamp = old_report.stem.split('_')[-1]
            
            related_files = [
                self.reports_dir / f"test_summary_{timestamp}.md",
                self.reports_dir / f"unit_tests_{timestamp}.xml",
                self.reports_dir / f"integration_tests_{timestamp}.xml", 
                self.reports_dir / f"selenium_tests_{timestamp}.xml",
                self.reports_dir / f"unit_tests_{timestamp}.json",
                self.reports_dir / f"integration_tests_{timestamp}.json",
                self.reports_dir / f"selenium_tests_{timestamp}.json"
            ]
            
            old_report.unlink()
            for related_file in related_files:
                if related_file.exists():
                    related_file.unlink()
    
    def run_all_tests(self):
        print("🚀 Component Management System - Test Report Generator")
        print("=" * 60)
        
        self.setup_reports_directory()
        
        test_results = []
        
        test_results.append(self.run_unit_tests())
        test_results.append(self.run_integration_tests())
        test_results.append(self.run_selenium_tests())
        
        summary_file, markdown_file = self.generate_summary_report(test_results)
        self.update_main_test_reports(summary_file, markdown_file)
        self.cleanup_old_reports()
        
        print("\n" + "=" * 60)
        print("📊 Test Report Generation Complete")
        print(f"📁 Reports saved to: {self.reports_dir}")
        print(f"📄 Summary: {markdown_file}")
        
        overall_passed = all(r["passed"] for r in test_results)
        if overall_passed:
            print("🎉 All test suites passed!")
            return 0
        else:
            print("❌ Some test suites failed")
            return 1

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Report Generator")
    parser.add_argument(
        '--project-root',
        default='.',
        help='Project root directory (default: current directory)'
    )
    parser.add_argument(
        '--unit-only',
        action='store_true',
        help='Run only unit tests'
    )
    parser.add_argument(
        '--integration-only', 
        action='store_true',
        help='Run only integration tests'
    )
    parser.add_argument(
        '--selenium-only',
        action='store_true',
        help='Run only Selenium tests'
    )
    
    args = parser.parse_args()
    
    generator = TestReportGenerator(args.project_root)
    
    if args.unit_only:
        generator.setup_reports_directory()
        result = generator.run_unit_tests()
        return 0 if result["passed"] else 1
    elif args.integration_only:
        generator.setup_reports_directory() 
        result = generator.run_integration_tests()
        return 0 if result["passed"] else 1
    elif args.selenium_only:
        generator.setup_reports_directory()
        result = generator.run_selenium_tests()
        return 0 if result["passed"] else 1
    else:
        return generator.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())