#!/usr/bin/env python3
"""
Test script to verify that brand editing functionality is working correctly.
This test simulates the JavaScript form submission flow to ensure brands are properly processed.
"""

import requests
import json

def test_brand_edit_fix():
    """Test that brand editing works with the fixed JavaScript form handler."""
    
    print("🧪 Testing brand editing fix...")
    
    try:
        # Use component ID 211 as a test case
        component_id = 211
        
        # Get component data first
        print(f"📋 Getting component {component_id} data...")
        response = requests.get(f"http://localhost:6002/api/components/{component_id}/edit-data")
        
        if response.status_code == 200:
            component_data = response.json()
            print(f"✅ Component data retrieved successfully")
            current_brands = component_data.get('component', {}).get('brands', [])
            print(f"📊 Current brands: {[b['name'] for b in current_brands]}")
            
            # Test brand update with existing brand ID
            print(f"🔄 Testing brand update with existing brand...")
            
            # Let's get the list of available brands first
            print("📋 Getting available brands...")
            brands_response = requests.get("http://localhost:6002/api/brands")
            if brands_response.status_code == 200:
                brands_data = brands_response.json()
                available_brands = brands_data.get('brands', [])
                print(f"📊 Available brands: {[b['name'] for b in available_brands[:5]]}")
                
                if available_brands:
                    # Select the first available brand for testing
                    test_brand_id = available_brands[0]['id']
                    test_brand_name = available_brands[0]['name']
                    
                    # Create minimal update data focusing on brand
                    update_data = {
                        "brand_ids": [test_brand_id]
                    }
                    
                    print(f"🔄 Updating component to use brand: {test_brand_name} (ID: {test_brand_id})")
                    
                    # Make the PUT request to update brand
                    headers = {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': 'test-token'  # We have CSRF exemption for testing
                    }
                    
                    response = requests.put(
                        f"http://localhost:6002/api/component/{component_id}",
                        json=update_data,
                        headers=headers
                    )
                    
                    print(f"📡 API Response Status: {response.status_code}")
                    print(f"📡 API Response: {response.text}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success'):
                            print("✅ Brand updated successfully!")
                            print(f"📈 Changes: {json.dumps(result.get('changes', {}), indent=2)}")
                            
                            # Verify the brand was actually updated
                            print("🔍 Verifying brand update...")
                            verify_response = requests.get(f"http://localhost:6002/api/components/{component_id}/edit-data")
                            if verify_response.status_code == 200:
                                verify_data = verify_response.json()
                                updated_brands = verify_data.get('component', {}).get('brands', [])
                                print(f"📊 Updated brands: {[b['name'] for b in updated_brands]}")
                                
                                if any(b['id'] == test_brand_id for b in updated_brands):
                                    print("✅ Brand update verified successfully!")
                                    return True
                                else:
                                    print("❌ Brand update not reflected in component data")
                                    return False
                            else:
                                print("❌ Failed to verify brand update")
                                return False
                        else:
                            print(f"❌ Update failed: {result.get('error', 'Unknown error')}")
                            return False
                    else:
                        print(f"❌ API request failed with status {response.status_code}")
                        return False
                else:
                    print("❌ No brands available for testing")
                    return False
            else:
                print(f"❌ Failed to get brands: {brands_response.status_code}")
                return False
                
        else:
            print(f"❌ Failed to get component data: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = test_brand_edit_fix()
    if success:
        print("\n🎉 Brand editing fix test PASSED!")
    else:
        print("\n💥 Brand editing fix test FAILED!")