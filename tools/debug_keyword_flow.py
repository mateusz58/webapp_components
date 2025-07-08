#!/usr/bin/env python3

"""
Debug script to trace keyword data flow through the component edit workflow
"""

import requests
import json
import sys

def test_keyword_flow():
    """Test the complete keyword data flow from frontend to backend"""
    
    base_url = "http://localhost:6002"
    
    print("=== Testing Keyword Data Flow ===")
    
    # Step 1: Test keyword search API (what frontend calls)
    print("\n1. Testing keyword search API...")
    try:
        response = requests.get(f"{base_url}/api/keyword/search?q=test&limit=5")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {len(data.get('keywords', []))} keywords")
            for kw in data.get('keywords', [])[:3]:
                print(f"   - {kw['name']} (usage: {kw['usage_count']})")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Step 2: Find a component to test with
    print("\n2. Finding a test component...")
    try:
        response = requests.get(f"{base_url}/api/components/search?q=&limit=1")
        if response.status_code == 200:
            components = response.json().get('results', [])
            if components:
                test_component = components[0]
                component_id = test_component['id']
                print(f"   Using component: {test_component['product_number']} (ID: {component_id})")
                
                # Step 3: Test component edit data API
                print("\n3. Testing component edit data API...")
                response = requests.get(f"{base_url}/api/components/{component_id}/edit-data")
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    edit_data = response.json()
                    component_data = edit_data.get('component', {})
                    keywords = component_data.get('keywords', [])
                    print(f"   Current keywords: {len(keywords)}")
                    for kw in keywords[:3]:
                        print(f"   - {kw['name']}")
                    
                    # Step 4: Test component update API with keywords
                    print("\n4. Testing component update API with keywords...")
                    
                    # Prepare test data
                    update_data = {
                        'product_number': component_data.get('product_number'),
                        'description': component_data.get('description'),
                        'component_type_id': component_data.get('component_type', {}).get('id'),
                        'keywords': ['test_keyword_1', 'test_keyword_2', 'existing_keyword']
                    }
                    
                    print(f"   Sending update data: {json.dumps(update_data, indent=2)}")
                    
                    # Get CSRF token (simplified - in real app this comes from form)
                    headers = {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                    
                    response = requests.put(
                        f"{base_url}/api/component/{component_id}",
                        json=update_data,
                        headers=headers
                    )
                    
                    print(f"   Update Status: {response.status_code}")
                    if response.status_code == 200:
                        result = response.json()
                        print(f"   Success: {result.get('message')}")
                        changes = result.get('changes', {})
                        print(f"   Changes made: {list(changes.keys())}")
                    else:
                        print(f"   Error: {response.text}")
                        
                    # Step 5: Verify keywords were saved
                    print("\n5. Verifying keywords were saved...")
                    response = requests.get(f"{base_url}/api/components/{component_id}/edit-data")
                    if response.status_code == 200:
                        edit_data = response.json()
                        component_data = edit_data.get('component', {})
                        keywords = component_data.get('keywords', [])
                        print(f"   Updated keywords: {len(keywords)}")
                        for kw in keywords:
                            print(f"   - {kw['name']}")
                    
                else:
                    print(f"   Error getting edit data: {response.text}")
            else:
                print("   No components found")
        else:
            print(f"   Error searching components: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")

if __name__ == "__main__":
    test_keyword_flow()