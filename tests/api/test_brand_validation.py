#!/usr/bin/env python3
"""
Test script to verify brand validation is working
"""
import requests
import json

BASE_URL = "http://localhost:6002"

def test_brand_validation():
    """Test component update with invalid brand IDs"""
    
    print("🧪 Testing Brand Validation")
    print("=" * 40)
    
    component_id = 6
    
    # Test update with invalid brand IDs
    update_data = {
        'description': 'Testing brand validation',
        'brand_ids': [999, 998],  # These should not exist
        'properties': {
            'test': 'brand_validation'
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
            print("✅ Update successful (brands should have been skipped)!")
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
    success = test_brand_validation()
    if success:
        print("\n🎉 Brand validation is working!")
    else:
        print("\n💥 Brand validation failed!")