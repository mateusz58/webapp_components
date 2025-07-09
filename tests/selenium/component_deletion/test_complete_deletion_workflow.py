#!/usr/bin/env python3
"""
Complete Selenium Integration Test for Component Deletion Workflow
Tests full end-to-end deletion functionality with database verification
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
from selenium.webdriver.common.keys import Keys

# Add config directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(os.path.dirname(current_dir), 'config')
sys.path.insert(0, config_path)

# Add app directory to path for database imports
app_path = os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'app')
sys.path.insert(0, os.path.dirname(os.path.dirname(current_dir)))

try:
    from test_config import TestConfig
except ImportError:
    class TestConfig:
        BASE_URL = "http://localhost:6002"
        SELENIUM_HEADLESS = False
        SELENIUM_IMPLICIT_WAIT = 10
        SELENIUM_EXPLICIT_WAIT = 20

# Import database models for verification
from app import create_app, db
from app.models import Component, ComponentVariant, Picture, ComponentBrand
from config import Config

class TestConfig(Config):
    """Test configuration"""
    TESTING = True
    WTF_CSRF_ENABLED = True
    SECRET_KEY = 'test-secret-key'


class CompleteDeletionWorkflowTestCase(unittest.TestCase):
    """Complete integration test for deletion workflow"""

    @classmethod
    def setUpClass(cls):
        """Set up Selenium WebDriver and Flask app"""
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
        
        # Set up Flask app for database verification
        cls.app = create_app(TestConfig)
        cls.app_context = cls.app.app_context()
        cls.app_context.push()

    @classmethod
    def tearDownClass(cls):
        """Clean up WebDriver and Flask app"""
        if hasattr(cls, 'driver'):
            cls.driver.quit()
        if hasattr(cls, 'app_context'):
            cls.app_context.pop()

    def setUp(self):
        """Set up each test"""
        self.test_logs = []
        self.add_log("🧪 Starting Complete Deletion Workflow Test")

    def add_log(self, message):
        """Add log with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.test_logs.append(log_entry)
        print(log_entry)

    def get_component_data_from_db(self, component_id):
        """Get component data from database for verification"""
        component = Component.query.get(component_id)
        if not component:
            return None
            
        return {
            'component': component,
            'variants': ComponentVariant.query.filter_by(component_id=component_id).all(),
            'pictures': Picture.query.filter_by(component_id=component_id).all(),
            'brands': ComponentBrand.query.filter_by(component_id=component_id).all()
        }

    def safe_click(self, element, max_attempts=3):
        """Safely click an element with retries"""
        for attempt in range(max_attempts):
            try:
                # Scroll to element
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", element)
                time.sleep(0.5)
                
                # Try regular click
                element.click()
                return True
                
            except ElementClickInterceptedException:
                if attempt < max_attempts - 1:
                    self.add_log(f"⚠️ Click intercepted, retrying... (attempt {attempt + 1})")
                    time.sleep(1)
                    # Try JavaScript click
                    try:
                        self.driver.execute_script("arguments[0].click();", element)
                        return True
                    except:
                        continue
                else:
                    # Final attempt with ActionChains
                    try:
                        ActionChains(self.driver).move_to_element(element).click().perform()
                        return True
                    except:
                        self.add_log("❌ All click attempts failed")
                        return False
        return False

    def test_single_component_deletion_complete_workflow(self):
        """Test complete single component deletion workflow with database verification"""
        self.add_log("🎯 Testing Single Component Deletion - Complete Workflow")
        
        try:
            # Navigate to components page
            self.driver.get(f"{self.base_url}/components")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Setup network monitoring
            self.driver.execute_script("""
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
                    
                    return window.originalFetch.apply(this, args);
                };
                
                console.log('🔍 Network monitoring enabled');
            """)
            
            time.sleep(2)
            
            # Find components with delete buttons
            delete_buttons = self.driver.find_elements(By.CSS_SELECTOR, "[data-bs-target*='deleteModal']")
            self.add_log(f"🔍 Found {len(delete_buttons)} components with delete buttons")
            
            if not delete_buttons:
                self.skipTest("No components with delete buttons found")
            
            # Get component ID from the first delete button
            delete_button = delete_buttons[0]
            modal_target = delete_button.get_attribute('data-bs-target')
            
            # Extract component ID from modal target
            component_id = None
            if modal_target:
                import re
                match = re.search(r'deleteModal(\d+)', modal_target)
                if match:
                    component_id = int(match.group(1))
            
            if not component_id:
                self.skipTest("Could not extract component ID from delete button")
            
            self.add_log(f"🎯 Testing deletion of component ID: {component_id}")
            
            # Get component data before deletion
            before_data = self.get_component_data_from_db(component_id)
            if not before_data:
                self.skipTest(f"Component {component_id} not found in database")
            
            component = before_data['component']
            variants_before = len(before_data['variants'])
            pictures_before = len(before_data['pictures'])
            brands_before = len(before_data['brands'])
            
            self.add_log(f"📊 Component before deletion: {component.product_number}")
            self.add_log(f"📊 Associated data: {variants_before} variants, {pictures_before} pictures, {brands_before} brands")
            
            # Click delete button to open modal
            self.add_log("🖱️ Clicking delete button to open modal")
            if not self.safe_click(delete_button):
                self.fail("Failed to click delete button")
            
            # Wait for modal
            modal = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"#deleteModal{component_id}")))
            self.add_log("✅ Delete modal opened")
            
            # Find and click confirm button
            confirm_button = modal.find_element(By.CSS_SELECTOR, "button[onclick*='deleteComponent']")
            self.add_log("🖱️ Clicking confirm delete button")
            
            if not self.safe_click(confirm_button):
                self.fail("Failed to click confirm delete button")
            
            # Wait for deletion to complete
            self.add_log("⏳ Waiting for deletion to complete...")
            time.sleep(5)
            
            # Check browser console logs for errors
            logs = self.driver.get_log('browser')
            error_logs = [log for log in logs if log['level'] == 'SEVERE']
            if error_logs:
                self.add_log(f"🔴 Found {len(error_logs)} console errors:")
                for log in error_logs:
                    self.add_log(f"🔴 {log['message']}")
            
            # Check captured network requests
            requests = self.driver.execute_script("return window.capturedRequests || [];")
            self.add_log(f"🌐 Captured {len(requests)} network requests")
            
            delete_requests = [r for r in requests if '/component/' in r['url'] and r['method'] == 'DELETE']
            self.add_log(f"🗑️ Found {len(delete_requests)} DELETE requests")
            
            for req in delete_requests:
                self.add_log(f"🗑️ DELETE {req['url']}")
            
            if not delete_requests:
                self.add_log("❌ No DELETE requests found - JavaScript deleteComponent function may not be working")
            
            # Verify component is deleted from database
            after_data = self.get_component_data_from_db(component_id)
            if after_data and after_data['component']:
                self.fail(f"Component {component_id} still exists in database after deletion")
            
            self.add_log("✅ Component successfully deleted from database")
            
            # Verify page updated (check if component is no longer visible)
            remaining_delete_buttons = self.driver.find_elements(By.CSS_SELECTOR, f"[data-bs-target='#deleteModal{component_id}']")
            if remaining_delete_buttons:
                self.fail(f"Component {component_id} still visible on page after deletion")
            
            self.add_log("✅ Component removed from page")
            self.add_log("🎉 Single component deletion test completed successfully")
            
        except Exception as e:
            self.add_log(f"❌ Single deletion test failed: {str(e)}")
            raise

    def test_bulk_component_deletion_complete_workflow(self):
        """Test complete bulk component deletion workflow with database verification"""
        self.add_log("🎯 Testing Bulk Component Deletion - Complete Workflow")
        
        try:
            # Navigate to components page
            self.driver.get(f"{self.base_url}/components")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)
            
            # Find component checkboxes
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']:not(#selectAll)")
            self.add_log(f"🔍 Found {len(checkboxes)} component checkboxes")
            
            if len(checkboxes) < 2:
                self.skipTest("Need at least 2 components for bulk deletion")
            
            # Select first 2 components and get their IDs
            selected_components = []
            selected_count = 0
            
            for checkbox in checkboxes[:2]:
                if checkbox.is_displayed() and checkbox.is_enabled():
                    # Extract component ID from checkbox
                    component_id = None
                    
                    # Try different methods to get component ID
                    for attr in ['data-component-id', 'data-id', 'value']:
                        value = checkbox.get_attribute(attr)
                        if value and value.isdigit():
                            component_id = int(value)
                            break
                    
                    # Try Alpine.js click handler
                    if not component_id:
                        alpine_click = checkbox.get_attribute('@click.stop')
                        if alpine_click and 'toggleSelection' in alpine_click:
                            import re
                            match = re.search(r'toggleSelection\\((\\d+)\\)', alpine_click)
                            if match:
                                component_id = int(match.group(1))
                    
                    if component_id:
                        # Get component data before deletion
                        before_data = self.get_component_data_from_db(component_id)
                        if before_data and before_data['component']:
                            selected_components.append({
                                'id': component_id,
                                'data': before_data,
                                'checkbox': checkbox
                            })
                            selected_count += 1
                            
                            if selected_count >= 2:
                                break
            
            if len(selected_components) < 2:
                self.skipTest("Could not find 2 valid components for bulk deletion")
            
            self.add_log(f"📊 Selected components: {[c['id'] for c in selected_components]}")
            
            # Click checkboxes to select components
            for comp in selected_components:
                self.add_log(f"☑️ Selecting component {comp['id']}")
                if not self.safe_click(comp['checkbox']):
                    self.fail(f"Failed to select component {comp['id']}")
                time.sleep(0.5)
            
            # Wait for bulk actions to appear
            time.sleep(2)
            
            # Find bulk delete button
            bulk_delete_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button.btn-danger-modern")
            if not bulk_delete_buttons:
                # Try alternative selector
                bulk_delete_buttons = self.driver.find_elements(By.CSS_SELECTOR, "[onclick*='bulkAction'][onclick*='delete']")
            
            if not bulk_delete_buttons:
                self.skipTest("No bulk delete button found")
            
            # Find the delete button
            bulk_delete_button = None
            for btn in bulk_delete_buttons:
                if "Delete" in btn.text or "delete" in btn.get_attribute('onclick'):
                    bulk_delete_button = btn
                    break
            
            if not bulk_delete_button:
                self.skipTest("No bulk delete button with delete action found")
            
            self.add_log(f"🎯 Found bulk delete button: '{bulk_delete_button.text}'")
            
            # Click bulk delete button
            self.add_log("🖱️ Clicking bulk delete button")
            if not self.safe_click(bulk_delete_button):
                self.fail("Failed to click bulk delete button")
            
            # Handle confirmation dialog
            try:
                alert = self.wait.until(EC.alert_is_present())
                alert_text = alert.text
                self.add_log(f"🚨 Confirmation dialog: {alert_text}")
                alert.accept()
                self.add_log("✅ Confirmation accepted")
            except TimeoutException:
                self.add_log("⚠️ No confirmation dialog appeared")
            
            # Wait for deletion to complete
            self.add_log("⏳ Waiting for bulk deletion to complete...")
            time.sleep(8)
            
            # Verify all selected components are deleted from database
            deleted_count = 0
            for comp in selected_components:
                component_id = comp['id']
                after_data = self.get_component_data_from_db(component_id)
                
                if after_data and after_data['component']:
                    self.fail(f"Component {component_id} still exists in database after bulk deletion")
                else:
                    deleted_count += 1
                    self.add_log(f"✅ Component {component_id} successfully deleted from database")
            
            self.add_log(f"🎉 Bulk deletion completed: {deleted_count} components deleted")
            
            # Verify page updated (components should no longer be visible)
            for comp in selected_components:
                component_id = comp['id']
                remaining_checkboxes = self.driver.find_elements(By.CSS_SELECTOR, f"[data-component-id='{component_id}']")
                if remaining_checkboxes:
                    self.fail(f"Component {component_id} still visible on page after bulk deletion")
            
            self.add_log("✅ All deleted components removed from page")
            self.add_log("🎉 Bulk component deletion test completed successfully")
            
        except Exception as e:
            self.add_log(f"❌ Bulk deletion test failed: {str(e)}")
            raise

    def tearDown(self):
        """Print test logs after each test"""
        print("\\n" + "="*70)
        print("COMPLETE DELETION WORKFLOW TEST LOGS")
        print("="*70)
        for log in self.test_logs:
            print(log)
        print("="*70 + "\\n")


if __name__ == '__main__':
    unittest.main(verbosity=2)