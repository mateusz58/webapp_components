#!/usr/bin/env python3
"""
Integration test to reproduce the brand association issue in component edit form

ISSUE: When creating or editing components via the form:
1. Brand selection is not being saved/associated with the component
2. New brand creation is not working properly
3. Subbrand association is not being handled correctly

This test will demonstrate the failing behavior before we fix it.
"""

import unittest
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app import create_app, db
from app.models import Component, Brand, ComponentBrand, Subbrand, ComponentType, Supplier

class TestBrandAssociationIssue(unittest.TestCase):
    """Test brand association functionality in component creation/editing"""
    
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
        cls.existing_brand = Brand(name='Existing Brand')
        db.session.add(cls.existing_brand)
        
        # Create subbrand under existing brand
        cls.existing_subbrand = Subbrand(name='Existing Subbrand', brand_id=None)  # Will set after flush
        
        db.session.flush()  # Get IDs
        cls.existing_subbrand.brand_id = cls.existing_brand.id
        db.session.add(cls.existing_subbrand)
        
        db.session.commit()
    
    def setUp(self):
        """Set up for each test"""
        # Clean up any components from previous tests
        Component.query.delete()
        ComponentBrand.query.delete()
        db.session.commit()
    
    def test_brand_association_when_creating_component_with_existing_brand(self):
        """Test that existing brand gets associated when creating a component"""
        print("\n🧪 Testing: Brand association when creating component with existing brand")
        
        # Simulate form submission for new component with existing brand selection
        form_data = {
            'product_number': 'TEST_BRAND_001',
            'description': 'Test component with existing brand',
            'component_type_id': self.component_type.id,
            'supplier_id': self.supplier.id,
            'brand_id': self.existing_brand.id,  # Select existing brand
        }
        
        response = self.client.post('/component/new', data=form_data, follow_redirects=False)
        
        # Check if component was created
        component = Component.query.filter_by(product_number='TEST_BRAND_001').first()
        self.assertIsNotNone(component, "Component should be created")
        
        # CRITICAL TEST: Check if brand association was created
        brand_associations = ComponentBrand.query.filter_by(component_id=component.id).all()
        
        print(f"   Component created: {component.product_number}")
        print(f"   Brand associations found: {len(brand_associations)}")
        
        if brand_associations:
            for assoc in brand_associations:
                print(f"   Associated brand: {assoc.brand.name}")
        
        # THIS IS THE FAILING TEST - brand association is not being created
        self.assertTrue(len(brand_associations) > 0, 
                       "Component should have at least one brand association")
        
        # Check if it's the correct brand
        brand_ids = [assoc.brand_id for assoc in brand_associations]
        self.assertIn(self.existing_brand.id, brand_ids,
                     f"Component should be associated with brand '{self.existing_brand.name}'")
    
    def test_new_brand_creation_when_creating_component(self):
        """Test that new brand gets created and associated when creating a component"""
        print("\n🧪 Testing: New brand creation when creating component")
        
        # Count existing brands
        initial_brand_count = Brand.query.count()
        
        # Simulate form submission for new component with new brand
        form_data = {
            'product_number': 'TEST_NEW_BRAND_001',
            'description': 'Test component with new brand',
            'component_type_id': self.component_type.id,
            'supplier_id': self.supplier.id,
            'brand_id': 'new',  # Indicate new brand creation
            'new_brand_name': 'New Test Brand',  # Name for new brand
        }
        
        response = self.client.post('/component/new', data=form_data, follow_redirects=False)
        
        # Check if component was created
        component = Component.query.filter_by(product_number='TEST_NEW_BRAND_001').first()
        self.assertIsNotNone(component, "Component should be created")
        
        # Check if new brand was created
        new_brand = Brand.query.filter_by(name='New Test Brand').first()
        
        print(f"   Component created: {component.product_number}")
        print(f"   New brand created: {new_brand.name if new_brand else 'NOT CREATED'}")
        print(f"   Total brands: {Brand.query.count()} (was {initial_brand_count})")
        
        # THIS SHOULD FAIL - new brand creation is not working
        self.assertIsNotNone(new_brand, "New brand should be created")
        self.assertEqual(Brand.query.count(), initial_brand_count + 1,
                        "Brand count should increase by 1")
        
        # Check if brand association was created
        brand_associations = ComponentBrand.query.filter_by(component_id=component.id).all()
        self.assertTrue(len(brand_associations) > 0,
                       "Component should be associated with the new brand")
        
        # Check if it's associated with the correct new brand
        associated_brand_ids = [assoc.brand_id for assoc in brand_associations]
        self.assertIn(new_brand.id, associated_brand_ids,
                     "Component should be associated with the newly created brand")
    
    def test_brand_association_when_editing_component(self):
        """Test that brand association works when editing an existing component"""
        print("\n🧪 Testing: Brand association when editing existing component")
        
        # Create a component without brand association
        component = Component(
            product_number='TEST_EDIT_001',
            description='Test component for editing',
            component_type_id=self.component_type.id,
            supplier_id=self.supplier.id
        )
        db.session.add(component)
        db.session.commit()
        
        # Verify component has no brand associations initially
        initial_associations = ComponentBrand.query.filter_by(component_id=component.id).count()
        self.assertEqual(initial_associations, 0, "Component should start with no brand associations")
        
        # Edit component to add brand association
        form_data = {
            'product_number': 'TEST_EDIT_001',
            'description': 'Test component for editing - updated',
            'component_type_id': self.component_type.id,
            'supplier_id': self.supplier.id,
            'brand_id': self.existing_brand.id,  # Add brand association
        }
        
        response = self.client.post(f'/component/edit/{component.id}', 
                                  data=form_data, follow_redirects=False)
        
        # Check if brand association was created during edit
        brand_associations = ComponentBrand.query.filter_by(component_id=component.id).all()
        
        print(f"   Component edited: {component.product_number}")
        print(f"   Brand associations after edit: {len(brand_associations)}")
        
        # THIS SHOULD FAIL - brand association is not being created during edit
        self.assertTrue(len(brand_associations) > 0,
                       "Component should have brand association after edit")
        
        # Check if it's the correct brand
        brand_ids = [assoc.brand_id for assoc in brand_associations]
        self.assertIn(self.existing_brand.id, brand_ids,
                     f"Component should be associated with brand '{self.existing_brand.name}' after edit")
    
    def test_subbrand_creation_and_association(self):
        """Test that new subbrand gets created and associated properly"""
        print("\n🧪 Testing: Subbrand creation and association")
        
        # Count initial subbrands
        initial_subbrand_count = Subbrand.query.count()
        
        # Simulate form submission with new subbrand under existing brand
        form_data = {
            'product_number': 'TEST_SUBBRAND_001',
            'description': 'Test component with new subbrand',
            'component_type_id': self.component_type.id,
            'supplier_id': self.supplier.id,
            'brand_id': self.existing_brand.id,  # Select existing brand
            'subbrand_id': 'new',  # Create new subbrand
            'new_subbrand_name': 'New Test Subbrand',  # Name for new subbrand
        }
        
        response = self.client.post('/component/new', data=form_data, follow_redirects=False)
        
        # Check if component was created
        component = Component.query.filter_by(product_number='TEST_SUBBRAND_001').first()
        self.assertIsNotNone(component, "Component should be created")
        
        # Check if new subbrand was created
        new_subbrand = Subbrand.query.filter_by(name='New Test Subbrand').first()
        
        print(f"   Component created: {component.product_number}")
        print(f"   New subbrand created: {new_subbrand.name if new_subbrand else 'NOT CREATED'}")
        print(f"   Total subbrands: {Subbrand.query.count()} (was {initial_subbrand_count})")
        
        # THIS SHOULD FAIL - subbrand creation is likely not working
        self.assertIsNotNone(new_subbrand, "New subbrand should be created")
        self.assertEqual(new_subbrand.brand_id, self.existing_brand.id,
                        "New subbrand should belong to the selected brand")


if __name__ == '__main__':
    unittest.main(verbosity=2)