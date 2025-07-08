#!/usr/bin/env python3
"""
Test script to verify the component update API endpoint
This tests the exact same endpoint that form-handler.js calls
"""
import requests
import json
import sys

BASE_URL = "http://localhost:6002"

def test_component_update_api():
    """Test the component update API endpoint that form-handler.js uses"""
    
    print("🧪 Testing Component Update API Endpoint")
    print("=" * 60)
    
    # First check if the application is accessible
    print("1. Checking application accessibility...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code != 200:
            print(f"❌ Application not accessible: {response.status_code}")
            return False
        print("✅ Application is accessible")
    except Exception as e:
        print(f"❌ Application not accessible: {str(e)}")
        return False
    
    # Get a list of components to find one to test with
    print("\n2. Finding a component to test with...")
    try:
        # Try to search for any component
        response = requests.get(f"{BASE_URL}/api/components/search?q=&limit=10")
        if response.status_code == 200:
            search_result = response.json()
            components = search_result.get('results', [])
            
            if not components:
                print("❌ No components found in database to test with")
                print("   You need to create at least one component first")
                return False
            
            # Use the first component for testing
            test_component = components[0]
            component_id = test_component['id']
            print(f"✅ Found component to test: ID={component_id}, Product={test_component['product_number']}")
            
        else:
            print(f"❌ Failed to search components: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error searching components: {str(e)}")
        return False
    
    # Test getting component edit data first (this should work)
    print(f"\n3. Testing GET edit data for component {component_id}...")
    try:
        response = requests.get(f"{BASE_URL}/api/components/{component_id}/edit-data")
        if response.status_code == 200:
            edit_data = response.json()
            component_data = edit_data['component']
            print("✅ Edit data endpoint working")
            print(f"   Product Number: {component_data['product_number']}")
            print(f"   Description: {component_data.get('description', 'None')}")
            print(f"   Component Type: {component_data.get('component_type', {}).get('name', 'None')}")
        else:
            print(f"❌ Edit data endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error getting edit data: {str(e)}")
        return False
    
    # Test the PUT update endpoint (exactly what form-handler.js does)
    print(f"\n4. Testing PUT update endpoint for component {component_id}...")
    
    # Prepare test data similar to what form-handler.js sends
    update_data = {
        'product_number': component_data['product_number'] + '_TEST',
        'description': (component_data.get('description', '') + ' - Updated by API test').strip(),
        'component_type_id': component_data.get('component_type', {}).get('id', 1),
        'supplier_id': component_data.get('supplier', {}).get('id') if component_data.get('supplier') else None,
        'brand_ids': [brand['id'] for brand in component_data.get('brands', [])],
        'category_ids': [cat['id'] for cat in component_data.get('categories', [])],
        'keywords': [kw['name'] for kw in component_data.get('keywords', [])],
        'properties': component_data.get('properties', {})
    }
    
    print(f"   Sending data: {json.dumps(update_data, indent=2)}")
    
    try:
        # Make PUT request exactly like form-handler.js does
        response = requests.put(
            f"{BASE_URL}/api/component/{component_id}",
            headers={'Content-Type': 'application/json'},
            json=update_data
        )
        
        print(f"   Response Status: {response.status_code}")
        print(f"   Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Component update successful!")
            print(f"   Response: {json.dumps(result, indent=2)}")
            
            # Test reverting the change
            print(f"\n5. Reverting changes...")
            revert_data = {
                'product_number': component_data['product_number'],
                'description': component_data.get('description', ''),
                'component_type_id': component_data.get('component_type', {}).get('id', 1),
                'supplier_id': component_data.get('supplier', {}).get('id') if component_data.get('supplier') else None,
                'brand_ids': [brand['id'] for brand in component_data.get('brands', [])],
                'category_ids': [cat['id'] for cat in component_data.get('categories', [])],
                'keywords': [kw['name'] for kw in component_data.get('keywords', [])],
                'properties': component_data.get('properties', {})
            }
            
            revert_response = requests.put(
                f"{BASE_URL}/api/component/{component_id}",
                headers={'Content-Type': 'application/json'},
                json=revert_data
            )
            
            if revert_response.status_code == 200:
                print("✅ Changes reverted successfully")
            else:
                print(f"⚠️ Failed to revert changes: {revert_response.status_code}")
            
            return True
            
        else:
            result = response.json() if response.headers.get('content-type', '').startswith('application/json') else {'error': response.text}
            print(f"❌ Component update failed!")
            print(f"   Error: {json.dumps(result, indent=2)}")
            return False
            
    except Exception as e:
        print(f"❌ Error making PUT request: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_component_update_api()
    if success:
        print("\n🎉 All tests passed! The component update API endpoint is working correctly.")
        sys.exit(0)
    else:
        print("\n💥 Tests failed! Check the application and database.")
        sys.exit(1)