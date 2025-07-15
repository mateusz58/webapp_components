#!/usr/bin/env python3
"""
Comprehensive Selenium tests for component edit form scenarios
Tests the complete component editing workflow with focus on component_edit_form logic

Based on docs analysis:
- Two-column layout with main form and sidebar
- Essential information, variants, keywords, and properties sections
- Real-time validation and error handling
- Picture management with drag-and-drop
- Dynamic form updates and SKU preview
- Manufacturing-focused workflow design
"""

import unittest
import time
import os
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    ElementClickInterceptedException,
    StaleElementReferenceException
)


class TestComponentEditFormComprehensive(unittest.TestCase):
    """Comprehensive tests for component edit form functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up Selenium WebDriver with optimized settings"""
        print(f"\n🔧 SELENIUM SETUP: Comprehensive Component Edit Form Testing")
        
        # Chrome options optimized for testing
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1366,768")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.driver.maximize_window()
            cls.driver.implicitly_wait(10)
            cls.wait = WebDriverWait(cls.driver, 20)
            cls.base_url = "http://localhost:6002"
            
            print(f"✅ Chrome browser initialized successfully")
            print(f"🌐 Testing against: {cls.base_url}")
            
        except Exception as e:
            print(f"❌ Failed to initialize WebDriver: {e}")
            raise

    @classmethod
    def tearDownClass(cls):
        """Clean up WebDriver"""
        print(f"\n🧹 SELENIUM TEARDOWN: Closing browser...")
        time.sleep(2)
        if hasattr(cls, 'driver'):
            cls.driver.quit()
            print(f"✅ Browser closed successfully")

    def setUp(self):
        """Set up for each test"""
        print(f"\n🧪 SELENIUM TEST SETUP: {self._testMethodName}")
        
        # Generate unique test identifiers
        self.timestamp = int(time.time())
        self.test_suffix = random.randint(1000, 9999)
        
        # Clear browser state
        self.driver.delete_all_cookies()
        
        # Test tracking
        self.test_component_id = None
        self.created_components = []

    def tearDown(self):
        """Clean up after each test"""
        print(f"🧹 Test cleanup: {self._testMethodName}")
        
        # Note: We don't delete test components to allow inspection
        # They can be cleaned up manually if needed
        if self.created_components:
            print(f"📝 Created components in this test: {self.created_components}")

    def test_navigate_to_component_edit_form(self):
        """Test navigation to component creation form and verify two-column layout"""
        print(f"\n🧪 SELENIUM TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Verify navigation and two-column layout structure")
        
        try:
            print(f"🔍 Step 1: Navigating to component creation form...")
            self.driver.get(f"{self.base_url}/component/new")
            
            # Wait for form to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            print(f"✅ Component creation form loaded")
            
            print(f"🔍 Step 2: Verifying two-column layout structure...")
            
            # Check for main form column
            main_form = self.driver.find_element(By.CSS_SELECTOR, ".col-lg-8, .main-form, .form-column")
            self.assertTrue(main_form.is_displayed(), "Main form column should be visible")
            print(f"✅ Main form column found and visible")
            
            # Check for sidebar column
            sidebar = self.driver.find_element(By.CSS_SELECTOR, ".col-lg-4, .sidebar, .info-column")
            self.assertTrue(sidebar.is_displayed(), "Sidebar column should be visible")
            print(f"✅ Sidebar column found and visible")
            
            print(f"🔍 Step 3: Verifying essential form sections...")
            
            # Essential Information section
            essential_section = self.driver.find_element(By.CSS_SELECTOR, 
                "[data-section='essential'], .essential-info, #essential-information")
            self.assertTrue(essential_section.is_displayed(), "Essential information section should be visible")
            print(f"✅ Essential information section found")
            
            # Component Variants section
            variants_section = self.driver.find_element(By.CSS_SELECTOR, 
                "[data-section='variants'], .variants-section, #component-variants")
            self.assertTrue(variants_section.is_displayed(), "Variants section should be visible")
            print(f"✅ Component variants section found")
            
            # Keywords section
            keywords_section = self.driver.find_element(By.CSS_SELECTOR, 
                "[data-section='keywords'], .keywords-section, #keywords")
            self.assertTrue(keywords_section.is_displayed(), "Keywords section should be visible")
            print(f"✅ Keywords section found")
            
            print(f"🔍 Step 4: Verifying form structure and CSRF protection...")
            
            # Check form has multipart encoding
            form = self.driver.find_element(By.TAG_NAME, "form")
            enctype = form.get_attribute("enctype")
            self.assertEqual(enctype, "multipart/form-data", "Form should have multipart encoding")
            print(f"✅ Form has correct multipart encoding")
            
            # Check CSRF token
            csrf_token = self.driver.find_element(By.CSS_SELECTOR, 
                "input[name='csrf_token'], meta[name='csrf-token']")
            self.assertTrue(csrf_token, "CSRF token should be present")
            print(f"✅ CSRF protection is in place")
            
            print(f"✅ SELENIUM TEST PASSED: Navigation and layout verification complete")
            
        except Exception as e:
            print(f"❌ SELENIUM TEST FAILED: {str(e)}")
            self._take_screenshot("navigation_failure")
            raise

    def test_essential_information_form_handling(self):
        """Test comprehensive essential information form handling"""
        print(f"\n🧪 SELENIUM TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test all essential information fields and validation")
        
        try:
            print(f"🔍 Step 1: Loading component creation form...")
            self.driver.get(f"{self.base_url}/component/new")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            
            # Generate unique test data
            product_number = f"SELENIUM-ESSENTIAL-{self.timestamp}"
            description = f"Comprehensive essential information test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            print(f"🔍 Step 2: Testing product number field...")
            product_field = self.wait.until(EC.presence_of_element_located((By.NAME, "product_number")))
            product_field.clear()
            product_field.send_keys(product_number)
            
            # Test real-time validation
            product_field.send_keys(Keys.TAB)
            time.sleep(1)
            print(f"✅ Product number entered and validated: {product_number}")
            
            print(f"🔍 Step 3: Testing component type selection...")
            component_type_select = Select(self.wait.until(
                EC.presence_of_element_located((By.NAME, "component_type_id"))))
            
            # Get available options
            options = component_type_select.options
            self.assertGreater(len(options), 1, "Should have component type options")
            
            # Select first non-empty option
            component_type_select.select_by_index(1)
            selected_type = component_type_select.first_selected_option.text
            print(f"✅ Component type selected: {selected_type}")
            
            print(f"🔍 Step 4: Testing supplier selection...")
            supplier_select = Select(self.wait.until(
                EC.presence_of_element_located((By.NAME, "supplier_id"))))
            
            supplier_options = supplier_select.options
            if len(supplier_options) > 1:
                supplier_select.select_by_index(1)
                selected_supplier = supplier_select.first_selected_option.text
                print(f"✅ Supplier selected: {selected_supplier}")
            else:
                print(f"⚠️ No suppliers available for selection")
            
            print(f"🔍 Step 5: Testing description field...")
            description_field = self.driver.find_element(By.NAME, "description")
            description_field.clear()
            description_field.send_keys(description)
            print(f"✅ Description entered")
            
            print(f"🔍 Step 6: Testing brand management...")
            # Test brand selection if available
            try:
                brand_section = self.driver.find_element(By.CSS_SELECTOR, 
                    ".brand-section, [data-section='brands'], #brand-management")
                
                # Look for brand selection mechanism
                brand_selects = self.driver.find_elements(By.CSS_SELECTOR, 
                    "select[name*='brand'], .brand-select")
                
                if brand_selects:
                    brand_select = Select(brand_selects[0])
                    brand_options = brand_select.options
                    if len(brand_options) > 1:
                        brand_select.select_by_index(1)
                        print(f"✅ Brand selected")
                    else:
                        print(f"⚠️ No brands available for selection")
                else:
                    print(f"⚠️ Brand selection not found")
                    
            except NoSuchElementException:
                print(f"⚠️ Brand management section not found")
            
            print(f"🔍 Step 7: Testing category selection...")
            try:
                category_section = self.driver.find_element(By.CSS_SELECTOR,
                    ".category-section, [data-section='categories'], #categories")
                
                # Look for category input or select
                category_inputs = self.driver.find_elements(By.CSS_SELECTOR,
                    "input[name*='category'], select[name*='category'], .category-input")
                
                if category_inputs:
                    category_input = category_inputs[0]
                    if category_input.tag_name == "select":
                        category_select = Select(category_input)
                        options = category_select.options
                        if len(options) > 1:
                            category_select.select_by_index(1)
                            print(f"✅ Category selected")
                    else:
                        # Text input with autocomplete
                        category_input.send_keys("test")
                        time.sleep(1)
                        print(f"✅ Category search tested")
                else:
                    print(f"⚠️ Category selection not found")
                    
            except NoSuchElementException:
                print(f"⚠️ Category section not found")
            
            print(f"🔍 Step 8: Verifying form data persistence...")
            # Verify all entered data is still present
            current_product = self.driver.find_element(By.NAME, "product_number").get_attribute("value")
            self.assertEqual(current_product, product_number, "Product number should persist")
            
            current_description = self.driver.find_element(By.NAME, "description").get_attribute("value")
            self.assertEqual(current_description, description, "Description should persist")
            
            print(f"✅ Form data persistence verified")
            
            print(f"✅ SELENIUM TEST PASSED: Essential information form handling complete")
            
        except Exception as e:
            print(f"❌ SELENIUM TEST FAILED: {str(e)}")
            self._take_screenshot("essential_info_failure")
            raise

    def test_component_variants_management_workflow(self):
        """Test comprehensive component variants management"""
        print(f"\n🧪 SELENIUM TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test variant creation, picture management, and validation")
        
        try:
            print(f"🔍 Step 1: Setting up component with basic information...")
            self.driver.get(f"{self.base_url}/component/new")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            
            # Fill essential information first
            product_number = f"SELENIUM-VARIANTS-{self.timestamp}"
            self._fill_essential_info_quickly(product_number)
            
            print(f"🔍 Step 2: Testing variant addition workflow...")
            
            # Find variant section
            variants_section = self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "[data-section='variants'], .variants-section, #component-variants")))
            
            # Look for add variant button
            try:
                add_variant_btn = self.driver.find_element(By.ID, "add_variant_btn")
            except NoSuchElementException:
                add_variant_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Add First Variant')]")
            
            # Add first variant
            print(f"🔍 Step 3: Adding first variant (Red)...")
            self._scroll_to_element(add_variant_btn)
            self._safe_click(add_variant_btn)
            time.sleep(1)
            
            # Fill variant details
            variant_containers = self.driver.find_elements(By.CSS_SELECTOR,
                ".variant-card, [data-variant-id]")
            self.assertGreater(len(variant_containers), 0, "Should have at least one variant container")
            
            first_variant = variant_containers[0]
            
            # Select color for first variant
            color_select = first_variant.find_element(By.CSS_SELECTOR, "select[name*='color']")
            color_select_obj = Select(color_select)
            color_options = color_select_obj.options
            self.assertGreater(len(color_options), 1, "Should have color options")
            
            # Find and select Red color
            red_option = None
            for option in color_options:
                if "red" in option.text.lower():
                    red_option = option
                    break
            
            if red_option:
                color_select_obj.select_by_visible_text(red_option.text)
                print(f"✅ Red color selected for first variant")
            else:
                color_select_obj.select_by_index(1)
                print(f"✅ First available color selected for first variant")
            
            print(f"🔍 Step 4: Testing picture upload for first variant...")
            
            # Find picture upload area
            picture_upload = first_variant.find_element(By.CSS_SELECTOR,
                "input[type='file'], .picture-upload, [data-upload]")
            
            # Create test image file
            test_image_path = self._create_test_image("red_variant_test.jpg")
            picture_upload.send_keys(test_image_path)
            time.sleep(2)  # Wait for upload processing
            
            # Verify picture was uploaded
            picture_previews = first_variant.find_elements(By.CSS_SELECTOR,
                ".picture-preview, .image-preview, img[src*='red_variant_test']")
            self.assertGreater(len(picture_previews), 0, "Should have picture preview")
            print(f"✅ Picture uploaded for first variant")
            
            print(f"🔍 Step 5: Adding second variant (Blue)...")
            self._safe_click(add_variant_btn)
            time.sleep(1)
            
            # Get updated variant containers
            variant_containers = self.driver.find_elements(By.CSS_SELECTOR,
                ".variant-item, .variant-container, [data-variant]")
            self.assertEqual(len(variant_containers), 2, "Should have two variant containers")
            
            second_variant = variant_containers[1]
            
            # Select different color for second variant
            color_select_2 = second_variant.find_element(By.CSS_SELECTOR, "select[name*='color']")
            color_select_2_obj = Select(color_select_2)
            
            # Find Blue color or select different option
            blue_option = None
            for option in color_select_2_obj.options:
                if "blue" in option.text.lower():
                    blue_option = option
                    break
            
            if blue_option:
                color_select_2_obj.select_by_visible_text(blue_option.text)
                print(f"✅ Blue color selected for second variant")
            else:
                # Select a different option than the first variant
                available_options = [opt for opt in color_select_2_obj.options if opt.text != color_select_obj.first_selected_option.text]
                if available_options:
                    color_select_2_obj.select_by_visible_text(available_options[0].text)
                    print(f"✅ Different color selected for second variant")
            
            print(f"🔍 Step 6: Testing picture upload for second variant...")
            picture_upload_2 = second_variant.find_element(By.CSS_SELECTOR,
                "input[type='file'], .picture-upload, [data-upload]")
            
            test_image_path_2 = self._create_test_image("blue_variant_test.jpg")
            picture_upload_2.send_keys(test_image_path_2)
            time.sleep(2)
            
            print(f"🔍 Step 7: Testing variant validation rules...")
            
            # Verify that each variant has required fields filled
            for i, variant in enumerate(variant_containers):
                variant_color = variant.find_element(By.CSS_SELECTOR, "select[name*='color']")
                color_value = Select(variant_color).first_selected_option.text
                self.assertNotEqual(color_value, "", f"Variant {i+1} should have color selected")
                
                variant_pictures = variant.find_elements(By.CSS_SELECTOR,
                    ".picture-preview, .image-preview, img")
                self.assertGreater(len(variant_pictures), 0, f"Variant {i+1} should have at least one picture")
            
            print(f"✅ Variant validation rules verified")
            
            print(f"🔍 Step 8: Testing variant removal functionality...")
            
            # Find remove button for second variant
            remove_buttons = second_variant.find_elements(By.CSS_SELECTOR,
                ".remove-variant, .btn-remove, [data-action='remove']")
            
            if remove_buttons:
                self._safe_click(remove_buttons[0])
                time.sleep(1)
                
                # Verify variant was removed
                updated_containers = self.driver.find_elements(By.CSS_SELECTOR,
                    ".variant-item, .variant-container, [data-variant]")
                self.assertEqual(len(updated_containers), 1, "Should have one variant after removal")
                print(f"✅ Variant removal functionality verified")
            else:
                print(f"⚠️ Remove variant button not found")
            
            print(f"✅ SELENIUM TEST PASSED: Component variants management workflow complete")
            
        except Exception as e:
            print(f"❌ SELENIUM TEST FAILED: {str(e)}")
            self._take_screenshot("variants_workflow_failure")
            raise

    def test_form_validation_and_error_handling(self):
        """Test comprehensive form validation and error handling"""
        print(f"\n🧪 SELENIUM TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test form validation, error messages, and real-time feedback")
        
        try:
            print(f"🔍 Step 1: Loading form for validation testing...")
            self.driver.get(f"{self.base_url}/component/new")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            
            print(f"🔍 Step 2: Testing empty form submission...")
            
            # Try to submit empty form
            submit_button = self.driver.find_element(By.CSS_SELECTOR,
                "button[type='submit'], input[type='submit'], .btn-submit")
            
            self._scroll_to_element(submit_button)
            self._safe_click(submit_button)
            time.sleep(2)
            
            # Check for validation messages
            validation_messages = self.driver.find_elements(By.CSS_SELECTOR,
                ".error, .invalid-feedback, .alert-danger, .validation-error, .field-error")
            
            if validation_messages:
                print(f"✅ Found {len(validation_messages)} validation messages for empty form")
                for msg in validation_messages[:3]:  # Show first 3
                    print(f"   - {msg.text[:50]}...")
            else:
                print(f"⚠️ No validation messages found for empty form")
            
            print(f"🔍 Step 3: Testing required field validation...")
            
            # Test product number validation
            product_field = self.driver.find_element(By.NAME, "product_number")
            product_field.clear()
            product_field.send_keys("   ")  # Spaces only
            product_field.send_keys(Keys.TAB)
            time.sleep(1)
            
            # Check for product number validation
            product_validation = self.driver.find_elements(By.CSS_SELECTOR,
                "input[name='product_number']:invalid, .product-number-error")
            
            if product_validation:
                print(f"✅ Product number validation working")
            else:
                print(f"⚠️ Product number validation not detected")
            
            print(f"🔍 Step 4: Testing component type validation...")
            
            # Ensure component type is not selected
            component_type_select = Select(self.driver.find_element(By.NAME, "component_type_id"))
            component_type_select.select_by_index(0)  # Select placeholder
            
            # Try to submit
            self._safe_click(submit_button)
            time.sleep(1)
            
            # Check for component type validation
            type_validation = self.driver.find_elements(By.CSS_SELECTOR,
                "select[name='component_type_id']:invalid, .component-type-error")
            
            if type_validation:
                print(f"✅ Component type validation working")
            else:
                print(f"⚠️ Component type validation not detected")
            
            print(f"🔍 Step 5: Testing variant validation...")
            
            # Fill minimal required fields
            product_field.clear()
            product_field.send_keys(f"VALIDATION-TEST-{self.timestamp}")
            
            if len(component_type_select.options) > 1:
                component_type_select.select_by_index(1)
            
            # Try to submit without variants
            self._safe_click(submit_button)
            time.sleep(2)
            
            # Check for variant validation messages
            variant_validation = self.driver.find_elements(By.CSS_SELECTOR,
                ".variant-error, .variants-required, .no-variants-error")
            
            if variant_validation:
                print(f"✅ Variant validation working")
            else:
                print(f"⚠️ Variant validation not detected")
            
            print(f"🔍 Step 6: Testing real-time validation feedback...")
            
            # Test product number length validation
            product_field.clear()
            long_product_number = "X" * 100  # Very long input
            product_field.send_keys(long_product_number)
            product_field.send_keys(Keys.TAB)
            time.sleep(1)
            
            # Check for length validation
            length_validation = self.driver.find_elements(By.CSS_SELECTOR,
                ".length-error, .too-long, input[name='product_number']:invalid")
            
            if length_validation:
                print(f"✅ Product number length validation working")
            else:
                print(f"⚠️ Product number length validation not detected")
            
            print(f"🔍 Step 7: Testing special character validation...")
            
            # Test special characters in product number
            product_field.clear()
            special_chars_product = "TEST@#$%^&*()"
            product_field.send_keys(special_chars_product)
            product_field.send_keys(Keys.TAB)
            time.sleep(1)
            
            # Check current value to see if special chars were filtered
            current_value = product_field.get_attribute("value")
            if current_value != special_chars_product:
                print(f"✅ Special character filtering working: '{special_chars_product}' → '{current_value}'")
            else:
                print(f"⚠️ Special characters allowed in product number")
            
            print(f"🔍 Step 8: Testing error message display and styling...")
            
            # Check if error messages have proper styling
            error_elements = self.driver.find_elements(By.CSS_SELECTOR,
                ".error, .invalid-feedback, .alert-danger")
            
            for error in error_elements[:3]:
                is_visible = error.is_displayed()
                color = error.value_of_css_property("color")
                background = error.value_of_css_property("background-color")
                
                if is_visible:
                    print(f"✅ Error message visible with styling")
                    break
            
            print(f"✅ SELENIUM TEST PASSED: Form validation and error handling complete")
            
        except Exception as e:
            print(f"❌ SELENIUM TEST FAILED: {str(e)}")
            self._take_screenshot("validation_failure")
            raise

    def test_complete_component_creation_workflow(self):
        """Test complete component creation workflow from start to finish"""
        print(f"\n🧪 SELENIUM TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Complete end-to-end component creation workflow")
        
        try:
            print(f"🔍 Step 1: Starting complete component creation workflow...")
            self.driver.get(f"{self.base_url}/component/new")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            
            # Generate unique test data
            product_number = f"SELENIUM-COMPLETE-{self.timestamp}"
            description = f"Complete workflow test component - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            print(f"🔍 Step 2: Filling essential information...")
            self._fill_essential_info_comprehensive(product_number, description)
            
            print(f"🔍 Step 3: Adding component variants with pictures...")
            self._add_multiple_variants_with_pictures()
            
            print(f"🔍 Step 4: Adding keywords...")
            self._add_keywords_to_component(["automation", "selenium", "test", "workflow"])
            
            print(f"🔍 Step 5: Adding component properties...")
            self._add_component_properties()
            
            print(f"🔍 Step 6: Final form validation before submission...")
            
            # Verify all required fields are filled
            validation_results = self._validate_complete_form()
            if not validation_results["is_valid"]:
                raise Exception(f"Form validation failed: {validation_results['errors']}")
            
            print(f"✅ Form validation passed")
            
            print(f"🔍 Step 7: Submitting form and handling response...")
            
            # Submit form
            submit_button = self.driver.find_element(By.CSS_SELECTOR,
                "button[type='submit'], input[type='submit'], .btn-submit")
            
            self._scroll_to_element(submit_button)
            self._safe_click(submit_button)
            
            # Wait for submission response
            print(f"⏳ Waiting for form submission response...")
            
            # Check for success redirect or error messages
            success = self._wait_for_submission_result()
            
            if success:
                print(f"✅ Component creation successful!")
                
                # Extract component ID from URL if redirected
                current_url = self.driver.current_url
                if "/component/" in current_url and "/component/new" not in current_url:
                    component_id = current_url.split("/component/")[-1].split("/")[0]
                    self.test_component_id = component_id
                    self.created_components.append(component_id)
                    print(f"✅ Redirected to component detail page: ID {component_id}")
                    
                    # Verify component details are displayed
                    self._verify_component_details_page(product_number)
                
            else:
                print(f"❌ Component creation failed or timed out")
                
                # Check for error messages
                error_messages = self.driver.find_elements(By.CSS_SELECTOR,
                    ".alert-danger, .error-message, .submission-error")
                
                if error_messages:
                    for error in error_messages:
                        print(f"🔴 Error: {error.text}")
                
                raise Exception("Component creation failed")
            
            print(f"✅ SELENIUM TEST PASSED: Complete component creation workflow successful")
            
        except Exception as e:
            print(f"❌ SELENIUM TEST FAILED: {str(e)}")
            self._take_screenshot("complete_workflow_failure")
            raise

    # Helper methods for comprehensive testing

    def _fill_essential_info_quickly(self, product_number):
        """Fill essential information quickly for setup"""
        product_field = self.driver.find_element(By.NAME, "product_number")
        product_field.clear()
        product_field.send_keys(product_number)
        
        component_type_select = Select(self.driver.find_element(By.NAME, "component_type_id"))
        if len(component_type_select.options) > 1:
            component_type_select.select_by_index(1)

    def _fill_essential_info_comprehensive(self, product_number, description):
        """Fill all essential information fields comprehensively"""
        # Product number
        product_field = self.driver.find_element(By.NAME, "product_number")
        product_field.clear()
        product_field.send_keys(product_number)
        
        # Description
        description_field = self.driver.find_element(By.NAME, "description")
        description_field.clear()
        description_field.send_keys(description)
        
        # Component type
        component_type_select = Select(self.driver.find_element(By.NAME, "component_type_id"))
        if len(component_type_select.options) > 1:
            component_type_select.select_by_index(1)
        
        # Supplier (if available)
        try:
            supplier_select = Select(self.driver.find_element(By.NAME, "supplier_id"))
            if len(supplier_select.options) > 1:
                supplier_select.select_by_index(1)
        except NoSuchElementException:
            pass
        
        # Categories (if available)
        try:
            category_inputs = self.driver.find_elements(By.CSS_SELECTOR,
                "input[name*='category'], select[name*='category']")
            if category_inputs:
                category_input = category_inputs[0]
                if category_input.tag_name == "select":
                    category_select = Select(category_input)
                    if len(category_select.options) > 1:
                        category_select.select_by_index(1)
                else:
                    category_input.send_keys("test")
        except NoSuchElementException:
            pass

    def _add_multiple_variants_with_pictures(self):
        """Add multiple variants with pictures"""
        # Add first variant
        add_variant_btn = self.driver.find_element(By.CSS_SELECTOR,
            ".add-variant, .btn-add-variant, [data-action='add-variant']")
        
        self._safe_click(add_variant_btn)
        time.sleep(1)
        
        # Get variant containers
        variant_containers = self.driver.find_elements(By.CSS_SELECTOR,
            ".variant-item, .variant-container, [data-variant]")
        
        if variant_containers:
            first_variant = variant_containers[0]
            
            # Select color
            color_select = Select(first_variant.find_element(By.CSS_SELECTOR, "select[name*='color']"))
            if len(color_select.options) > 1:
                color_select.select_by_index(1)
            
            # Add picture
            picture_upload = first_variant.find_element(By.CSS_SELECTOR, "input[type='file']")
            test_image_path = self._create_test_image("variant1_test.jpg")
            picture_upload.send_keys(test_image_path)
            time.sleep(2)

    def _add_keywords_to_component(self, keywords):
        """Add keywords to component"""
        try:
            keywords_section = self.driver.find_element(By.CSS_SELECTOR,
                "[data-section='keywords'], .keywords-section, #keywords")
            
            for keyword in keywords:
                # Look for keyword input
                keyword_inputs = keywords_section.find_elements(By.CSS_SELECTOR,
                    "input[name*='keyword'], .keyword-input")
                
                if keyword_inputs:
                    keyword_input = keyword_inputs[0]
                    keyword_input.send_keys(keyword)
                    keyword_input.send_keys(Keys.ENTER)
                    time.sleep(0.5)
                    
        except NoSuchElementException:
            print(f"⚠️ Keywords section not found")

    def _add_component_properties(self):
        """Add component properties if available"""
        try:
            properties_section = self.driver.find_element(By.CSS_SELECTOR,
                "[data-section='properties'], .properties-section, #component-properties")
            
            # Look for property fields
            property_inputs = properties_section.find_elements(By.CSS_SELECTOR,
                "input, select, textarea")
            
            for i, prop_input in enumerate(property_inputs[:3]):  # Limit to first 3
                if prop_input.tag_name == "input":
                    prop_input.send_keys(f"test_value_{i}")
                elif prop_input.tag_name == "select":
                    prop_select = Select(prop_input)
                    if len(prop_select.options) > 1:
                        prop_select.select_by_index(1)
                elif prop_input.tag_name == "textarea":
                    prop_input.send_keys(f"test_description_{i}")
                    
        except NoSuchElementException:
            print(f"⚠️ Properties section not found")

    def _validate_complete_form(self):
        """Validate that the complete form is properly filled"""
        errors = []
        
        # Check product number
        product_value = self.driver.find_element(By.NAME, "product_number").get_attribute("value")
        if not product_value.strip():
            errors.append("Product number is empty")
        
        # Check component type
        component_type_select = Select(self.driver.find_element(By.NAME, "component_type_id"))
        if component_type_select.first_selected_option.get_attribute("value") == "":
            errors.append("Component type not selected")
        
        # Check variants
        variant_containers = self.driver.find_elements(By.CSS_SELECTOR,
            ".variant-item, .variant-container, [data-variant]")
        if len(variant_containers) == 0:
            errors.append("No variants added")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }

    def _wait_for_submission_result(self, timeout=30):
        """Wait for form submission result"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            current_url = self.driver.current_url
            
            # Check for success redirect
            if "/component/" in current_url and "/component/new" not in current_url:
                return True
            
            # Check for error messages
            error_messages = self.driver.find_elements(By.CSS_SELECTOR,
                ".alert-danger, .error-message, .submission-error")
            if error_messages:
                return False
            
            time.sleep(1)
        
        return False

    def _verify_component_details_page(self, expected_product_number):
        """Verify component details page shows correct information"""
        try:
            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Check for product number on page
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            if expected_product_number in page_text:
                print(f"✅ Product number found on details page")
            else:
                print(f"⚠️ Product number not found on details page")
            
            # Check for component details sections
            detail_sections = self.driver.find_elements(By.CSS_SELECTOR,
                ".component-details, .product-info, .component-info")
            if detail_sections:
                print(f"✅ Component details section found")
            
        except Exception as e:
            print(f"⚠️ Could not verify details page: {e}")

    def _create_test_image(self, filename):
        """Create a simple test image file"""
        from PIL import Image
        import tempfile
        
        # Create a simple colored image
        img = Image.new('RGB', (100, 100), color='red' if 'red' in filename else 'blue')
        
        # Save to temporary file
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, filename)
        img.save(file_path, 'JPEG')
        
        return file_path

    def _scroll_to_element(self, element):
        """Scroll element into view"""
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)

    def _safe_click(self, element):
        """Safely click element with fallback to JavaScript"""
        try:
            element.click()
        except ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].click();", element)

    def _take_screenshot(self, name):
        """Take screenshot for debugging"""
        try:
            screenshot_path = f"/tmp/selenium_{name}_{self.timestamp}.png"
            self.driver.save_screenshot(screenshot_path)
            print(f"📸 Screenshot saved: {screenshot_path}")
        except Exception:
            pass


if __name__ == '__main__':
    # Instructions for running
    print("""
    🎬 COMPREHENSIVE COMPONENT EDIT FORM TESTING
    
    Prerequisites:
    1. Application must be running: ./start.sh
    2. Chrome/Chromium browser installed
    3. Python PIL library: pip install Pillow
    
    Run tests:
    python -m pytest tests/selenium/component_editing/test_component_edit_form_comprehensive.py -v -s
    
    This test suite covers:
    ✅ Navigation and layout verification
    ✅ Essential information form handling
    ✅ Component variants management workflow
    ✅ Form validation and error handling
    ✅ Complete component creation workflow
    
    Based on docs component_edit_form analysis.
    """)
    
    unittest.main()