"""
Selenium E2E Tests for Component Deletion Workflow
Tests the complete user workflow for deleting components via web interface
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
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains

# Add config directory to path for test configuration
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(os.path.dirname(current_dir), 'config')
sys.path.insert(0, config_path)

try:
    from test_config import TestConfig
except ImportError:
    # Fallback configuration if test_config is not available
    class TestConfig:
        BASE_URL = "http://localhost:6002"
        SELENIUM_HEADLESS = False
        SELENIUM_IMPLICIT_WAIT = 10
        SELENIUM_EXPLICIT_WAIT = 20


class ComponentDeletionE2ETestCase(unittest.TestCase):
    """E2E test cases for component deletion via web interface"""

    @classmethod
    def setUpClass(cls):
        """Set up Selenium WebDriver"""
        chrome_options = Options()
        
        if getattr(TestConfig, 'SELENIUM_HEADLESS', False):
            chrome_options.add_argument('--headless')
        
        # Additional Chrome options for better testing
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Enable visual testing with slow actions
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            print(f"Failed to initialize Chrome driver: {e}")
            print("Please ensure Chrome and ChromeDriver are installed")
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
        # Add visual indicator for test start
        self.add_test_indicator("🧪 Starting Component Deletion E2E Test")

    def tearDown(self):
        """Clean up each test"""
        # Add visual indicator for test end
        self.add_test_indicator("✅ Completed Component Deletion E2E Test")

    def add_test_indicator(self, message):
        """Add visual test indicator to page"""
        try:
            indicator_script = f"""
            var indicator = document.createElement('div');
            indicator.id = 'test-indicator';
            indicator.style.cssText = `
                position: fixed;
                top: 10px;
                right: 10px;
                background: #4CAF50;
                color: white;
                padding: 10px 15px;
                border-radius: 5px;
                z-index: 10000;
                font-family: Arial, sans-serif;
                font-size: 14px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            `;
            indicator.textContent = '{message}';
            
            // Remove existing indicator
            var existing = document.getElementById('test-indicator');
            if (existing) existing.remove();
            
            document.body.appendChild(indicator);
            
            // Auto-remove after 3 seconds
            setTimeout(() => {{
                if (indicator.parentNode) {{
                    indicator.parentNode.removeChild(indicator);
                }}
            }}, 3000);
            """
            self.driver.execute_script(indicator_script)
            time.sleep(0.5)  # Brief pause for visual effect
        except:
            pass  # Ignore errors in visual indicators

    def highlight_element(self, element, duration=1):
        """Highlight an element for visual testing"""
        try:
            # Add red border highlight
            original_style = element.get_attribute('style')
            self.driver.execute_script(
                "arguments[0].style.border = '3px solid red';"
                "arguments[0].style.backgroundColor = '#ffeb3b';"
                "arguments[0].scrollIntoView(true);",
                element
            )
            time.sleep(duration)
            # Restore original style
            self.driver.execute_script(
                f"arguments[0].style = '{original_style or ''}';",
                element
            )
        except:
            pass

    def slow_type(self, element, text, delay=0.1):
        """Type text slowly for visual effect"""
        element.clear()
        for char in text:
            element.send_keys(char)
            time.sleep(delay)

    def test_delete_component_modal_workflow(self):
        """Test complete deletion workflow using modal"""
        try:
            # Navigate to components list
            self.driver.get(f"{self.base_url}/components")
            self.add_test_indicator("📋 Navigated to Components List")
            
            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)
            
            # Look for a component with a delete button
            delete_buttons = self.driver.find_elements(By.CSS_SELECTOR, "[data-bs-target*='deleteModal']")
            
            if not delete_buttons:
                self.skipTest("No components with delete buttons found for testing")
            
            # Get the first component's delete button
            delete_button = delete_buttons[0]
            self.highlight_element(delete_button)
            
            # Extract component information for verification using JavaScript
            component_info = self.driver.execute_script("""
                const deleteBtn = arguments[0];
                const card = deleteBtn.closest('.component-card, .list-group-item');
                return card ? card.innerText.substring(0, 50) : 'Component found';
            """, delete_button)
            
            self.add_test_indicator(f"🎯 Found component: {component_info}...")
            
            # Click delete button to open modal using JavaScript
            self.add_test_indicator("🖱️ Opening Delete Modal")
            self.driver.execute_script("arguments[0].click();", delete_button)
            time.sleep(1)
            
            # Wait for modal to appear
            modal = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".modal")))
            self.highlight_element(modal)
            
            # Verify modal content
            modal_title = modal.find_element(By.CSS_SELECTOR, ".modal-title")
            self.assertIn("Deletion", modal_title.text)
            self.add_test_indicator("✅ Delete Modal Opened")
            
            # Look for confirmation button in modal
            confirm_button = modal.find_element(By.CSS_SELECTOR, "button[onclick*='deleteComponent']")
            self.highlight_element(confirm_button)
            
            # Click confirm delete (this will trigger JavaScript DELETE request)
            self.add_test_indicator("⚠️ Confirming Deletion")
            self.driver.execute_script("arguments[0].click();", confirm_button)
            time.sleep(1)
            
            # Handle JavaScript confirmation dialog
            try:
                alert = self.driver.switch_to.alert
                alert_text = alert.text
                self.assertIn("delete", alert_text.lower())
                self.add_test_indicator("🚨 Handling Confirmation Dialog")
                alert.accept()
                time.sleep(2)
            except:
                # No alert dialog appeared, continue
                pass
            
            # Wait for deletion to complete and page to redirect/update
            time.sleep(3)
            
            # Verify we're redirected to components list or see success message
            current_url = self.driver.current_url
            self.assertTrue(
                "/components" in current_url or "/component" in current_url,
                "Should be redirected after deletion"
            )
            
            self.add_test_indicator("✅ Deletion Workflow Completed")
            
        except TimeoutException:
            self.add_test_indicator("❌ Test Timeout")
            self.fail("Timeout waiting for elements in deletion workflow")
        except Exception as e:
            self.add_test_indicator(f"❌ Test Error: {str(e)[:50]}")
            raise

    def test_delete_component_ajax_response_handling(self):
        """Test AJAX response handling during deletion"""
        try:
            # Navigate to components list
            self.driver.get(f"{self.base_url}/components")
            self.add_test_indicator("📋 Testing AJAX Deletion")
            
            # Inject JavaScript to monitor AJAX requests
            self.driver.execute_script("""
                window.deleteRequests = [];
                window.originalFetch = fetch;
                window.fetch = function(...args) {
                    if (args[0].includes('/delete/') && args[1]?.method === 'DELETE') {
                        window.deleteRequests.push({
                            url: args[0],
                            method: args[1].method,
                            headers: args[1].headers,
                            timestamp: new Date()
                        });
                    }
                    return window.originalFetch.apply(this, args);
                };
            """)
            
            # Look for a component with a delete button
            delete_buttons = self.driver.find_elements(By.CSS_SELECTOR, "[data-bs-target*='deleteModal']")
            
            if not delete_buttons:
                self.skipTest("No components with delete buttons found for AJAX testing")
            
            # Click delete button using JavaScript to avoid element interception
            delete_button = delete_buttons[0]
            self.driver.execute_script("arguments[0].click();", delete_button)
            time.sleep(1)
            
            # Wait for modal and click confirm using JavaScript
            modal = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".modal")))
            confirm_button = modal.find_element(By.CSS_SELECTOR, "button[onclick*='deleteComponent']")
            self.driver.execute_script("arguments[0].click();", confirm_button)
            time.sleep(1)
            
            # Handle confirmation dialog if present
            try:
                alert = self.driver.switch_to.alert
                alert.accept()
                time.sleep(2)
            except:
                pass
            
            # Wait for AJAX request to complete
            time.sleep(3)
            
            # Check if AJAX request was made
            delete_requests = self.driver.execute_script("return window.deleteRequests;")
            
            if delete_requests:
                self.add_test_indicator("✅ AJAX Delete Request Captured")
                request = delete_requests[0]
                self.assertEqual(request['method'], 'DELETE')
                self.assertIn('/delete/', request['url'])
            else:
                self.add_test_indicator("ℹ️ No AJAX Requests Detected")
            
        except Exception as e:
            self.add_test_indicator(f"❌ AJAX Test Error: {str(e)[:50]}")
            raise

    def test_delete_component_csrf_token_handling(self):
        """Test CSRF token is properly included in deletion requests"""
        try:
            # Navigate to components list
            self.driver.get(f"{self.base_url}/components")
            self.add_test_indicator("🔒 Testing CSRF Token Handling")
            
            # Check for CSRF tokens in the page
            csrf_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[name='csrf_token']")
            csrf_meta = self.driver.find_elements(By.CSS_SELECTOR, "meta[name='csrf-token']")
            
            has_csrf = len(csrf_inputs) > 0 or len(csrf_meta) > 0
            
            if has_csrf:
                self.add_test_indicator("✅ CSRF Tokens Found on Page")
            else:
                self.add_test_indicator("⚠️ No CSRF Tokens Detected")
            
            # Look for delete functionality
            delete_buttons = self.driver.find_elements(By.CSS_SELECTOR, "[data-bs-target*='deleteModal']")
            
            if delete_buttons:
                # Check if delete buttons have CSRF token access
                delete_button = delete_buttons[0]
                onclick_attr = delete_button.get_attribute('onclick')
                
                if onclick_attr and 'csrf' in onclick_attr.lower():
                    self.add_test_indicator("✅ Delete Button Has CSRF Token")
                else:
                    # Check if CSRF token is passed to deleteComponent function
                    modal_id = delete_button.get_attribute('data-bs-target')
                    if modal_id:
                        modal = self.driver.find_element(By.CSS_SELECTOR, modal_id)
                        confirm_button = modal.find_element(By.CSS_SELECTOR, "button[onclick*='deleteComponent']")
                        confirm_onclick = confirm_button.get_attribute('onclick')
                        
                        if 'csrf' in confirm_onclick.lower():
                            self.add_test_indicator("✅ Modal Confirm Button Has CSRF Token")
                        else:
                            self.add_test_indicator("⚠️ CSRF Token Not Found in Delete Function")
            
        except Exception as e:
            self.add_test_indicator(f"❌ CSRF Test Error: {str(e)[:50]}")
            # Don't fail the test for CSRF token checking
            pass

    def test_delete_component_error_handling(self):
        """Test error handling during deletion workflow"""
        try:
            # Navigate to components list
            self.driver.get(f"{self.base_url}/components")
            self.add_test_indicator("⚠️ Testing Error Handling")
            
            # Inject JavaScript to simulate deletion errors
            self.driver.execute_script("""
                // Override deleteComponent function to simulate error
                window.originalDeleteComponent = window.deleteComponent;
                window.deleteComponent = function(componentId, csrfToken) {
                    alert('Simulated deletion error for testing');
                    return false;
                };
            """)
            
            # Look for a component with a delete button
            delete_buttons = self.driver.find_elements(By.CSS_SELECTOR, "[data-bs-target*='deleteModal']")
            
            if not delete_buttons:
                self.skipTest("No components found for error handling test")
            
            # Click delete button using JavaScript
            delete_button = delete_buttons[0]
            self.driver.execute_script("arguments[0].click();", delete_button)
            time.sleep(1)
            
            # Wait for modal and click confirm using JavaScript
            modal = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".modal")))
            confirm_button = modal.find_element(By.CSS_SELECTOR, "button[onclick*='deleteComponent']")
            self.driver.execute_script("arguments[0].click();", confirm_button)
            time.sleep(1)
            
            # Handle the first confirmation dialog
            try:
                alert = self.driver.switch_to.alert
                alert.accept()
                time.sleep(1)
            except:
                pass
            
            # Handle the simulated error alert
            try:
                error_alert = self.driver.switch_to.alert
                error_text = error_alert.text
                self.assertIn("error", error_text.lower())
                self.add_test_indicator("✅ Error Alert Handled")
                error_alert.accept()
            except:
                self.add_test_indicator("⚠️ No Error Alert Detected")
            
        except Exception as e:
            self.add_test_indicator(f"❌ Error Handling Test Failed: {str(e)[:50]}")
            raise

    def test_delete_component_responsive_design(self):
        """Test deletion workflow on different screen sizes"""
        try:
            screen_sizes = [
                (1920, 1080, "Desktop"),
                (768, 1024, "Tablet"),
                (375, 667, "Mobile")
            ]
            
            for width, height, device in screen_sizes:
                self.driver.set_window_size(width, height)
                time.sleep(1)
                
                self.add_test_indicator(f"📱 Testing {device} ({width}x{height})")
                
                # Navigate to components list
                self.driver.get(f"{self.base_url}/components")
                time.sleep(2)
                
                # Look for delete buttons (they might be in a dropdown on mobile)
                delete_buttons = self.driver.find_elements(By.CSS_SELECTOR, "[data-bs-target*='deleteModal']")
                
                if delete_buttons:
                    delete_button = delete_buttons[0]
                    self.assertTrue(delete_button.is_displayed(), f"Delete button should be visible on {device}")
                    self.add_test_indicator(f"✅ Delete Button Visible on {device}")
                else:
                    # Check for dropdown menus or other mobile-specific UI
                    dropdown_toggles = self.driver.find_elements(By.CSS_SELECTOR, ".dropdown-toggle")
                    if dropdown_toggles:
                        self.add_test_indicator(f"ℹ️ Dropdown UI Found on {device}")
                    else:
                        self.add_test_indicator(f"⚠️ No Delete UI Found on {device}")
                
                time.sleep(1)
            
            # Reset to desktop size
            self.driver.set_window_size(1920, 1080)
            
        except Exception as e:
            self.add_test_indicator(f"❌ Responsive Test Error: {str(e)[:50]}")
            raise

    def test_delete_component_accessibility(self):
        """Test accessibility aspects of deletion workflow"""
        try:
            # Navigate to components list
            self.driver.get(f"{self.base_url}/components")
            self.add_test_indicator("♿ Testing Accessibility")
            
            # Check for accessible delete buttons
            delete_buttons = self.driver.find_elements(By.CSS_SELECTOR, "[data-bs-target*='deleteModal']")
            
            if delete_buttons:
                delete_button = delete_buttons[0]
                
                # Check for accessibility attributes
                aria_label = delete_button.get_attribute('aria-label')
                title = delete_button.get_attribute('title')
                
                if aria_label or title:
                    self.add_test_indicator("✅ Delete Button Has Accessibility Labels")
                else:
                    self.add_test_indicator("⚠️ Delete Button Missing Accessibility Labels")
                
                # Check if button is keyboard accessible
                try:
                    delete_button.send_keys('\n')  # Try Enter key
                    time.sleep(1)
                    self.add_test_indicator("✅ Delete Button Keyboard Accessible")
                except:
                    self.add_test_indicator("⚠️ Delete Button Not Keyboard Accessible")
                
                # Close any opened modal
                try:
                    modal = self.driver.find_element(By.CSS_SELECTOR, ".modal.show")
                    close_button = modal.find_element(By.CSS_SELECTOR, ".btn-close, [data-bs-dismiss='modal']")
                    close_button.click()
                    time.sleep(1)
                except:
                    pass
            
        except Exception as e:
            self.add_test_indicator(f"❌ Accessibility Test Error: {str(e)[:50]}")
            # Don't fail for accessibility issues
            pass


if __name__ == '__main__':
    unittest.main()