#!/usr/bin/env python3
"""
Selenium Test to Reproduce JSON Parsing Issue
Targeted test to reproduce the exact "JSON.parse: unexpected character" error
"""
import time
import json
import os
import sys
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

# Add app directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app import create_app, db
from app.models import Component
from config import Config


class JSONParsingReproductionTest(unittest.TestCase):
    """Targeted Selenium test to reproduce JSON parsing issues"""

    @classmethod
    def setUpClass(cls):
        """Set up browser and test environment"""
        print("\n🚀 SELENIUM JSON PARSING REPRODUCTION TEST")
        print("=" * 70)
        print("🎯 Target: Reproduce 'JSON.parse: unexpected character' error")
        print("=" * 70)
        
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.driver.implicitly_wait(10)
        
        # Set up Flask app
        cls.app = create_app()
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        
        cls.test_component = Component.query.first()
        if not cls.test_component:
            raise ValueError("No test component found")
        
        print(f"✅ Setup complete - Test component: {cls.test_component.product_number}")

    @classmethod
    def tearDownClass(cls):
        """Clean up"""
        if hasattr(cls, 'driver'):
            cls.driver.quit()
        if hasattr(cls, 'app_context'):
            cls.app_context.pop()

    def test_product_number_validation_json_error(self):
        """Test that reproduces the JSON parsing error in product number validation"""
        print(f"\n🧪 JSON PARSING REPRODUCTION TEST")
        print(f"🎯 Purpose: Reproduce JSON.parse error in product validation")
        
        try:
            # Step 1: Navigate to edit form
            print(f"\n📍 STEP 1: Navigate to component edit form")
            edit_url = f"http://localhost:6002/component/edit/{self.test_component.id}"
            self.driver.get(edit_url)
            print(f"✅ Navigated to: {edit_url}")
            
            # Wait for form to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "componentForm"))
            )
            print(f"✅ Form loaded successfully")
            
            # Step 2: Set up comprehensive JavaScript monitoring
            print(f"\n📍 STEP 2: Set up JavaScript error monitoring")
            
            self.driver.execute_script("""
                console.log('🔍 SELENIUM: Setting up JSON parsing error detection');
                
                // Track all JSON parsing attempts
                window.seleniumJSONErrors = [];
                
                // Override JSON.parse to catch errors
                const originalJSONParse = JSON.parse;
                JSON.parse = function(text) {
                    try {
                        console.log('📤 JSON.parse called with:', typeof text, text.substring(0, 100));
                        return originalJSONParse(text);
                    } catch (error) {
                        console.error('❌ JSON.parse ERROR:', error.message);
                        console.error('❌ Input text:', text.substring(0, 200));
                        window.seleniumJSONErrors.push({
                            error: error.message,
                            input: text.substring(0, 500),
                            stack: error.stack
                        });
                        throw error;
                    }
                };
                
                // Monitor fetch requests and responses
                const originalFetch = window.fetch;
                window.fetch = function(...args) {
                    const url = args[0];
                    console.log('🌐 FETCH REQUEST to:', url);
                    
                    return originalFetch.apply(this, args)
                        .then(response => {
                            console.log('📡 FETCH RESPONSE:', response.status, response.statusText);
                            console.log('📡 Content-Type:', response.headers.get('content-type'));
                            
                            // Clone response to read body without consuming it
                            const clonedResponse = response.clone();
                            return clonedResponse.text().then(text => {
                                console.log('📡 Response body (first 200 chars):', text.substring(0, 200));
                                
                                // Check if response looks like HTML when JSON expected
                                const contentType = response.headers.get('content-type') || '';
                                if (contentType.includes('application/json') && text.trim().startsWith('<')) {
                                    console.error('🚨 JSON CONTENT-TYPE BUT HTML RESPONSE!');
                                    console.error('🚨 This will cause JSON.parse errors!');
                                    window.seleniumJSONErrors.push({
                                        error: 'HTML response with JSON content-type',
                                        url: url,
                                        contentType: contentType,
                                        responseText: text.substring(0, 500)
                                    });
                                }
                                
                                return response;
                            });
                        })
                        .catch(error => {
                            console.error('❌ FETCH ERROR:', error);
                            throw error;
                        });
                };
                
                // Monitor XMLHttpRequest as well
                const originalXHROpen = XMLHttpRequest.prototype.open;
                XMLHttpRequest.prototype.open = function(method, url) {
                    console.log('📡 XHR REQUEST:', method, url);
                    this.addEventListener('load', function() {
                        console.log('📡 XHR RESPONSE:', this.status, this.statusText);
                        console.log('📡 XHR Content-Type:', this.getResponseHeader('content-type'));
                        if (this.responseText) {
                            console.log('📡 XHR Response (first 200 chars):', this.responseText.substring(0, 200));
                        }
                    });
                    return originalXHROpen.apply(this, arguments);
                };
            """)
            
            # Step 3: Trigger product number validation that causes the error
            print(f"\n📍 STEP 3: Trigger product number validation")
            
            product_number_field = self.driver.find_element(By.ID, "product_number")
            original_value = product_number_field.get_attribute("value")
            print(f"📊 Original product number: '{original_value}'")
            
            # Change to a value that will trigger validation
            test_product_number = f"{original_value}_trigger_validation"
            product_number_field.clear()
            product_number_field.send_keys(test_product_number)
            print(f"✅ Changed product number to: '{test_product_number}'")
            
            # Trigger validation by moving focus (blur event)
            product_number_field.send_keys(Keys.TAB)
            print(f"🚀 Triggered blur event to start validation")
            
            # Wait for validation to complete
            time.sleep(3)
            
            # Step 4: Check for JSON parsing errors
            print(f"\n📍 STEP 4: Check for JSON parsing errors")
            
            json_errors = self.driver.execute_script("return window.seleniumJSONErrors || []")
            
            if json_errors:
                print(f"🚨 JSON PARSING ERRORS DETECTED!")
                for i, error in enumerate(json_errors):
                    print(f"\n❌ ERROR #{i+1}:")
                    print(f"   Message: {error.get('error', 'Unknown')}")
                    if 'url' in error:
                        print(f"   URL: {error['url']}")
                    if 'contentType' in error:
                        print(f"   Content-Type: {error['contentType']}")
                    if 'input' in error:
                        print(f"   Input: {error['input'][:200]}...")
                    if 'responseText' in error:
                        print(f"   Response: {error['responseText'][:200]}...")
                
                # This reproduces the user's issue!
                print(f"\n🎯 SUCCESS: Reproduced the JSON parsing error!")
                print(f"🚨 This is the exact issue the user is experiencing!")
                
            else:
                print(f"✅ No JSON parsing errors detected")
            
            # Step 5: Check browser console for additional errors
            print(f"\n📍 STEP 5: Check browser console logs")
            
            console_logs = self.driver.get_log('browser')
            json_console_errors = [log for log in console_logs if 
                                 'JSON.parse' in log['message'] or 
                                 'Unexpected token' in log['message'] or
                                 'is not valid JSON' in log['message']]
            
            if json_console_errors:
                print(f"🚨 JSON ERRORS IN BROWSER CONSOLE:")
                for error in json_console_errors:
                    print(f"❌ {error['level']}: {error['message']}")
                    print(f"   Timestamp: {error['timestamp']}")
                
                print(f"\n🎯 CONFIRMED: Browser console shows JSON parsing errors!")
                
            else:
                print(f"✅ No JSON errors in browser console")
            
            # Step 6: Analyze specific validation endpoint issues
            print(f"\n📍 STEP 6: Test validation endpoint directly")
            
            # Test the validation endpoint that's causing issues
            validation_result = self.driver.execute_script("""
                return fetch('/api/component/validate-product-number', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        product_number: arguments[0],
                        supplier_id: null,
                        component_id: arguments[1]
                    })
                })
                .then(response => {
                    console.log('🔍 Validation endpoint response:', response.status, response.statusText);
                    console.log('🔍 Content-Type:', response.headers.get('content-type'));
                    return response.text();
                })
                .then(text => {
                    console.log('🔍 Validation response text:', text.substring(0, 200));
                    return {
                        success: true,
                        responseText: text.substring(0, 500),
                        isHTML: text.trim().startsWith('<')
                    };
                })
                .catch(error => {
                    console.error('🔍 Validation endpoint error:', error);
                    return {
                        success: false,
                        error: error.message
                    };
                });
            """, test_product_number, self.test_component.id)
            
            print(f"📊 Direct validation test result: {validation_result}")
            
            if validation_result.get('isHTML'):
                print(f"🚨 CONFIRMED: Validation endpoint returns HTML instead of JSON!")
                print(f"🚨 This is the root cause of the JSON parsing error!")
                print(f"📊 Response starts with: {validation_result['responseText'][:100]}...")
            
            # Final summary
            print(f"\n📊 FINAL ANALYSIS:")
            print(f"   JSON errors detected: {len(json_errors)}")
            print(f"   Console errors: {len(json_console_errors)}")
            print(f"   Validation endpoint issues: {validation_result.get('isHTML', False)}")
            
            if json_errors or json_console_errors or validation_result.get('isHTML'):
                print(f"\n✅ SUCCESS: Successfully reproduced the user's JSON parsing issue!")
                print(f"🎯 Root cause: Server returning HTML responses with JSON content-type")
            else:
                print(f"\n⚠️ JSON parsing error not reproduced in this test run")
                
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            
            # Get any final console logs
            try:
                final_logs = self.driver.get_log('browser')
                if final_logs:
                    print(f"🔍 Final console logs:")
                    for log in final_logs[-5:]:  # Last 5 logs
                        print(f"   {log['level']}: {log['message']}")
            except:
                pass
            
            raise

    def test_form_submission_json_errors(self):
        """Test form submission to catch JSON parsing errors during submit"""
        print(f"\n🧪 FORM SUBMISSION JSON ERROR TEST")
        print(f"🎯 Purpose: Catch JSON errors during form submission")
        
        try:
            # Navigate to form
            edit_url = f"http://localhost:6002/component/edit/{self.test_component.id}"
            self.driver.get(edit_url)
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "componentForm"))
            )
            print(f"✅ Form loaded")
            
            # Set up error monitoring
            self.driver.execute_script("""
                window.formSubmissionErrors = [];
                
                // Monitor form submission specifically
                if (window.submitViaAPI) {
                    const originalSubmit = window.submitViaAPI;
                    window.submitViaAPI = function() {
                        console.log('📝 submitViaAPI called');
                        return originalSubmit.apply(this, arguments)
                            .catch(error => {
                                console.error('❌ submitViaAPI error:', error);
                                window.formSubmissionErrors.push({
                                    error: error.message,
                                    stack: error.stack
                                });
                                throw error;
                            });
                    };
                }
                
                // Monitor response.json() calls specifically
                const originalResponseJSON = Response.prototype.json;
                Response.prototype.json = function() {
                    console.log('📤 response.json() called on response with status:', this.status);
                    console.log('📤 Content-Type:', this.headers.get('content-type'));
                    
                    return originalResponseJSON.apply(this)
                        .catch(error => {
                            console.error('❌ response.json() parsing error:', error.message);
                            window.formSubmissionErrors.push({
                                error: 'response.json() failed: ' + error.message,
                                status: this.status,
                                contentType: this.headers.get('content-type')
                            });
                            throw error;
                        });
                };
            """)
            
            # Make a simple change and try to submit
            product_number_field = self.driver.find_element(By.ID, "product_number")
            original_value = product_number_field.get_attribute("value")
            
            product_number_field.clear()
            product_number_field.send_keys(f"{original_value}_form_submit_test")
            
            # Scroll submit button into view and click
            submit_button = self.driver.find_element(By.ID, "submitBtn")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
            time.sleep(1)
            
            # Use JavaScript to click to avoid interception
            self.driver.execute_script("arguments[0].click();", submit_button)
            print(f"🚀 Form submitted via JavaScript")
            
            # Wait for submission to complete
            time.sleep(5)
            
            # Check for form submission errors
            submission_errors = self.driver.execute_script("return window.formSubmissionErrors || []")
            
            if submission_errors:
                print(f"🚨 FORM SUBMISSION ERRORS DETECTED!")
                for error in submission_errors:
                    print(f"❌ {error}")
                
                print(f"🎯 SUCCESS: Reproduced JSON parsing errors during form submission!")
            else:
                print(f"✅ No form submission JSON errors detected")
            
        except Exception as e:
            print(f"❌ Form submission test failed: {str(e)}")
            raise


if __name__ == '__main__':
    unittest.main(verbosity=2)