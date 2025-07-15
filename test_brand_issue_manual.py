#!/usr/bin/env python3
"""
Manual test to verify the brand association issue using the actual running application
"""
import requests
import json

BASE_URL = "http://localhost:6002"

def test_brand_association_issue():
    """Test the brand association issue with the running application"""
    print("🔍 MANUAL TEST: Brand Association Issue")
    print("=" * 50)
    
    # Test 1: Check if we can get component data for editing
    print("\n1️⃣ Testing component edit data retrieval...")
    try:
        response = requests.get(f"{BASE_URL}/api/components/213/edit-data")
        if response.status_code == 200:
            data = response.json()
            component = data.get('component', {})
            brands = component.get('brands', [])
            print(f"   ✅ Component 213 has {len(brands)} brand(s) associated:")
            for brand in brands:
                print(f"      - {brand['name']} (ID: {brand['id']})")
        else:
            print(f"   ❌ Failed to get component data: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Test component update with brand selection
    print("\n2️⃣ Testing component update with brand selection...")
    try:
        update_data = {
            "product_number": "BRAND_TEST_001",
            "description": "Testing brand association",
            "brand_ids": [12],  # Select an existing brand
        }
        
        response = requests.put(
            f"{BASE_URL}/api/component/213",
            headers={"Content-Type": "application/json"},
            json=update_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Update successful: {result.get('success', False)}")
            
            # Check if brand was actually associated
            changes = result.get('changes', {})
            if 'brands' in changes or 'associations' in changes:
                print("   ✅ Brand association changes detected")
            else:
                print("   ⚠️ No brand association changes in response")
                
        else:
            print(f"   ❌ Update failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Raw response: {response.text[:200]}")
                
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Verify the brand association was saved
    print("\n3️⃣ Verifying brand association was saved...")
    try:
        response = requests.get(f"{BASE_URL}/api/components/213/edit-data")
        if response.status_code == 200:
            data = response.json()
            component = data.get('component', {})
            brands = component.get('brands', [])
            print(f"   Component 213 now has {len(brands)} brand(s) associated:")
            for brand in brands:
                print(f"      - {brand['name']} (ID: {brand['id']})")
            
            # Check if our test brand (ID 12) is in the list
            brand_ids = [b['id'] for b in brands]
            if 12 in brand_ids:
                print("   ✅ Brand ID 12 is associated")
            else:
                print("   ❌ Brand ID 12 is NOT associated (ISSUE CONFIRMED)")
        else:
            print(f"   ❌ Failed to verify: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Test new brand creation
    print("\n4️⃣ Testing new brand creation...")
    try:
        update_data = {
            "product_number": "BRAND_TEST_002",
            "description": "Testing new brand creation",
            "new_brand_name": "Test New Brand 123"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/component/213",
            headers={"Content-Type": "application/json"},
            json=update_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Update successful: {result.get('success', False)}")
            
            changes = result.get('changes', {})
            print(f"   Changes: {list(changes.keys())}")
        else:
            print(f"   ❌ Update failed: {response.status_code}")
                
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("📊 Manual test completed")
    print("If brand associations are not working, the issue is confirmed")

if __name__ == "__main__":
    test_brand_association_issue()