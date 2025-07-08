#!/usr/bin/env python3
"""
Simple test to check if variant picture upload interface is properly set up.
"""

import requests
import re

def test_variant_picture_interface():
    """Test that the variant picture upload interface is correctly rendered."""
    
    print("🧪 Testing variant picture upload interface...")
    
    try:
        # Get the component edit page HTML
        component_id = 211
        edit_url = f"http://localhost:6002/component/edit/{component_id}"
        print(f"🌐 Fetching: {edit_url}")
        
        response = requests.get(edit_url)
        if response.status_code != 200:
            print(f"❌ Failed to load page: {response.status_code}")
            return False
            
        html = response.text
        print("✅ Page loaded successfully")
        
        # Check if variantManager is loaded
        if 'variant-manager.js' in html:
            print("✅ variant-manager.js is loaded")
        else:
            print("❌ variant-manager.js is NOT loaded")
            return False
            
        # Check if the handleVariantImages function call is correct
        variant_pattern = r'onchange="variantManager\.handleVariantImages\(\'(\d+)\', this\.files\)"'
        matches = re.findall(variant_pattern, html)
        
        if matches:
            print(f"✅ Found {len(matches)} properly quoted variant file input(s): {matches}")
        else:
            # Check for unquoted version
            variant_pattern_unquoted = r'onchange="variantManager\.handleVariantImages\((\d+), this\.files\)"'
            matches_unquoted = re.findall(variant_pattern_unquoted, html)
            if matches_unquoted:
                print(f"❌ Found {len(matches_unquoted)} UNQUOTED variant file input(s): {matches_unquoted}")
                print("❌ This will cause JavaScript errors - variant IDs need to be quoted as strings")
                return False
            else:
                print("❌ No variant file inputs found")
                return False
        
        # Check if pictures grid exists
        if 'id="pictures_grid_251"' in html:
            print("✅ Pictures grid found for variant 251")
        else:
            print("❌ Pictures grid NOT found for variant 251")
            return False
            
        # Check if miniatures container exists  
        if 'id="miniatures_251"' in html:
            print("✅ Miniatures container found for variant 251")
        else:
            print("❌ Miniatures container NOT found for variant 251")
            return False
            
        # Check if the drag and drop functionality is set up
        if 'ondrop="variantManager.handleVariantDrop' in html:
            print("✅ Drag and drop functionality is set up")
        else:
            print("❌ Drag and drop functionality is NOT set up")
            
        # Check if variant manager initialization code is present
        if 'window.variantManager = new VariantManager()' in html:
            print("✅ VariantManager initialization found")
        else:
            print("⚠️ VariantManager initialization not found in HTML (might be in separate script)")
            
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = test_variant_picture_interface()
    if success:
        print("\n🎉 Variant picture interface test PASSED!")
    else:
        print("\n💥 Variant picture interface test FAILED!")