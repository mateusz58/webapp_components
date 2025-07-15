#!/usr/bin/env python3
"""
Comprehensive test for component picture visibility issue
Tests the Main Image Display section specifically
"""
import logging
import sys
import time
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Add config path for direct import
config_path = os.path.join(current_dir, 'config')
sys.path.insert(0, config_path)

from ..utils.driver_manager import DriverManager
from ..pages.component_form_page import ComponentFormPage
from ..pages.component_detail_page import ComponentDetailPage
from ..config.test_config import TestConfig

class ComponentPictureVisibilityTest:
    """Test component picture visibility issue"""
    
    def __init__(self):
        self.driver = None
        self.component_id = None
        self.test_results = {}
    
    def setup(self):
        """Initialize test environment"""
        logger.info("🚀 === STARTING COMPONENT PICTURE VISIBILITY TEST ===")
        
        # Create driver
        self.driver = DriverManager.create_chrome_driver()
        
        # Navigate to application
        logger.info("🌐 Opening application...")
        self.driver.get(f"{TestConfig.APP_URL}/component/new")
        
        # Wait for page load
        form_page = ComponentFormPage(self.driver)
        form_page.wait_for_element("body")
        logger.info("✅ Component form loaded")
        
        return form_page
    
    def create_test_component(self, form_page):
        """Create a component with variants and pictures"""
        timestamp = int(time.time())
        product_number = f"AUTO-TEST-{timestamp}"
        description = f"Automated picture visibility test component created at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Fill form
        form_page.fill_essential_info(product_number, description)
        form_page.select_component_type("alloverprints")
        form_page.select_supplier("SAB")
        form_page.add_keywords(["automation", "test", "selenium", "visibility"])
        
        # Add variants with pictures
        form_page.add_variant("Red", create_image=True)
        time.sleep(3)  # Give time for first variant
        form_page.add_variant("Green", create_image=True)
        time.sleep(3)  # Give time for second variant
        
        # Submit form
        component_id = form_page.submit_form()
        
        # Cleanup form page resources
        form_page.cleanup()
        
        return component_id, product_number
    
    def test_immediate_visibility(self, detail_page):
        """Test picture visibility immediately after redirect"""
        logger.info("🔍 Testing IMMEDIATE picture visibility...")
        
        # Small wait for page stabilization
        time.sleep(2)
        
        # Comprehensive check
        immediate_results = detail_page.comprehensive_picture_check()
        
        return immediate_results
    
    def test_after_refresh(self, detail_page):
        """Test picture visibility after page refresh"""
        logger.info("🔄 Testing picture visibility AFTER REFRESH...")
        
        # Refresh page
        self.driver.refresh()
        detail_page.wait_for_element("body")
        
        # Wait for page to fully load
        time.sleep(3)
        
        # Comprehensive check
        refresh_results = detail_page.comprehensive_picture_check()
        
        return refresh_results
    
    def analyze_results(self, immediate_results, refresh_results, product_number):
        """Analyze test results and determine if issue exists"""
        logger.info("📊 === ANALYZING RESULTS ===")
        
        # Extract key metrics
        immediate_main = immediate_results["main_image"]["status"]
        refresh_main = refresh_results["main_image"]["status"]
        
        immediate_count = immediate_results["picture_count"]["count"]
        refresh_count = refresh_results["picture_count"]["count"]
        
        # Log detailed results
        logger.info(f"✅ Component created: {product_number} (ID: {self.component_id})")
        logger.info(f"🖼️  Main Image (immediate): {immediate_main}")
        logger.info(f"🖼️  Main Image (after refresh): {refresh_main}")
        logger.info(f"📊 Picture count (immediate): {immediate_count}")
        logger.info(f"📊 Picture count (after refresh): {refresh_count}")
        
        # Determine if issue exists
        has_issue = False
        issue_details = []
        
        # Check main image visibility
        if immediate_main in ["PLACEHOLDER", "NO_SRC", "NOT_DISPLAYED", "MISSING_ELEMENTS", "NO_CONTAINER"]:
            if refresh_main == "VISIBLE":
                has_issue = True
                issue_details.append("Main image not visible immediately but appears after refresh")
        
        # Check picture count differences
        if immediate_count < refresh_count:
            has_issue = True
            issue_details.append(f"Picture count differs: {immediate_count} immediate vs {refresh_count} after refresh")
        
        # Check variant switching
        immediate_switching = immediate_results.get("switching_test", [])
        if immediate_switching:
            failing_variants = [r for r in immediate_switching if r["main_image"]["status"] != "VISIBLE"]
            if failing_variants:
                has_issue = True
                issue_details.append(f"Variant switching issues: {len(failing_variants)} variants not showing images")
        
        # Final verdict
        if has_issue:
            logger.error("🔧 TEST FAILED - Picture visibility issue CONFIRMED!")
            logger.error("📝 Issues found:")
            for issue in issue_details:
                logger.error(f"  - {issue}")
            logger.error("📸 Check screenshots in /tmp/ for visual evidence")
            logger.error("🐛 The bug: Pictures don't appear immediately after component creation")
            return False
        else:
            logger.info("🎉 TEST PASSED - Pictures appear immediately!")
            logger.info("✅ No picture visibility issues detected")
            return True
    
    def run(self):
        """Run the complete test"""
        try:
            # Setup
            form_page = self.setup()
            
            # Create component
            self.component_id, product_number = self.create_test_component(form_page)
            if not self.component_id:
                logger.error("❌ Failed to create component")
                return False
            
            # Create detail page instance
            detail_page = ComponentDetailPage(self.driver)
            
            # Test immediate visibility
            immediate_results = self.test_immediate_visibility(detail_page)
            
            # Test after refresh
            refresh_results = self.test_after_refresh(detail_page)
            
            # Analyze results
            test_passed = self.analyze_results(immediate_results, refresh_results, product_number)
            
            return test_passed
            
        except Exception as e:
            logger.error(f"❌ Test failed with exception: {e}")
            return False
        
        finally:
            # Keep browser open for inspection
            if self.driver:
                logger.info("⏳ Keeping browser open for 15 seconds for inspection...")
                time.sleep(15)
                DriverManager.quit_driver(self.driver)

def main():
    """Main test execution"""
    test = ComponentPictureVisibilityTest()
    success = test.run()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()