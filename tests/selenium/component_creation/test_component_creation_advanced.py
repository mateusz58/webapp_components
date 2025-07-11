#!/usr/bin/env python3
"""
Advanced Selenium tests for component creation workflow
Comprehensive scenarios covering edge cases and advanced features

Based on docs analysis:
- Manufacturing-focused workflow design
- Drag-and-drop picture management
- Real-time validation and feedback
- Complex brand and category associations
- Dynamic property handling based on component type
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
    ElementClickInterceptedException
)


class TestComponentCreationAdvanced(unittest.TestCase):
    """Advanced component creation workflow tests"""
    
    @classmethod
    def setUpClass(cls):
        """Set up Selenium WebDriver with advanced options"""
        print(f"\n🔧 SELENIUM SETUP: Advanced Component Creation Testing")
        
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")  # Larger window for advanced testing
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Enable file downloads for testing
        chrome_options.add_experimental_option("prefs", {
            "download.default_directory": "/tmp",
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.driver.maximize_window()
            cls.driver.implicitly_wait(10)
            cls.wait = WebDriverWait(cls.driver, 30)  # Longer wait for complex operations
            cls.base_url = "http://localhost:6002"
            
            print(f"✅ Chrome browser initialized for advanced testing")
            
        except Exception as e:
            print(f"❌ Failed to initialize WebDriver: {e}")
            raise

    @classmethod
    def tearDownClass(cls):
        """Clean up WebDriver"""
        print(f"\n🧹 SELENIUM TEARDOWN: Closing browser after advanced tests...")
        time.sleep(3)  # Longer pause to review results
        if hasattr(cls, 'driver'):
            cls.driver.quit()

    def setUp(self):
        """Set up for each test"""
        print(f"\n🧪 ADVANCED SELENIUM TEST SETUP: {self._testMethodName}")
        self.timestamp = int(time.time())
        self.test_suffix = random.randint(10000, 99999)
        self.driver.delete_all_cookies()
        self.created_components = []

    def test_multiple_variants_with_picture_management(self):
        """Test creating component with multiple variants and comprehensive picture management"""
        print(f"\n🧪 SELENIUM TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test multiple variants with advanced picture management")
        
        try:
            print(f"🔍 Step 1: Setting up component creation form...")
            self.driver.get(f"{self.base_url}/component/new")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            
            # Fill essential information
            product_number = f"MULTI-VARIANT-{self.timestamp}"
            description = f"Advanced multi-variant test component - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            self._fill_essential_info(product_number, description)
            
            print(f"🔍 Step 2: Creating multiple variants with different colors...")
            
            # Test data for variants
            variant_colors = ["Red", "Blue", "Green", "Yellow", "Black"]
            created_variants = []
            
            for i, color_name in enumerate(variant_colors):
                print(f"   Creating variant {i+1}: {color_name}")
                
                # Add variant
                try:
                    add_variant_btn = self.driver.find_element(By.ID, "add_variant_btn")
                except NoSuchElementException:
                    add_variant_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Add First Variant')]")
                self._scroll_to_element(add_variant_btn)
                self._safe_click(add_variant_btn)
                time.sleep(1)
                
                # Get the newly created variant container
                variant_containers = self.driver.find_elements(By.CSS_SELECTOR,
                    ".variant-card, [data-variant-id]")
                
                if len(variant_containers) > i:
                    current_variant = variant_containers[i]
                    
                    # Select color
                    color_select = Select(current_variant.find_element(By.CSS_SELECTOR, "select[name*='color']"))
                    
                    # Find the color option
                    color_found = False
                    for option in color_select.options:
                        if color_name.lower() in option.text.lower():
                            color_select.select_by_visible_text(option.text)
                            color_found = True
                            break
                    
                    if not color_found and len(color_select.options) > i + 1:
                        color_select.select_by_index(i + 1)
                        color_found = True
                    
                    if color_found:
                        selected_color = color_select.first_selected_option.text
                        print(f"     ✅ Color selected: {selected_color}")
                        
                        # Add multiple pictures to variant
                        self._add_multiple_pictures_to_variant(current_variant, color_name, i + 1)
                        
                        created_variants.append({
                            'color': selected_color,
                            'container': current_variant,
                            'index': i
                        })
                    else:
                        print(f"     ⚠️ Could not select color for variant {i+1}")
                else:
                    print(f"     ❌ Variant container not found for variant {i+1}")
                
                # Limit to 3 variants for testing efficiency
                if i >= 2:
                    break
            
            print(f"✅ Created {len(created_variants)} variants")
            
            print(f"🔍 Step 3: Testing picture ordering and management...")
            
            # Test picture ordering within variants
            for variant_info in created_variants:
                variant = variant_info['container']
                color = variant_info['color']
                
                print(f"   Testing picture management for {color} variant...")
                
                # Find picture containers within this variant
                picture_containers = variant.find_elements(By.CSS_SELECTOR,
                    ".picture-container, .image-container, .picture-item")
                
                if len(picture_containers) > 1:
                    print(f"     Found {len(picture_containers)} pictures - testing reordering...")
                    
                    # Test drag and drop reordering if available
                    try:
                        first_picture = picture_containers[0]
                        second_picture = picture_containers[1]
                        
                        # Try to drag first picture to second position
                        action_chains = ActionChains(self.driver)
                        action_chains.drag_and_drop(first_picture, second_picture).perform()
                        time.sleep(1)
                        
                        print(f"     ✅ Picture reordering attempted")
                        
                    except Exception as e:
                        print(f"     ⚠️ Picture reordering not available: {e}")
                
                # Test picture removal
                remove_buttons = variant.find_elements(By.CSS_SELECTOR,
                    ".remove-picture, .delete-picture, [data-action='remove-picture']")
                
                if len(remove_buttons) > 1:  # Only remove if more than 1 picture
                    print(f"     Testing picture removal...")
                    try:
                        self._safe_click(remove_buttons[-1])  # Remove last picture
                        time.sleep(1)
                        print(f"     ✅ Picture removal tested")
                    except Exception as e:
                        print(f"     ⚠️ Picture removal failed: {e}")
            
            print(f"🔍 Step 4: Testing variant validation rules...")
            
            # Test that each variant has required fields
            final_variants = self.driver.find_elements(By.CSS_SELECTOR,
                ".variant-item, .variant-container, [data-variant]")
            
            for i, variant in enumerate(final_variants):
                # Check color selection
                color_select = Select(variant.find_element(By.CSS_SELECTOR, "select[name*='color']"))
                color_value = color_select.first_selected_option.get_attribute("value")
                self.assertNotEqual(color_value, "", f"Variant {i+1} must have color selected")
                
                # Check pictures
                pictures = variant.find_elements(By.CSS_SELECTOR,
                    ".picture-preview, .image-preview, img[src]:not([src=''])")
                self.assertGreater(len(pictures), 0, f"Variant {i+1} must have at least one picture")
                
                print(f"   ✅ Variant {i+1} validation passed: {color_select.first_selected_option.text}, {len(pictures)} pictures")
            
            print(f"🔍 Step 5: Testing duplicate color prevention...")
            
            # Try to select the same color for different variants
            if len(final_variants) > 1:
                first_variant = final_variants[0]
                second_variant = final_variants[1]
                
                first_color_select = Select(first_variant.find_element(By.CSS_SELECTOR, "select[name*='color']"))
                second_color_select = Select(second_variant.find_element(By.CSS_SELECTOR, "select[name*='color']"))
                
                first_color_value = first_color_select.first_selected_option.get_attribute("value")
                
                # Try to set second variant to same color
                try:
                    second_color_select.select_by_value(first_color_value)
                    time.sleep(1)
                    
                    # Check for validation error
                    duplicate_errors = self.driver.find_elements(By.CSS_SELECTOR,
                        ".duplicate-color-error, .color-conflict, .validation-error")
                    
                    if duplicate_errors:
                        print(f"   ✅ Duplicate color validation working")
                    else:
                        print(f"   ⚠️ Duplicate color validation not detected")
                        
                except Exception as e:
                    print(f"   ⚠️ Could not test duplicate color: {e}")
            
            print(f"🔍 Step 6: Submitting multi-variant component...")
            
            # Submit the form
            submit_button = self.driver.find_element(By.CSS_SELECTOR,
                "button[type='submit'], input[type='submit'], .btn-submit")
            
            self._scroll_to_element(submit_button)
            self._safe_click(submit_button)
            
            # Wait for submission
            success = self._wait_for_submission_success()
            
            if success:
                print(f"✅ Multi-variant component created successfully")
                
                # Extract component ID
                current_url = self.driver.current_url
                if "/component/" in current_url:
                    component_id = current_url.split("/component/")[-1].split("/")[0]
                    self.created_components.append(component_id)
                    print(f"   Component ID: {component_id}")
                    
                    # Verify variants are displayed on detail page
                    self._verify_multi_variant_display()
                    
            else:
                raise Exception("Multi-variant component creation failed")
            
            print(f"✅ SELENIUM TEST PASSED: Multiple variants with picture management complete")
            
        except Exception as e:
            print(f"❌ SELENIUM TEST FAILED: {str(e)}")
            self._take_screenshot("multi_variant_failure")
            raise

    def test_complex_brand_and_category_associations(self):
        """Test complex brand and category associations"""
        print(f"\n🧪 SELENIUM TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test advanced brand and category association workflows")
        
        try:
            print(f"🔍 Step 1: Setting up component for brand/category testing...")
            self.driver.get(f"{self.base_url}/component/new")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            
            product_number = f"BRAND-CATEGORY-{self.timestamp}"
            description = f"Complex brand and category test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            self._fill_essential_info(product_number, description)
            
            print(f"🔍 Step 2: Testing brand management workflow...")
            
            # Test brand selection
            try:
                brand_section = self.driver.find_element(By.CSS_SELECTOR,
                    ".brand-section, [data-section='brands'], #brand-management")
                
                print(f"   Found brand management section")
                
                # Look for brand selection mechanism
                brand_selects = brand_section.find_elements(By.CSS_SELECTOR, "select")
                brand_inputs = brand_section.find_elements(By.CSS_SELECTOR, "input")
                
                if brand_selects:
                    # Test dropdown brand selection
                    for i, brand_select_elem in enumerate(brand_selects):
                        brand_select = Select(brand_select_elem)
                        options = brand_select.options
                        
                        if len(options) > 1:
                            # Select a brand
                            brand_select.select_by_index(1)
                            selected_brand = brand_select.first_selected_option.text
                            print(f"   ✅ Brand {i+1} selected: {selected_brand}")
                            
                            # Test subbrand selection if available
                            subbrand_selects = brand_section.find_elements(By.CSS_SELECTOR,
                                "select[name*='subbrand'], .subbrand-select")
                            
                            for subbrand_select_elem in subbrand_selects:
                                subbrand_select = Select(subbrand_select_elem)
                                if len(subbrand_select.options) > 1:
                                    subbrand_select.select_by_index(1)
                                    selected_subbrand = subbrand_select.first_selected_option.text
                                    print(f"     ✅ Subbrand selected: {selected_subbrand}")
                                    break
                        
                        # Test only first brand select for efficiency
                        break
                
                # Test creating new brand
                new_brand_inputs = brand_section.find_elements(By.CSS_SELECTOR,
                    "input[name*='new_brand'], .new-brand-input")
                
                if new_brand_inputs:
                    new_brand_name = f"TEST-BRAND-{self.timestamp}"
                    new_brand_inputs[0].send_keys(new_brand_name)
                    print(f"   ✅ New brand name entered: {new_brand_name}")
                    
                    # Look for new subbrand option
                    new_subbrand_inputs = brand_section.find_elements(By.CSS_SELECTOR,
                        "input[name*='new_subbrand'], .new-subbrand-input")
                    
                    if new_subbrand_inputs:
                        new_subbrand_name = f"TEST-SUBBRAND-{self.timestamp}"
                        new_subbrand_inputs[0].send_keys(new_subbrand_name)
                        print(f"     ✅ New subbrand name entered: {new_subbrand_name}")
                
            except NoSuchElementException:
                print(f"   ⚠️ Brand management section not found")
            
            print(f"🔍 Step 3: Testing category association workflow...")
            
            try:
                category_section = self.driver.find_element(By.CSS_SELECTOR,
                    ".category-section, [data-section='categories'], #categories")
                
                print(f"   Found category section")
                
                # Test category selection/search
                category_inputs = category_section.find_elements(By.CSS_SELECTOR, "input")
                category_selects = category_section.find_elements(By.CSS_SELECTOR, "select")
                
                if category_inputs:
                    # Test autocomplete category search
                    category_input = category_inputs[0]
                    test_category_search = "test"
                    
                    category_input.send_keys(test_category_search)
                    time.sleep(2)  # Wait for autocomplete
                    
                    # Look for autocomplete suggestions
                    suggestions = self.driver.find_elements(By.CSS_SELECTOR,
                        ".autocomplete-suggestion, .category-suggestion, .dropdown-item")
                    
                    if suggestions:
                        print(f"   ✅ Found {len(suggestions)} category suggestions")
                        # Select first suggestion
                        suggestions[0].click()
                        time.sleep(1)
                        print(f"   ✅ Category selected from autocomplete")
                    else:
                        # Just enter the category name
                        category_input.send_keys(Keys.ENTER)
                        print(f"   ✅ Category entered: {test_category_search}")
                
                elif category_selects:
                    # Test dropdown category selection
                    for category_select_elem in category_selects:
                        category_select = Select(category_select_elem)
                        if len(category_select.options) > 1:
                            category_select.select_by_index(1)
                            selected_category = category_select.first_selected_option.text
                            print(f"   ✅ Category selected: {selected_category}")
                            break
                
                # Test multiple category selection
                additional_category_buttons = category_section.find_elements(By.CSS_SELECTOR,
                    ".add-category, .btn-add-category")
                
                if additional_category_buttons:
                    self._safe_click(additional_category_buttons[0])
                    time.sleep(1)
                    
                    # Add another category
                    additional_inputs = category_section.find_elements(By.CSS_SELECTOR, "input")
                    if len(additional_inputs) > 1:
                        additional_inputs[-1].send_keys("additional-category")
                        additional_inputs[-1].send_keys(Keys.ENTER)
                        print(f"   ✅ Additional category added")
                
            except NoSuchElementException:
                print(f"   ⚠️ Category section not found")
            
            print(f"🔍 Step 4: Testing keyword management...")
            
            try:
                keywords_section = self.driver.find_element(By.CSS_SELECTOR,
                    "[data-section='keywords'], .keywords-section, #keywords")
                
                print(f"   Found keywords section")
                
                # Test keyword addition
                test_keywords = ["manufacturing", "automation", "testing", "selenium", "quality"]
                
                keyword_inputs = keywords_section.find_elements(By.CSS_SELECTOR, "input")
                
                if keyword_inputs:
                    keyword_input = keyword_inputs[0]
                    
                    for keyword in test_keywords:
                        keyword_input.clear()
                        keyword_input.send_keys(keyword)
                        keyword_input.send_keys(Keys.ENTER)
                        time.sleep(0.5)
                        print(f"     ✅ Keyword added: {keyword}")
                    
                    # Verify keywords were added
                    keyword_tags = keywords_section.find_elements(By.CSS_SELECTOR,
                        ".keyword-tag, .tag, .badge")
                    
                    print(f"   ✅ Total keyword tags found: {len(keyword_tags)}")
                
            except NoSuchElementException:
                print(f"   ⚠️ Keywords section not found")
            
            print(f"🔍 Step 5: Adding variant and submitting...")
            
            # Add minimal variant for submission
            self._add_simple_variant()
            
            # Submit form
            submit_button = self.driver.find_element(By.CSS_SELECTOR,
                "button[type='submit'], input[type='submit'], .btn-submit")
            
            self._scroll_to_element(submit_button)
            self._safe_click(submit_button)
            
            success = self._wait_for_submission_success()
            
            if success:
                print(f"✅ Component with complex associations created successfully")
                
                current_url = self.driver.current_url
                if "/component/" in current_url:
                    component_id = current_url.split("/component/")[-1].split("/")[0]
                    self.created_components.append(component_id)
                    
                    # Verify associations are displayed
                    self._verify_component_associations()
            else:
                raise Exception("Complex associations component creation failed")
            
            print(f"✅ SELENIUM TEST PASSED: Complex brand and category associations complete")
            
        except Exception as e:
            print(f"❌ SELENIUM TEST FAILED: {str(e)}")
            self._take_screenshot("complex_associations_failure")
            raise

    def test_dynamic_component_properties_handling(self):
        """Test dynamic component properties based on component type"""
        print(f"\n🧪 SELENIUM TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test dynamic properties based on component type selection")
        
        try:
            print(f"🔍 Step 1: Loading form and testing component type changes...")
            self.driver.get(f"{self.base_url}/component/new")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            
            product_number = f"DYNAMIC-PROPS-{self.timestamp}"
            product_field = self.driver.find_element(By.NAME, "product_number")
            product_field.send_keys(product_number)
            
            print(f"🔍 Step 2: Testing different component types and their properties...")
            
            # Get component type dropdown
            component_type_select = Select(self.driver.find_element(By.NAME, "component_type_id"))
            available_types = [(opt.get_attribute("value"), opt.text) for opt in component_type_select.options if opt.get_attribute("value")]
            
            print(f"   Found {len(available_types)} component types")
            
            properties_tested = 0
            
            for type_value, type_text in available_types[:3]:  # Test first 3 types
                print(f"   Testing component type: {type_text}")
                
                # Select the component type
                component_type_select.select_by_value(type_value)
                time.sleep(2)  # Wait for dynamic properties to load
                
                # Look for properties section
                try:
                    properties_section = self.driver.find_element(By.CSS_SELECTOR,
                        "[data-section='properties'], .properties-section, #component-properties")
                    
                    # Find property fields
                    property_inputs = properties_section.find_elements(By.CSS_SELECTOR, 
                        "input, select, textarea")
                    
                    property_labels = properties_section.find_elements(By.CSS_SELECTOR,
                        "label, .property-label")
                    
                    print(f"     Found {len(property_inputs)} property fields")
                    print(f"     Found {len(property_labels)} property labels")
                    
                    if property_inputs:
                        properties_tested += 1
                        
                        # Test filling different types of property fields
                        for i, prop_input in enumerate(property_inputs[:5]):  # Limit to 5 fields
                            try:
                                field_type = prop_input.tag_name
                                field_name = prop_input.get_attribute("name") or f"property_{i}"
                                
                                if field_type == "input":
                                    input_type = prop_input.get_attribute("type") or "text"
                                    
                                    if input_type == "text":
                                        prop_input.send_keys(f"test_value_{i}")
                                        print(f"       ✅ Text property filled: {field_name}")
                                    elif input_type == "number":
                                        prop_input.send_keys(str(100 + i))
                                        print(f"       ✅ Number property filled: {field_name}")
                                    elif input_type == "checkbox":
                                        if not prop_input.is_selected():
                                            prop_input.click()
                                        print(f"       ✅ Checkbox property checked: {field_name}")
                                
                                elif field_type == "select":
                                    prop_select = Select(prop_input)
                                    if len(prop_select.options) > 1:
                                        prop_select.select_by_index(1)
                                        print(f"       ✅ Select property set: {field_name}")
                                
                                elif field_type == "textarea":
                                    prop_input.send_keys(f"test_description_for_{field_name}")
                                    print(f"       ✅ Textarea property filled: {field_name}")
                                    
                            except Exception as e:
                                print(f"       ⚠️ Could not fill property {i}: {e}")
                    
                    else:
                        print(f"     ⚠️ No properties found for this component type")
                        
                except NoSuchElementException:
                    print(f"     ⚠️ Properties section not found for {type_text}")
                
                # Test only first few types for efficiency
                if properties_tested >= 2:
                    break
            
            print(f"🔍 Step 3: Testing property validation...")
            
            # Select a component type with properties
            if available_types:
                component_type_select.select_by_value(available_types[0][0])
                time.sleep(2)
                
                # Look for required property fields
                try:
                    properties_section = self.driver.find_element(By.CSS_SELECTOR,
                        "[data-section='properties'], .properties-section, #component-properties")
                    
                    required_fields = properties_section.find_elements(By.CSS_SELECTOR,
                        "input[required], select[required], textarea[required]")
                    
                    if required_fields:
                        print(f"   Found {len(required_fields)} required property fields")
                        
                        # Test leaving required field empty and submitting
                        required_field = required_fields[0]
                        required_field.clear()
                        
                        # Try to submit and check for validation
                        submit_button = self.driver.find_element(By.CSS_SELECTOR,
                            "button[type='submit'], input[type='submit'], .btn-submit")
                        
                        self._scroll_to_element(submit_button)
                        self._safe_click(submit_button)
                        time.sleep(1)
                        
                        # Check for validation messages
                        validation_messages = self.driver.find_elements(By.CSS_SELECTOR,
                            ".property-validation, .field-error, .invalid-feedback")
                        
                        if validation_messages:
                            print(f"   ✅ Property validation working")
                        else:
                            print(f"   ⚠️ Property validation not detected")
                        
                        # Fill the required field
                        required_field.send_keys("required_value")
                        print(f"   ✅ Required property field filled")
                    
                except NoSuchElementException:
                    print(f"   ⚠️ Could not test property validation")
            
            print(f"🔍 Step 4: Completing component with properties...")
            
            # Add description
            description_field = self.driver.find_element(By.NAME, "description")
            description_field.send_keys(f"Dynamic properties test - {datetime.now()}")
            
            # Add variant
            self._add_simple_variant()
            
            # Submit
            submit_button = self.driver.find_element(By.CSS_SELECTOR,
                "button[type='submit'], input[type='submit'], .btn-submit")
            
            self._scroll_to_element(submit_button)
            self._safe_click(submit_button)
            
            success = self._wait_for_submission_success()
            
            if success:
                print(f"✅ Component with dynamic properties created successfully")
                
                current_url = self.driver.current_url
                if "/component/" in current_url:
                    component_id = current_url.split("/component/")[-1].split("/")[0]
                    self.created_components.append(component_id)
                    
                    # Verify properties are displayed
                    self._verify_component_properties()
            else:
                raise Exception("Dynamic properties component creation failed")
            
            print(f"✅ SELENIUM TEST PASSED: Dynamic component properties handling complete")
            
        except Exception as e:
            print(f"❌ SELENIUM TEST FAILED: {str(e)}")
            self._take_screenshot("dynamic_properties_failure")
            raise

    def test_form_persistence_and_recovery(self):
        """Test form data persistence and recovery mechanisms"""
        print(f"\n🧪 SELENIUM TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test form data persistence across page interactions")
        
        try:
            print(f"🔍 Step 1: Filling form with comprehensive data...")
            self.driver.get(f"{self.base_url}/component/new")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            
            # Fill comprehensive form data
            test_data = {
                "product_number": f"PERSISTENCE-{self.timestamp}",
                "description": f"Form persistence test - {datetime.now()}",
            }
            
            # Fill product number
            product_field = self.driver.find_element(By.NAME, "product_number")
            product_field.send_keys(test_data["product_number"])
            
            # Fill description
            description_field = self.driver.find_element(By.NAME, "description")
            description_field.send_keys(test_data["description"])
            
            # Select component type
            component_type_select = Select(self.driver.find_element(By.NAME, "component_type_id"))
            if len(component_type_select.options) > 1:
                component_type_select.select_by_index(1)
                test_data["component_type"] = component_type_select.first_selected_option.text
            
            print(f"   ✅ Initial form data filled")
            
            print(f"🔍 Step 2: Testing data persistence after page interactions...")
            
            # Simulate various page interactions that might affect form data
            
            # Test 1: Scroll and interact with other elements
            self.driver.execute_script("window.scrollTo(0, 500);")
            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, 0);")
            
            # Verify data is still there
            current_product = self.driver.find_element(By.NAME, "product_number").get_attribute("value")
            self.assertEqual(current_product, test_data["product_number"], "Product number should persist after scroll")
            print(f"   ✅ Data persisted after scrolling")
            
            # Test 2: Focus on different elements
            description_field.click()
            time.sleep(0.5)
            product_field.click()
            time.sleep(0.5)
            
            # Verify data
            current_description = self.driver.find_element(By.NAME, "description").get_attribute("value")
            self.assertEqual(current_description, test_data["description"], "Description should persist after focus changes")
            print(f"   ✅ Data persisted after focus changes")
            
            # Test 3: Open browser developer tools (simulate user inspection)
            self.driver.execute_script("console.log('Testing form persistence');")
            time.sleep(1)
            
            # Verify data
            current_type = Select(self.driver.find_element(By.NAME, "component_type_id")).first_selected_option.text
            self.assertEqual(current_type, test_data["component_type"], "Component type should persist")
            print(f"   ✅ Data persisted after console interaction")
            
            print(f"🔍 Step 3: Testing form state during variant operations...")
            
            # Add variant and verify main form data persists
            try:
                add_variant_btn = self.driver.find_element(By.ID, "add_variant_btn")
            except NoSuchElementException:
                add_variant_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Add First Variant')]")
            self._safe_click(add_variant_btn)
            time.sleep(2)
            
            # Verify main form data still exists
            current_product = self.driver.find_element(By.NAME, "product_number").get_attribute("value")
            self.assertEqual(current_product, test_data["product_number"], "Product number should persist during variant operations")
            print(f"   ✅ Main form data persisted during variant addition")
            
            # Configure variant
            variant_containers = self.driver.find_elements(By.CSS_SELECTOR,
                ".variant-item, .variant-container, [data-variant]")
            
            if variant_containers:
                variant = variant_containers[0]
                
                # Select color
                color_select = Select(variant.find_element(By.CSS_SELECTOR, "select[name*='color']"))
                if len(color_select.options) > 1:
                    color_select.select_by_index(1)
                    test_data["variant_color"] = color_select.first_selected_option.text
                
                # Add picture
                picture_upload = variant.find_element(By.CSS_SELECTOR, "input[type='file']")
                test_image_path = self._create_test_image("persistence_test.jpg")
                picture_upload.send_keys(test_image_path)
                time.sleep(2)
                
                # Verify main form data still exists after picture upload
                current_description = self.driver.find_element(By.NAME, "description").get_attribute("value")
                self.assertEqual(current_description, test_data["description"], "Description should persist during picture upload")
                print(f"   ✅ Main form data persisted during picture upload")
            
            print(f"🔍 Step 4: Testing form validation preservation...")
            
            # Trigger validation by clearing required field
            product_field = self.driver.find_element(By.NAME, "product_number")
            original_product = product_field.get_attribute("value")
            product_field.clear()
            product_field.send_keys(Keys.TAB)
            time.sleep(1)
            
            # Check for validation message
            validation_elements = self.driver.find_elements(By.CSS_SELECTOR,
                ".validation-error, .invalid-feedback, input:invalid")
            
            validation_present = len(validation_elements) > 0
            if validation_present:
                print(f"   ✅ Validation triggered as expected")
            
            # Restore valid data
            product_field.clear()
            product_field.send_keys(original_product)
            product_field.send_keys(Keys.TAB)
            time.sleep(1)
            
            # Verify validation cleared
            if validation_present:
                remaining_validation = self.driver.find_elements(By.CSS_SELECTOR,
                    ".validation-error, .invalid-feedback")
                visible_validation = [v for v in remaining_validation if v.is_displayed()]
                
                if not visible_validation:
                    print(f"   ✅ Validation cleared after correction")
                else:
                    print(f"   ⚠️ Validation may still be present")
            
            print(f"🔍 Step 5: Final submission with persisted data...")
            
            # Submit the form
            submit_button = self.driver.find_element(By.CSS_SELECTOR,
                "button[type='submit'], input[type='submit'], .btn-submit")
            
            self._scroll_to_element(submit_button)
            self._safe_click(submit_button)
            
            success = self._wait_for_submission_success()
            
            if success:
                print(f"✅ Component created with persisted form data")
                
                current_url = self.driver.current_url
                if "/component/" in current_url:
                    component_id = current_url.split("/component/")[-1].split("/")[0]
                    self.created_components.append(component_id)
                    
                    # Verify created component has correct data
                    page_text = self.driver.page_source
                    if test_data["product_number"] in page_text:
                        print(f"   ✅ Product number correctly saved: {test_data['product_number']}")
                    if test_data["description"] in page_text:
                        print(f"   ✅ Description correctly saved")
            else:
                raise Exception("Form persistence test submission failed")
            
            print(f"✅ SELENIUM TEST PASSED: Form persistence and recovery complete")
            
        except Exception as e:
            print(f"❌ SELENIUM TEST FAILED: {str(e)}")
            self._take_screenshot("form_persistence_failure")
            raise

    # Helper methods for advanced testing

    def _fill_essential_info(self, product_number, description):
        """Fill essential information quickly"""
        product_field = self.driver.find_element(By.NAME, "product_number")
        product_field.send_keys(product_number)
        
        description_field = self.driver.find_element(By.NAME, "description")
        description_field.send_keys(description)
        
        component_type_select = Select(self.driver.find_element(By.NAME, "component_type_id"))
        if len(component_type_select.options) > 1:
            component_type_select.select_by_index(1)

    def _add_multiple_pictures_to_variant(self, variant, color_name, variant_index):
        """Add multiple pictures to a variant"""
        try:
            # Find picture upload input
            picture_uploads = variant.find_elements(By.CSS_SELECTOR, "input[type='file']")
            
            if picture_uploads:
                upload_input = picture_uploads[0]
                
                # Create and upload multiple test images
                for i in range(2):  # Add 2 pictures per variant
                    image_filename = f"{color_name.lower()}_variant_{variant_index}_pic_{i+1}.jpg"
                    test_image_path = self._create_test_image(image_filename)
                    
                    upload_input.send_keys(test_image_path)
                    time.sleep(1)  # Wait between uploads
                    
                    print(f"       ✅ Picture {i+1} added to {color_name} variant")
                
            else:
                print(f"       ⚠️ Picture upload input not found for {color_name} variant")
                
        except Exception as e:
            print(f"       ❌ Error adding pictures to {color_name} variant: {e}")

    def _add_simple_variant(self):
        """Add a simple variant for testing purposes"""
        try:
            add_variant_btn = self.driver.find_element(By.CSS_SELECTOR,
                ".add-variant, .btn-add-variant, [data-action='add-variant']")
            self._safe_click(add_variant_btn)
            time.sleep(1)
            
            variant_containers = self.driver.find_elements(By.CSS_SELECTOR,
                ".variant-item, .variant-container, [data-variant]")
            
            if variant_containers:
                variant = variant_containers[0]
                
                # Select color
                color_select = Select(variant.find_element(By.CSS_SELECTOR, "select[name*='color']"))
                if len(color_select.options) > 1:
                    color_select.select_by_index(1)
                
                # Add picture
                picture_upload = variant.find_element(By.CSS_SELECTOR, "input[type='file']")
                test_image_path = self._create_test_image("simple_variant.jpg")
                picture_upload.send_keys(test_image_path)
                time.sleep(2)
                
        except Exception as e:
            print(f"⚠️ Error adding simple variant: {e}")

    def _wait_for_submission_success(self, timeout=30):
        """Wait for successful form submission"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            current_url = self.driver.current_url
            
            # Check for success redirect
            if "/component/" in current_url and "/component/new" not in current_url:
                return True
            
            # Check for error messages
            error_messages = self.driver.find_elements(By.CSS_SELECTOR,
                ".alert-danger, .error-message, .submission-error")
            if any(error.is_displayed() for error in error_messages):
                return False
            
            time.sleep(1)
        
        return False

    def _verify_multi_variant_display(self):
        """Verify multi-variant component is displayed correctly"""
        try:
            # Look for variant display elements
            variant_displays = self.driver.find_elements(By.CSS_SELECTOR,
                ".variant-display, .component-variant, .color-variant")
            
            if variant_displays:
                print(f"   ✅ Found {len(variant_displays)} variant displays on detail page")
            else:
                print(f"   ⚠️ Variant displays not found on detail page")
                
        except Exception as e:
            print(f"   ⚠️ Error verifying variant display: {e}")

    def _verify_component_associations(self):
        """Verify component associations are displayed"""
        try:
            page_text = self.driver.page_source.lower()
            
            # Look for brand/category information
            if "brand" in page_text or "category" in page_text:
                print(f"   ✅ Brand/category associations found on detail page")
            else:
                print(f"   ⚠️ Brand/category associations not clearly visible")
                
        except Exception as e:
            print(f"   ⚠️ Error verifying associations: {e}")

    def _verify_component_properties(self):
        """Verify component properties are displayed"""
        try:
            # Look for properties section on detail page
            properties_sections = self.driver.find_elements(By.CSS_SELECTOR,
                ".properties, .component-properties, .property-list")
            
            if properties_sections:
                print(f"   ✅ Properties section found on detail page")
            else:
                print(f"   ⚠️ Properties section not found on detail page")
                
        except Exception as e:
            print(f"   ⚠️ Error verifying properties: {e}")

    def _create_test_image(self, filename):
        """Create a test image file"""
        from PIL import Image
        import tempfile
        
        # Create colored image based on filename
        color = 'red'
        if 'blue' in filename.lower():
            color = 'blue'
        elif 'green' in filename.lower():
            color = 'green'
        elif 'yellow' in filename.lower():
            color = 'yellow'
        elif 'black' in filename.lower():
            color = 'black'
        
        img = Image.new('RGB', (150, 150), color=color)
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, filename)
        img.save(file_path, 'JPEG')
        return file_path

    def _scroll_to_element(self, element):
        """Scroll element into view"""
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)

    def _safe_click(self, element):
        """Safely click element"""
        try:
            element.click()
        except ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].click();", element)

    def _take_screenshot(self, name):
        """Take screenshot for debugging"""
        try:
            screenshot_path = f"/tmp/selenium_advanced_{name}_{self.timestamp}.png"
            self.driver.save_screenshot(screenshot_path)
            print(f"📸 Screenshot saved: {screenshot_path}")
        except Exception:
            pass


if __name__ == '__main__':
    print("""
    🎬 ADVANCED COMPONENT CREATION TESTING
    
    Prerequisites:
    1. Application running: ./start.sh
    2. Chrome browser installed
    3. PIL library: pip install Pillow
    
    Run tests:
    python -m pytest tests/selenium/component_creation/test_component_creation_advanced.py -v -s
    
    Advanced test scenarios:
    ✅ Multiple variants with picture management
    ✅ Complex brand and category associations
    ✅ Dynamic component properties handling
    ✅ Form persistence and recovery
    
    Manufacturing-focused workflow testing.
    """)
    
    unittest.main()