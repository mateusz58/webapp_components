#!/usr/bin/env python3
"""
Test brand association through ComponentService (proper MVC)
"""
import time
from app import create_app, db
from app.services.component_service import ComponentService

def test_service_brand_association():
    print("🧪 Testing brand association via ComponentService")
    print("=" * 50)
    
    app = create_app()
    with app.app_context():
        try:
            # Test data with brand association
            component_data = {
                'product_number': f'SERVICE_BRAND_TEST_{int(time.time())}',
                'description': 'Testing brand via service layer',
                'component_type_id': 5,
                'supplier_id': 1,
                'brand_ids': [12],  # Modern Essentials
                'new_brand_name': ''  # No new brand
            }
            
            print(f"Creating component via service with data: {component_data}")
            
            # Use service layer
            result = ComponentService.create_component(component_data)
            
            print(f"✅ Component created: {result}")
            print(f"Brands count: {result['component']['brands_count']}")
            
            if result['component']['brands_count'] > 0:
                print("✅ Brand association SUCCESS via service layer!")
                return True
            else:
                print("❌ Brand association FAILED via service layer!")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

def test_service_new_brand_creation():
    print("\n🧪 Testing NEW brand creation via ComponentService")
    print("=" * 50)
    
    app = create_app()
    with app.app_context():
        try:
            # Test data with new brand creation
            component_data = {
                'product_number': f'SERVICE_NEW_BRAND_TEST_{int(time.time())}',
                'description': 'Testing new brand via service layer',
                'component_type_id': 5,
                'supplier_id': 1,
                'brand_ids': [],
                'new_brand_name': 'Service Test Brand 2025'
            }
            
            print(f"Creating component with new brand via service: {component_data}")
            
            # Use service layer
            result = ComponentService.create_component(component_data)
            
            print(f"✅ Component created: {result}")
            print(f"Brands count: {result['component']['brands_count']}")
            
            if result['component']['brands_count'] > 0:
                print("✅ New brand creation SUCCESS via service layer!")
                return True
            else:
                print("❌ New brand creation FAILED via service layer!")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

if __name__ == "__main__":
    print("🚀 TESTING COMPONENTSERVICE BRAND ASSOCIATION")
    print("=" * 60)
    
    results = []
    results.append(test_service_brand_association())
    results.append(test_service_new_brand_creation())
    
    print("\n" + "=" * 60)
    print("📊 SERVICE LAYER TEST RESULTS")
    print("=" * 60)
    
    test_names = [
        "Brand association via service",
        "New brand creation via service"
    ]
    
    for i, (test_name, result) in enumerate(zip(test_names, results), 1):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {i}. {test_name}: {status}")
    
    overall = "✅ ALL TESTS PASSED" if all(results) else "❌ SOME TESTS FAILED"
    print(f"\n{overall}")
    
    if all(results):
        print("\n✅ Service layer handles brand associations correctly!")
        print("The issue is that API endpoints need to use the service layer properly.")
    else:
        print("\n❌ Service layer has brand association issues that need fixing")