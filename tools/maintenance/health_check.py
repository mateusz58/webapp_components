#!/usr/bin/env python3
"""
System Health Check Tool
Performs comprehensive health checks on the Component Management System
"""
import sys
import os
import requests
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app import create_app, db
from app.models import Component, ComponentVariant, Picture

class HealthChecker:
    """System health checker"""
    
    def __init__(self, base_url="http://localhost:6002"):
        self.base_url = base_url
        self.results = []
        self.app = create_app()
    
    def log_check(self, name, status, message="", details=None):
        """Log a health check result"""
        result = {
            'name': name,
            'status': status,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {name}: {message}")
        if details:
            print(f"   Details: {details}")
    
    def check_database_connection(self):
        """Check database connectivity"""
        try:
            with self.app.app_context():
                component_count = Component.query.count()
                variant_count = ComponentVariant.query.count()
                
                self.log_check(
                    "Database Connection", 
                    "PASS",
                    f"Connected successfully",
                    f"Components: {component_count}, Variants: {variant_count}"
                )
                return True
        except Exception as e:
            self.log_check(
                "Database Connection",
                "FAIL", 
                f"Connection failed: {str(e)}"
            )
            return False
    
    def check_webdav_connectivity(self):
        """Check WebDAV storage connectivity"""
        try:
            webdav_url = "http://31.182.67.115/webdav/components"
            response = requests.head(webdav_url, timeout=10)
            
            if response.status_code in [200, 401]:  # 401 is OK, means auth required
                self.log_check(
                    "WebDAV Storage",
                    "PASS",
                    "WebDAV server accessible"
                )
                return True
            else:
                self.log_check(
                    "WebDAV Storage",
                    "WARN",
                    f"Unexpected status: {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_check(
                "WebDAV Storage",
                "FAIL",
                f"WebDAV unreachable: {str(e)}"
            )
            return False
    
    def check_api_endpoints(self):
        """Check critical API endpoints"""
        endpoints = [
            ("/api/components", "GET", "Component list API"),
            ("/api/brand", "GET", "Brand API"),
            ("/api/supplier", "GET", "Supplier API"),
            ("/api/component-types", "GET", "Component types API")
        ]
        
        all_passed = True
        
        for path, method, description in endpoints:
            try:
                url = f"{self.base_url}{path}"
                response = requests.request(method, url, timeout=5)
                
                if response.status_code == 200:
                    self.log_check(
                        f"API: {description}",
                        "PASS",
                        f"Responding correctly ({response.status_code})"
                    )
                else:
                    self.log_check(
                        f"API: {description}",
                        "WARN", 
                        f"Status: {response.status_code}"
                    )
                    all_passed = False
                    
            except Exception as e:
                self.log_check(
                    f"API: {description}",
                    "FAIL",
                    f"Request failed: {str(e)}"
                )
                all_passed = False
        
        return all_passed
    
    def check_data_integrity(self):
        """Check database data integrity"""
        try:
            with self.app.app_context():
                issues = []
                
                # Check for components without variants
                components_without_variants = Component.query.filter(
                    ~Component.variants.any()
                ).count()
                
                # Check for variants without SKUs
                variants_without_skus = ComponentVariant.query.filter(
                    ComponentVariant.variant_sku.is_(None)
                ).count()
                
                # Check for pictures without URLs
                pictures_without_urls = Picture.query.filter(
                    Picture.url.is_(None)
                ).count()
                
                if components_without_variants > 0:
                    issues.append(f"{components_without_variants} components without variants")
                
                if variants_without_skus > 0:
                    issues.append(f"{variants_without_skus} variants without SKUs")
                
                if pictures_without_urls > 0:
                    issues.append(f"{pictures_without_urls} pictures without URLs")
                
                if issues:
                    self.log_check(
                        "Data Integrity",
                        "WARN",
                        "Issues found",
                        "; ".join(issues)
                    )
                    return False
                else:
                    self.log_check(
                        "Data Integrity",
                        "PASS",
                        "All data integrity checks passed"
                    )
                    return True
                    
        except Exception as e:
            self.log_check(
                "Data Integrity",
                "FAIL",
                f"Integrity check failed: {str(e)}"
            )
            return False
    
    def check_application_status(self):
        """Check if main application is accessible"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            
            if response.status_code == 200:
                self.log_check(
                    "Application Status",
                    "PASS", 
                    "Application is accessible and responding"
                )
                return True
            else:
                self.log_check(
                    "Application Status",
                    "FAIL",
                    f"Application returned status: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_check(
                "Application Status",
                "FAIL",
                f"Application unreachable: {str(e)}"
            )
            return False
    
    def run_all_checks(self):
        """Run all health checks"""
        print("🏥 Component Management System - Health Check")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Target: {self.base_url}")
        print("=" * 60)
        
        checks = [
            ("Application Status", self.check_application_status),
            ("Database Connection", self.check_database_connection),
            ("WebDAV Storage", self.check_webdav_connectivity),
            ("API Endpoints", self.check_api_endpoints),
            ("Data Integrity", self.check_data_integrity)
        ]
        
        passed = 0
        total = len(checks)
        
        for check_name, check_func in checks:
            try:
                if check_func():
                    passed += 1
            except Exception as e:
                self.log_check(
                    check_name,
                    "FAIL",
                    f"Check failed with exception: {str(e)}"
                )
        
        print("\n" + "=" * 60)
        print(f"📊 Health Check Summary: {passed}/{total} checks passed")
        
        if passed == total:
            print("🎉 System is healthy!")
            return 0
        elif passed >= total * 0.8:
            print("⚠️  System has minor issues")
            return 1
        else:
            print("🚨 System has serious issues!")
            return 2

def main():
    """Main health check function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="System Health Checker")
    parser.add_argument(
        '--url', 
        default='http://localhost:6002',
        help='Base URL for the application (default: http://localhost:6002)'
    )
    parser.add_argument(
        '--json',
        action='store_true', 
        help='Output results in JSON format'
    )
    
    args = parser.parse_args()
    
    checker = HealthChecker(args.url)
    exit_code = checker.run_all_checks()
    
    if args.json:
        import json
        print("\n" + "=" * 60)
        print("JSON Results:")
        print(json.dumps(checker.results, indent=2))
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())