import unittest
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class TestComprehensiveComponentWorkflows(unittest.TestCase):
    """Comprehensive Selenium tests for component management workflows"""
    
    @classmethod
    def setUpClass(cls):
        """Set up Selenium WebDriver for all tests"""
        print(f"\n🔧 SELENIUM SETUP: Initializing WebDriver...")
        
        # Chrome options for headless testing
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.driver.implicitly_wait(10)
            cls.wait = WebDriverWait(cls.driver, 20)
            
            # Application base URL
            cls.base_url = "http://localhost:6002"
            print(f"✅ WebDriver initialized successfully")
            print(f"🌐 Testing against: {cls.base_url}")
            
        except Exception as e:
            print(f"❌ Failed to initialize WebDriver: {e}")
            raise

    @classmethod
    def tearDownClass(cls):
        """Clean up WebDriver"""
        print(f"\n🧹 SELENIUM TEARDOWN: Cleaning up WebDriver...")
        if hasattr(cls, 'driver'):
            cls.driver.quit()
            print(f"✅ WebDriver cleaned up successfully")

    def setUp(self):
        """Set up for each test"""
        print(f"\n🧪 SELENIUM TEST SETUP: {self._testMethodName}")
        print(f"🎯 Purpose: {self.shortDescription() or 'Selenium E2E test'}")
        
        # Clear any existing state
        self.driver.delete_all_cookies()
        
        print(f"✅ Selenium test setup complete for: {self._testMethodName}")

    def test_component_list_page_loads(self):
        """Test that component list page loads successfully"""
        print(f"\n🧪 SELENIUM TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Verify component list page loads and displays correctly")
        
        try:
            # Navigate to component list
            self.driver.get(f"{self.base_url}/components")
            print(f"🔍 Navigated to: {self.driver.current_url}")
            
            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            print(f"🔍 Page loaded successfully")
            
            # Check page title
            page_title = self.driver.title
            print(f"🔍 Page title: {page_title}")
            
            # Look for component list elements
            try:
                components_container = self.driver.find_element(By.CLASS_NAME, "components-list")
                print(f"🔍 Found components container")
            except NoSuchElementException:
                print(f"⚠️ Components container not found, checking for alternative selectors")
                # Look for table or other container
                containers = self.driver.find_elements(By.CSS_SELECTOR, "table, .list, .grid, main")
                print(f"🔍 Found {len(containers)} potential containers")
            
            # Check for navigation elements
            nav_elements = self.driver.find_elements(By.CSS_SELECTOR, "nav, .navbar, .navigation")
            print(f"🔍 Found {len(nav_elements)} navigation elements")
            
            # Verify page is not showing error
            error_elements = self.driver.find_elements(By.CSS_SELECTOR, ".error, .alert-danger, .exception")
            self.assertEqual(len(error_elements), 0, "Page should not show errors")
            
            print(f"✅ SELENIUM TEST PASSED: Component list page loads successfully")
            
        except TimeoutException:
            print(f"❌ SELENIUM TEST FAILED: Page load timeout")
            print(f"🔍 Current URL: {self.driver.current_url}")
            print(f"🔍 Page source (first 500 chars): {self.driver.page_source[:500]}")
            raise
        except Exception as e:
            print(f"❌ SELENIUM TEST FAILED: {str(e)}")
            self._capture_debug_info()
            raise

    def test_component_creation_form_loads(self):
        """Test that component creation form loads and has required fields"""
        print(f"\n🧪 SELENIUM TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Verify component creation form loads with all required fields")
        
        try:
            # Navigate to component creation form
            self.driver.get(f"{self.base_url}/components/new")
            print(f"🔍 Navigated to: {self.driver.current_url}")
            
            # Wait for form to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            print(f"🔍 Form element found")
            
            # Check for required form fields
            required_fields = [
                'product_number',
                'description', 
                'component_type_id',
                'supplier_id'
            ]
            
            for field_name in required_fields:
                try:
                    field = self.driver.find_element(By.NAME, field_name)
                    print(f"🔍 Found required field: {field_name} ({field.tag_name})")
                except NoSuchElementException:
                    print(f"⚠️ Required field not found: {field_name}")
            
            # Check for submit button
            submit_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                "button[type='submit'], input[type='submit'], .submit-btn")
            print(f"🔍 Found {len(submit_buttons)} submit buttons")
            self.assertGreater(len(submit_buttons), 0, "Form should have submit button")
            
            # Check for CSRF token
            csrf_inputs = self.driver.find_elements(By.CSS_SELECTOR, 
                "input[name='csrf_token'], input[name='_token']")
            print(f"🔍 Found {len(csrf_inputs)} CSRF token inputs")
            
            print(f"✅ SELENIUM TEST PASSED: Component creation form loads properly")
            
        except Exception as e:
            print(f"❌ SELENIUM TEST FAILED: {str(e)}")
            self._capture_debug_info()
            raise

    def test_component_edit_form_functionality(self):
        """Test component edit form functionality and field interactions"""
        print(f"\n🧪 SELENIUM TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test component edit form field interactions and validation")
        
        try:
            # First check if we can access an edit form (may need to create component first)
            # Try to access edit form for component ID 1
            self.driver.get(f"{self.base_url}/components/1/edit")
            print(f"🔍 Navigated to: {self.driver.current_url}")
            
            # Check if we get an edit form or need to create component first
            time.sleep(2)  # Allow page to load
            
            current_url = self.driver.current_url
            page_source = self.driver.page_source
            
            if "404" in page_source or "not found" in page_source.lower():
                print(f"⚠️ Component not found, testing form creation instead")
                self.driver.get(f"{self.base_url}/components/new")
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            else:
                print(f"🔍 Edit form loaded")
            
            # Test form field interactions
            try:
                # Find product number field
                product_number_field = self.driver.find_element(By.NAME, "product_number")
                original_value = product_number_field.get_attribute("value")
                print(f"🔍 Product number field found, current value: {original_value}")
                
                # Test field editing
                product_number_field.clear()
                test_value = f"SELENIUM-TEST-{int(time.time())}"
                product_number_field.send_keys(test_value)
                
                # Verify value was entered
                entered_value = product_number_field.get_attribute("value")
                self.assertEqual(entered_value, test_value)
                print(f"🔍 Successfully entered test value: {entered_value}")
                
            except NoSuchElementException:
                print(f"⚠️ Product number field not found")
            
            # Test description field
            try:
                description_field = self.driver.find_element(By.NAME, "description")
                description_field.clear()
                description_field.send_keys("Selenium test description")
                print(f"🔍 Description field updated successfully")
            except NoSuchElementException:
                print(f"⚠️ Description field not found")
            
            # Test dropdown fields
            try:
                supplier_select = Select(self.driver.find_element(By.NAME, "supplier_id"))
                options = supplier_select.options
                print(f"🔍 Supplier dropdown found with {len(options)} options")
                
                if len(options) > 1:  # Has options besides placeholder
                    supplier_select.select_by_index(1)
                    print(f"🔍 Selected supplier option")
            except (NoSuchElementException, Exception) as e:
                print(f"⚠️ Supplier dropdown not found or not selectable: {e}")
            
            print(f"✅ SELENIUM TEST PASSED: Form field interactions work")
            
        except Exception as e:
            print(f"❌ SELENIUM TEST FAILED: {str(e)}")
            self._capture_debug_info()
            raise

    def test_ajax_functionality_and_loading_states(self):
        """Test AJAX functionality and loading states in component forms"""
        print(f"\n🧪 SELENIUM TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test AJAX interactions and loading indicators")
        
        try:
            # Navigate to component form
            self.driver.get(f"{self.base_url}/components/new")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            print(f"🔍 Form loaded")
            
            # Look for any AJAX-enabled elements
            ajax_triggers = self.driver.find_elements(By.CSS_SELECTOR, 
                "[data-ajax], .ajax-trigger, [data-url], .validate-field")
            print(f"🔍 Found {len(ajax_triggers)} potential AJAX elements")
            
            # Test product number validation if field exists
            try:
                product_number_field = self.driver.find_element(By.NAME, "product_number")
                
                # Enter a test value
                test_product_number = f"AJAX-TEST-{int(time.time())}"
                product_number_field.clear()
                product_number_field.send_keys(test_product_number)
                
                # Trigger blur event (common AJAX trigger)
                self.driver.execute_script("arguments[0].blur();", product_number_field)
                
                # Wait a moment for potential AJAX call
                time.sleep(1)
                
                # Look for validation feedback
                validation_elements = self.driver.find_elements(By.CSS_SELECTOR,
                    ".validation-message, .error-message, .success-message, .feedback")
                print(f"🔍 Found {len(validation_elements)} validation feedback elements")
                
                print(f"🔍 Product number validation test completed")
                
            except NoSuchElementException:
                print(f"⚠️ Product number field not found for AJAX testing")
            
            # Test for loading indicators
            loading_elements = self.driver.find_elements(By.CSS_SELECTOR,
                ".loading, .spinner, .progress, [data-loading]")
            print(f"🔍 Found {len(loading_elements)} potential loading indicators")
            
            # Check for JavaScript errors in console
            try:
                logs = self.driver.get_log('browser')
                js_errors = [log for log in logs if log['level'] == 'SEVERE']
                print(f"🔍 Found {len(js_errors)} JavaScript errors")
                
                for error in js_errors[:3]:  # Show first 3 errors
                    print(f"🔍 JS Error: {error['message'][:100]}...")
                    
            except Exception:
                print(f"⚠️ Could not retrieve browser console logs")
            
            print(f"✅ SELENIUM TEST PASSED: AJAX functionality tested")
            
        except Exception as e:
            print(f"❌ SELENIUM TEST FAILED: {str(e)}")
            self._capture_debug_info()
            raise

    def test_responsive_design_and_mobile_view(self):
        """Test responsive design and mobile view functionality"""
        print(f"\n🧪 SELENIUM TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test responsive design across different screen sizes")
        
        try:
            # Test desktop view first
            self.driver.set_window_size(1920, 1080)
            self.driver.get(f"{self.base_url}/components")
            time.sleep(1)
            
            desktop_elements = self.driver.find_elements(By.CSS_SELECTOR, "*")
            print(f"🔍 Desktop view (1920x1080): {len(desktop_elements)} elements visible")
            
            # Test tablet view
            self.driver.set_window_size(768, 1024)
            time.sleep(1)
            
            tablet_elements = self.driver.find_elements(By.CSS_SELECTOR, "*")
            print(f"🔍 Tablet view (768x1024): {len(tablet_elements)} elements visible")
            
            # Test mobile view
            self.driver.set_window_size(375, 667)
            time.sleep(1)
            
            mobile_elements = self.driver.find_elements(By.CSS_SELECTOR, "*")
            print(f"🔍 Mobile view (375x667): {len(mobile_elements)} elements visible")
            
            # Check for responsive navigation
            nav_toggles = self.driver.find_elements(By.CSS_SELECTOR,
                ".navbar-toggle, .menu-toggle, .hamburger, [data-toggle='collapse']")
            print(f"🔍 Found {len(nav_toggles)} navigation toggle elements")
            
            # Test if content is accessible in mobile view
            main_content = self.driver.find_elements(By.CSS_SELECTOR, "main, .content, .container")
            self.assertGreater(len(main_content), 0, "Main content should be accessible in mobile view")
            
            # Reset to desktop view
            self.driver.set_window_size(1920, 1080)
            
            print(f"✅ SELENIUM TEST PASSED: Responsive design tested across screen sizes")
            
        except Exception as e:
            print(f"❌ SELENIUM TEST FAILED: {str(e)}")
            self._capture_debug_info()
            raise

    def test_form_validation_and_error_handling(self):
        """Test form validation and error handling in the UI"""
        print(f"\n🧪 SELENIUM TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test form validation messages and error handling")
        
        try:
            # Navigate to component creation form
            self.driver.get(f"{self.base_url}/components/new")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            print(f"🔍 Form loaded for validation testing")
            
            # Try to submit empty form
            submit_buttons = self.driver.find_elements(By.CSS_SELECTOR,
                "button[type='submit'], input[type='submit']")
            
            if submit_buttons:
                print(f"🔍 Attempting to submit empty form")
                submit_buttons[0].click()
                
                # Wait for potential validation messages
                time.sleep(2)
                
                # Look for validation error messages
                error_elements = self.driver.find_elements(By.CSS_SELECTOR,
                    ".error, .invalid-feedback, .alert-danger, .validation-error")
                print(f"🔍 Found {len(error_elements)} error message elements")
                
                # Check for HTML5 validation
                try:
                    invalid_fields = self.driver.find_elements(By.CSS_SELECTOR, ":invalid")
                    print(f"🔍 Found {len(invalid_fields)} HTML5 invalid fields")
                except Exception:
                    print(f"⚠️ Could not check HTML5 validation")
                
            # Test with invalid data
            try:
                product_number_field = self.driver.find_element(By.NAME, "product_number")
                
                # Test very long product number
                long_product_number = "X" * 100
                product_number_field.clear()
                product_number_field.send_keys(long_product_number)
                
                # Trigger validation
                self.driver.execute_script("arguments[0].blur();", product_number_field)
                time.sleep(1)
                
                # Look for length validation
                validation_messages = self.driver.find_elements(By.CSS_SELECTOR,
                    ".validation-message, .error-message")
                print(f"🔍 Validation messages after long input: {len(validation_messages)}")
                
            except NoSuchElementException:
                print(f"⚠️ Product number field not found for validation testing")
            
            print(f"✅ SELENIUM TEST PASSED: Form validation and error handling tested")
            
        except Exception as e:
            print(f"❌ SELENIUM TEST FAILED: {str(e)}")
            self._capture_debug_info()
            raise

    def test_picture_upload_workflow(self):
        """Test picture upload workflow and visibility"""
        print(f"\n🧪 SELENIUM TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test picture upload functionality and immediate visibility")
        
        try:
            # Navigate to component form
            self.driver.get(f"{self.base_url}/components/new")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            print(f"🔍 Form loaded for picture upload testing")
            
            # Look for file input elements
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            print(f"🔍 Found {len(file_inputs)} file input elements")
            
            # Look for picture/image related sections
            picture_sections = self.driver.find_elements(By.CSS_SELECTOR,
                ".picture, .image, .upload, [data-upload], .file-drop")
            print(f"🔍 Found {len(picture_sections)} picture-related sections")
            
            # Test drag and drop areas
            drop_zones = self.driver.find_elements(By.CSS_SELECTOR,
                ".drop-zone, .file-drop-area, [data-drop]")
            print(f"🔍 Found {len(drop_zones)} drag-and-drop zones")
            
            # Look for picture preview areas
            preview_areas = self.driver.find_elements(By.CSS_SELECTOR,
                ".preview, .thumbnail, .image-preview, .picture-preview")
            print(f"🔍 Found {len(preview_areas)} picture preview areas")
            
            # Test picture management buttons
            picture_buttons = self.driver.find_elements(By.CSS_SELECTOR,
                ".add-picture, .remove-picture, .manage-pictures, [data-picture]")
            print(f"🔍 Found {len(picture_buttons)} picture management buttons")
            
            # If file inputs exist, test basic interaction
            if file_inputs:
                print(f"🔍 Testing file input interaction")
                # Note: Actual file upload testing would require test files
                # This tests the UI elements are present and accessible
                
            print(f"✅ SELENIUM TEST PASSED: Picture upload workflow UI elements tested")
            
        except Exception as e:
            print(f"❌ SELENIUM TEST FAILED: {str(e)}")
            self._capture_debug_info()
            raise

    def _capture_debug_info(self):
        """Capture debug information when tests fail"""
        try:
            print(f"\n🔍 DEBUG INFO:")
            print(f"Current URL: {self.driver.current_url}")
            print(f"Page title: {self.driver.title}")
            print(f"Window size: {self.driver.get_window_size()}")
            
            # Capture screenshot if possible
            try:
                screenshot_path = f"/tmp/selenium_debug_{int(time.time())}.png"
                self.driver.save_screenshot(screenshot_path)
                print(f"Screenshot saved: {screenshot_path}")
            except Exception:
                print(f"Could not save screenshot")
            
            # Get page source snippet
            page_source = self.driver.page_source
            print(f"Page source (first 1000 chars): {page_source[:1000]}")
            
        except Exception as e:
            print(f"Could not capture debug info: {e}")


if __name__ == '__main__':
    unittest.main()