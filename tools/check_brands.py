#!/usr/bin/env python3
"""Check what brands exist in the database"""
import requests

# Get component edit data to see what's available
response = requests.get("http://localhost:6002/api/components/6/edit-data")
if response.status_code == 200:
    data = response.json()
    component = data['component']
    
    print("Current component associations:")
    print(f"Brands: {component['brands']}")
    print(f"Categories: {component['categories']}")
    print(f"Keywords: {component['keywords']}")
    print(f"Properties: {component['properties']}")
else:
    print(f"Failed to get component data: {response.status_code}")

# Let's also try to get all brands via API if there's such an endpoint
try:
    brands_response = requests.get("http://localhost:6002/api/brand")
    if brands_response.status_code == 200:
        print(f"\nAvailable brands: {brands_response.json()}")
except:
    print("No brands API endpoint available")