#!/usr/bin/env python3
"""
Create a test component in the database
"""
import requests
import json

# First, let's create a test component
create_data = {
    "product_number": "TEST-COMP-001", 
    "description": "Test Component for Update Testing",
    "component_type_id": 1,
    "supplier_id": 1,
    "brand_ids[]": [1],
    "category_ids[]": [1], 
    "keywords": "test,component,debug",
    "properties": json.dumps({"material": "plastic"})
}

# Create component
create_url = "http://localhost:6002/api/component/create"
print(f"Creating test component at {create_url}")

response = requests.post(create_url, data=create_data)
print(f"Create Response Status: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    print(f"Create Response: {json.dumps(result, indent=2)}")
    
    if result.get('success'):
        component_id = result['component']['id']
        print(f"\nComponent created with ID: {component_id}")
        
        # Now test update
        update_data = {
            "product_number": "TEST-COMP-001-UPDATED",
            "description": "Updated Test Component",
            "component_type_id": "1",
            "supplier_id": "1",
            "brand_ids[]": ["1", "2"],
            "category_ids[]": ["1"],
            "keywords": "test,component,debug,updated",
            "properties": json.dumps({"material": "metal", "weight": "200g"})
        }
        
        update_url = f"http://localhost:6002/api/component/{component_id}"
        print(f"\nTesting update at {update_url}")
        print(f"Update data: {json.dumps(update_data, indent=2)}")
        
        update_response = requests.put(update_url, json=update_data)
        print(f"\nUpdate Response Status: {update_response.status_code}")
        
        try:
            update_result = update_response.json()
            print(f"Update Response: {json.dumps(update_result, indent=2)}")
        except:
            print(f"Update Response Text: {update_response.text}")
else:
    print(f"Failed to create component: {response.text}")