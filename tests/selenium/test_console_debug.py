#!/usr/bin/env python3
"""
Test to capture browser console logs during component creation
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
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.driver_manager import DriverManager
from pages.component_form_page import ComponentFormPage
from pages.component_detail_page import ComponentDetailPage
from config.test_config import TestConfig

class ConsoleDebugTest:
    """Test to capture console logs during component creation"""
    
    def __init__(self):
        self.driver = None
        self.console_logs = []
    
    def setup(self):
        """Initialize test environment with console logging"""
        logger.info("🚀 === CONSOLE DEBUG TEST ===")
        
        # Create driver with logging enabled
        self.driver = DriverManager.create_chrome_driver(enable_logging=True)
        
        # Navigate to application
        logger.info("🌐 Opening component creation form...")
        self.driver.get(f"{TestConfig.APP_URL}/component/new")
        
        # Wait for page load
        form_page = ComponentFormPage(self.driver)
        form_page.wait_for_element("body")
        logger.info("✅ Component form loaded")
        
        return form_page
    
    def create_test_component(self, form_page):
        """Create a component and capture console logs"""
        timestamp = int(time.time())
        product_number = f"CONSOLE-TEST-{timestamp}"
        description = f"Console debug test component created at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Fill form quickly
        form_page.fill_essential_info(product_number, description)
        form_page.select_component_type("alloverprints")
        form_page.select_supplier("SAB")
        
        # Add one variant with picture
        form_page.add_variant("Red", create_image=True)
        time.sleep(2)  # Give time for image upload
        
        # Capture console logs before submit
        self.capture_console_logs("BEFORE_SUBMIT")
        
        # Submit form
        logger.info("📤 Submitting form...")
        component_id = form_page.submit_form()
        
        if component_id:
            logger.info(f"✅ Component {component_id} created")
        else:
            logger.error("❌ Component creation failed")
        
        return component_id
    
    def capture_console_logs(self, stage):
        """Capture browser console logs"""
        try:
            logs = self.driver.get_log('browser')
            if logs:
                logger.info(f"📋 Console logs at {stage}:")
                for log_entry in logs:
                    level = log_entry['level']
                    message = log_entry['message']
                    timestamp = log_entry['timestamp']
                    
                    # Only show relevant logs
                    if any(keyword in message.lower() for keyword in ['component', 'loading', 'alpine', 'error', 'warning']):
                        logger.info(f"  [{level}] {message}")
                        
                        # Store for analysis
                        self.console_logs.append({
                            'stage': stage,
                            'level': level,
                            'message': message,
                            'timestamp': timestamp
                        })
            else:
                logger.info(f"📋 No console logs at {stage}")
                
        except Exception as e:
            logger.warning(f"⚠️  Could not capture console logs: {e}")
    
    def test_detail_page_loading(self, component_id):
        """Test the detail page loading behavior"""
        if not component_id:
            return
        
        logger.info("🔍 Testing detail page loading behavior...")
        
        # Wait a moment for page to load
        time.sleep(1)
        
        # Capture console logs after redirect
        self.capture_console_logs("AFTER_REDIRECT")
        
        # Check current URL
        current_url = self.driver.current_url
        logger.info(f"🔗 Current URL: {current_url}")
        
        # Check Alpine.js state
        alpine_state = self.driver.execute_script("""
            try {
                // Wait a moment for Alpine to initialize
                if (typeof Alpine === 'undefined') {
                    return { error: 'Alpine not available' };
                }
                
                // Find the Alpine component element
                const element = document.querySelector('[x-data="componentDetail()"]') || 
                               document.querySelector('[x-data]');
                
                if (!element) {
                    return { error: 'No Alpine element found' };
                }
                
                // Try multiple methods to get Alpine data
                let component = null;
                
                // Method 1: Direct Alpine access
                if (element._x_dataStack && element._x_dataStack.length > 0) {
                    component = element._x_dataStack[0];
                }
                
                // Method 2: Alpine.$data method
                if (!component && Alpine.$data) {
                    component = Alpine.$data(element);
                }
                
                // Method 3: Check if Alpine data is in a different location
                if (!component && element.__x) {
                    component = element.__x.$data;
                }
                
                if (!component) {
                    return { error: 'Could not access Alpine component data' };
                }
                
                return {
                    imagesLoading: component.imagesLoading,
                    loadingMessage: component.loadingMessage,
                    componentImages: component.componentImages ? component.componentImages.length : 0,
                    variants: component.variants ? component.variants.length : 0,
                    initCalled: component._initCalled || false,
                    hasComponent: true
                };
            } catch (e) {
                return { error: 'Exception: ' + e.message };
            }
        """)
        
        logger.info(f"🔍 Alpine.js state: {alpine_state}")
        
        # Wait and capture logs again
        time.sleep(3)
        self.capture_console_logs("AFTER_3_SECONDS")
        
        # Check if loading indicator is visible
        loading_visible = self.driver.execute_script("""
            const loadingElements = document.querySelectorAll('.image-loading-state, .spinner-border');
            return Array.from(loadingElements).some(el => el.offsetParent !== null);
        """)
        
        logger.info(f"👁️  Loading indicator visible: {loading_visible}")
        
        # Check URL parameters
        has_loading_param = self.driver.execute_script("""
            return window.location.search.includes('loading=true');
        """)
        
        logger.info(f"🔗 URL has loading parameter: {has_loading_param}")
        
        # Check body data attribute
        body_loading = self.driver.execute_script("""
            return document.body.getAttribute('data-initial-loading');
        """)
        
        logger.info(f"🏷️  Body data-initial-loading: {body_loading}")
    
    def analyze_console_logs(self):
        """Analyze captured console logs"""
        logger.info("📊 === CONSOLE LOG ANALYSIS ===")
        
        if not self.console_logs:
            logger.info("📋 No relevant console logs captured")
            return
        
        # Group by stage
        stages = {}
        for log in self.console_logs:
            stage = log['stage']
            if stage not in stages:
                stages[stage] = []
            stages[stage].append(log)
        
        # Analyze each stage
        for stage, logs in stages.items():
            logger.info(f"📋 {stage}: {len(logs)} relevant logs")
            
            for log in logs:
                level_emoji = "🔴" if log['level'] == 'SEVERE' else "🟡" if log['level'] == 'WARNING' else "ℹ️"
                logger.info(f"  {level_emoji} {log['message']}")
        
        # Look for specific issues
        error_logs = [log for log in self.console_logs if log['level'] == 'SEVERE']
        if error_logs:
            logger.error(f"🚨 Found {len(error_logs)} JavaScript errors!")
            for error in error_logs:
                logger.error(f"  🔴 {error['message']}")
        
        loading_logs = [log for log in self.console_logs if 'loading' in log['message'].lower()]
        if loading_logs:
            logger.info(f"🔄 Found {len(loading_logs)} loading-related logs")
            for log in loading_logs:
                logger.info(f"  🔄 {log['message']}")
    
    def run(self):
        """Run the complete test"""
        try:
            # Setup
            form_page = self.setup()
            
            # Create component
            component_id = self.create_test_component(form_page)
            
            # Test detail page
            self.test_detail_page_loading(component_id)
            
            # Analyze logs
            self.analyze_console_logs()
            
            # Final screenshot
            self.driver.save_screenshot("/tmp/console_debug_final.png")
            logger.info("📸 Final screenshot saved: /tmp/console_debug_final.png")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Test failed with exception: {e}")
            return False
        
        finally:
            # Keep browser open for inspection
            if self.driver:
                logger.info("⏳ Keeping browser open for 10 seconds for inspection...")
                time.sleep(10)
                DriverManager.quit_driver(self.driver)

def main():
    """Main test execution"""
    test = ConsoleDebugTest()
    success = test.run()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()