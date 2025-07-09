"""
Integration Tests for Component Deletion Database Operations
Tests database cascade operations, transaction handling, and data integrity
"""
import unittest
import os
import sys
import tempfile
import time

# Add the app directory to the path so we can import from app
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(os.path.dirname(os.path.dirname(current_dir)))
sys.path.insert(0, app_dir)

from app import create_app, db
from app.models import (
    Component, ComponentType, Supplier, Brand, Color,
    ComponentVariant, Picture, ComponentBrand, Keyword
)
from app.services.component_service import ComponentService
from config import Config
from sqlalchemy import text


class TestConfig(Config):
    TESTING = True
    # Use the actual PostgreSQL database but with a test prefix
    SQLALCHEMY_DATABASE_URI = 'postgresql://component_user:component_app_123@192.168.100.35:5432/promo_database'
    UPLOAD_FOLDER = '/tmp/test_uploads'
    WTF_CSRF_ENABLED = False


class ComponentDeletionDatabaseIntegrationTestCase(unittest.TestCase):
    """Integration test cases for component deletion database operations"""

    def setUp(self):
        """Set up test environment"""
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Don't create/drop tables - use existing schema
        # Just get or create test data entities
        
        # Get or create component type
        self.component_type = ComponentType.query.filter_by(name='Integration Test Type').first()
        if not self.component_type:
            self.component_type = ComponentType(name='Integration Test Type')
            db.session.add(self.component_type)
        
        # Get or create supplier
        self.supplier = Supplier.query.filter_by(supplier_code='INTTEST').first()
        if not self.supplier:
            self.supplier = Supplier(supplier_code='INTTEST', address='Integration Test Address')
            db.session.add(self.supplier)
        
        # Get or create brand
        self.brand = Brand.query.filter_by(name='Integration Test Brand').first()
        if not self.brand:
            self.brand = Brand(name='Integration Test Brand')
            db.session.add(self.brand)
        
        # Get or create color
        self.color = Color.query.filter_by(name='Integration Red').first()
        if not self.color:
            self.color = Color(name='Integration Red')
            db.session.add(self.color)
        
        # Get or create keyword
        self.keyword = Keyword.query.filter_by(name='integration-test').first()
        if not self.keyword:
            self.keyword = Keyword(name='integration-test')
            db.session.add(self.keyword)
        
        db.session.flush()
        db.session.commit()
        
        # Create test upload directory
        self.test_upload_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test environment"""
        db.session.remove()
        # Don't drop tables - we don't have owner privileges
        self.app_context.pop()
        
        # Clean up test upload directory
        import shutil
        if os.path.exists(self.test_upload_dir):
            shutil.rmtree(self.test_upload_dir)

    def _create_complex_component(self):
        """Create a complex component with all possible associations"""
        unique_suffix = int(time.time() * 1000) % 10000
        product_number = f'COMPLEX_INT_{unique_suffix}'
        
        # Create component
        component = Component(
            product_number=product_number,
            description=f'Complex Integration Test Component {unique_suffix}',
            component_type_id=self.component_type.id,
            supplier_id=self.supplier.id
        )
        db.session.add(component)
        db.session.flush()
        
        # Add variant
        variant = ComponentVariant(
            component_id=component.id,
            color_id=self.color.id,
            variant_name=f'Red Variant {unique_suffix}'
        )
        db.session.add(variant)
        db.session.flush()
        
        # Add pictures (component and variant)
        component_picture = Picture(
            component_id=component.id,
            variant_id=None,
            picture_name=f'{product_number}_main_1',
            url=f'http://test-webdav/components/{product_number}_main_1.jpg',
            picture_order=1
        )
        db.session.add(component_picture)
        
        variant_picture = Picture(
            component_id=component.id,
            variant_id=variant.id,
            picture_name=f'{product_number}_red_1',
            url=f'http://test-webdav/components/{product_number}_red_1.jpg',
            picture_order=1
        )
        db.session.add(variant_picture)
        
        # Add brand association
        brand_association = ComponentBrand(
            component_id=component.id,
            brand_id=self.brand.id
        )
        db.session.add(brand_association)
        
        # Add keyword association
        keyword_association = text(
            "INSERT INTO component_app.keyword_component (component_id, keyword_id) VALUES (:component_id, :keyword_id)"
        )
        db.session.execute(keyword_association, {'component_id': component.id, 'keyword_id': self.keyword.id})
        
        db.session.flush()
        db.session.commit()
        
        return {
            'component': component,
            'variant': variant,
            'component_picture': component_picture,
            'variant_picture': variant_picture,
            'brand_association': brand_association
        }

    def test_database_cascade_deletion_variants(self):
        """Test that variants are properly cascade deleted"""
        # Create component with variant
        test_data = self._create_complex_component()
        component = test_data['component']
        variant = test_data['variant']
        component_id = component.id
        variant_id = variant.id
        
        # Verify variant exists
        self.assertIsNotNone(ComponentVariant.query.get(variant_id))
        
        # Delete component
        result = ComponentService.delete_component(component_id)
        
        # Verify component is deleted
        self.assertIsNone(Component.query.get(component_id))
        
        # Verify variant is cascade deleted
        self.assertIsNone(ComponentVariant.query.get(variant_id))
        
        # Verify result summary
        self.assertTrue(result['success'])
        self.assertEqual(result['summary']['associations_deleted']['variants'], 1)

    def test_database_cascade_deletion_pictures(self):
        """Test that pictures are properly cascade deleted"""
        # Create component with pictures
        test_data = self._create_complex_component()
        component = test_data['component']
        component_picture = test_data['component_picture']
        variant_picture = test_data['variant_picture']
        component_id = component.id
        
        # Verify pictures exist
        self.assertIsNotNone(Picture.query.get(component_picture.id))
        self.assertIsNotNone(Picture.query.get(variant_picture.id))
        
        # Delete component
        result = ComponentService.delete_component(component_id)
        
        # Verify component is deleted
        self.assertIsNone(Component.query.get(component_id))
        
        # Verify pictures are cascade deleted
        self.assertIsNone(Picture.query.get(component_picture.id))
        self.assertIsNone(Picture.query.get(variant_picture.id))
        
        # Verify result summary
        self.assertTrue(result['success'])
        self.assertEqual(result['summary']['associations_deleted']['pictures'], 2)

    def test_database_cascade_deletion_brand_associations(self):
        """Test that brand associations are properly cascade deleted"""
        # Create component with brand association
        test_data = self._create_complex_component()
        component = test_data['component']
        brand_association = test_data['brand_association']
        component_id = component.id
        brand_association_id = brand_association.id
        
        # Verify brand association exists
        self.assertIsNotNone(ComponentBrand.query.get(brand_association_id))
        
        # Delete component
        result = ComponentService.delete_component(component_id)
        
        # Verify component is deleted
        self.assertIsNone(Component.query.get(component_id))
        
        # Verify brand association is cascade deleted
        self.assertIsNone(ComponentBrand.query.get(brand_association_id))
        
        # Verify brand itself still exists (should not be deleted)
        self.assertIsNotNone(Brand.query.get(self.brand.id))
        
        # Verify result summary
        self.assertTrue(result['success'])
        self.assertEqual(result['summary']['associations_deleted']['brands'], 1)

    def test_database_manual_deletion_keyword_associations(self):
        """Test that keyword associations are properly deleted (many-to-many)"""
        # Create component with keyword association
        test_data = self._create_complex_component()
        component = test_data['component']
        component_id = component.id
        
        # Verify keyword association exists
        association_count = db.session.execute(
            text("SELECT COUNT(*) FROM component_app.keyword_component WHERE component_id = :component_id"),
            {'component_id': component_id}
        ).scalar()
        self.assertEqual(association_count, 1)
        
        # Delete component
        result = ComponentService.delete_component(component_id)
        
        # Verify component is deleted
        self.assertIsNone(Component.query.get(component_id))
        
        # Verify keyword association is deleted
        association_count_after = db.session.execute(
            text("SELECT COUNT(*) FROM component_app.keyword_component WHERE component_id = :component_id"),
            {'component_id': component_id}
        ).scalar()
        self.assertEqual(association_count_after, 0)
        
        # Verify keyword itself still exists (should not be deleted)
        self.assertIsNotNone(Keyword.query.get(self.keyword.id))

    def test_database_transaction_integrity(self):
        """Test that deletion operations are transactionally safe"""
        # Create component
        test_data = self._create_complex_component()
        component = test_data['component']
        variant = test_data['variant']
        component_id = component.id
        variant_id = variant.id
        
        # Verify initial state
        self.assertIsNotNone(Component.query.get(component_id))
        self.assertIsNotNone(ComponentVariant.query.get(variant_id))
        
        # Test successful deletion
        result = ComponentService.delete_component(component_id)
        self.assertTrue(result['success'])
        
        # Verify all data is gone
        self.assertIsNone(Component.query.get(component_id))
        self.assertIsNone(ComponentVariant.query.get(variant_id))

    def test_database_foreign_key_integrity(self):
        """Test that foreign key constraints are respected"""
        # Create component
        test_data = self._create_complex_component()
        component = test_data['component']
        component_id = component.id
        
        # Verify referenced entities still exist after component deletion
        supplier_id = self.supplier.id
        component_type_id = self.component_type.id
        brand_id = self.brand.id
        color_id = self.color.id
        
        # Delete component
        result = ComponentService.delete_component(component_id)
        self.assertTrue(result['success'])
        
        # Verify referenced entities are NOT deleted (foreign key integrity)
        self.assertIsNotNone(Supplier.query.get(supplier_id))
        self.assertIsNotNone(ComponentType.query.get(component_type_id))
        self.assertIsNotNone(Brand.query.get(brand_id))
        self.assertIsNotNone(Color.query.get(color_id))

    def test_database_deletion_with_orphaned_references(self):
        """Test deletion when some references are missing"""
        # Create component
        unique_suffix = int(time.time() * 1000) % 10000
        component = Component(
            product_number=f'ORPHAN_TEST_{unique_suffix}',
            description='Test Component with Orphaned References',
            component_type_id=self.component_type.id,
            supplier_id=None  # No supplier reference
        )
        db.session.add(component)
        db.session.flush()
        component_id = component.id
        db.session.commit()
        
        # Delete component (should handle missing references gracefully)
        result = ComponentService.delete_component(component_id)
        
        # Verify successful deletion despite missing references
        self.assertTrue(result['success'])
        self.assertIsNone(Component.query.get(component_id))

    def test_database_concurrent_deletion_safety(self):
        """Test deletion safety under concurrent access scenarios"""
        # Create component
        test_data = self._create_complex_component()
        component = test_data['component']
        component_id = component.id
        
        # Simulate concurrent modification by manually changing data
        # This tests if the deletion handles concurrent data changes gracefully
        
        # Manually delete a variant to simulate concurrent modification
        variant_id = test_data['variant'].id
        db.session.delete(ComponentVariant.query.get(variant_id))
        db.session.commit()
        
        # Now delete the component (should handle missing variant gracefully)
        result = ComponentService.delete_component(component_id)
        
        # Verify successful deletion despite concurrent changes
        self.assertTrue(result['success'])
        self.assertIsNone(Component.query.get(component_id))

    def test_database_complex_association_cleanup(self):
        """Test comprehensive cleanup of all association types"""
        # Create component with maximum associations
        test_data = self._create_complex_component()
        component = test_data['component']
        component_id = component.id
        
        # Add additional associations for comprehensive testing
        
        # Add second variant with different color
        color2 = Color(name='Integration Blue')
        db.session.add(color2)
        db.session.flush()
        
        variant2 = ComponentVariant(
            component_id=component_id,
            color_id=color2.id,
            variant_name='Blue Variant'
        )
        db.session.add(variant2)
        db.session.flush()
        
        # Add additional pictures for second variant
        picture2 = Picture(
            component_id=component_id,
            variant_id=variant2.id,
            picture_name=f'{component.product_number}_blue_1',
            url=f'http://test-webdav/components/{component.product_number}_blue_1.jpg',
            picture_order=1
        )
        db.session.add(picture2)
        
        # Add second brand association
        brand2 = Brand(name='Integration Brand 2')
        db.session.add(brand2)
        db.session.flush()
        
        brand_association2 = ComponentBrand(
            component_id=component_id,
            brand_id=brand2.id
        )
        db.session.add(brand_association2)
        
        # Add second keyword association
        keyword2 = Keyword(name='integration-test-2')
        db.session.add(keyword2)
        db.session.flush()
        
        keyword_association2 = text(
            "INSERT INTO component_app.keyword_component (component_id, keyword_id) VALUES (:component_id, :keyword_id)"
        )
        db.session.execute(keyword_association2, {'component_id': component_id, 'keyword_id': keyword2.id})
        
        db.session.commit()
        
        # Count associations before deletion
        variants_before = ComponentVariant.query.filter_by(component_id=component_id).count()
        pictures_before = Picture.query.filter_by(component_id=component_id).count()
        brands_before = ComponentBrand.query.filter_by(component_id=component_id).count()
        keywords_before = db.session.execute(
            text("SELECT COUNT(*) FROM component_app.keyword_component WHERE component_id = :component_id"),
            {'component_id': component_id}
        ).scalar()
        
        # Verify expected counts
        self.assertEqual(variants_before, 2)
        self.assertEqual(pictures_before, 3)  # 1 component + 2 variant pictures
        self.assertEqual(brands_before, 2)
        self.assertEqual(keywords_before, 2)
        
        # Delete component
        result = ComponentService.delete_component(component_id)
        
        # Verify successful deletion
        self.assertTrue(result['success'])
        self.assertIsNone(Component.query.get(component_id))
        
        # Verify all associations are cleaned up
        variants_after = ComponentVariant.query.filter_by(component_id=component_id).count()
        pictures_after = Picture.query.filter_by(component_id=component_id).count()
        brands_after = ComponentBrand.query.filter_by(component_id=component_id).count()
        keywords_after = db.session.execute(
            text("SELECT COUNT(*) FROM component_app.keyword_component WHERE component_id = :component_id"),
            {'component_id': component_id}
        ).scalar()
        
        self.assertEqual(variants_after, 0)
        self.assertEqual(pictures_after, 0)
        self.assertEqual(brands_after, 0)
        self.assertEqual(keywords_after, 0)
        
        # Verify summary in result
        summary = result['summary']
        self.assertEqual(summary['associations_deleted']['variants'], 2)
        self.assertEqual(summary['associations_deleted']['pictures'], 3)
        self.assertEqual(summary['associations_deleted']['brands'], 2)


if __name__ == '__main__':
    unittest.main()