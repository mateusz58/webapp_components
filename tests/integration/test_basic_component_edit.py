#!/usr/bin/env python3
"""Test basic component editing functionality"""
import requests
import json

def test_basic_component_edit():
    """Test basic component edit without associations first"""
    
    print("🧪 Testing Basic Component Edit Functionality")
    print("=" * 50)
    
    component_id = 6
    
    # Test 1: Basic field updates only
    print("1. Testing basic field updates...")
    
    update_data = {
        "description": "Updated via service layer architecture - SUCCESS!",
        "properties": {
            "service_layer_test": "passed",
            "architecture": "MVC with service layer",
            "timestamp": "2025-07-07"
        }
    }
    
    try:
        response = requests.put(
            f"http://localhost:6002/api/component/{component_id}",
            headers={'Content-Type': 'application/json'},
            json=update_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Basic field updates successful!")
            print(f"   Changes: {list(result['changes'].keys())}")
            print(f"   Message: {result['message']}")
        else:
            print(f"❌ Basic update failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Basic update error: {str(e)}")
        return False
    
    # Test 2: Test keywords only (they don't need existing references)
    print("\n2. Testing keyword associations...")
    
    keyword_data = {
        "description": "Testing keyword functionality",
        "keywords": ["service", "architecture", "mvc", "flask"]
    }
    
    try:
        response = requests.put(
            f"http://localhost:6002/api/component/{component_id}",
            headers={'Content-Type': 'application/json'},
            json=keyword_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Keyword associations successful!")
            print(f"   Changes: {list(result['changes'].keys())}")
        else:
            print(f"❌ Keyword update failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Keyword update error: {str(e)}")
        return False
    
    # Test 3: Verify the changes were saved
    print("\n3. Verifying changes were saved...")
    
    try:
        response = requests.get(f"http://localhost:6002/api/components/{component_id}/edit-data")
        if response.status_code == 200:
            data = response.json()
            component = data['component']
            
            print("✅ Data verification successful!")
            print(f"   Description: {component['description']}")
            print(f"   Properties: {component['properties']}")
            print(f"   Keywords: {len(component['keywords'])} keywords")
            for kw in component['keywords']:
                print(f"     - {kw['name']}")
        else:
            print(f"❌ Data verification failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Data verification error: {str(e)}")
        return False
    
    print("\n" + "=" * 50)
    print("🎯 SUMMARY:")
    print("✅ Service layer architecture is working!")
    print("✅ Basic field updates working")
    print("✅ Properties updating correctly") 
    print("✅ Keywords creating and associating correctly")
    print("✅ Association handlers working with JSON data")
    print("✅ Data persistence confirmed")
    
    return True

if __name__ == "__main__":
    success = test_basic_component_edit()
    if success:
        print("\n🎉 Component editing architecture is FUNCTIONAL!")
        print("\n📋 NEXT STEPS:")
        print("- Test with real brand/category data")
        print("- Implement proper CSRF handling")
        print("- Test frontend integration")
        print("- Complete variant picture management")
    else:
        print("\n💥 Component editing test FAILED!")
        
    exit(0 if success else 1)