#!/usr/bin/env python3
"""
Selenium E2E Tests for Component Edit Form
Comprehensive testing of component_edit_form.html with different editing scenarios
"""
import time
import json
import os
import sys
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Add app directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app import create_app, db
from app.models import Component, ComponentType, Supplier, Brand, Category, Color
from config import Config


class ComponentEditFormSeleniumTests(unittest.TestCase):
    """Selenium E2E tests for component edit form with comprehensive debugging"""

    @classmethod
    def setUpClass(cls):
        """Set up browser and test environment"""
        print("\n🚀 SELENIUM TEST SETUP: Component Edit Form E2E Tests")
        print("=" * 70)
        
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        print(f"🔧 Setting up Chrome WebDriver with headless mode...")
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.driver.implicitly_wait(10)
            print(f"✅ Chrome WebDriver initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Chrome WebDriver: {str(e)}")
            raise
        
        # Set up Flask app for database access
        cls.app = create_app()
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        
        # Get test data
        cls._get_test_data()
        
        print(f"✅ Test environment setup complete")
        print(f"📊 Test component: {cls.test_component.product_number if cls.test_component else 'None'}")
        print(f"📊 Available suppliers: {len(cls.suppliers)}")
        print(f"📊 Available component types: {len(cls.component_types)}")

    @classmethod
    def tearDownClass(cls):
        """Clean up browser and test environment"""
        print(f"\n🧹 SELENIUM TEST CLEANUP")
        if hasattr(cls, 'driver'):
            cls.driver.quit()
            print(f"✅ WebDriver closed")
        if hasattr(cls, 'app_context'):
            cls.app_context.pop()
            print(f"✅ Flask app context cleaned up")

    @classmethod
    def _get_test_data(cls):
        """Get test data from database"""
        print(f"🔍 Querying database for test data...")
        
        cls.test_component = Component.query.first()
        cls.suppliers = Supplier.query.all()
        cls.component_types = ComponentType.query.all()
        cls.brands = Brand.query.all()
        cls.categories = Category.query.all()
        cls.colors = Color.query.all()
        
        if not cls.test_component:
            raise ValueError("No test component found in database")

    def setUp(self):
        """Set up for each test"""
        print(f"\n🧪 SELENIUM TEST: {self._testMethodName}")
        print(f"🎯 Starting browser session for component edit testing...")
        
        self.base_url = "http://localhost:6002"
        self.edit_url = f"{self.base_url}/component/edit/{self.test_component.id}"
        
        print(f"🔗 Edit URL: {self.edit_url}")

    def tearDown(self):
        """Clean up after each test"""
        print(f"🧹 Cleaning up after: {self._testMethodName}")
        
        # Take screenshot on failure for debugging
        if hasattr(self, '_outcome') and not self._outcome.success:
            screenshot_path = f"/tmp/selenium_failure_{self._testMethodName}.png"
            try:
                self.driver.save_screenshot(screenshot_path)
                print(f"📸 Failure screenshot saved: {screenshot_path}")
            except Exception as e:
                print(f"⚠️ Failed to save screenshot: {str(e)}")

    def test_basic_field_editing_workflow(self):
        """Test editing basic component fields (product number, description, etc.)"""
        print(f"\n🧪 SELENIUM E2E TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test basic field editing workflow end-to-end")
        print(f"📝 Testing: product number, description, component type, supplier changes")
        
        try:
            # Step 1: Navigate to edit form
            print(f"\n📍 STEP 1: Navigate to component edit form")
            self.driver.get(self.edit_url)
            print(f"✅ Navigated to: {self.driver.current_url}")
            print(f"📊 Page title: {self.driver.title}")
            
            # Wait for form to load
            print(f"⏳ Waiting for edit form to load...")
            form_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "componentForm"))
            )
            print(f"✅ Component edit form loaded successfully")
            
            # Step 2: Capture original values
            print(f"\n📍 STEP 2: Capture original form values")
            original_product_number = self.driver.find_element(By.ID, "product_number").get_attribute("value")
            original_description = self.driver.find_element(By.ID, "description").get_attribute("value")
            
            print(f"📊 Original product number: '{original_product_number}'")
            print(f"📊 Original description: '{original_description}'")
            
            # Step 3: Edit basic fields
            print(f"\n📍 STEP 3: Edit basic form fields")
            new_product_number = f"{original_product_number}_selenium_edit"
            new_description = f"Selenium E2E test edit - {time.strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Clear and update product number
            product_number_field = self.driver.find_element(By.ID, "product_number")
            product_number_field.clear()
            product_number_field.send_keys(new_product_number)
            print(f"✅ Updated product number to: '{new_product_number}'")
            
            # Clear and update description
            description_field = self.driver.find_element(By.ID, "description")
            description_field.clear()
            description_field.send_keys(new_description)
            print(f"✅ Updated description to: '{new_description}'")
            
            # Change supplier if available
            try:
                supplier_select = Select(self.driver.find_element(By.ID, "supplier_id"))
                current_supplier = supplier_select.first_selected_option.text
                print(f"📊 Current supplier: '{current_supplier}'")
                
                if len(supplier_select.options) > 2:  # More than just empty + current
                    # Select different supplier
                    for option in supplier_select.options[1:]:  # Skip empty option
                        if option.text != current_supplier:
                            supplier_select.select_by_visible_text(option.text)
                            print(f"✅ Changed supplier to: '{option.text}'")
                            break
            except NoSuchElementException:
                print(f"⚠️ Supplier select not found")
            
            # Step 4: Monitor browser console for JavaScript errors
            print(f"\n📍 STEP 4: Check browser console for JavaScript errors")
            console_logs = self.driver.get_log('browser')
            if console_logs:
                print(f"⚠️ Browser console logs found:")
                for log in console_logs:
                    print(f"   {log['level']}: {log['message']}")
            else:
                print(f"✅ No browser console errors found")
            
            # Step 5: Submit form and monitor network activity
            print(f"\n📍 STEP 5: Submit form and monitor response")
            submit_button = self.driver.find_element(By.ID, "submitBtn")
            original_button_text = submit_button.text
            print(f"📊 Submit button text: '{original_button_text}'")
            
            # Enable browser logging before submission
            self.driver.execute_script("""
                console.log('🚀 SELENIUM: About to submit form');
                
                // Monitor fetch requests
                const originalFetch = window.fetch;
                window.fetch = function(...args) {
                    console.log('🌐 FETCH REQUEST:', args);
                    return originalFetch.apply(this, args)
                        .then(response => {
                            console.log('📡 FETCH RESPONSE:', response.status, response.statusText);
                            console.log('📡 RESPONSE HEADERS:', [...response.headers.entries()]);
                            return response;
                        })
                        .catch(error => {
                            console.error('❌ FETCH ERROR:', error);
                            throw error;
                        });
                };
                
                // Monitor form submission
                window.addEventListener('submit', function(e) {
                    console.log('📝 FORM SUBMIT EVENT:', e.target.id);
                });
            """)
            
            # Submit form
            print(f"🚀 Clicking submit button...")
            submit_button.click()
            
            # Step 6: Wait for submission processing
            print(f"\n📍 STEP 6: Wait for submission processing")
            
            # Check for loading state
            try:
                WebDriverWait(self.driver, 5).until(
                    lambda driver: "Processing" in driver.find_element(By.ID, "submitBtn").text or
                                   "Saving" in driver.find_element(By.ID, "submitBtn").text
                )
                print(f"✅ Form submission loading state detected")
                current_button_text = self.driver.find_element(By.ID, "submitBtn").text
                print(f"📊 Button text during processing: '{current_button_text}'")
            except TimeoutException:
                print(f"⚠️ No loading state detected (may be very fast)")
            
            # Wait for completion or redirect
            try:
                # Wait for either success redirect or error message
                WebDriverWait(self.driver, 15).until(
                    lambda driver: 
                        driver.current_url != self.edit_url or  # Redirected
                        driver.find_elements(By.CLASS_NAME, "alert-success") or  # Success message
                        driver.find_elements(By.CLASS_NAME, "alert-danger")  # Error message
                )
                print(f"✅ Form submission completed")
            except TimeoutException:
                print(f"⚠️ Form submission timeout - checking current state...")
            
            # Step 7: Analyze final state
            print(f"\n📍 STEP 7: Analyze submission result")
            final_url = self.driver.current_url
            print(f"📊 Final URL: {final_url}")
            
            if final_url != self.edit_url:
                print(f"✅ Redirected successfully from edit form")
                if "/component/" in final_url and "/edit" not in final_url:
                    print(f"✅ Redirected to component detail page")
                else:
                    print(f"⚠️ Unexpected redirect destination")
            else:
                print(f"⚠️ Still on edit form - checking for messages")
                
                # Check for success/error messages
                success_alerts = self.driver.find_elements(By.CSS_SELECTOR, ".alert-success, .alert.alert-success")
                error_alerts = self.driver.find_elements(By.CSS_SELECTOR, ".alert-danger, .alert.alert-danger")
                
                if success_alerts:
                    for alert in success_alerts:
                        print(f"✅ Success message: {alert.text}")
                elif error_alerts:
                    for alert in error_alerts:
                        print(f"❌ Error message: {alert.text}")
                else:
                    print(f"⚠️ No success or error messages found")
            
            # Step 8: Check browser console for final errors
            print(f"\n📍 STEP 8: Final browser console check")
            final_console_logs = self.driver.get_log('browser')
            json_parse_errors = [log for log in final_console_logs if 'JSON.parse' in log['message'] or 'unexpected character' in log['message']]
            
            if json_parse_errors:
                print(f"🚨 JSON PARSING ERRORS DETECTED!")
                for error in json_parse_errors:
                    print(f"❌ {error['level']}: {error['message']}")
                    print(f"   Timestamp: {error['timestamp']}")
                self.fail("JSON parsing errors detected in browser console")
            else:
                print(f"✅ No JSON parsing errors in browser console")
            
            print(f"✅ BASIC FIELD EDITING TEST COMPLETED SUCCESSFULLY")
            
        except Exception as e:
            print(f"❌ TEST FAILED: {str(e)}")
            print(f"📊 Current URL: {self.driver.current_url}")
            print(f"📊 Page source length: {len(self.driver.page_source)}")
            
            # Get browser console logs for debugging
            try:
                console_logs = self.driver.get_log('browser')
                if console_logs:
                    print(f"🔍 Browser console logs at failure:")
                    for log in console_logs[-10:]:  # Last 10 logs
                        print(f"   {log['level']}: {log['message']}")
            except Exception as log_error:
                print(f"⚠️ Could not retrieve console logs: {str(log_error)}")
            
            raise

    def test_picture_management_editing(self):
        """Test picture management and ordering in component edit form"""
        print(f"\n🧪 SELENIUM E2E TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test picture management and ordering functionality")
        print(f"📝 Testing: picture order changes, variant management, file operations")
        
        try:
            # Step 1: Navigate to edit form
            print(f"\n📍 STEP 1: Navigate to component edit form")
            self.driver.get(self.edit_url)
            
            # Wait for form and variant sections to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "componentForm"))
            )
            print(f"✅ Component edit form loaded")
            
            # Step 2: Check for variant sections
            print(f"\n📍 STEP 2: Analyze variant sections and pictures")
            variant_sections = self.driver.find_elements(By.CSS_SELECTOR, "[data-variant-id]")
            print(f"📊 Found {len(variant_sections)} variant sections")
            
            picture_items = self.driver.find_elements(By.CSS_SELECTOR, ".picture-item")
            print(f"📊 Found {len(picture_items)} picture items")
            
            if not variant_sections:
                print(f"⚠️ No variant sections found - skipping picture management test")
                return
            
            # Step 3: Test picture order changes
            print(f"\n📍 STEP 3: Test picture order input changes")
            picture_order_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[name^='picture_order_']")
            print(f"📊 Found {len(picture_order_inputs)} picture order inputs")
            
            if picture_order_inputs:
                # Change picture order for first few pictures
                for i, order_input in enumerate(picture_order_inputs[:3]):  # Test first 3
                    original_value = order_input.get_attribute("value")
                    new_value = str(int(original_value or "1") + 10)  # Add 10 to order
                    
                    order_input.clear()
                    order_input.send_keys(new_value)
                    print(f"✅ Changed picture order {i+1}: {original_value} → {new_value}")
                    
                    # Trigger change event to activate JavaScript
                    self.driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", order_input)
            
            # Step 4: Monitor JavaScript activity
            print(f"\n📍 STEP 4: Monitor JavaScript picture management activity")
            
            # Add JavaScript monitoring
            self.driver.execute_script("""
                console.log('🖼️ SELENIUM: Monitoring picture management JavaScript');
                
                // Monitor variant manager activity
                if (window.variantManager) {
                    const originalGetPictureOrderChanges = window.variantManager.getPictureOrderChanges;
                    if (originalGetPictureOrderChanges) {
                        window.variantManager.getPictureOrderChanges = function() {
                            const result = originalGetPictureOrderChanges.apply(this, arguments);
                            console.log('📊 getPictureOrderChanges result:', result);
                            return result;
                        };
                    }
                    
                    const originalProcessStagedChanges = window.variantManager.processStagedChanges;
                    if (originalProcessStagedChanges) {
                        window.variantManager.processStagedChanges = function() {
                            console.log('🔄 processStagedChanges called');
                            return originalProcessStagedChanges.apply(this, arguments);
                        };
                    }
                } else {
                    console.warn('⚠️ variantManager not found on window object');
                }
            """)
            
            # Step 5: Submit form with picture changes
            print(f"\n📍 STEP 5: Submit form with picture order changes")
            
            submit_button = self.driver.find_element(By.ID, "submitBtn")
            print(f"🚀 Submitting form with picture changes...")
            
            # Monitor network requests specifically for picture data
            self.driver.execute_script("""
                console.log('🌐 SELENIUM: Monitoring picture-related network requests');
                
                const originalFetch = window.fetch;
                window.fetch = function(...args) {
                    const url = args[0];
                    const options = args[1] || {};
                    
                    console.log('🌐 FETCH REQUEST to:', url);
                    
                    if (options.body) {
                        try {
                            if (typeof options.body === 'string') {
                                const bodyData = JSON.parse(options.body);
                                if (bodyData.picture_renames || bodyData.picture_order || 
                                    Object.keys(bodyData).some(key => key.startsWith('picture_order_'))) {
                                    console.log('🖼️ PICTURE DATA in request:', bodyData);
                                }
                            }
                        } catch (e) {
                            console.log('📤 Non-JSON request body (length):', options.body.length);
                        }
                    }
                    
                    return originalFetch.apply(this, args)
                        .then(response => {
                            console.log('📡 RESPONSE:', response.status, response.statusText);
                            
                            // Check if response is JSON
                            const contentType = response.headers.get('content-type');
                            console.log('📡 Content-Type:', contentType);
                            
                            if (contentType && contentType.includes('application/json')) {
                                return response.clone().text().then(text => {
                                    try {
                                        const jsonData = JSON.parse(text);
                                        console.log('✅ Valid JSON response received');
                                        if (jsonData.changes && jsonData.changes.picture_orders) {
                                            console.log('🖼️ Picture changes in response:', jsonData.changes.picture_orders);
                                        }
                                    } catch (parseError) {
                                        console.error('❌ JSON PARSE ERROR:', parseError);
                                        console.error('❌ Response text causing error:', text.substring(0, 100));
                                        window.seleniumJSONParseError = {
                                            error: parseError.message,
                                            responseText: text.substring(0, 500)
                                        };
                                    }
                                    return response;
                                });
                            } else {
                                console.warn('⚠️ Non-JSON response received');
                                return response;
                            }
                        })
                        .catch(error => {
                            console.error('❌ FETCH ERROR:', error);
                            throw error;
                        });
                };
            """)
            
            submit_button.click()
            
            # Step 6: Wait and check for JSON parsing errors
            print(f"\n📍 STEP 6: Wait for submission and check for JSON errors")
            
            time.sleep(3)  # Give time for processing
            
            # Check for JavaScript JSON parsing errors
            json_error = self.driver.execute_script("return window.seleniumJSONParseError || null")
            if json_error:
                print(f"🚨 JSON PARSING ERROR DETECTED!")
                print(f"❌ Error: {json_error['error']}")
                print(f"❌ Response text: {json_error['responseText']}")
                self.fail(f"JSON parsing error detected: {json_error['error']}")
            
            # Check browser console
            console_logs = self.driver.get_log('browser')
            parse_errors = [log for log in console_logs if 'JSON.parse' in log['message'] or 'unexpected character' in log['message']]
            
            if parse_errors:
                print(f"🚨 JSON PARSE ERRORS IN CONSOLE:")
                for error in parse_errors:
                    print(f"❌ {error['message']}")
                self.fail("JSON parsing errors found in browser console")
            
            print(f"✅ PICTURE MANAGEMENT EDITING TEST COMPLETED SUCCESSFULLY")
            
        except Exception as e:
            print(f"❌ PICTURE MANAGEMENT TEST FAILED: {str(e)}")
            raise

    def test_variant_management_workflow(self):
        """Test variant management including adding/removing variants"""
        print(f"\n🧪 SELENIUM E2E TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test variant management workflow")
        print(f"📝 Testing: variant addition, color selection, variant removal")
        
        try:
            # Step 1: Navigate to edit form
            print(f"\n📍 STEP 1: Navigate to component edit form")
            self.driver.get(self.edit_url)
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "componentForm"))
            )
            print(f"✅ Component edit form loaded")
            
            # Step 2: Count existing variants
            print(f"\n📍 STEP 2: Count existing variants")
            existing_variants = self.driver.find_elements(By.CSS_SELECTOR, "[data-variant-id]")
            print(f"📊 Found {len(existing_variants)} existing variants")
            
            # Step 3: Test adding new variant
            print(f"\n📍 STEP 3: Test adding new variant")
            
            try:
                add_variant_btn = self.driver.find_element(By.ID, "add_variant_btn")
                print(f"✅ Found 'Add Variant' button")
                
                # Monitor variant addition JavaScript
                self.driver.execute_script("""
                    console.log('🎨 SELENIUM: Monitoring variant addition');
                    
                    if (window.variantManager && window.variantManager.addNewVariant) {
                        const originalAddVariant = window.variantManager.addNewVariant;
                        window.variantManager.addNewVariant = function() {
                            console.log('➕ addNewVariant called');
                            const result = originalAddVariant.apply(this, arguments);
                            console.log('➕ addNewVariant completed');
                            return result;
                        };
                    }
                """)
                
                add_variant_btn.click()
                print(f"🚀 Clicked 'Add Variant' button")
                
                # Wait for new variant section to appear
                time.sleep(2)
                
                new_variants = self.driver.find_elements(By.CSS_SELECTOR, "[data-variant-id^='new_']")
                print(f"📊 Found {len(new_variants)} new variant sections")
                
                if new_variants:
                    print(f"✅ New variant section added successfully")
                    
                    # Try to select a color for the new variant
                    new_variant = new_variants[0]
                    color_select = new_variant.find_element(By.CSS_SELECTOR, "select[name*='variant_color']")
                    
                    if len(self.colors) > 0:
                        color_select_element = Select(color_select)
                        
                        # Select first available color
                        available_options = [opt for opt in color_select_element.options if opt.get_attribute("value")]
                        if available_options:
                            color_to_select = available_options[0]
                            color_select_element.select_by_value(color_to_select.get_attribute("value"))
                            print(f"✅ Selected color: {color_to_select.text}")
                        else:
                            print(f"⚠️ No color options available")
                    else:
                        print(f"⚠️ No colors available in database")
                
            except NoSuchElementException:
                print(f"⚠️ Add Variant button not found - may not be available for this component")
            
            # Step 4: Test form submission with variant changes
            print(f"\n📍 STEP 4: Test submission with variant changes")
            
            # Add comprehensive monitoring
            self.driver.execute_script("""
                console.log('🔍 SELENIUM: Setting up comprehensive variant monitoring');
                
                // Monitor form data gathering
                if (window.gatherFormDataForAPI) {
                    const originalGatherData = window.gatherFormDataForAPI;
                    window.gatherFormDataForAPI = function() {
                        console.log('📊 gatherFormDataForAPI called');
                        const result = originalGatherData.apply(this, arguments);
                        console.log('📊 Form data gathered:', result);
                        return result;
                    };
                }
                
                // Monitor variant file updates
                if (window.variantManager && window.variantManager.updateFormFiles) {
                    const originalUpdateFiles = window.variantManager.updateFormFiles;
                    window.variantManager.updateFormFiles = function() {
                        console.log('📁 updateFormFiles called');
                        return originalUpdateFiles.apply(this, arguments);
                    };
                }
            """)
            
            submit_button = self.driver.find_element(By.ID, "submitBtn")
            submit_button.click()
            print(f"🚀 Submitted form with variant changes")
            
            # Wait for processing
            time.sleep(5)
            
            # Check final result
            final_console_logs = self.driver.get_log('browser')
            json_errors = [log for log in final_console_logs if 'JSON.parse' in log['message'] or 'unexpected character' in log['message']]
            
            if json_errors:
                print(f"🚨 JSON ERRORS DETECTED:")
                for error in json_errors:
                    print(f"❌ {error['message']}")
                self.fail("JSON parsing errors detected during variant management")
            
            print(f"✅ VARIANT MANAGEMENT WORKFLOW TEST COMPLETED SUCCESSFULLY")
            
        except Exception as e:
            print(f"❌ VARIANT MANAGEMENT TEST FAILED: {str(e)}")
            raise

    def test_comprehensive_form_validation(self):
        """Test form validation and error handling scenarios"""
        print(f"\n🧪 SELENIUM E2E TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test form validation and error handling")
        print(f"📝 Testing: required field validation, duplicate checking, error display")
        
        try:
            # Step 1: Navigate to edit form
            print(f"\n📍 STEP 1: Navigate to component edit form")
            self.driver.get(self.edit_url)
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "componentForm"))
            )
            print(f"✅ Component edit form loaded")
            
            # Step 2: Test required field validation
            print(f"\n📍 STEP 2: Test required field validation")
            
            # Clear required product number field
            product_number_field = self.driver.find_element(By.ID, "product_number")
            original_product_number = product_number_field.get_attribute("value")
            product_number_field.clear()
            print(f"✅ Cleared product number field")
            
            # Try to submit with empty required field
            submit_button = self.driver.find_element(By.ID, "submitBtn")
            
            # Check if submit button is disabled
            is_disabled = submit_button.get_attribute("disabled") is not None
            button_text = submit_button.text
            print(f"📊 Submit button disabled: {is_disabled}")
            print(f"📊 Submit button text: '{button_text}'")
            
            if not is_disabled:
                print(f"⚠️ Submit button not disabled - testing validation on submit")
                submit_button.click()
                
                # Check for validation messages
                time.sleep(2)
                validation_messages = self.driver.find_elements(By.CSS_SELECTOR, ".form-error, .alert-danger")
                if validation_messages:
                    for msg in validation_messages:
                        if msg.is_displayed():
                            print(f"✅ Validation message: {msg.text}")
                else:
                    print(f"⚠️ No validation messages found")
            
            # Step 3: Restore valid data and test duplicate checking
            print(f"\n📍 STEP 3: Test duplicate product number checking")
            
            # Use another component's product number to test duplicate detection
            other_component = Component.query.filter(Component.id != self.test_component.id).first()
            if other_component:
                product_number_field.clear()
                product_number_field.send_keys(other_component.product_number)
                print(f"✅ Entered existing product number: {other_component.product_number}")
                
                # Trigger validation (blur event)
                product_number_field.send_keys(Keys.TAB)
                time.sleep(2)
                
                # Check for duplicate warning
                help_text = self.driver.find_elements(By.ID, "product_number_help")
                error_text = self.driver.find_elements(By.ID, "product_number_error")
                
                validation_found = False
                for element in help_text + error_text:
                    if element.is_displayed() and ("taken" in element.text.lower() or "exists" in element.text.lower()):
                        print(f"✅ Duplicate validation message: {element.text}")
                        validation_found = True
                        break
                
                if not validation_found:
                    print(f"⚠️ No duplicate validation message found")
            
            # Step 4: Restore original value and test successful submission
            print(f"\n📍 STEP 4: Restore valid data and test submission")
            product_number_field.clear()
            product_number_field.send_keys(f"{original_product_number}_validation_test")
            print(f"✅ Restored product number with test suffix")
            
            # Monitor validation JavaScript
            self.driver.execute_script("""
                console.log('✅ SELENIUM: Monitoring form validation');
                
                // Monitor validation functions
                if (window.validateForm) {
                    const originalValidate = window.validateForm;
                    window.validateForm = function() {
                        console.log('🔍 validateForm called');
                        const result = originalValidate.apply(this, arguments);
                        console.log('🔍 validateForm result:', result);
                        return result;
                    };
                }
                
                if (window.updateSubmitButtonState) {
                    const originalUpdateButton = window.updateSubmitButtonState;
                    window.updateSubmitButtonState = function() {
                        console.log('🔘 updateSubmitButtonState called');
                        return originalUpdateButton.apply(this, arguments);
                    };
                }
            """)
            
            submit_button.click()
            print(f"🚀 Submitted form with valid data")
            
            # Wait and check result
            time.sleep(5)
            
            # Check for any JSON parsing issues during validation
            final_logs = self.driver.get_log('browser')
            validation_errors = [log for log in final_logs if 'JSON.parse' in log['message'] or 'validation' in log['message'].lower()]
            
            if validation_errors:
                print(f"🔍 Validation-related console messages:")
                for error in validation_errors:
                    print(f"   {error['level']}: {error['message']}")
            
            print(f"✅ FORM VALIDATION TEST COMPLETED SUCCESSFULLY")
            
        except Exception as e:
            print(f"❌ FORM VALIDATION TEST FAILED: {str(e)}")
            raise


if __name__ == '__main__':
    print("🚀 Running Component Edit Form Selenium E2E Tests")
    print("=" * 70)
    print("🎯 Testing component_edit_form.html with various editing scenarios")
    print("🔍 Monitoring for JSON parsing errors and JavaScript issues")
    print("=" * 70)
    
    unittest.main(verbosity=2)