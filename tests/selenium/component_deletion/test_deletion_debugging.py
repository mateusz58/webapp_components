"""
Comprehensive Selenium Tests for Component Deletion Debugging
Tests both single and bulk deletion workflows with detailed logging
"""
import unittest
import time
import os
import sys
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains

# Add config directory to path for test configuration
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


class DeletionDebuggingTestCase(unittest.TestCase):
    """Comprehensive deletion debugging tests"""

    @classmethod
    def setUpClass(cls):
        """Set up Selenium WebDriver"""
        chrome_options = Options()
        
        if getattr(TestConfig, 'SELENIUM_HEADLESS', False):
            chrome_options.add_argument('--headless')
        
        # Chrome options for better testing
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Enable console logging
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
        self.add_log("🧪 Starting Deletion Debug Test")

    def add_log(self, message):
        """Add log message with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.test_logs.append(log_entry)
        print(log_entry)
        
        # Add visual indicator if possible
        try:
            self.driver.execute_script(f"""
                console.log('{log_entry}');
                if (window.testLogs) {{
                    window.testLogs.push('{log_entry}');
                }} else {{
                    window.testLogs = ['{log_entry}'];
                }}
            """)
        except:
            pass

    def capture_browser_logs(self):
        """Capture browser console logs"""
        try:
            logs = self.driver.get_log('browser')
            console_logs = []
            for log in logs:
                console_logs.append({
                    'level': log['level'],
                    'message': log['message'],
                    'timestamp': log['timestamp']
                })
            return console_logs
        except:
            return []

    def capture_network_requests(self):
        """Get network requests from JavaScript monitoring"""
        try:
            return self.driver.execute_script("return window.capturedRequests || [];")
        except:
            return []

    def setup_request_monitoring(self):
        """Setup JavaScript to monitor network requests"""
        monitoring_script = """
        window.capturedRequests = [];
        window.originalFetch = fetch;
        
        window.fetch = function(...args) {
            const request = {
                url: args[0],
                method: args[1]?.method || 'GET',
                headers: args[1]?.headers || {},
                body: args[1]?.body || null,
                timestamp: new Date().toISOString()
            };
            
            console.log('🌐 Fetch Request:', request);
            window.capturedRequests.push(request);
            
            const promise = window.originalFetch.apply(this, args);
            
            promise.then(response => {
                console.log('✅ Fetch Response:', {
                    url: request.url,
                    status: response.status,
                    statusText: response.statusText,
                    headers: Object.fromEntries(response.headers.entries())
                });
                
                // Capture response text
                const responseClone = response.clone();
                responseClone.text().then(text => {
                    console.log('📄 Response Body:', text.substring(0, 500));
                }).catch(e => console.log('❌ Could not read response body:', e));
                
            }).catch(error => {
                console.log('❌ Fetch Error:', error);
            });
            
            return promise;
        };
        
        console.log('🔍 Request monitoring enabled');
        """
        self.driver.execute_script(monitoring_script)
        self.add_log("🔍 Network request monitoring enabled")

    def test_single_component_deletion_debug(self):
        """Debug single component deletion with comprehensive logging"""
        try:
            self.add_log("🎯 Testing Single Component Deletion")
            
            # Navigate to components list
            self.driver.get(f"{self.base_url}/components")
            self.setup_request_monitoring()
            
            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)
            
            # Look for components with delete buttons
            delete_buttons = self.driver.find_elements(By.CSS_SELECTOR, "[data-bs-target*='deleteModal']")
            self.add_log(f"🔍 Found {len(delete_buttons)} components with delete buttons")
            
            if not delete_buttons:
                self.add_log("❌ No components found for deletion test")
                self.skipTest("No components with delete buttons found")
            
            # Get first component
            delete_button = delete_buttons[0]
            
            # Extract component info
            component_card = delete_button.find_element(By.XPATH, "./ancestor::*[contains(@class, 'component-card') or contains(@class, 'card')]")
            component_id = self.extract_component_id(delete_button)
            self.add_log(f"🎯 Testing deletion of component ID: {component_id}")
            
            # Check CSRF token availability
            csrf_tokens = self.driver.find_elements(By.CSS_SELECTOR, "input[name='csrf_token']")
            csrf_meta = self.driver.find_elements(By.CSS_SELECTOR, "meta[name='csrf-token']")
            self.add_log(f"🔒 CSRF tokens found: {len(csrf_tokens)} inputs, {len(csrf_meta)} meta tags")
            
            # Click delete button to open modal
            self.add_log("🖱️ Clicking delete button to open modal")
            delete_button.click()
            time.sleep(1)
            
            # Wait for modal
            modal = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".modal")))
            self.add_log("✅ Delete modal opened")
            
            # Find confirm button
            confirm_buttons = modal.find_elements(By.CSS_SELECTOR, "button[onclick*='deleteComponent']")
            if not confirm_buttons:
                self.add_log("❌ No confirm button with deleteComponent found in modal")
                # Look for any delete buttons
                all_delete_buttons = modal.find_elements(By.CSS_SELECTOR, "button")
                for btn in all_delete_buttons:
                    onclick = btn.get_attribute('onclick')
                    if onclick:
                        self.add_log(f"🔍 Found button with onclick: {onclick}")
                self.fail("No deleteComponent confirm button found")
            
            confirm_button = confirm_buttons[0]
            onclick_attr = confirm_button.get_attribute('onclick')
            self.add_log(f"🎯 Confirm button onclick: {onclick_attr}")
            
            # Click confirm delete
            self.add_log("⚠️ Clicking confirm delete button")
            confirm_button.click()
            time.sleep(1)
            
            # Wait for any network requests
            time.sleep(3)
            
            # Capture browser logs
            browser_logs = self.capture_browser_logs()
            self.add_log(f"📋 Captured {len(browser_logs)} browser log entries")
            
            for log in browser_logs[-10:]:  # Show last 10 logs
                self.add_log(f"🖥️ Browser: [{log['level']}] {log['message']}")
            
            # Capture network requests
            network_requests = self.capture_network_requests()
            self.add_log(f"🌐 Captured {len(network_requests)} network requests")
            
            for req in network_requests:
                self.add_log(f"🌐 Request: {req['method']} {req['url']}")
                if req.get('body'):
                    self.add_log(f"📦 Body: {req['body']}")
            
            # Check current URL
            current_url = self.driver.current_url
            self.add_log(f"🌍 Current URL: {current_url}")
            
            # Check for any error messages or alerts
            try:
                alert = self.driver.switch_to.alert
                alert_text = alert.text
                self.add_log(f"🚨 Alert detected: {alert_text}")
                alert.accept()
            except:
                self.add_log("ℹ️ No alert detected")
            
            # Look for success/error messages on page
            flash_messages = self.driver.find_elements(By.CSS_SELECTOR, ".alert, .flash-message, .message")
            for msg in flash_messages:
                if msg.is_displayed():
                    self.add_log(f"💬 Page message: {msg.text}")
            
            self.add_log("✅ Single deletion test completed")
            
        except Exception as e:
            self.add_log(f"❌ Single deletion test failed: {str(e)}")
            raise

    def test_bulk_component_deletion_debug(self):
        """Debug bulk component deletion with comprehensive logging"""
        try:
            self.add_log("🎯 Testing Bulk Component Deletion")
            
            # Navigate to components list
            self.driver.get(f"{self.base_url}/components")
            self.setup_request_monitoring()
            
            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)
            
            # Look for components with checkboxes
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']:not(#selectAll)")
            self.add_log(f"🔍 Found {len(checkboxes)} component checkboxes")
            
            if len(checkboxes) < 2:
                self.add_log("❌ Need at least 2 components for bulk deletion test")
                self.skipTest("Not enough components for bulk deletion test")
            
            # Select first 2 components
            selected_components = []
            for i in range(min(2, len(checkboxes))):
                checkbox = checkboxes[i]
                if checkbox.is_displayed() and checkbox.is_enabled():
                    # Get component ID
                    component_id = self.extract_component_id_from_checkbox(checkbox)
                    selected_components.append(component_id)
                    
                    self.add_log(f"☑️ Selecting component {component_id}")
                    checkbox.click()
                    time.sleep(0.5)
            
            self.add_log(f"✅ Selected {len(selected_components)} components: {selected_components}")
            
            # Wait for bulk actions to appear
            time.sleep(1)
            
            # Look for bulk delete button
            bulk_delete_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[onclick*='bulkAction'][onclick*='delete'], button.btn-danger-modern")
            if not bulk_delete_buttons:
                # Try alternative selectors
                bulk_delete_buttons = self.driver.find_elements(By.CSS_SELECTOR, "[x-on\\:click*='bulkAction'][x-on\\:click*='delete']")
            
            self.add_log(f"🔍 Found {len(bulk_delete_buttons)} bulk delete buttons")
            
            if not bulk_delete_buttons:
                self.add_log("❌ No bulk delete button found")
                self.fail("No bulk delete button found")
            
            bulk_delete_button = bulk_delete_buttons[0]
            self.add_log(f"🎯 Bulk delete button text: '{bulk_delete_button.text}'")
            
            # Check if button is visible and enabled
            if not bulk_delete_button.is_displayed():
                self.add_log("❌ Bulk delete button is not visible")
            if not bulk_delete_button.is_enabled():
                self.add_log("❌ Bulk delete button is not enabled")
            
            # Click bulk delete button
            self.add_log("🖱️ Clicking bulk delete button")
            bulk_delete_button.click()
            time.sleep(1)
            
            # Handle confirmation dialog
            try:
                alert = self.driver.switch_to.alert
                alert_text = alert.text
                self.add_log(f"🚨 Confirmation dialog: {alert_text}")
                alert.accept()
                time.sleep(1)
            except:
                self.add_log("ℹ️ No confirmation dialog appeared")
            
            # Wait for network requests
            time.sleep(5)
            
            # Capture browser logs
            browser_logs = self.capture_browser_logs()
            self.add_log(f"📋 Captured {len(browser_logs)} browser log entries")
            
            for log in browser_logs[-15:]:  # Show last 15 logs
                level_emoji = {"SEVERE": "🔴", "WARNING": "🟡", "INFO": "🔵"}.get(log['level'], "⚪")
                self.add_log(f"{level_emoji} Browser: {log['message']}")
            
            # Capture network requests
            network_requests = self.capture_network_requests()
            self.add_log(f"🌐 Captured {len(network_requests)} network requests")
            
            for req in network_requests:
                self.add_log(f"🌐 {req['method']} {req['url']}")
                if req.get('body'):
                    try:
                        body_data = json.loads(req['body'])
                        self.add_log(f"📦 Body: {json.dumps(body_data, indent=2)}")
                    except:
                        self.add_log(f"📦 Body: {req['body']}")
                
                # Check if this is our bulk delete request
                if 'bulk-delete' in req['url']:
                    self.add_log(f"🎯 Found bulk delete request!")
            
            # Check for any error messages
            flash_messages = self.driver.find_elements(By.CSS_SELECTOR, ".alert, .flash-message, .message")
            for msg in flash_messages:
                if msg.is_displayed():
                    self.add_log(f"💬 Page message: {msg.text}")
            
            # Check if page reloaded or redirected
            current_url = self.driver.current_url
            self.add_log(f"🌍 Current URL: {current_url}")
            
            self.add_log("✅ Bulk deletion test completed")
            
        except Exception as e:
            self.add_log(f"❌ Bulk deletion test failed: {str(e)}")
            raise

    def extract_component_id(self, element):
        """Extract component ID from various element attributes"""
        # Try different ways to extract component ID
        
        # Check data-bs-target for modal ID
        target = element.get_attribute('data-bs-target')
        if target and 'deleteModal' in target:
            import re
            match = re.search(r'deleteModal(\d+)', target)
            if match:
                return match.group(1)
        
        # Check onclick attribute
        onclick = element.get_attribute('onclick')
        if onclick:
            import re
            match = re.search(r'deleteComponent\((\d+)', onclick)
            if match:
                return match.group(1)
        
        # Check parent element data attributes
        parent = element.find_element(By.XPATH, "./ancestor::*[@data-component-id]")
        if parent:
            return parent.get_attribute('data-component-id')
        
        return "unknown"

    def extract_component_id_from_checkbox(self, checkbox):
        """Extract component ID from checkbox or its parent"""
        # Check if checkbox has component ID in attributes
        for attr in ['data-component-id', 'data-id', 'value']:
            value = checkbox.get_attribute(attr)
            if value and value.isdigit():
                return value
        
        # Check parent elements
        try:
            parent = checkbox.find_element(By.XPATH, "./ancestor::*[@data-component-id]")
            return parent.get_attribute('data-component-id')
        except:
            pass
        
        # Check Alpine.js click handler
        try:
            alpine_click = checkbox.get_attribute('@click.stop')
            if alpine_click and 'toggleSelection' in alpine_click:
                import re
                match = re.search(r'toggleSelection\((\d+)\)', alpine_click)
                if match:
                    return match.group(1)
        except:
            pass
        
        return "unknown"

    def test_api_endpoint_direct_test(self):
        """Test API endpoints directly via JavaScript"""
        try:
            self.add_log("🔗 Testing API endpoints directly")
            
            # Navigate to components list
            self.driver.get(f"{self.base_url}/components")
            self.setup_request_monitoring()
            time.sleep(2)
            
            # Test single delete API endpoint
            self.add_log("🧪 Testing single delete API endpoint")
            
            single_delete_test = """
            fetch('/api/component/1', {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrf_token]')?.value || 'test-token',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                console.log('Single Delete Response Status:', response.status);
                return response.text();
            })
            .then(text => {
                console.log('Single Delete Response Body:', text);
                return text;
            })
            .catch(error => {
                console.log('Single Delete Error:', error);
                return error.toString();
            });
            """
            
            result = self.driver.execute_script(f"return {single_delete_test}")
            self.add_log(f"🔍 Single delete result: {result}")
            
            # Test bulk delete API endpoint
            self.add_log("🧪 Testing bulk delete API endpoint")
            
            bulk_delete_test = """
            fetch('/api/components/bulk-delete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrf_token]')?.value || 'test-token',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ component_ids: [1, 2] })
            })
            .then(response => {
                console.log('Bulk Delete Response Status:', response.status);
                return response.text();
            })
            .then(text => {
                console.log('Bulk Delete Response Body:', text);
                return text;
            })
            .catch(error => {
                console.log('Bulk Delete Error:', error);
                return error.toString();
            });
            """
            
            time.sleep(1)
            result = self.driver.execute_script(f"return {bulk_delete_test}")
            self.add_log(f"🔍 Bulk delete result: {result}")
            
            # Wait for requests to complete
            time.sleep(3)
            
            # Get all logs
            browser_logs = self.capture_browser_logs()
            for log in browser_logs[-10:]:
                self.add_log(f"🖥️ API Test Log: {log['message']}")
            
            self.add_log("✅ API endpoint testing completed")
            
        except Exception as e:
            self.add_log(f"❌ API endpoint test failed: {str(e)}")
            raise

    def tearDown(self):
        """Print all test logs"""
        print("\n" + "="*80)
        print("DELETION DEBUG TEST LOGS")
        print("="*80)
        for log in self.test_logs:
            print(log)
        print("="*80 + "\n")


if __name__ == '__main__':
    unittest.main()