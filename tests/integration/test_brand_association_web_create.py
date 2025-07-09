#!/usr/bin/env python3
"""
Integration test for brand association in web component creation
Tests that web component creation properly associates brands using service layer

Following TDD methodology:
1. Write failing test first (RED)
2. Implement minimal fix (GREEN) 
3. Refactor while keeping tests green
"""

import unittest
import sys
import os
import tempfile

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app import create_app, db
from app.models import Component, Brand, ComponentBrand, ComponentType, Supplier
from app.services.component_service import ComponentService

class TestBrandAssociationWebCreate(unittest.TestCase):
    """Integration test for brand association in web component creation"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        cls.app.config['WTF_CSRF_ENABLED'] = False
        
        cls.client = cls.app.test_client()
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        
        # Create tables
        db.create_all()
        
        # Create test data
        cls._create_test_data()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()
    
    @classmethod
    def _create_test_data(cls):
        """Create test data for brand association tests"""
        # Create component type
        cls.component_type = ComponentType(name='Test Component Type')
        db.session.add(cls.component_type)
        
        # Create supplier
        cls.supplier = Supplier(supplier_code='TEST_SUPPLIER')
        db.session.add(cls.supplier)
        
        # Create existing brand
        cls.existing_brand = Brand(name='Existing Test Brand')
        db.session.add(cls.existing_brand)
        
        db.session.commit()
    
    def setUp(self):
        """Set up for each test"""
        # Clean up any components from previous tests
        Component.query.delete()
        ComponentBrand.query.delete()
        db.session.commit()
    
    def test_service_layer_brand_association_existing_brand(self):
        """Test that ComponentService correctly associates existing brands"""
        print("\n🧪 Testing: Service layer brand association with existing brand")
        
        # Test data matching web form structure
        form_data = {
            'product_number': 'SVC_BRAND_TEST_001',
            'description': 'Service layer test with existing brand',
            'component_type_id': self.component_type.id,
            'supplier_id': self.supplier.id,
            'brand_ids': [str(self.existing_brand.id)],  # Form data comes as strings
        }
        
        print(f"   Creating component via service with data: {form_data}")
        
        # Use ComponentService.create_component (proper MVC)
        result = ComponentService.create_component(form_data)
        
        print(f"   Result: {result}")
        
        # Verify component was created
        self.assertTrue(result['success'], "Component creation should succeed")
        component_id = result['component']['id']
        self.assertIsNotNone(component_id, "Component ID should be returned")
        
        # Verify brand association was created
        brand_associations = ComponentBrand.query.filter_by(component_id=component_id).all()
        self.assertEqual(len(brand_associations), 1, "Should have exactly 1 brand association")
        
        # Verify correct brand was associated
        self.assertEqual(brand_associations[0].brand_id, self.existing_brand.id,
                        f"Should be associated with brand {self.existing_brand.id}")
        
        print(f"   ✅ Brand association SUCCESS: Component {component_id} -> Brand {self.existing_brand.name}")
        
    def test_service_layer_new_brand_creation(self):
        """Test that ComponentService correctly creates and associates new brands"""
        print("\n🧪 Testing: Service layer new brand creation")
        
        # Count initial brands
        initial_brand_count = Brand.query.count()
        print(f"   Initial brand count: {initial_brand_count}")
        
        # Test data with new brand creation
        form_data = {
            'product_number': 'SVC_NEW_BRAND_TEST_001',
            'description': 'Service layer test with new brand creation',
            'component_type_id': self.component_type.id,
            'supplier_id': self.supplier.id,
            'new_brand_name': 'Service Created Brand 2025',
        }
        
        print(f"   Creating component via service with data: {form_data}")
        
        # Use ComponentService.create_component
        result = ComponentService.create_component(form_data)
        
        print(f"   Result: {result}")
        
        # Verify component was created
        self.assertTrue(result['success'], "Component creation should succeed")
        component_id = result['component']['id']
        
        # Verify new brand was created
        final_brand_count = Brand.query.count()
        self.assertEqual(final_brand_count, initial_brand_count + 1,
                        "Should create exactly 1 new brand")
        
        # Find the new brand
        new_brand = Brand.query.filter_by(name='Service Created Brand 2025').first()
        self.assertIsNotNone(new_brand, "New brand should be created")
        
        # Verify brand association was created
        brand_associations = ComponentBrand.query.filter_by(component_id=component_id).all()
        self.assertEqual(len(brand_associations), 1, "Should have exactly 1 brand association")
        self.assertEqual(brand_associations[0].brand_id, new_brand.id,
                        "Should be associated with the newly created brand")
        
        print(f"   ✅ New brand creation SUCCESS: Brand '{new_brand.name}' (ID: {new_brand.id}) created and associated")

    def test_web_form_data_conversion(self):
        """Test that web form data is properly converted for service layer"""
        print("\n🧪 Testing: Web form data conversion for service layer")
        
        # Simulate form submission data (how web forms send data)
        form_data = {
            'product_number': 'WEB_FORM_TEST_001',
            'description': 'Web form data conversion test',
            'component_type_id': str(self.component_type.id),  # Forms send as strings
            'supplier_id': str(self.supplier.id),
            'brand_id': str(self.existing_brand.id),  # Single brand selection
        }
        
        print(f"   Form data (strings): {form_data}")
        
        # Convert for service layer (web route should do this)
        service_data = {
            'product_number': form_data['product_number'],
            'description': form_data['description'],
            'component_type_id': int(form_data['component_type_id']),
            'supplier_id': int(form_data['supplier_id']),
            'brand_ids': [form_data['brand_id']] if form_data.get('brand_id') else [],
        }
        
        print(f"   Service data (converted): {service_data}")
        
        # Use ComponentService.create_component
        result = ComponentService.create_component(service_data)
        
        # Verify success
        self.assertTrue(result['success'], "Component creation should succeed")
        self.assertEqual(result['component']['brands_count'], 1,
                        "Should have 1 brand association")
        
        print(f"   ✅ Form data conversion SUCCESS")


if __name__ == '__main__':
    unittest.main(verbosity=2)