#!/usr/bin/env python3
"""
Test brand display in component detail pages
"""
import requests
from bs4 import BeautifulSoup

BASE_URL = "http://localhost:6002"

def test_component_brand_display(component_id, expected_brands=0):
    """Test brand display for a specific component"""
    print(f"\n🧪 Testing component {component_id} brand display")
    print("-" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/component/{component_id}")
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check if Brands tab exists
            brands_tab = soup.find('button', {'@click': lambda x: x and 'brands' in x})
            brands_tab_alt = soup.find(text='Brands')
            
            if brands_tab or brands_tab_alt:
                print("   ✅ Brands tab found in navigation")
            else:
                print("   ❌ Brands tab NOT found in navigation")
            
            # Check for brand content
            brand_content = soup.find('div', {'id': 'brands'}) or soup.find(text=lambda t: 'brand_associations' in str(t))
            
            if brand_content:
                print("   ✅ Brand content section found")
            else:
                print("   ❌ Brand content section NOT found")
            
            # Check for empty state vs brand data
            empty_state = soup.find(text=lambda t: 'No Brands Associated' in str(t)) if soup.find(text=lambda t: 'No Brands Associated' in str(t)) else None
            brand_cards = soup.find_all(class_='brand-card') if hasattr(soup, 'find_all') else []
            
            if expected_brands == 0:
                if empty_state:
                    print("   ✅ Empty state displayed correctly (no brands)")
                    return True
                else:
                    print("   ❌ Expected empty state but found brand data")
                    return False
            else:
                if brand_cards:
                    print(f"   ✅ Brand cards found (expected {expected_brands} brands)")
                    return True
                else:
                    print(f"   ❌ Expected brand cards but found empty state")
                    return False
        else:
            print(f"   ❌ Failed to load component: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("🚀 TESTING BRAND DISPLAY IN COMPONENT DETAIL PAGES")
    print("=" * 60)
    
    results = []
    
    # Test component 218 (no brands)
    results.append(test_component_brand_display(218, expected_brands=0))
    
    # Test component 217 (has brands)  
    results.append(test_component_brand_display(217, expected_brands=1))
    
    print("\n" + "=" * 60)
    print("📊 BRAND DISPLAY TEST RESULTS")
    print("=" * 60)
    
    test_names = [
        "Component 218 (no brands)",
        "Component 217 (with brands)"
    ]
    
    for i, (test_name, result) in enumerate(zip(test_names, results), 1):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {i}. {test_name}: {status}")
    
    overall = "✅ ALL TESTS PASSED" if all(results) else "❌ SOME TESTS FAILED"
    print(f"\n{overall}")
    
    if all(results):
        print("\n✅ Brand display is working correctly!")
        print("   - Empty state shows for components without brands")
        print("   - Brand information shows for components with brands")
    else:
        print("\n❌ Brand display needs fixing")

if __name__ == "__main__":
    main()