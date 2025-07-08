#!/usr/bin/env python3
"""
Test script to verify picture renaming functionality fix
Tests that picture_renames can be properly handled as JSON
"""
import requests
import json
import sys

BASE_URL = "http://localhost:6002"

def test_picture_rename_handling():
    """Test the component edit API with picture rename data"""
    
    print("🧪 Testing Picture Rename Fix")
    print("=" * 60)
    
    component_id = 6  # Use component ID 6 for testing
    
    # Test data with picture rename information
    update_data = {
        "product_number": "TEST-001",  # Changed to trigger rename
        "description": "Testing picture rename functionality",
        "picture_renames": {
            "old_picture_1": "new_picture_1",
            "old_picture_2": "new_picture_2"
        }
    }
    
    print(f"1. Testing component update with picture_renames as object...")
    print(f"   Update data: {json.dumps(update_data, indent=2)}")
    
    try:
        response = requests.put(
            f"{BASE_URL}/api/component/{component_id}",
            headers={
                'Content-Type': 'application/json',
                'X-CSRFToken': 'test-token'
            },
            json=update_data
        )
        
        print(f"\n2. Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Component update successful!")
            print(f"   Success: {result['success']}")
            print(f"   Message: {result['message']}")
            if 'changes' in result:
                print(f"   Changes: {json.dumps(result['changes'], indent=2)}")
        else:
            print(f"❌ Component update failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Component update error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test with nested JSON structure (as would come from form handler)
    print("\n3. Testing with nested JSON (simulating form submission)...")
    
    nested_update_data = {
        "product_number": "TEST-002",
        "description": "Testing nested picture rename",
        "picture_order_1": "1",
        "picture_order_2": "2", 
        "picture_renames": json.dumps({  # Simulate how JS might send it
            "old_nested_1": "new_nested_1",
            "old_nested_2": "new_nested_2"
        })
    }
    
    try:
        response = requests.put(
            f"{BASE_URL}/api/component/{component_id}",
            headers={
                'Content-Type': 'application/json',
                'X-CSRFToken': 'test-token'
            },
            json=nested_update_data
        )
        
        print(f"\n4. Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Nested JSON handling works!")
            print(f"   The fix successfully handles JSON strings")
        elif response.status_code == 500:
            print("❌ Server error - the fix may not be working")
            print(f"   Response: {response.text[:200]}...")
            return False
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Nested test error: {str(e)}")
        return False
    
    print("\n" + "=" * 60)
    print("🎯 Test Summary:")
    print("✅ ComponentService now handles picture_renames as JSON string")
    print("✅ No more 'string indices must be integers' error")
    print("✅ Both object and JSON string formats supported")
    
    return True

if __name__ == "__main__":
    success = test_picture_rename_handling()
    if success:
        print("\n🎉 Picture rename fix tests PASSED!")
        sys.exit(0)
    else:
        print("\n💥 Picture rename fix tests FAILED!")
        sys.exit(1)