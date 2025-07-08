#!/usr/bin/env python3

"""
Test script to verify that the "Manage Pictures" button works for existing variants
in the component edit form.
"""

import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def test_manage_pictures_button():
    """Test the Manage Pictures button functionality"""
    
    # First, check if the app is running
    try:
        response = requests.get('http://localhost:6002', timeout=5)
        print(f"✓ App is running - Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"✗ App is not accessible: {e}")
        print("Please start the application first with ./start.sh")
        return False
    
    # Setup Chrome driver
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run headless
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        
        # Navigate to component edit page
        print("🔧 Navigating to component edit page...")
        driver.get('http://localhost:6002/component/edit/2')
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        print("✓ Page loaded successfully")
        
        # Check if there are any JavaScript errors in console
        logs = driver.get_log('browser')
        js_errors = [log for log in logs if log['level'] == 'SEVERE']
        if js_errors:
            print("⚠️  JavaScript errors found:")
            for error in js_errors[:5]:  # Show first 5 errors
                print(f"   - {error['message']}")
        else:
            print("✓ No JavaScript errors found")
        
        # Check if variantManager is available in global scope
        print("🔧 Checking if variantManager is available...")
        variant_manager_exists = driver.execute_script("return typeof window.variantManager !== 'undefined';")
        
        if variant_manager_exists:
            print("✓ variantManager is available in global scope")
        else:
            print("✗ variantManager is NOT available in global scope")
            return False
        
        # Find variant cards on the page
        print("🔧 Looking for component variants...")
        variant_cards = driver.find_elements(By.CSS_SELECTOR, "[data-variant-id]")
        
        if not variant_cards:
            print("✗ No variant cards found on the page")
            return False
        
        print(f"✓ Found {len(variant_cards)} variant card(s)")
        
        # For each variant card, check if it has a "Manage Pictures" button
        success_count = 0
        for i, variant_card in enumerate(variant_cards):
            variant_id = variant_card.get_attribute('data-variant-id')
            print(f"🔧 Testing variant {variant_id}...")
            
            # Look for "Manage Pictures" buttons in this variant
            manage_buttons = variant_card.find_elements(By.XPATH, ".//button[contains(text(), 'Manage Pictures')]")
            
            if not manage_buttons:
                print(f"   ✗ No 'Manage Pictures' button found in variant {variant_id}")
                continue
            
            print(f"   ✓ Found {len(manage_buttons)} 'Manage Pictures' button(s)")
            
            # Test clicking the first button
            try:
                button = manage_buttons[0]
                print(f"   🔧 Clicking 'Manage Pictures' button...")
                
                # Scroll to button to ensure it's visible
                driver.execute_script("arguments[0].scrollIntoView(true);", button)
                time.sleep(0.5)
                
                # Click the button
                button.click()
                time.sleep(1)
                
                # Check if the pictures section became visible
                pictures_section = driver.find_element(By.ID, f"pictures_section_{variant_id}")
                is_visible = pictures_section.is_displayed()
                
                if is_visible:
                    print(f"   ✓ Pictures section opened successfully for variant {variant_id}")
                    success_count += 1
                    
                    # Try clicking again to close it
                    button.click()
                    time.sleep(1)
                    
                    is_hidden = not pictures_section.is_displayed()
                    if is_hidden:
                        print(f"   ✓ Pictures section closed successfully for variant {variant_id}")
                    else:
                        print(f"   ⚠️  Pictures section did not close for variant {variant_id}")
                else:
                    print(f"   ✗ Pictures section did not open for variant {variant_id}")
                
            except Exception as e:
                print(f"   ✗ Error clicking button for variant {variant_id}: {e}")
        
        # Final results
        if success_count > 0:
            print(f"\n✓ SUCCESS: {success_count}/{len(variant_cards)} variants have working 'Manage Pictures' buttons")
            return True
        else:
            print(f"\n✗ FAILURE: None of the {len(variant_cards)} variants have working 'Manage Pictures' buttons")
            return False
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        return False
    
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    print("Testing Manage Pictures Button Functionality")
    print("=" * 50)
    
    success = test_manage_pictures_button()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ Test completed successfully - Manage Pictures buttons are working")
    else:
        print("✗ Test failed - Manage Pictures buttons are not working properly")
        print("\nPossible issues to investigate:")
        print("1. JavaScript not loading properly")
        print("2. variantManager not initialized")
        print("3. Button onclick handlers not set correctly")
        print("4. CSS selectors changed")
    
    exit(0 if success else 1)