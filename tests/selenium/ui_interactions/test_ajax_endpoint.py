#!/usr/bin/env python3
"""
Quick test to verify the AJAX endpoint is working
"""
import requests
import json

def test_ajax_endpoint():
    """Test the new AJAX variant endpoint"""
    try:
        # Test with a known component ID (from our test)
        component_id = 104  # From the last test run
        
        response = requests.get(f"http://localhost:6002/api/components/{component_id}/variants")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ AJAX endpoint working!")
            print(f"📊 Component ID: {data.get('component_id')}")
            print(f"🎨 Variants found: {len(data.get('variants', []))}")
            print(f"🖼️  Component images: {len(data.get('component_images', []))}")
            
            for variant in data.get('variants', []):
                print(f"  - {variant['name']}: {len(variant['images'])} pictures")
            
            return True
        else:
            print(f"❌ Endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_ajax_endpoint()