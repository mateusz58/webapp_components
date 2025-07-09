#!/usr/bin/env python3
"""
Unit tests for Component Deletion API endpoint
Following TDD methodology - tests written first before implementation
"""
import unittest
import json
import os
import tempfile
import time
from io import BytesIO
from unittest.mock import patch, MagicMock

# Add app directory to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models import Component, ComponentType, Supplier, Color, ComponentVariant, Picture, Brand, ComponentBrand, Keyword, keyword_component, Category, component_category
from config import Config


class TestConfig(Config):
    """Test configuration - use existing PostgreSQL database"""
    TESTING = True
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'
    UPLOAD_FOLDER = tempfile.mkdtemp()
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024


class ComponentDeleteAPITestCase(unittest.TestCase):
    """Test cases for Component Deletion API endpoint following TDD methodology"""

    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        
        # Create test upload directory
        self.test_upload_dir = tempfile.mkdtemp()
        self.app.config['UPLOAD_FOLDER'] = self.test_upload_dir
        self.app.config['UPLOAD_URL_PREFIX'] = 'http://test-webdav/components'
        
        # Get existing database data for testing
        self._get_test_data()

    def tearDown(self):
        """Clean up after tests"""
        # Clean up any test components we created
        self._cleanup_test_components()
        
        # Clean up test files
        import shutil
        try:
            shutil.rmtree(self.test_upload_dir)
        except:
            pass
        
        db.session.remove()
        self.app_context.pop()

    def _get_test_data(self):
        """Get existing data from PostgreSQL database for testing"""
        self.component_type = ComponentType.query.first()
        self.supplier = Supplier.query.first()
        self.color = Color.query.first()
        self.brand = Brand.query.first()
        
        if not self.component_type:
            self.fail("No ComponentType found in database. Please seed test data.")
        if not self.color:
            self.fail("No Color found in database. Please seed test data.")

    def _cleanup_test_components(self):
        """Clean up any components created during testing"""
        # Delete components that start with TEST_DELETE_
        test_components = Component.query.filter(
            Component.product_number.like('TEST_DELETE_%')
        ).all()
        
        for component in test_components:
            try:
                db.session.delete(component)
                db.session.commit()
            except:
                db.session.rollback()

    def _create_test_component(self, product_number=None, with_variants=False, with_pictures=False, with_brands=False):
        """Create a test component with specified associations"""
        if not product_number:
            unique_suffix = int(time.time() * 1000) % 10000
            product_number = f'TEST_DELETE_{unique_suffix}'
        
        component = Component(
            product_number=product_number,
            description=f'Test Component for Deletion - {product_number}',
            component_type_id=self.component_type.id,
            supplier_id=self.supplier.id if self.supplier else None
        )
        db.session.add(component)
        db.session.flush()
        
        # Add variants if requested
        variants = []
        if with_variants and self.color:
            variant = ComponentVariant(
                component_id=component.id,
                color_id=self.color.id
            )
            db.session.add(variant)
            db.session.flush()
            variants.append(variant)
        
        # Add pictures if requested
        pictures = []
        if with_pictures:
            # Create one picture per variant OR one component picture if no variants
            if variants:
                # Create variant pictures
                for i, variant in enumerate(variants):
                    test_filename = f'{product_number.lower()}_{self.color.name.lower()}_{i+1}.jpg'
                    test_image_path = os.path.join(self.test_upload_dir, test_filename)
                    with open(test_image_path, 'w') as f:
                        f.write(f'fake image data {i+1}')
                    
                    picture = Picture(
                        component_id=component.id,
                        variant_id=variant.id,
                        picture_name=test_filename.replace('.jpg', ''),
                        url=f'http://test-webdav/components/{test_filename}',
                        picture_order=i+1
                    )
                    db.session.add(picture)
                    db.session.flush()
                    pictures.append(picture)
            else:
                # Create component picture (no variant)
                test_filename = f'{product_number.lower()}_main_1.jpg'
                test_image_path = os.path.join(self.test_upload_dir, test_filename)
                with open(test_image_path, 'w') as f:
                    f.write('fake image data 1')
                
                picture = Picture(
                    component_id=component.id,
                    variant_id=None,
                    picture_name=test_filename.replace('.jpg', ''),
                    url=f'http://test-webdav/components/{test_filename}',
                    picture_order=1
                )
                db.session.add(picture)
                db.session.flush()
                pictures.append(picture)
        
        # Add brand associations if requested
        brand_associations = []
        if with_brands and self.brand:
            brand_assoc = ComponentBrand(
                component_id=component.id,
                brand_id=self.brand.id
            )
            db.session.add(brand_assoc)
            db.session.flush()
            brand_associations.append(brand_assoc)
        
        db.session.commit()
        
        return {
            'component': component,
            'variants': variants,
            'pictures': pictures,
            'brand_associations': brand_associations
        }

    # ===== TDD TESTS - RED PHASE =====
    # These tests should fail initially as the endpoint doesn't exist yet

    def test_delete_nonexistent_component_should_return_404(self):
        """RED: Test deletion of non-existent component returns 404"""
        response = self.client.delete('/api/component/99999')
        self.assertEqual(response.status_code, 404)

    def test_delete_component_without_associations_should_succeed(self):
        """RED: Test deletion of simple component without associations"""
        # Create test component
        test_data = self._create_test_component()
        component = test_data['component']
        component_id = component.id
        
        # Attempt deletion
        response = self.client.delete(f'/api/component/{component_id}')
        
        # Should succeed
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn(component.product_number, data['message'])
        
        # Component should be deleted from database
        deleted_component = Component.query.get(component_id)
        self.assertIsNone(deleted_component)

    def test_delete_component_with_variants_should_cascade_delete(self):
        """RED: Test deletion cascades to variants"""
        # Create test component with variants
        test_data = self._create_test_component(with_variants=True)
        component = test_data['component']
        variants = test_data['variants']
        
        component_id = component.id
        variant_id = variants[0].id if variants else None
        
        # Attempt deletion
        response = self.client.delete(f'/api/component/{component_id}')
        
        # Should succeed
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['summary']['associations_deleted']['variants'], 1)
        
        # Both component and variant should be deleted
        self.assertIsNone(Component.query.get(component_id))
        if variant_id:
            self.assertIsNone(ComponentVariant.query.get(variant_id))

    def test_delete_component_with_pictures_should_delete_files_and_records(self):
        """RED: Test deletion removes picture files and database records"""
        # Create test component with pictures
        test_data = self._create_test_component(with_variants=True, with_pictures=True)
        component = test_data['component']
        pictures = test_data['pictures']
        
        component_id = component.id
        picture_id = pictures[0].id if pictures else None
        
        # Verify test file exists
        if pictures:
            test_filename = pictures[0].url.split('/')[-1]
            test_file_path = os.path.join(self.test_upload_dir, test_filename)
            self.assertTrue(os.path.exists(test_file_path))
        
        # Attempt deletion
        response = self.client.delete(f'/api/component/{component_id}')
        
        # Should succeed
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        if pictures:
            self.assertEqual(data['summary']['associations_deleted']['pictures'], 1)
            self.assertEqual(data['summary']['files_deleted']['successful'], 1)
        
        # Component and picture record should be deleted
        self.assertIsNone(Component.query.get(component_id))
        if picture_id:
            self.assertIsNone(Picture.query.get(picture_id))
        
        # Picture file should be deleted
        if pictures:
            self.assertFalse(os.path.exists(test_file_path))

    def test_delete_component_with_brand_associations_should_cascade_delete(self):
        """RED: Test deletion removes brand associations"""
        # Create test component with brand associations
        test_data = self._create_test_component(with_brands=True)
        component = test_data['component']
        brand_associations = test_data['brand_associations']
        
        component_id = component.id
        brand_assoc_id = brand_associations[0].id if brand_associations else None
        brand_id = self.brand.id
        
        # Attempt deletion
        response = self.client.delete(f'/api/component/{component_id}')
        
        # Should succeed
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        if brand_associations:
            self.assertEqual(data['summary']['associations_deleted']['brands'], 1)
        
        # Component and brand association should be deleted, brand should remain
        self.assertIsNone(Component.query.get(component_id))
        if brand_assoc_id:
            self.assertIsNone(ComponentBrand.query.get(brand_assoc_id))
        self.assertIsNotNone(Brand.query.get(brand_id))

    def test_delete_component_comprehensive_with_all_associations(self):
        """RED: Test deletion of component with all possible associations"""
        # Create comprehensive test component
        test_data = self._create_test_component(
            with_variants=True, 
            with_pictures=True, 
            with_brands=True
        )
        component = test_data['component']
        variants = test_data['variants']
        pictures = test_data['pictures']
        brand_associations = test_data['brand_associations']
        
        component_id = component.id
        
        # Verify test files exist
        test_files = []
        for picture in pictures:
            test_filename = picture.url.split('/')[-1]
            test_file_path = os.path.join(self.test_upload_dir, test_filename)
            self.assertTrue(os.path.exists(test_file_path))
            test_files.append(test_file_path)
        
        # Attempt deletion
        response = self.client.delete(f'/api/component/{component_id}')
        
        # Should succeed
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        
        summary = data['summary']
        expected_variants = len(variants)
        expected_pictures = len(pictures)
        expected_brands = len(brand_associations)
        
        self.assertEqual(summary['associations_deleted']['variants'], expected_variants)
        self.assertEqual(summary['associations_deleted']['pictures'], expected_pictures)
        self.assertEqual(summary['associations_deleted']['brands'], expected_brands)
        self.assertEqual(summary['files_deleted']['successful'], expected_pictures)
        
        # All component data should be deleted
        self.assertIsNone(Component.query.get(component_id))
        remaining_variants = ComponentVariant.query.filter_by(component_id=component_id).all()
        self.assertEqual(len(remaining_variants), 0)
        remaining_pictures = Picture.query.filter_by(component_id=component_id).all()
        self.assertEqual(len(remaining_pictures), 0)
        remaining_brands = ComponentBrand.query.filter_by(component_id=component_id).all()
        self.assertEqual(len(remaining_brands), 0)
        
        # Reference data should remain
        self.assertIsNotNone(ComponentType.query.get(self.component_type.id))
        if self.supplier:
            self.assertIsNotNone(Supplier.query.get(self.supplier.id))
        self.assertIsNotNone(Color.query.get(self.color.id))
        if self.brand:
            self.assertIsNotNone(Brand.query.get(self.brand.id))
        
        # Files should be deleted
        for test_file in test_files:
            self.assertFalse(os.path.exists(test_file))

    def test_delete_component_should_handle_missing_files_gracefully(self):
        """RED: Test deletion when picture files don't exist on filesystem"""
        # Create test component with pictures but delete the file
        test_data = self._create_test_component(with_variants=True, with_pictures=True)
        component = test_data['component']
        pictures = test_data['pictures']
        
        component_id = component.id
        
        # Delete the test file to simulate missing file
        if pictures:
            test_filename = pictures[0].url.split('/')[-1]
            test_file_path = os.path.join(self.test_upload_dir, test_filename)
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
        
        # Attempt deletion
        response = self.client.delete(f'/api/component/{component_id}')
        
        # Should succeed despite missing files
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        if pictures:
            self.assertEqual(data['summary']['associations_deleted']['pictures'], 1)
            # File deletion count should be 0 since file didn't exist
            self.assertEqual(data['summary']['files_deleted']['successful'], 0)
        
        # Component should be deleted
        self.assertIsNone(Component.query.get(component_id))

    def test_delete_api_endpoint_content_type_handling(self):
        """RED: Test API handles different content types properly"""
        # Create test component
        test_data = self._create_test_component()
        component = test_data['component']
        component_id = component.id
        
        # Test with no specific content type
        response = self.client.delete(f'/api/component/{component_id}')
        self.assertEqual(response.status_code, 200)
        
        # Verify it's actually deleted
        self.assertIsNone(Component.query.get(component_id))


if __name__ == '__main__':
    unittest.main()