#!/usr/bin/env python3
"""
Test the API directly for brand association workflow
Create new component and edit existing component with brand associations
"""
import requests
import json

BASE_URL = "http://localhost:6002"

def test_create_component_with_existing_brand():
    """Test creating a new component with existing brand via API"""
    print("🧪 TEST 1: Create component with existing brand via API")
    print("-" * 60)
    
    # First, get available brands
    try:
        response = requests.get(f"{BASE_URL}/")
        print("   Available brands from main page scan...")
    except:
        pass
    
    # Create component data with existing brand
    component_data = {
        "product_number": f"API_BRAND_TEST_001",
        "description": "API test component with existing brand",
        "component_type_id": 5,  # Should exist
        "supplier_id": 1,  # Should exist
        "brand_ids": [12],  # Existing brand ID (Modern Essentials)
    }
    
    print(f"   Sending component data: {json.dumps(component_data, indent=2)}")
    
    try:
        # Create via API
        response = requests.post(
            f"{BASE_URL}/api/component/create",
            headers={"Content-Type": "application/json"},
            json=component_data
        )
        
        print(f"   Response status: {response.status_code}")
        print(f"   Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Component created successfully!")
            print(f"   Component ID: {result.get('component', {}).get('id')}")
            print(f"   Brands count: {result.get('component', {}).get('brands_count', 0)}")
            
            component_id = result.get('component', {}).get('id')
            if component_id:
                # Verify brand association by fetching edit data
                print(f"\n   🔍 Verifying brand association for component {component_id}...")
                edit_response = requests.get(f"{BASE_URL}/api/components/{component_id}/edit-data")
                if edit_response.status_code == 200:
                    edit_data = edit_response.json()
                    brands = edit_data.get('component', {}).get('brands', [])
                    print(f"   Component has {len(brands)} brand(s) associated:")
                    for brand in brands:
                        print(f"      - {brand['name']} (ID: {brand['id']})")
                    
                    if len(brands) > 0:
                        print("   ✅ Brand association SUCCESS!")
                        return True
                    else:
                        print("   ❌ Brand association FAILED!")
                        return False
                else:
                    print(f"   ❌ Failed to fetch edit data: {edit_response.status_code}")
                    return False
        else:
            print(f"   ❌ Component creation failed: {response.status_code}")
            print(f"   Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_create_component_with_new_brand():
    """Test creating a new component with new brand via API"""
    print("\n🧪 TEST 2: Create component with NEW brand via API")
    print("-" * 60)
    
    # Create component data with new brand
    component_data = {
        "product_number": f"API_NEW_BRAND_TEST_001",
        "description": "API test component with new brand",
        "component_type_id": 5,
        "supplier_id": 1,
        "new_brand_name": "API Test Brand 2025"  # New brand to create
    }
    
    print(f"   Sending component data: {json.dumps(component_data, indent=2)}")
    
    try:
        # Create via API
        response = requests.post(
            f"{BASE_URL}/api/component/create",
            headers={"Content-Type": "application/json"},
            json=component_data
        )
        
        print(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Component created successfully!")
            print(f"   Component ID: {result.get('component', {}).get('id')}")
            print(f"   Brands count: {result.get('component', {}).get('brands_count', 0)}")
            
            component_id = result.get('component', {}).get('id')
            if component_id:
                # Verify brand association and new brand creation
                print(f"\n   🔍 Verifying new brand creation and association...")
                edit_response = requests.get(f"{BASE_URL}/api/components/{component_id}/edit-data")
                if edit_response.status_code == 200:
                    edit_data = edit_response.json()
                    brands = edit_data.get('component', {}).get('brands', [])
                    print(f"   Component has {len(brands)} brand(s) associated:")
                    for brand in brands:
                        print(f"      - {brand['name']} (ID: {brand['id']})")
                    
                    # Check if our new brand was created
                    new_brand_found = any(brand['name'] == 'API Test Brand 2025' for brand in brands)
                    if new_brand_found:
                        print("   ✅ New brand creation and association SUCCESS!")
                        return True
                    else:
                        print("   ❌ New brand creation FAILED!")
                        return False
                else:
                    print(f"   ❌ Failed to fetch edit data: {edit_response.status_code}")
                    return False
        else:
            print(f"   ❌ Component creation failed: {response.status_code}")
            print(f"   Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_edit_component_brand_association():
    """Test editing existing component to add/change brand association"""
    print("\n🧪 TEST 3: Edit existing component brand association via API")
    print("-" * 60)
    
    component_id = 213  # Use existing component
    
    # Get current brand associations
    try:
        response = requests.get(f"{BASE_URL}/api/components/{component_id}/edit-data")
        if response.status_code == 200:
            current_data = response.json()
            current_brands = current_data.get('component', {}).get('brands', [])
            print(f"   Current brands: {[b['name'] for b in current_brands]}")
        else:
            print(f"   ❌ Failed to get current data: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error getting current data: {e}")
        return False
    
    # Update with different brand
    update_data = {
        "product_number": "API_EDIT_BRAND_TEST",
        "description": "Testing brand edit via API", 
        "brand_ids": [13, 11],  # Different brands (Artisan Collection, Heritage Brands)
    }
    
    print(f"   Updating with data: {json.dumps(update_data, indent=2)}")
    
    try:
        response = requests.put(
            f"{BASE_URL}/api/component/{component_id}",
            headers={"Content-Type": "application/json"},
            json=update_data
        )
        
        print(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Component updated successfully!")
            
            # Verify the brand changes
            print(f"\n   🔍 Verifying brand changes...")
            edit_response = requests.get(f"{BASE_URL}/api/components/{component_id}/edit-data")
            if edit_response.status_code == 200:
                edit_data = edit_response.json()
                new_brands = edit_data.get('component', {}).get('brands', [])
                print(f"   Updated brands: {[b['name'] for b in new_brands]}")
                
                # Check if the brands were updated correctly
                brand_ids = [b['id'] for b in new_brands]
                if 13 in brand_ids and 11 in brand_ids:
                    print("   ✅ Brand association update SUCCESS!")
                    return True
                else:
                    print(f"   ❌ Brand association update FAILED! Expected [13, 11], got {brand_ids}")
                    return False
            else:
                print(f"   ❌ Failed to verify update: {edit_response.status_code}")
                return False
        else:
            print(f"   ❌ Component update failed: {response.status_code}")
            print(f"   Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("🚀 API BRAND WORKFLOW TESTING")
    print("=" * 70)
    print("Testing brand association functionality via API endpoints")
    print("=" * 70)
    
    results = []
    
    # Test 1: Create with existing brand
    results.append(test_create_component_with_existing_brand())
    
    # Test 2: Create with new brand
    results.append(test_create_component_with_new_brand())
    
    # Test 3: Edit brand association
    results.append(test_edit_component_brand_association())
    
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    test_names = [
        "Create component with existing brand",
        "Create component with new brand", 
        "Edit component brand association"
    ]
    
    for i, (test_name, result) in enumerate(zip(test_names, results), 1):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {i}. {test_name}: {status}")
    
    overall = "✅ ALL TESTS PASSED" if all(results) else "❌ SOME TESTS FAILED"
    print(f"\n{overall}")
    
    if not all(results):
        print("\n🔧 ISSUE CONFIRMED: Brand association is not working properly")
        print("   This confirms the bug report - brands are not being created/associated")
    else:
        print("\n✅ Brand association is working via API")
        print("   The issue might be in the web form submission, not the API")
    
    return all(results)

if __name__ == "__main__":
    main()