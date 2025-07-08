#!/usr/bin/env python3
"""
Test to verify if picture staging is working by checking browser console output.
"""

import requests
import json

def test_picture_staging_console():
    """Test if we can see console output from picture staging."""
    
    print("🧪 Testing picture staging console output...")
    
    try:
        # Get the component edit page to see if debug console messages are working
        component_id = 211
        edit_url = f"http://localhost:6002/component/edit/{component_id}"
        print(f"🌐 Getting: {edit_url}")
        
        response = requests.get(edit_url)
        if response.status_code != 200:
            print(f"❌ Failed to load page: {response.status_code}")
            return False
            
        html = response.text
        
        # Check if console.log statements are in the JavaScript
        debug_messages = [
            "🔥 handleVariantImages called",
            "🖼️ Adding picture to grid",
            "📁 Handling EXISTING variant images",
            "✅ Grid found for variant",
            "✅ Picture added to grid"
        ]
        
        found_debug = []
        for msg in debug_messages:
            if msg in html:
                found_debug.append(msg)
                
        print(f"✅ Found {len(found_debug)} debug messages in JavaScript:")
        for msg in found_debug:
            print(f"   ✅ {msg}")
            
        if len(found_debug) >= 3:
            print("✅ Debug logging is properly set up")
            return True
        else:
            print("❌ Debug logging is missing or incomplete")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

def test_variant_grid_structure():
    """Test that the variant grid structure is correct."""
    
    print("\n🧪 Testing variant grid HTML structure...")
    
    try:
        response = requests.get("http://localhost:6002/component/edit/211")
        html = response.text
        
        # Check critical elements
        checks = [
            ('variant_images_251', 'File input for variant 251'),
            ('pictures_grid_251', 'Pictures grid for variant 251'),
            ('miniatures_251', 'Miniatures container for variant 251'),
            ('pictures_section_251', 'Pictures section for variant 251'),
            ("handleVariantImages('251'", 'Correct function call format')
        ]
        
        passed = 0
        for element, description in checks:
            if element in html:
                print(f"   ✅ {description}")
                passed += 1
            else:
                print(f"   ❌ {description}")
                
        print(f"\n📊 HTML Structure: {passed}/{len(checks)} checks passed")
        return passed == len(checks)
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    success1 = test_picture_staging_console()
    success2 = test_variant_grid_structure()
    
    if success1 and success2:
        print("\n🎉 Picture staging setup tests PASSED!")
        print("\n💡 Next step: Test actual file upload in browser to see console output")
    else:
        print("\n💥 Picture staging setup tests FAILED!")