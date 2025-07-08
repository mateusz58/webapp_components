#!/usr/bin/env python3
"""
Test script for simple component update without problematic associations
"""
import requests
import json

BASE_URL = "http://localhost:6002"

def test_simple_update():
    """Test component update with minimal data"""
    
    print("🧪 Testing Simple Component Update")
    print("=" * 50)
    
    component_id = 6
    
    # Test update with minimal data - no brands or categories
    update_data = {
        'description': 'Simple test update without associations',
        'properties': {
            'test_property': 'simple_test',
            'timestamp': '2025-07-07'
        }
    }
    
    print(f"Testing PUT /api/component/{component_id}")
    print(f"Data: {json.dumps(update_data, indent=2)}")
    
    try:
        response = requests.put(
            f"{BASE_URL}/api/component/{component_id}",
            headers={'Content-Type': 'application/json'},
            json=update_data
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Simple update successful!")
            print(f"Result: {json.dumps(result, indent=2)}")
            return True
        else:
            error = response.json() if response.headers.get('content-type', '').startswith('application/json') else {'error': response.text}
            print(f"❌ Update failed: {json.dumps(error, indent=2)}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_simple_update()
    if success:
        print("\n🎉 Simple update works! The issue is with brand/category associations.")
    else:
        print("\n💥 Even simple update failed!")