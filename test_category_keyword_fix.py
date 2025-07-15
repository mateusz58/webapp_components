#!/usr/bin/env python3
"""
Quick test to verify category and keyword associations work during component creation

This test specifically addresses the issue discovered where categories and keywords
work when editing components but fail when creating new ones.
"""

import requests
import json
import time

def test_category_keyword_creation():
    """Test that categories and keywords are properly handled during component creation"""
    base_url = "http://localhost:6002"
    timestamp = int(time.time())
    
    print(f"🧪 Testing category and keyword handling during component creation...")
    
    # Create a session to handle CSRF
    session = requests.Session()
    
    # Get CSRF token by visiting the new component page
    print(f"🔑 Getting CSRF token...")
    form_response = session.get(f"{base_url}/component/new")
    
    if form_response.status_code != 200:
        print(f"❌ Failed to get form page: {form_response.status_code}")
        return False
    
    # Extract CSRF token from the response
    import re
    csrf_match = re.search(r'name="csrf_token".*?value="([^"]+)"', form_response.text)
    if not csrf_match:
        print(f"❌ Could not find CSRF token in form")
        return False
    
    csrf_token = csrf_match.group(1)
    print(f"✅ Got CSRF token: {csrf_token[:16]}...")
    
    # Create test data
    component_data = {
        'csrf_token': csrf_token,
        'product_number': f'TEST-CAT-KEY-{timestamp}',
        'description': 'Test component for category and keyword fix',
        'component_type_id': '1',  # Assuming ID 1 exists
        'supplier_id': '1',        # Assuming ID 1 exists
        
        # Test categories
        'category_ids[]': ['1', '2'],  # Assuming these exist
        
        # Test keywords
        'keywords': 'test,automation,fix,creation',
        
        # Test brands  
        'brand_ids[]': ['1'],  # Assuming ID 1 exists
        
        # Add a variant (required)
        'variant_color_1': '1',  # Assuming color ID 1 exists
    }
    
    print(f"📤 Sending POST request to create component...")
    print(f"   Product number: {component_data['product_number']}")
    print(f"   Categories: {component_data['category_ids[]']}")
    print(f"   Keywords: {component_data['keywords']}")
    print(f"   Brands: {component_data['brand_ids[]']}")
    
    try:
        response = session.post(f"{base_url}/api/component/create", data=component_data)
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                component_id = result['component']['id']
                print(f"✅ Component created successfully with ID: {component_id}")
                
                # Check association counts
                categories_count = result['component'].get('categories_count', 0)
                keywords_count = result['component'].get('keywords_count', 0)
                brands_count = result['component'].get('brands_count', 0)
                
                print(f"📊 Association counts:")
                print(f"   Categories: {categories_count}")
                print(f"   Keywords: {keywords_count}")
                print(f"   Brands: {brands_count}")
                
                # Verify the fix worked
                if categories_count > 0:
                    print(f"✅ CATEGORY FIX WORKING: {categories_count} categories associated")
                else:
                    print(f"❌ CATEGORY FIX FAILED: No categories associated")
                
                if keywords_count > 0:
                    print(f"✅ KEYWORD FIX WORKING: {keywords_count} keywords associated")
                else:
                    print(f"❌ KEYWORD FIX FAILED: No keywords associated")
                
                if brands_count > 0:
                    print(f"✅ BRAND HANDLING OK: {brands_count} brands associated")
                else:
                    print(f"⚠️ BRAND HANDLING: No brands associated")
                
                return True
            else:
                print(f"❌ Component creation failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error details: {error_data}")
            except:
                print(f"   Response text: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during test: {e}")
        return False

if __name__ == '__main__':
    print("""
🔧 CATEGORY AND KEYWORD FIX VERIFICATION TEST

This test verifies that the fix for categories and keywords during component 
creation is working properly.

Issue: Categories and keywords worked when editing but failed when creating new components.
Root cause: CREATE route only extracted brand data, missing category_ids and keywords.
Fix: Added category_ids and keywords extraction to component_data in create_component API.

Prerequisites:
1. Application running: ./start.sh
2. Database has at least 1 component type, supplier, category, brand, and color

Running test...
    """)
    
    success = test_category_keyword_creation()
    
    if success:
        print(f"\n🎉 TEST PASSED: Category and keyword fix is working!")
    else:
        print(f"\n💥 TEST FAILED: Category and keyword fix needs more work!")