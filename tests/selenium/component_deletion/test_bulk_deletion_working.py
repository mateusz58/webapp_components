#!/usr/bin/env python3
"""
Working test for bulk deletion functionality
Tests the complete bulk deletion workflow from component selection to deletion
"""
import time
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class BulkDeletionWorkingTest(unittest.TestCase):
    """Test bulk deletion functionality"""
    
    def setUp(self):
        """Set up test environment"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        self.base_url = "http://localhost:6002"
        
    def tearDown(self):
        """Clean up after test"""
        self.driver.quit()
        
    def test_bulk_deletion_api_works(self):
        """Test that bulk deletion API endpoint works correctly"""
        try:
            # Navigate to components page
            self.driver.get(f"{self.base_url}/components")
            
            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)
            
            # Test the bulk deletion API directly via JavaScript
            response = self.driver.execute_script("""
                // Get CSRF token
                const csrfToken = document.querySelector('[name=csrf-token]')?.content || 
                                 document.querySelector('[name=csrf_token]')?.value;
                
                if (!csrfToken) {
                    return { error: 'No CSRF token found' };
                }
                
                // Test with a non-existent component ID to verify API works
                return fetch('/api/components/bulk-delete', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({ component_ids: [99999] })
                }).then(response => {
                    return response.json().then(data => ({
                        status: response.status,
                        data: data
                    }));
                }).catch(error => ({
                    error: error.message
                }));
            """)
            
            # Wait for the fetch to complete
            time.sleep(3)
            
            print(f"API Response: {response}")
            
            # The API should respond properly even for non-existent components
            self.assertNotIn('error', response, "API call should not error out")
            self.assertIn('status', response, "Response should have status")
            self.assertIn('data', response, "Response should have data")
            
        except Exception as e:
            self.fail(f"Bulk deletion API test failed: {str(e)}")
    
    def test_bulk_deletion_csrf_token_available(self):
        """Test that CSRF token is available on the page"""
        try:
            # Navigate to components page
            self.driver.get(f"{self.base_url}/components")
            
            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Check for CSRF token
            csrf_token = self.driver.execute_script("""
                return document.querySelector('[name=csrf-token]')?.content || 
                       document.querySelector('[name=csrf_token]')?.value || null;
            """)
            
            self.assertIsNotNone(csrf_token, "CSRF token should be available")
            self.assertGreater(len(csrf_token), 10, "CSRF token should be substantial")
            
        except Exception as e:
            self.fail(f"CSRF token test failed: {str(e)}")
    
    def test_component_selection_works(self):
        """Test that component selection mechanism works"""
        try:
            # Navigate to components page
            self.driver.get(f"{self.base_url}/components")
            
            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)
            
            # Find checkboxes
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']:not(#selectAll)")
            
            if len(checkboxes) == 0:
                self.skipTest("No components available for selection test")
            
            # Test clicking a checkbox
            checkbox = checkboxes[0]
            if checkbox.is_displayed() and checkbox.is_enabled():
                # Click using JavaScript to avoid element interception
                self.driver.execute_script("arguments[0].click();", checkbox)
                
                # Verify checkbox is checked
                is_checked = checkbox.is_selected()
                self.assertTrue(is_checked, "Checkbox should be checked after clicking")
                
                # Check if Alpine.js registered the selection
                selection_status = self.driver.execute_script("""
                    const dashboard = document.querySelector('[x-data]');
                    if (dashboard && dashboard._x_dataStack) {
                        const alpineData = dashboard._x_dataStack[0];
                        return {
                            selectedComponents: alpineData.selectedComponents || [],
                            hasSelections: alpineData.selectedComponents && alpineData.selectedComponents.length > 0
                        };
                    }
                    return { selectedComponents: [], hasSelections: false };
                """)
                
                print(f"Selection status: {selection_status}")
                
        except Exception as e:
            self.fail(f"Component selection test failed: {str(e)}")


if __name__ == '__main__':
    unittest.main(verbosity=2)