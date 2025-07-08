#!/usr/bin/env python3
"""
Debug script to test component update API endpoint
"""
import requests
import json

# Test data mimicking what form-handler.js sends
test_data = {
    "product_number": "TEST-001",
    "description": "Test Component Description",
    "component_type_id": "1",
    "supplier_id": "1",
    "brand_ids[]": ["1", "2"],
    "category_ids[]": ["1"],
    "keywords": "test,debug,component",
    "properties": json.dumps({"material": "plastic", "weight": "100g"})
}

# API endpoint
url = "http://localhost:6002/api/component/1"

try:
    # Send PUT request
    print(f"Sending PUT request to {url}")
    print(f"Data: {json.dumps(test_data, indent=2)}")
    
    response = requests.put(url, json=test_data)
    
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    try:
        response_data = response.json()
        print(f"Response JSON: {json.dumps(response_data, indent=2)}")
    except:
        print(f"Response Text: {response.text}")
        
except Exception as e:
    print(f"Error: {str(e)}")