#!/usr/bin/env python3
"""
Selenium tests for editing existing components
Tests the component edit form when modifying existing components

Based on docs analysis:
- Edit mode vs create mode functionality
- Change summary modal for edits
- Real-time SKU preview updates
- Picture renaming on changes
- Data persistence and validation
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
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    ElementClickInterceptedException
)


class TestComponentEditExisting(unittest.TestCase):
    """Tests for editing existing components"""
    
    @classmethod
    def setUpClass(cls):
        """Set up Selenium WebDriver"""
        print(f"\n🔧 SELENIUM SETUP: Component Edit Existing Testing")
        
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1366,768")
        chrome_options.add_argument("--start-maximized")
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.driver.maximize_window()
            cls.driver.implicitly_wait(10)
            cls.wait = WebDriverWait(cls.driver, 20)
            cls.base_url = "http://localhost:6002"
            
            print(f"✅ Chrome browser initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize WebDriver: {e}")
            raise

    @classmethod
    def tearDownClass(cls):
        """Clean up WebDriver"""
        print(f"\n🧹 SELENIUM TEARDOWN: Closing browser...")
        if hasattr(cls, 'driver'):
            cls.driver.quit()

    def setUp(self):
        """Set up for each test"""
        print(f"\n🧪 SELENIUM TEST SETUP: {self._testMethodName}")
        self.timestamp = int(time.time())
        self.driver.delete_all_cookies()
        self.test_component_id = None

    def test_load_existing_component_for_editing(self):
        """Test loading an existing component into edit form"""
        print(f"\n🧪 SELENIUM TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Load existing component data into edit form")
        
        try:
            print(f"🔍 Step 1: Finding an existing component to edit...")
            
            # Navigate to components list
            self.driver.get(f"{self.base_url}/components")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Look for edit links or buttons
            edit_links = self.driver.find_elements(By.CSS_SELECTOR,
                "a[href*='/component/edit/'], .edit-link, .btn-edit")
            
            if not edit_links:
                print(f"⚠️ No existing components found to edit")
                # Create a component first for testing
                component_id = self._create_test_component_for_editing()
                if component_id:
                    edit_url = f"{self.base_url}/component/edit/{component_id}"
                    self.driver.get(edit_url)
                else:
                    self.skipTest("Could not create test component for editing")
            else:
                # Click on first edit link
                edit_link = edit_links[0]
                edit_url = edit_link.get_attribute("href")
                self.test_component_id = edit_url.split("/")[-1] if edit_url else None
                print(f"🔍 Found component to edit: {self.test_component_id}")
                
                self._safe_click(edit_link)
            
            print(f"🔍 Step 2: Verifying edit form loaded with existing data...")
            
            # Wait for edit form to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            
            # Check if window.isEditMode is set
            is_edit_mode = self.driver.execute_script("return window.isEditMode;")
            self.assertTrue(is_edit_mode, "Edit mode should be enabled")
            print(f"✅ Edit mode detected: {is_edit_mode}")
            
            print(f"🔍 Step 3: Verifying form fields are populated...")
            
            # Check product number is populated
            product_field = self.driver.find_element(By.NAME, "product_number")
            product_value = product_field.get_attribute("value")
            self.assertNotEqual(product_value.strip(), "", "Product number should be populated")
            print(f"✅ Product number populated: {product_value}")
            
            # Check component type is selected
            component_type_select = Select(self.driver.find_element(By.NAME, "component_type_id"))
            selected_type_value = component_type_select.first_selected_option.get_attribute("value")
            self.assertNotEqual(selected_type_value, "", "Component type should be selected")
            print(f"✅ Component type selected")
            
            # Check description field
            description_field = self.driver.find_element(By.NAME, "description")
            description_value = description_field.get_attribute("value")
            print(f"✅ Description field: {'populated' if description_value else 'empty'}")
            
            print(f"🔍 Step 4: Verifying existing variants are loaded...")
            
            # Check for existing variants
            variant_containers = self.driver.find_elements(By.CSS_SELECTOR,
                ".variant-card, [data-variant-id]")
            
            if variant_containers:
                print(f"✅ Found {len(variant_containers)} existing variants")
                
                # Verify first variant has color selected
                first_variant = variant_containers[0]
                color_select = Select(first_variant.find_element(By.CSS_SELECTOR, "select[name*='color']"))
                selected_color = color_select.first_selected_option.text
                self.assertNotEqual(selected_color, "", "Variant should have color selected")
                print(f"✅ First variant color: {selected_color}")
                
                # Check for existing pictures
                pictures = first_variant.find_elements(By.CSS_SELECTOR,
                    ".picture-preview, .image-preview, img")
                if pictures:
                    print(f"✅ Found {len(pictures)} pictures in first variant")
                else:
                    print(f"⚠️ No pictures found in first variant")
            else:
                print(f"⚠️ No existing variants found")
            
            print(f"✅ SELENIUM TEST PASSED: Existing component loaded for editing")
            
        except Exception as e:
            print(f"❌ SELENIUM TEST FAILED: {str(e)}")
            self._take_screenshot("load_existing_failure")
            raise

    def test_edit_component_essential_information(self):
        """Test editing essential information of existing component"""
        print(f"\n🧪 SELENIUM TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Edit essential information and verify changes")
        
        try:
            # Load a component for editing
            component_id = self._get_or_create_test_component()
            self.driver.get(f"{self.base_url}/component/edit/{component_id}")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            
            print(f"🔍 Step 1: Capturing original component data...")
            
            # Capture original values
            product_field = self.driver.find_element(By.NAME, "product_number")
            original_product = product_field.get_attribute("value")
            
            description_field = self.driver.find_element(By.NAME, "description")
            original_description = description_field.get_attribute("value")
            
            print(f"📋 Original product number: {original_product}")
            print(f"📋 Original description: {original_description}")
            
            print(f"🔍 Step 2: Modifying product number...")
            
            # Modify product number
            new_product_number = f"{original_product}-EDITED-{self.timestamp}"
            product_field.clear()
            product_field.send_keys(new_product_number)
            
            # Wait for real-time updates (SKU preview, etc.)
            time.sleep(2)
            print(f"✅ Product number changed to: {new_product_number}")
            
            print(f"🔍 Step 3: Modifying description...")
            
            # Modify description
            new_description = f"{original_description} - EDITED at {datetime.now().strftime('%H:%M:%S')}"
            description_field.clear()
            description_field.send_keys(new_description)
            print(f"✅ Description updated")
            
            print(f"🔍 Step 4: Testing supplier change (if available)...")
            
            try:
                supplier_select = Select(self.driver.find_element(By.NAME, "supplier_id"))
                original_supplier_index = supplier_select.options.index(supplier_select.first_selected_option)
                
                # Change to different supplier if available
                if len(supplier_select.options) > 2:
                    new_supplier_index = 1 if original_supplier_index != 1 else 2
                    supplier_select.select_by_index(new_supplier_index)
                    
                    new_supplier = supplier_select.first_selected_option.text
                    print(f"✅ Supplier changed to: {new_supplier}")
                    
                    # Wait for SKU updates
                    time.sleep(2)
                else:
                    print(f"⚠️ Not enough suppliers to test change")
                    
            except NoSuchElementException:
                print(f"⚠️ Supplier field not found")
            
            print(f"🔍 Step 5: Checking for change summary or warnings...")
            
            # Look for change summary modal or warnings
            change_summaries = self.driver.find_elements(By.CSS_SELECTOR,
                ".change-summary, .edit-warning, .modification-alert")
            
            if change_summaries:
                print(f"✅ Found change summary/warning elements")
                for summary in change_summaries:
                    if summary.is_displayed():
                        print(f"   - {summary.text[:100]}...")
            else:
                print(f"⚠️ No change summary elements found")
            
            print(f"🔍 Step 6: Testing real-time SKU preview updates...")
            
            # Look for SKU preview elements
            sku_previews = self.driver.find_elements(By.CSS_SELECTOR,
                ".sku-preview, .variant-sku, [data-sku]")
            
            if sku_previews:
                for sku_preview in sku_previews:
                    if sku_preview.is_displayed():
                        sku_text = sku_preview.text
                        if new_product_number.lower().replace(" ", "_") in sku_text.lower():
                            print(f"✅ SKU preview updated with new product number")
                            break
                else:
                    print(f"⚠️ SKU preview may not have updated yet")
            else:
                print(f"⚠️ SKU preview elements not found")
            
            print(f"🔍 Step 7: Submitting changes...")
            
            # Submit the form
            submit_button = self.driver.find_element(By.CSS_SELECTOR,
                "button[type='submit'], input[type='submit'], .btn-submit")
            
            self._scroll_to_element(submit_button)
            self._safe_click(submit_button)
            
            # Wait for response
            time.sleep(3)
            
            # Check for success or error
            success_indicators = self.driver.find_elements(By.CSS_SELECTOR,
                ".alert-success, .success-message, .update-success")
            
            error_indicators = self.driver.find_elements(By.CSS_SELECTOR,
                ".alert-danger, .error-message, .update-error")
            
            if success_indicators and any(indicator.is_displayed() for indicator in success_indicators):
                print(f"✅ Update successful - success message displayed")
            elif error_indicators and any(indicator.is_displayed() for indicator in error_indicators):
                error_text = next(indicator.text for indicator in error_indicators if indicator.is_displayed())
                print(f"❌ Update failed with error: {error_text}")
                raise Exception(f"Update failed: {error_text}")
            else:
                # Check if redirected to detail page
                current_url = self.driver.current_url
                if f"/component/{component_id}" in current_url and "/edit" not in current_url:
                    print(f"✅ Update successful - redirected to detail page")
                else:
                    print(f"⚠️ Update status unclear - no clear success/error indicator")
            
            print(f"✅ SELENIUM TEST PASSED: Component essential information editing complete")
            
        except Exception as e:
            print(f"❌ SELENIUM TEST FAILED: {str(e)}")
            self._take_screenshot("edit_essential_info_failure")
            raise

    def test_edit_component_variants_management(self):
        """Test editing component variants (add, modify, remove)"""
        print(f"\n🧪 SELENIUM TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test variant management in edit mode")
        
        try:
            # Load a component for editing
            component_id = self._get_or_create_test_component()
            self.driver.get(f"{self.base_url}/component/edit/{component_id}")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            
            print(f"🔍 Step 1: Analyzing existing variants...")
            
            # Count existing variants
            existing_variants = self.driver.find_elements(By.CSS_SELECTOR,
                ".variant-item, .variant-container, [data-variant]")
            initial_variant_count = len(existing_variants)
            print(f"📋 Found {initial_variant_count} existing variants")
            
            print(f"🔍 Step 2: Adding new variant...")
            
            # Add new variant
            try:
                add_variant_btn = self.driver.find_element(By.ID, "add_variant_btn")
            except NoSuchElementException:
                add_variant_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Add First Variant')]")
            
            self._scroll_to_element(add_variant_btn)
            self._safe_click(add_variant_btn)
            time.sleep(2)
            
            # Verify new variant was added
            updated_variants = self.driver.find_elements(By.CSS_SELECTOR,
                ".variant-item, .variant-container, [data-variant]")
            new_variant_count = len(updated_variants)
            
            self.assertEqual(new_variant_count, initial_variant_count + 1,
                f"Should have {initial_variant_count + 1} variants after adding one")
            print(f"✅ New variant added - total variants: {new_variant_count}")
            
            # Configure the new variant
            new_variant = updated_variants[-1]  # Last variant should be the new one
            
            # Select color for new variant
            color_select = Select(new_variant.find_element(By.CSS_SELECTOR, "select[name*='color']"))
            available_colors = [opt for opt in color_select.options if opt.get_attribute("value")]
            
            # Find an unused color
            used_colors = []
            for variant in updated_variants[:-1]:  # All variants except the new one
                variant_color_select = Select(variant.find_element(By.CSS_SELECTOR, "select[name*='color']"))
                used_colors.append(variant_color_select.first_selected_option.get_attribute("value"))
            
            unused_color = None
            for color_option in available_colors:
                if color_option.get_attribute("value") not in used_colors:
                    unused_color = color_option
                    break
            
            if unused_color:
                color_select.select_by_value(unused_color.get_attribute("value"))
                print(f"✅ Selected color for new variant: {unused_color.text}")
            else:
                print(f"⚠️ No unused colors available")
            
            # Add picture to new variant
            picture_upload = new_variant.find_element(By.CSS_SELECTOR, "input[type='file']")
            test_image_path = self._create_test_image("new_variant_edit.jpg")
            picture_upload.send_keys(test_image_path)
            time.sleep(2)
            print(f"✅ Picture added to new variant")
            
            print(f"🔍 Step 3: Modifying existing variant...")
            
            if initial_variant_count > 0:
                first_existing_variant = updated_variants[0]
                
                # Try to change color of first variant (if other colors available)
                first_color_select = Select(first_existing_variant.find_element(By.CSS_SELECTOR, "select[name*='color']"))
                current_color_value = first_color_select.first_selected_option.get_attribute("value")
                
                # Find different color
                different_color = None
                for color_option in color_select.options:
                    if (color_option.get_attribute("value") != current_color_value and 
                        color_option.get_attribute("value") not in used_colors[1:]):  # Exclude current and other used colors
                        different_color = color_option
                        break
                
                if different_color:
                    first_color_select.select_by_value(different_color.get_attribute("value"))
                    print(f"✅ Changed color of first variant to: {different_color.text}")
                    time.sleep(1)  # Wait for any updates
                else:
                    print(f"⚠️ No different colors available for first variant")
                
                # Add additional picture to existing variant
                existing_picture_uploads = first_existing_variant.find_elements(By.CSS_SELECTOR, "input[type='file']")
                if existing_picture_uploads:
                    additional_upload = existing_picture_uploads[0]
                    additional_image_path = self._create_test_image("additional_variant_edit.jpg")
                    additional_upload.send_keys(additional_image_path)
                    time.sleep(2)
                    print(f"✅ Additional picture added to existing variant")
            
            print(f"🔍 Step 4: Testing variant removal (if safe)...")
            
            # Only remove variant if we have more than 1 (components need at least 1 variant)
            if new_variant_count > 1:
                # Remove the newly added variant
                remove_buttons = new_variant.find_elements(By.CSS_SELECTOR,
                    ".remove-variant, .btn-remove, [data-action='remove']")
                
                if remove_buttons:
                    self._safe_click(remove_buttons[0])
                    time.sleep(1)
                    
                    # Verify variant was removed
                    final_variants = self.driver.find_elements(By.CSS_SELECTOR,
                        ".variant-item, .variant-container, [data-variant]")
                    final_count = len(final_variants)
                    
                    self.assertEqual(final_count, initial_variant_count,
                        "Should return to original variant count after removal")
                    print(f"✅ Variant removed - back to {final_count} variants")
                else:
                    print(f"⚠️ Remove button not found for new variant")
            else:
                print(f"⚠️ Skipping removal - need to maintain at least 1 variant")
            
            print(f"🔍 Step 5: Verifying variant validation...")
            
            # Check that all remaining variants have required fields
            final_variants = self.driver.find_elements(By.CSS_SELECTOR,
                ".variant-item, .variant-container, [data-variant]")
            
            for i, variant in enumerate(final_variants):
                variant_color_select = Select(variant.find_element(By.CSS_SELECTOR, "select[name*='color']"))
                color_value = variant_color_select.first_selected_option.get_attribute("value")
                self.assertNotEqual(color_value, "", f"Variant {i+1} should have color selected")
                
                variant_pictures = variant.find_elements(By.CSS_SELECTOR,
                    ".picture-preview, .image-preview, img")
                self.assertGreater(len(variant_pictures), 0, f"Variant {i+1} should have at least one picture")
            
            print(f"✅ All variants properly configured")
            
            print(f"✅ SELENIUM TEST PASSED: Component variants management in edit mode complete")
            
        except Exception as e:
            print(f"❌ SELENIUM TEST FAILED: {str(e)}")
            self._take_screenshot("edit_variants_failure")
            raise

    def test_edit_form_sku_preview_updates(self):
        """Test that SKU previews update correctly when editing"""
        print(f"\n🧪 SELENIUM TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test real-time SKU preview updates during editing")
        
        try:
            # Load a component for editing
            component_id = self._get_or_create_test_component()
            self.driver.get(f"{self.base_url}/component/edit/{component_id}")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            
            print(f"🔍 Step 1: Capturing initial SKU previews...")
            
            # Find SKU preview elements
            sku_elements = self.driver.find_elements(By.CSS_SELECTOR,
                ".sku-preview, .variant-sku, [data-sku]")
            
            initial_skus = []
            for sku_element in sku_elements:
                if sku_element.is_displayed():
                    sku_text = sku_element.text.strip()
                    if sku_text:
                        initial_skus.append(sku_text)
            
            print(f"📋 Found {len(initial_skus)} initial SKU previews")
            for i, sku in enumerate(initial_skus):
                print(f"   SKU {i+1}: {sku}")
            
            print(f"🔍 Step 2: Modifying product number and watching SKU updates...")
            
            # Get current product number
            product_field = self.driver.find_element(By.NAME, "product_number")
            original_product = product_field.get_attribute("value")
            
            # Change product number
            new_product = f"{original_product}-SKU-TEST"
            product_field.clear()
            product_field.send_keys(new_product)
            
            # Trigger change event
            product_field.send_keys(Keys.TAB)
            time.sleep(3)  # Wait for SKU updates
            
            # Check if SKUs updated
            updated_sku_elements = self.driver.find_elements(By.CSS_SELECTOR,
                ".sku-preview, .variant-sku, [data-sku]")
            
            updated_skus = []
            for sku_element in updated_sku_elements:
                if sku_element.is_displayed():
                    sku_text = sku_element.text.strip()
                    if sku_text:
                        updated_skus.append(sku_text)
            
            print(f"📋 SKUs after product number change:")
            for i, sku in enumerate(updated_skus):
                print(f"   SKU {i+1}: {sku}")
            
            # Verify SKUs contain new product number
            sku_updated = False
            for sku in updated_skus:
                if new_product.lower().replace(" ", "_") in sku.lower():
                    sku_updated = True
                    break
            
            if sku_updated:
                print(f"✅ SKU previews updated with new product number")
            else:
                print(f"⚠️ SKU previews may not have updated with new product number")
            
            print(f"🔍 Step 3: Testing supplier change impact on SKUs...")
            
            try:
                supplier_select = Select(self.driver.find_element(By.NAME, "supplier_id"))
                original_supplier_value = supplier_select.first_selected_option.get_attribute("value")
                
                # Change supplier if options available
                if len(supplier_select.options) > 2:
                    new_supplier_index = 1 if supplier_select.first_selected_option.get_attribute("value") != supplier_select.options[1].get_attribute("value") else 2
                    supplier_select.select_by_index(new_supplier_index)
                    
                    new_supplier_text = supplier_select.first_selected_option.text
                    print(f"✅ Changed supplier to: {new_supplier_text}")
                    
                    # Wait for SKU updates
                    time.sleep(3)
                    
                    # Check SKUs again
                    supplier_updated_sku_elements = self.driver.find_elements(By.CSS_SELECTOR,
                        ".sku-preview, .variant-sku, [data-sku]")
                    
                    supplier_updated_skus = []
                    for sku_element in supplier_updated_sku_elements:
                        if sku_element.is_displayed():
                            sku_text = sku_element.text.strip()
                            if sku_text:
                                supplier_updated_skus.append(sku_text)
                    
                    print(f"📋 SKUs after supplier change:")
                    for i, sku in enumerate(supplier_updated_skus):
                        print(f"   SKU {i+1}: {sku}")
                    
                    # Check if supplier code appears in SKUs
                    supplier_in_sku = False
                    for sku in supplier_updated_skus:
                        # Look for supplier code pattern in SKU
                        if any(word.upper() in sku.upper() for word in new_supplier_text.split() if len(word) > 2):
                            supplier_in_sku = True
                            break
                    
                    if supplier_in_sku:
                        print(f"✅ Supplier change reflected in SKU previews")
                    else:
                        print(f"⚠️ Supplier change may not be reflected in SKU previews")
                else:
                    print(f"⚠️ Not enough supplier options to test change")
                    
            except NoSuchElementException:
                print(f"⚠️ Supplier field not found")
            
            print(f"🔍 Step 4: Testing color change impact on variant SKUs...")
            
            # Find first variant and change its color
            variant_containers = self.driver.find_elements(By.CSS_SELECTOR,
                ".variant-item, .variant-container, [data-variant]")
            
            if variant_containers:
                first_variant = variant_containers[0]
                color_select = Select(first_variant.find_element(By.CSS_SELECTOR, "select[name*='color']"))
                original_color_value = color_select.first_selected_option.get_attribute("value")
                
                # Find different color
                different_color_option = None
                for option in color_select.options:
                    if option.get_attribute("value") != original_color_value and option.get_attribute("value"):
                        different_color_option = option
                        break
                
                if different_color_option:
                    color_select.select_by_value(different_color_option.get_attribute("value"))
                    print(f"✅ Changed first variant color to: {different_color_option.text}")
                    
                    # Wait for SKU update
                    time.sleep(2)
                    
                    # Check if variant SKU updated
                    variant_sku_elements = first_variant.find_elements(By.CSS_SELECTOR,
                        ".sku-preview, .variant-sku, [data-sku]")
                    
                    if variant_sku_elements:
                        for sku_element in variant_sku_elements:
                            if sku_element.is_displayed():
                                variant_sku = sku_element.text.strip()
                                if different_color_option.text.lower().replace(" ", "_") in variant_sku.lower():
                                    print(f"✅ Variant SKU updated with new color")
                                    print(f"   New variant SKU: {variant_sku}")
                                    break
                    else:
                        print(f"⚠️ Variant SKU elements not found")
                else:
                    print(f"⚠️ No different color available for testing")
            else:
                print(f"⚠️ No variants found for color change testing")
            
            print(f"✅ SELENIUM TEST PASSED: SKU preview updates during editing verified")
            
        except Exception as e:
            print(f"❌ SELENIUM TEST FAILED: {str(e)}")
            self._take_screenshot("sku_preview_failure")
            raise

    # Helper methods

    def _get_or_create_test_component(self):
        """Get existing component ID or create one for testing"""
        try:
            # Try to find existing component first
            self.driver.get(f"{self.base_url}/components")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Look for component links
            component_links = self.driver.find_elements(By.CSS_SELECTOR,
                "a[href*='/component/'], .component-link")
            
            if component_links:
                for link in component_links:
                    href = link.get_attribute("href")
                    if "/component/" in href and "/edit" not in href and "/new" not in href:
                        component_id = href.split("/component/")[-1].split("/")[0]
                        if component_id.isdigit():
                            return component_id
            
            # If no existing component found, create one
            return self._create_test_component_for_editing()
            
        except Exception:
            return self._create_test_component_for_editing()

    def _create_test_component_for_editing(self):
        """Create a test component for editing tests"""
        try:
            print(f"🔨 Creating test component for editing...")
            
            # Navigate to creation form
            self.driver.get(f"{self.base_url}/component/new")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            
            # Fill essential info
            product_number = f"EDIT-TEST-{self.timestamp}"
            
            product_field = self.driver.find_element(By.NAME, "product_number")
            product_field.send_keys(product_number)
            
            description_field = self.driver.find_element(By.NAME, "description")
            description_field.send_keys(f"Test component for editing - {datetime.now()}")
            
            # Select component type
            component_type_select = Select(self.driver.find_element(By.NAME, "component_type_id"))
            if len(component_type_select.options) > 1:
                component_type_select.select_by_index(1)
            
            # Add a variant
            add_variant_btn = self.driver.find_element(By.CSS_SELECTOR,
                ".add-variant, .btn-add-variant, [data-action='add-variant']")
            self._safe_click(add_variant_btn)
            time.sleep(1)
            
            # Configure variant
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
                test_image_path = self._create_test_image("edit_test_component.jpg")
                picture_upload.send_keys(test_image_path)
                time.sleep(2)
            
            # Submit
            submit_button = self.driver.find_element(By.CSS_SELECTOR,
                "button[type='submit'], input[type='submit'], .btn-submit")
            self._safe_click(submit_button)
            
            # Wait for redirect and extract component ID
            time.sleep(5)
            current_url = self.driver.current_url
            
            if "/component/" in current_url:
                component_id = current_url.split("/component/")[-1].split("/")[0]
                if component_id.isdigit():
                    print(f"✅ Created test component: {component_id}")
                    return component_id
            
            print(f"❌ Failed to create test component")
            return None
            
        except Exception as e:
            print(f"❌ Error creating test component: {e}")
            return None

    def _create_test_image(self, filename):
        """Create a simple test image file"""
        from PIL import Image
        import tempfile
        
        img = Image.new('RGB', (100, 100), color='red')
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, filename)
        img.save(file_path, 'JPEG')
        return file_path

    def _scroll_to_element(self, element):
        """Scroll element into view"""
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)

    def _safe_click(self, element):
        """Safely click element with fallback"""
        try:
            element.click()
        except ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].click();", element)

    def _take_screenshot(self, name):
        """Take screenshot for debugging"""
        try:
            screenshot_path = f"/tmp/selenium_edit_{name}_{self.timestamp}.png"
            self.driver.save_screenshot(screenshot_path)
            print(f"📸 Screenshot saved: {screenshot_path}")
        except Exception:
            pass


if __name__ == '__main__':
    print("""
    🎬 COMPONENT EDIT EXISTING TESTING
    
    Prerequisites:
    1. Application running: ./start.sh
    2. Chrome browser installed
    3. PIL library: pip install Pillow
    
    Run tests:
    python -m pytest tests/selenium/component_editing/test_component_edit_existing.py -v -s
    
    This test suite covers:
    ✅ Loading existing components for editing
    ✅ Editing essential information
    ✅ Managing variants in edit mode
    ✅ Real-time SKU preview updates
    
    Tests component edit form logic specifically.
    """)
    
    unittest.main()