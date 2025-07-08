#!/usr/bin/env python3
"""
Test script to verify that keyword editing functionality is working correctly.
This test simulates the JavaScript form submission flow to ensure keywords are properly processed.
"""

import requests
import json

def test_keyword_edit_fix():
    """Test that keyword editing works with the fixed JavaScript form handler."""
    
    # Test data - simulating what the fixed JavaScript would send
    test_data = {
        "keywords": ["summer", "casual", "outdoor"],  # Array format as expected by service layer
        "product_number": "TEST123",
        "description": "Test component for keyword editing"
    }
    
    print("🧪 Testing keyword editing fix...")
    print(f"📤 Sending data: {json.dumps(test_data, indent=2)}")
    
    try:
        # First, let's test if we can get a component to edit
        # We'll use component ID 211 as a test case (from the home page)
        component_id = 211
        
        # Get component data first
        print(f"📋 Getting component {component_id} data...")
        response = requests.get(f"http://localhost:6002/api/components/{component_id}/edit-data")
        
        if response.status_code == 200:
            component_data = response.json()
            print(f"✅ Component data retrieved successfully")
            print(f"📊 Current keywords: {component_data.get('component', {}).get('keywords', [])}")
            
            # Now test the keyword update
            print(f"🔄 Testing keyword update...")
            
            # Create minimal update data focusing on keywords
            update_data = {
                "keywords": ["test", "keyword", "functionality"]
            }
            
            # Make the PUT request to update keywords
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
                    print("✅ Keywords updated successfully!")
                    print(f"📈 Changes: {json.dumps(result.get('changes', {}), indent=2)}")
                    return True
                else:
                    print(f"❌ Update failed: {result.get('error', 'Unknown error')}")
                    return False
            else:
                print(f"❌ API request failed with status {response.status_code}")
                return False
                
        else:
            print(f"❌ Failed to get component data: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = test_keyword_edit_fix()
    if success:
        print("\n🎉 Keyword editing fix test PASSED!")
    else:
        print("\n💥 Keyword editing fix test FAILED!")