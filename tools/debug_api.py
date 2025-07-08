#!/usr/bin/env python3
"""Debug API response"""
import requests

try:
    response = requests.put(
        "http://localhost:6002/api/component/6",
        headers={'Content-Type': 'application/json'},
        json={"description": "test"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Content: {response.text}")
    
except Exception as e:
    print(f"Error: {e}")