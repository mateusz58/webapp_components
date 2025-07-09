"""
Comprehensive Selenium Tests for Component Deletion
Organized by deletion type: single deletion and bulk deletion
"""
import unittest
import time
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.action_chains import ActionChains

# Add config directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(os.path.dirname(current_dir), 'config')
sys.path.insert(0, config_path)

try:
    from test_config import TestConfig
except ImportError:
    class TestConfig:
        BASE_URL = "http://localhost:6002"
        SELENIUM_HEADLESS = False
        SELENIUM_IMPLICIT_WAIT = 10
        SELENIUM_EXPLICIT_WAIT = 20


class ComponentDeletionComprehensiveTestCase(unittest.TestCase):
    """Comprehensive tests for component deletion functionality"""

    @classmethod
    def setUpClass(cls):
        """Set up Selenium WebDriver"""
        chrome_options = Options()
        
        if getattr(TestConfig, 'SELENIUM_HEADLESS', False):
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--enable-logging')
        chrome_options.add_argument('--log-level=0')
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            print(f"Failed to initialize Chrome driver: {e}")
            raise
        
        cls.driver.implicitly_wait(getattr(TestConfig, 'SELENIUM_IMPLICIT_WAIT', 10))
        cls.wait = WebDriverWait(cls.driver, getattr(TestConfig, 'SELENIUM_EXPLICIT_WAIT', 20))
        cls.base_url = getattr(TestConfig, 'BASE_URL', 'http://localhost:6002')

    @classmethod
    def tearDownClass(cls):
        """Clean up WebDriver"""
        if hasattr(cls, 'driver'):
            cls.driver.quit()

    def setUp(self):
        """Set up each test"""
        self.test_logs = []
        self.add_log("🧪 Starting Component Deletion Test")

    def add_log(self, message):
        """Add log with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.test_logs.append(log_entry)
        print(log_entry)

    def setup_network_monitoring(self):
        """Setup JavaScript network monitoring"""
        monitoring_script = """
        window.testNetworkRequests = [];
        
        // Store original fetch
        if (!window.originalFetch) {
            window.originalFetch = fetch;
        }
        
        // Override fetch to capture requests
        window.fetch = function(...args) {
            const request = {
                url: args[0],
                method: args[1]?.method || 'GET',
                headers: args[1]?.headers || {},
                body: args[1]?.body || null,
                timestamp: new Date().toISOString()
            };
            
            console.log('🌐 Network Request:', request);
            window.testNetworkRequests.push(request);
            
            return window.originalFetch.apply(this, args).then(response => {
                console.log('📥 Network Response:', {
                    url: request.url,
                    status: response.status,
                    ok: response.ok
                });
                return response;
            }).catch(error => {
                console.log('❌ Network Error:', error);
                throw error;
            });
        };
        
        console.log('🔍 Network monitoring enabled');
        """
        self.driver.execute_script(monitoring_script)

    def get_network_requests(self):
        """Get captured network requests"""
        try:
            return self.driver.execute_script("return window.testNetworkRequests || [];")
        except:
            return []

    def test_single_component_deletion_modal_workflow(self):
        """Test single component deletion through modal workflow"""
        self.add_log("🎯 Testing Single Component Deletion Modal Workflow")
        
        try:
            # Navigate to components page
            self.driver.get(f"{self.base_url}/components")
            self.setup_network_monitoring()
            
            # Wait for page load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)
            
            # Find delete buttons
            delete_buttons = self.driver.find_elements(By.CSS_SELECTOR, "[data-bs-target*='deleteModal']")
            self.add_log(f"🔍 Found {len(delete_buttons)} delete buttons")
            
            if not delete_buttons:
                self.skipTest("No delete buttons found")
            
            # Use first delete button
            delete_button = delete_buttons[0]
            
            # Extract component ID for logging
            modal_target = delete_button.get_attribute('data-bs-target')
            component_id = modal_target.replace('#deleteModal', '') if modal_target else 'unknown'
            self.add_log(f"🎯 Testing deletion of component {component_id}")
            
            # Scroll to element and click
            self.driver.execute_script("arguments[0].scrollIntoView(true);", delete_button)
            time.sleep(1)
            
            # Click delete button
            delete_button.click()
            self.add_log("✅ Delete button clicked, modal should open")
            
            # Wait for modal
            modal = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".modal.show")))
            self.add_log("✅ Modal opened")
            
            # Find confirm button
            confirm_button = modal.find_element(By.CSS_SELECTOR, "button[onclick*='deleteComponent']")
            self.add_log("✅ Confirm button found")
            
            # Click confirm
            confirm_button.click()
            self.add_log("✅ Confirm button clicked")
            
            # Wait for network request
            time.sleep(3)
            
            # Check network requests
            requests = self.get_network_requests()
            self.add_log(f"📊 Captured {len(requests)} network requests")
            
            delete_requests = [r for r in requests if '/delete/' in r['url'] or '/component/' in r['url']]
            self.add_log(f"📊 Found {len(delete_requests)} delete-related requests")
            
            for req in delete_requests:
                self.add_log(f"🌐 {req['method']} {req['url']}")
            
            # Check if we were redirected or page updated
            current_url = self.driver.current_url
            self.add_log(f"🌍 Current URL: {current_url}")
            
            self.add_log("✅ Single deletion test completed")
            
        except Exception as e:
            self.add_log(f"❌ Single deletion test failed: {str(e)}")
            raise

    def test_bulk_component_deletion_workflow(self):
        """Test bulk component deletion workflow"""
        self.add_log("🎯 Testing Bulk Component Deletion Workflow")
        
        try:
            # Navigate to components page
            self.driver.get(f"{self.base_url}/components")
            self.setup_network_monitoring()
            
            # Wait for page load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)
            
            # Find component checkboxes
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']:not(#selectAll)")
            self.add_log(f"🔍 Found {len(checkboxes)} component checkboxes")
            
            if len(checkboxes) < 2:
                self.skipTest("Need at least 2 components for bulk deletion")
            
            # Select first 2 components
            selected_count = 0
            for checkbox in checkboxes[:2]:
                if checkbox.is_displayed() and checkbox.is_enabled():
                    # Scroll to checkbox
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
                    time.sleep(0.5)
                    
                    # Click checkbox
                    checkbox.click()
                    selected_count += 1
                    self.add_log(f"☑️ Selected component {selected_count}")
                    
                    if selected_count >= 2:
                        break
            
            self.add_log(f"✅ Selected {selected_count} components")
            
            # Wait for bulk actions to appear
            time.sleep(1)
            
            # Find bulk delete button
            bulk_delete_buttons = self.driver.find_elements(By.CSS_SELECTOR, ".btn-danger-modern")
            self.add_log(f"🔍 Found {len(bulk_delete_buttons)} bulk delete buttons")
            
            if not bulk_delete_buttons:
                self.skipTest("No bulk delete button found")
            
            # Find the correct bulk delete button (should contain "Delete" text)
            bulk_delete_button = None
            for btn in bulk_delete_buttons:
                if "Delete" in btn.text:
                    bulk_delete_button = btn
                    break
            
            if not bulk_delete_button:
                self.skipTest("No bulk delete button with 'Delete' text found")
            
            self.add_log(f"🎯 Found bulk delete button: '{bulk_delete_button.text}'")
            
            # Check if button is visible
            if not bulk_delete_button.is_displayed():
                self.add_log("❌ Bulk delete button not visible")
                self.fail("Bulk delete button not visible")
            
            # Click bulk delete button
            bulk_delete_button.click()
            self.add_log("✅ Bulk delete button clicked")
            
            # Handle confirmation dialog
            try:
                alert = self.wait.until(EC.alert_is_present())
                alert_text = alert.text
                self.add_log(f"🚨 Confirmation dialog: {alert_text}")
                alert.accept()
                self.add_log("✅ Confirmation accepted")
            except TimeoutException:
                self.add_log("⚠️ No confirmation dialog appeared")
            
            # Wait for network request
            time.sleep(5)
            
            # Check network requests
            requests = self.get_network_requests()
            self.add_log(f"📊 Captured {len(requests)} network requests")
            
            bulk_requests = [r for r in requests if 'bulk-delete' in r['url']]
            self.add_log(f"📊 Found {len(bulk_requests)} bulk delete requests")
            
            for req in bulk_requests:
                self.add_log(f"🌐 {req['method']} {req['url']}")
                if req.get('body'):
                    self.add_log(f"📦 Request body: {req['body']}")
            
            # Check browser console logs
            logs = self.driver.get_log('browser')
            error_logs = [log for log in logs if log['level'] == 'SEVERE']
            self.add_log(f"📋 Found {len(error_logs)} console errors")
            
            for log in error_logs:
                self.add_log(f"🔴 Console Error: {log['message']}")
            
            # Check current URL
            current_url = self.driver.current_url
            self.add_log(f"🌍 Current URL: {current_url}")
            
            self.add_log("✅ Bulk deletion test completed")
            
        except Exception as e:
            self.add_log(f"❌ Bulk deletion test failed: {str(e)}")
            raise

    def test_csrf_token_availability(self):
        """Test CSRF token availability for deletion requests"""
        self.add_log("🔒 Testing CSRF Token Availability")
        
        try:
            # Navigate to components page
            self.driver.get(f"{self.base_url}/components")
            
            # Wait for page load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)
            
            # Check for CSRF tokens
            csrf_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[name='csrf_token']")
            csrf_meta = self.driver.find_elements(By.CSS_SELECTOR, "meta[name='csrf-token']")
            
            self.add_log(f"🔍 Found {len(csrf_inputs)} CSRF input fields")
            self.add_log(f"🔍 Found {len(csrf_meta)} CSRF meta tags")
            
            if csrf_inputs:
                token_value = csrf_inputs[0].get_attribute('value')
                self.add_log(f"🔑 CSRF token (input): {token_value[:20]}...")
            
            if csrf_meta:
                token_value = csrf_meta[0].get_attribute('content')
                self.add_log(f"🔑 CSRF token (meta): {token_value[:20]}...")
            
            # Check if tokens are accessible via JavaScript
            js_token_check = """
            var tokenFromMeta = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
            var tokenFromInput = document.querySelector('input[name="csrf_token"]')?.value;
            return {
                meta: tokenFromMeta,
                input: tokenFromInput,
                available: !!(tokenFromMeta || tokenFromInput)
            };
            """
            
            token_info = self.driver.execute_script(js_token_check)
            self.add_log(f"🔍 JavaScript token access: {token_info}")
            
            self.add_log("✅ CSRF token test completed")
            
        except Exception as e:
            self.add_log(f"❌ CSRF token test failed: {str(e)}")
            raise

    def tearDown(self):
        """Print test logs after each test"""
        print("\n" + "="*60)
        print("COMPREHENSIVE DELETION TEST LOGS")
        print("="*60)
        for log in self.test_logs:
            print(log)
        print("="*60 + "\n")


if __name__ == '__main__':
    unittest.main(verbosity=2)