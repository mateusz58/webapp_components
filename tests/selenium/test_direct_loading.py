#!/usr/bin/env python3
"""
Test loading indicator by directly navigating to component detail with loading parameter
"""
import logging
import sys
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.driver_manager import DriverManager
from config.test_config import TestConfig

class DirectLoadingTest:
    """Test loading indicator by direct navigation"""
    
    def __init__(self):
        self.driver = None
    
    def setup(self):
        """Initialize test environment"""
        logger.info("🚀 === TESTING DIRECT LOADING INDICATOR ===")
        
        # Create driver
        self.driver = DriverManager.create_chrome_driver()
        
        return self.driver
    
    def test_direct_navigation_with_loading(self):
        """Navigate directly to a component with loading parameter"""
        # Use a known component ID (from previous tests)
        component_id = 148  # Or any existing component
        
        # Navigate with loading parameter
        url_with_loading = f"{TestConfig.APP_URL}/component/{component_id}?loading=true"
        logger.info(f"🌐 Navigating to: {url_with_loading}")
        
        self.driver.get(url_with_loading)
        
        # Check immediate state
        logger.info("🔍 Checking immediate state after navigation...")
        
        # Check URL
        current_url = self.driver.current_url
        logger.info(f"📍 Current URL: {current_url}")
        
        if 'loading=true' in current_url:
            logger.info("✅ Loading parameter present in URL")
        else:
            logger.error("❌ Loading parameter NOT in URL")
        
        # Check body attribute
        body_loading = self.driver.execute_script("return document.body.getAttribute('data-initial-loading');")
        logger.info(f"📊 Body data-initial-loading: {body_loading}")
        
        # Check Alpine.js state
        time.sleep(0.5)  # Give Alpine time to initialize
        
        try:
            alpine_state = self.driver.execute_script("""
                try {
                    const component = Alpine.$data(document.querySelector('[x-data]'));
                    return {
                        imagesLoading: component.imagesLoading,
                        loadingMessage: component.loadingMessage
                    };
                } catch (e) {
                    return { error: e.message };
                }
            """)
            
            logger.info(f"🔄 Alpine state: {alpine_state}")
            
            if alpine_state.get('imagesLoading'):
                logger.info("✅ Alpine loading state is TRUE")
            else:
                logger.error("❌ Alpine loading state is FALSE")
                
        except Exception as e:
            logger.error(f"❌ Error checking Alpine state: {e}")
        
        # Check for visible loading elements
        try:
            from selenium.webdriver.common.by import By
            loading_elements = self.driver.find_elements(By.CSS_SELECTOR, ".image-loading-state")
            
            for elem in loading_elements:
                if elem.is_displayed():
                    logger.info("✅ Loading indicator element is VISIBLE")
                else:
                    logger.error("❌ Loading indicator element exists but NOT VISIBLE")
                    
        except Exception as e:
            logger.error(f"❌ Error checking loading elements: {e}")
        
        # Take screenshot
        self.driver.save_screenshot("/tmp/direct_loading_test.png")
        logger.info("📸 Screenshot saved: /tmp/direct_loading_test.png")
        
        return True
    
    def test_navigation_without_loading(self):
        """Navigate without loading parameter for comparison"""
        component_id = 148
        
        url_without_loading = f"{TestConfig.APP_URL}/component/{component_id}"
        logger.info(f"\n🌐 Navigating WITHOUT loading parameter: {url_without_loading}")
        
        self.driver.get(url_without_loading)
        time.sleep(0.5)
        
        # Check Alpine state
        try:
            alpine_state = self.driver.execute_script("""
                try {
                    const component = Alpine.$data(document.querySelector('[x-data]'));
                    return {
                        imagesLoading: component.imagesLoading,
                        loadingMessage: component.loadingMessage
                    };
                } catch (e) {
                    return { error: e.message };
                }
            """)
            
            logger.info(f"🔄 Alpine state (no param): {alpine_state}")
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
    
    def run(self):
        """Run the complete test"""
        try:
            self.setup()
            
            # Test with loading parameter
            self.test_direct_navigation_with_loading()
            
            time.sleep(2)
            
            # Test without loading parameter for comparison
            self.test_navigation_without_loading()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Test failed with exception: {e}")
            return False
        
        finally:
            if self.driver:
                logger.info("⏳ Keeping browser open for 10 seconds...")
                time.sleep(10)
                DriverManager.quit_driver(self.driver)

def main():
    """Main test execution"""
    test = DirectLoadingTest()
    success = test.run()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()