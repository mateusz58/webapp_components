#!/usr/bin/env python3
"""
Test script to test variant picture upload functionality in the browser.
This will check if the JavaScript functions are working correctly.
"""

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import tempfile
import os
import time
from PIL import Image
import io

def create_test_image():
    """Create a small test image file."""
    img = Image.new('RGB', (100, 100), color='red')
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
    img.save(temp_file.name, 'JPEG')
    return temp_file.name

def test_variant_picture_upload():
    """Test variant picture upload in browser."""
    
    print("🧪 Testing variant picture upload functionality...")
    
    # Create a test image
    test_image_path = create_test_image()
    print(f"📸 Created test image: {test_image_path}")
    
    try:
        # Setup Chrome driver
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        
        # Navigate to component edit page (component 211 has variants)
        component_id = 211
        edit_url = f"http://localhost:6002/component/edit/{component_id}"
        print(f"🌐 Navigating to: {edit_url}")
        
        driver.get(edit_url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "variants_container"))
        )
        
        print("✅ Page loaded successfully")
        
        # Look for variant with ID 251 (Brown variant from component 211)
        variant_id = "251"
        
        # Check if variant exists
        variant_element = driver.find_element(By.CSS_SELECTOR, f"[data-variant-id='{variant_id}']")
        if not variant_element:
            print(f"❌ Variant {variant_id} not found on page")
            return False
            
        print(f"✅ Found variant {variant_id}")
        
        # Click on "Manage Pictures" button to expand the pictures section
        manage_pictures_btn = driver.find_element(By.CSS_SELECTOR, f"button[onclick*='toggleVariantPictures({variant_id})']")
        print(f"🖱️ Clicking 'Manage Pictures' button...")
        manage_pictures_btn.click()
        
        # Wait for pictures section to expand
        time.sleep(1)
        
        # Check if the pictures section is now visible
        pictures_section = driver.find_element(By.ID, f"pictures_section_{variant_id}")
        if pictures_section.value_of_css_property("display") == "none":
            print(f"❌ Pictures section did not expand for variant {variant_id}")
            return False
            
        print(f"✅ Pictures section expanded for variant {variant_id}")
        
        # Find the file input element
        file_input = driver.find_element(By.ID, f"variant_images_{variant_id}")
        print(f"✅ Found file input: variant_images_{variant_id}")
        
        # Upload the test image
        print(f"📤 Uploading test image...")
        file_input.send_keys(test_image_path)
        
        # Wait a moment for JavaScript to process the file
        time.sleep(2)
        
        # Check browser console for our debug messages
        logs = driver.get_log('browser')
        console_messages = [log['message'] for log in logs if log['level'] == 'INFO']
        
        print("🖥️ Browser console messages:")
        for msg in console_messages[-10:]:  # Show last 10 messages
            print(f"   {msg}")
        
        # Check if picture was added to the grid
        pictures_grid = driver.find_element(By.ID, f"pictures_grid_{variant_id}")
        picture_items = pictures_grid.find_elements(By.CSS_SELECTOR, ".picture-item")
        
        print(f"📊 Pictures in grid after upload: {len(picture_items)}")
        
        # Check if miniatures were updated
        miniatures_container = driver.find_element(By.ID, f"miniatures_{variant_id}")
        miniature_items = miniatures_container.find_elements(By.CSS_SELECTOR, ".miniature-item")
        
        print(f"📊 Miniatures after upload: {len(miniature_items)}")
        
        # Check if any error messages appeared
        error_messages = driver.find_elements(By.CSS_SELECTOR, ".error-message, .alert-danger")
        if error_messages:
            print("❌ Error messages found:")
            for error in error_messages:
                print(f"   {error.text}")
        
        # Look for success indicators
        if len(picture_items) > len(miniature_items):
            print("✅ New picture appears to have been added to grid!")
            return True
        else:
            print("❌ Picture was not added to grid")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
        
    finally:
        if 'driver' in locals():
            driver.quit()
        
        # Clean up test image
        if os.path.exists(test_image_path):
            os.unlink(test_image_path)
            
    return False

if __name__ == "__main__":
    success = test_variant_picture_upload()
    if success:
        print("\n🎉 Variant picture upload test PASSED!")
    else:
        print("\n💥 Variant picture upload test FAILED!")