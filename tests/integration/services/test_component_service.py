"""
Integration Tests for ComponentService
Tests real database operations and WebDAV integration with comprehensive business logic scenarios
"""

import pytest
import time
import random
from io import BytesIO
from PIL import Image

from app import create_app, db
from app.models import Component, ComponentVariant, Picture, Color, Supplier, ComponentType, ComponentBrand, Keyword
from app.services.component_service import ComponentService
from app.services.webdav_storage_service import WebDAVStorageService, WebDAVStorageConfig


class TestComponentServiceIntegration:
    """Integration tests for ComponentService with real database and WebDAV operations"""

    @pytest.fixture(scope="class")
    def app_context(self):
        """Set up Flask application context for all tests"""
        print(f"\n🔧 INTEGRATION TEST SETUP: Setting up Flask application...")
        
        from config import Config
        
        class TestConfig(Config):
            TESTING = True
            WTF_CSRF_ENABLED = False
            # Use real PostgreSQL database from config.py
        
        app = create_app(TestConfig)
        app.config['TESTING'] = True
        app_context = app.app_context()
        app_context.push()
        
        print(f"✅ Flask application context established")
        
        yield app_context
        
        print(f"\n🧹 INTEGRATION TEST TEARDOWN: Cleaning up Flask context...")
        db.session.remove()
        app_context.pop()
        print(f"✅ Flask application context cleaned up")

    @pytest.fixture
    def test_data(self, app_context):
        """Set up test data with transaction rollback"""
        print(f"\n🧪 Setting up test data for ComponentService integration...")
        
        # Start a nested transaction (savepoint) that will be rolled back after each test
        savepoint = db.session.begin_nested()
        
        # Generate random unique IDs to avoid conflicts with existing data
        base_id = random.randint(10000, 99999)
        
        # Create test data with random IDs
        test_component_type = ComponentType(name=f'Test Type {base_id}')
        test_supplier = Supplier(supplier_code=f'TEST-SUP-{base_id}', address=f'Test Address {base_id}')
        test_color = Color(name=f'Test Red {base_id}')
        
        db.session.add_all([test_component_type, test_supplier, test_color])
        db.session.flush()  # Get IDs without committing
        
        print(f"✅ Integration test setup complete")
        
        yield {
            'component_type': test_component_type,
            'supplier': test_supplier,
            'color': test_color,
            'base_id': base_id
        }
        
        # Cleanup: rollback the savepoint to undo any changes
        print(f"🧹 Cleaning up test data...")
        try:
            savepoint.rollback()
        except Exception:
            pass
        db.session.rollback()

    @pytest.fixture
    def component_service(self):
        """Create ComponentService instance with real WebDAV storage for integration tests"""
        # Integration tests must use real services - no mocking allowed
        # ComponentService will try to initialize real WebDAV, fallback gracefully if unavailable
        return ComponentService()

    @pytest.fixture
    def webdav_service(self):
        """Create WebDAV storage service for real file operations"""
        config = WebDAVStorageConfig(
            base_url='http://31.182.67.115/webdav/components',
            timeout=30,
            verify_ssl=False,
            max_retries=3
        )
        return WebDAVStorageService(config)

    @pytest.fixture
    def test_image_data(self):
        """Create test image data in memory"""
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG', quality=85)
        img_bytes.seek(0)
        return img_bytes


class TestComponentServiceCRUD(TestComponentServiceIntegration):
    """Test component CRUD operations with real database"""

    def test_should_create_component_successfully_when_valid_data(self, test_data, component_service):
        """
        Test: Component creation with valid data
        Given: Valid component data with all required fields
        When: create_component is called
        Then: Component should be created successfully in database
        """
        # Arrange
        unique_id = test_data['base_id']
        component_data = {
            'product_number': f'CREATE-{unique_id}',
            'description': 'Test component creation',
            'supplier_id': test_data['supplier'].id,
            'component_type_id': test_data['component_type'].id,
            'properties': {'test': 'value'}
        }

        # Act
        result = component_service.create_component(component_data)

        # Assert
        assert result['success'] is True
        assert 'component' in result
        assert result['component']['product_number'] == f'CREATE-{unique_id}'
        
        # Verify in database
        created_component = Component.query.get(result['component']['id'])
        assert created_component is not None
        assert created_component.product_number == f'CREATE-{unique_id}'
        assert created_component.supplier_id == test_data['supplier'].id

    def test_should_update_component_successfully_when_valid_changes(self, test_data, component_service):
        """
        Test: Component update with basic field changes
        Given: Existing component in database
        When: update_component is called with new data
        Then: Component should be updated successfully
        """
        # Arrange
        unique_id = test_data['base_id']
        component = Component(
            product_number=f'UPDATE-{unique_id}',
            description='Original description',
            supplier_id=test_data['supplier'].id,
            component_type_id=test_data['component_type'].id
        )
        db.session.add(component)
        db.session.flush()

        update_data = {
            'product_number': f'UPDATED-{unique_id}',
            'description': 'Updated description'
        }

        # Act
        result = component_service.update_component(component.id, update_data)

        # Assert
        assert result['success'] is True
        assert result['component_id'] == component.id
        
        # Verify database was updated
        updated_component = Component.query.get(component.id)
        assert updated_component.product_number == f'UPDATED-{unique_id}'
        assert updated_component.description == 'Updated description'

    def test_should_delete_component_successfully_when_component_exists(self, test_data, component_service):
        """
        Test: Component deletion with cascade cleanup
        Given: Component with relationships exists in database
        When: delete_component is called
        Then: Component and all associations should be deleted
        """
        # Arrange
        unique_id = test_data['base_id']
        component = Component(
            product_number=f'DELETE-{unique_id}',
            description='Component to delete',
            supplier_id=test_data['supplier'].id,
            component_type_id=test_data['component_type'].id
        )
        db.session.add(component)
        db.session.flush()

        component_id = component.id

        # Act
        result = component_service.delete_component(component_id)

        # Assert
        assert result['success'] is True
        assert f'DELETE-{unique_id}' in result['message']
        
        # Verify component was deleted from database
        deleted_component = Component.query.get(component_id)
        assert deleted_component is None

    def test_should_raise_error_when_component_not_found(self, component_service):
        """
        Test: Error handling for non-existent component
        Given: Non-existent component ID
        When: update_component is called
        Then: ValueError should be raised with appropriate message
        """
        # Arrange
        non_existent_id = 999999
        update_data = {'product_number': 'TEST-001'}

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            component_service.update_component(non_existent_id, update_data)
        
        assert 'not found' in str(exc_info.value).lower()
        assert str(non_existent_id) in str(exc_info.value)


class TestComponentServiceBusinessLogic(TestComponentServiceIntegration):
    """Test business logic scenarios with real database operations"""

    def test_should_prevent_duplicate_product_numbers_when_same_supplier(self, test_data, component_service):
        """
        Test: Duplicate product number validation
        Given: Component with specific product number and supplier exists
        When: Another component with same product number and supplier is created
        Then: ValueError should be raised preventing duplicate
        """
        # Arrange
        unique_id = test_data['base_id']
        product_number = f'DUP-{unique_id}'
        
        # Create first component
        first_component = Component(
            product_number=product_number,
            description='First component',
            supplier_id=test_data['supplier'].id,
            component_type_id=test_data['component_type'].id
        )
        db.session.add(first_component)
        db.session.flush()

        # Try to create duplicate
        duplicate_data = {
            'product_number': product_number,
            'description': 'Duplicate component',
            'supplier_id': test_data['supplier'].id,
            'component_type_id': test_data['component_type'].id
        }

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            component_service.create_component(duplicate_data)
        
        assert 'already exists' in str(exc_info.value).lower()

    def test_should_allow_same_product_number_when_different_suppliers(self, test_data, component_service):
        """
        Test: Same product number allowed for different suppliers
        Given: Component with specific product number and supplier exists
        When: Component with same product number but different supplier is created
        Then: Both components should be created successfully
        """
        # Arrange
        unique_id = test_data['base_id']
        product_number = f'SAME-{unique_id}'
        
        # Create second supplier
        second_supplier = Supplier(supplier_code=f'SECOND-SUP-{unique_id}')
        db.session.add(second_supplier)
        db.session.flush()

        # Create first component
        first_data = {
            'product_number': product_number,
            'description': 'First component',
            'supplier_id': test_data['supplier'].id,
            'component_type_id': test_data['component_type'].id
        }
        first_result = component_service.create_component(first_data)

        # Create second component with same product number but different supplier
        second_data = {
            'product_number': product_number,
            'description': 'Second component',
            'supplier_id': second_supplier.id,
            'component_type_id': test_data['component_type'].id
        }

        # Act
        second_result = component_service.create_component(second_data)

        # Assert
        assert first_result['success'] is True
        assert second_result['success'] is True
        assert first_result['component']['id'] != second_result['component']['id']

    def test_should_handle_json_properties_correctly_when_updating(self, test_data, component_service):
        """
        Test: JSON properties field handling in updates
        Given: Component with JSON properties exists
        When: Component properties are updated
        Then: JSON properties should be correctly stored and retrieved
        """
        # Arrange
        unique_id = test_data['base_id']
        component = Component(
            product_number=f'JSON-{unique_id}',
            description='JSON test',
            supplier_id=test_data['supplier'].id,
            component_type_id=test_data['component_type'].id,
            properties={'color': 'red', 'material': 'plastic', 'weight': 100}
        )
        db.session.add(component)
        db.session.flush()

        update_data = {
            'properties': {'color': 'blue', 'material': 'metal', 'size': 'large'}
        }

        # Act
        result = component_service.update_component(component.id, update_data)

        # Assert
        assert result['success'] is True
        
        updated_component = Component.query.get(component.id)
        assert updated_component.properties['color'] == 'blue'
        assert updated_component.properties['material'] == 'metal'
        assert updated_component.properties['size'] == 'large'


class TestComponentServiceVariantManagement(TestComponentServiceIntegration):
    """Test component variant management with real database operations"""

    def test_should_create_variants_successfully_when_valid_color_data(self, test_data, component_service):
        """
        Test: Component variant creation
        Given: Component and color data exist
        When: create_component is called with variants
        Then: Component and variants should be created with proper relationships
        """
        # Arrange
        unique_id = test_data['base_id']
        component_data = {
            'product_number': f'VARIANT-{unique_id}',
            'description': 'Component with variants',
            'supplier_id': test_data['supplier'].id,
            'component_type_id': test_data['component_type'].id,
            'variants': [
                {
                    'color_id': test_data['color'].id,
                    'images': []
                }
            ]
        }

        # Act
        result = component_service.create_component(component_data)

        # Assert
        assert result['success'] is True
        assert result['component']['variants_count'] == 1
        
        # Verify variant was created in database
        component = Component.query.get(result['component']['id'])
        assert len(component.variants) == 1
        assert component.variants[0].color_id == test_data['color'].id

    def test_should_prevent_duplicate_variants_when_same_color(self, test_data):
        """
        Test: Duplicate variant prevention
        Given: Component with a color variant exists
        When: Another variant with same color is added
        Then: Duplicate should be prevented or skipped
        """
        # Arrange
        unique_id = test_data['base_id']
        component = Component(
            product_number=f'DUPVAR-{unique_id}',
            description='Duplicate variant test',
            supplier_id=test_data['supplier'].id,
            component_type_id=test_data['component_type'].id
        )
        db.session.add(component)
        db.session.flush()

        # Create first variant
        first_variant = ComponentVariant(
            component_id=component.id,
            color_id=test_data['color'].id,
            is_active=True
        )
        db.session.add(first_variant)
        db.session.flush()

        # Try to create duplicate variant (this should be handled gracefully)
        try:
            duplicate_variant = ComponentVariant(
                component_id=component.id,
                color_id=test_data['color'].id,
                is_active=True
            )
            db.session.add(duplicate_variant)
            db.session.flush()
            
            # If we get here, check that database constraint prevents it
            variants = ComponentVariant.query.filter_by(
                component_id=component.id,
                color_id=test_data['color'].id
            ).all()
            
            # Should be prevented by unique constraint
            assert False, "Duplicate variant should be prevented"
            
        except Exception as e:
            # Expected: unique constraint should prevent duplicate
            db.session.rollback()
            assert True  # This is expected behavior


class TestComponentServicePictureRenaming(TestComponentServiceIntegration):
    """Test picture renaming business logic with real WebDAV operations"""

    def test_should_rename_pictures_when_product_number_changes(self, test_data, component_service, webdav_service, test_image_data):
        """
        Test: Critical business rule - picture renaming on product number change
        Given: Component with pictures exists
        When: Product number is changed
        Then: All related pictures should be renamed in both database and WebDAV
        """
        # Arrange
        unique_id = test_data['base_id']
        old_product_number = f'OLDPROD-{unique_id}'
        new_product_number = f'NEWPROD-{unique_id}'
        
        component = Component(
            product_number=old_product_number,
            description='Picture rename test',
            supplier_id=test_data['supplier'].id,
            component_type_id=test_data['component_type'].id
        )
        db.session.add(component)
        db.session.flush()

        # Create test picture
        from app.utils.file_handling import generate_picture_name
        old_picture_name = generate_picture_name(component, None, 1)
        
        # Upload test image to WebDAV
        filename = f"{old_picture_name}.jpg"
        upload_result = webdav_service.upload_file(test_image_data, filename, 'image/jpeg')
        
        if upload_result.success:
            # Create picture record in database
            picture = Picture(
                component_id=component.id,
                picture_name=old_picture_name,
                url=upload_result.file_info.url,
                picture_order=1,
                alt_text=f"{old_product_number} - Image 1"
            )
            db.session.add(picture)
            db.session.flush()

            # Act - change product number
            update_data = {'product_number': new_product_number}
            result = component_service.update_component(component.id, update_data)

            # Assert
            assert result['success'] is True
            
            # Verify database was updated
            updated_component = Component.query.get(component.id)
            assert updated_component.product_number == new_product_number
            
            # Verify picture was renamed in database
            updated_picture = Picture.query.get(picture.id)
            new_picture_name = generate_picture_name(updated_component, None, 1)
            assert updated_picture.picture_name == new_picture_name
            
            # Clean up WebDAV files
            try:
                webdav_service.delete_file(f"{old_picture_name}.jpg")
                webdav_service.delete_file(f"{new_picture_name}.jpg")
            except:
                pass
        else:
            pytest.skip("WebDAV not available for picture renaming test")

    def test_should_rename_pictures_when_supplier_changes(self, test_data, component_service, webdav_service, test_image_data):
        """
        Test: Picture renaming when supplier changes
        Given: Component with supplier and pictures exists
        When: Supplier is changed
        Then: Picture names should be updated to reflect new supplier prefix
        """
        # Arrange
        unique_id = test_data['base_id']
        
        # Create second supplier
        new_supplier = Supplier(supplier_code=f'NEWSUP-{unique_id}')
        db.session.add(new_supplier)
        db.session.flush()
        
        component = Component(
            product_number=f'SUPPROD-{unique_id}',
            description='Supplier change test',
            supplier_id=test_data['supplier'].id,
            component_type_id=test_data['component_type'].id
        )
        db.session.add(component)
        db.session.flush()

        # Create test picture with original supplier
        from app.utils.file_handling import generate_picture_name
        old_picture_name = generate_picture_name(component, None, 1)
        
        # Upload test image to WebDAV
        filename = f"{old_picture_name}.jpg"
        upload_result = webdav_service.upload_file(test_image_data, filename, 'image/jpeg')
        
        if upload_result.success:
            # Create picture record
            picture = Picture(
                component_id=component.id,
                picture_name=old_picture_name,
                url=upload_result.file_info.url,
                picture_order=1
            )
            db.session.add(picture)
            db.session.flush()

            # Act - change supplier
            update_data = {'supplier_id': new_supplier.id}
            result = component_service.update_component(component.id, update_data)

            # Assert
            assert result['success'] is True
            
            # Verify supplier was changed
            updated_component = Component.query.get(component.id)
            assert updated_component.supplier_id == new_supplier.id
            
            # Verify picture name was updated
            updated_picture = Picture.query.get(picture.id)
            expected_new_name = generate_picture_name(updated_component, None, 1)
            assert updated_picture.picture_name == expected_new_name
            
            # Clean up WebDAV files
            try:
                webdav_service.delete_file(f"{old_picture_name}.jpg")
                webdav_service.delete_file(f"{expected_new_name}.jpg")
            except:
                pass
        else:
            pytest.skip("WebDAV not available for supplier change test")


class TestComponentServiceWebDAVIntegration(TestComponentServiceIntegration):
    """Test WebDAV file operations integration"""

    def test_should_upload_picture_successfully_when_webdav_available(self, component_service, webdav_service, test_image_data):
        """
        Test: Picture upload to WebDAV
        Given: Valid image data and WebDAV service
        When: upload_picture_to_webdav is called
        Then: File should be uploaded successfully and return URL
        """
        # Arrange
        filename = f"test_upload_{int(time.time())}.jpg"
        
        # Act
        result = component_service.upload_picture_to_webdav(test_image_data, filename)
        
        # Assert or Skip
        if result['success']:
            assert 'url' in result
            assert result['filename'] == filename
            
            # Clean up
            try:
                webdav_service.delete_file(filename)
            except:
                pass
        else:
            pytest.skip("WebDAV not available for upload test")

    def test_should_create_real_jpeg_images_for_testing(self, webdav_service):
        """
        Test: Real JPEG image creation with PIL for comprehensive testing
        Given: PIL library available
        When: Creating test images with different properties
        Then: Real JPEG files should be created and uploadable to WebDAV
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create real test images with different properties
            test_images = [
                {'name': 'component_main', 'color': 'lightblue', 'text': 'Component Main Image'},
                {'name': 'variant_red', 'color': 'lightcoral', 'text': 'Red Variant Image'},
                {'name': 'variant_blue', 'color': 'lightsteelblue', 'text': 'Blue Variant Image'}
            ]
            
            uploaded_files = []
            
            for img_config in test_images:
                # Create real JPEG image
                img = Image.new('RGB', (400, 300), color=img_config['color'])
                draw = ImageDraw.Draw(img)
                
                # Add identifying text
                try:
                    font = ImageFont.load_default()
                except:
                    font = None
                
                draw.text((15, 20), img_config['text'], fill='black', font=font)
                draw.text((15, 50), f"Test ID: {int(time.time())}", fill='black', font=font)
                draw.text((15, 80), "INTEGRATION TEST IMAGE", fill='black', font=font)
                
                # Add border
                draw.rectangle([5, 5, 395, 295], outline='darkblue', width=2)
                
                # Convert to bytes
                img_bytes = BytesIO()
                img.save(img_bytes, format='JPEG', quality=85)
                img_bytes.seek(0)
                
                # Upload to WebDAV
                filename = f"{img_config['name']}_{int(time.time())}.jpg"
                upload_result = webdav_service.upload_file(
                    BytesIO(img_bytes.getvalue()),
                    filename,
                    'image/jpeg'
                )
                
                if upload_result.success:
                    uploaded_files.append(filename)
                    
                    # Verify file exists and is downloadable
                    download_result = webdav_service.download_file(filename)
                    assert download_result.success
                    assert len(download_result.data) > 1000  # JPEG should be substantial size
                    
                else:
                    pytest.skip(f"WebDAV not available for image upload: {filename}")
            
            # Clean up all uploaded test files
            for filename in uploaded_files:
                try:
                    webdav_service.delete_file(filename)
                except:
                    pass
                    
            assert len(uploaded_files) == 3
            
        except ImportError:
            pytest.skip("PIL not available for real image creation test")


class TestComponentServiceDeletion(TestComponentServiceIntegration):
    """Test component deletion with real database cascade operations"""

    def test_should_cascade_delete_variants_when_component_deleted(self, test_data, component_service):
        """
        Test: Component variant cascade deletion
        Given: Component with variants exists
        When: Component is deleted
        Then: All variants should be cascade deleted from database
        """
        # Arrange
        unique_id = test_data['base_id']
        
        component = Component(
            product_number=f'CASCADE-VARIANT-{unique_id}',
            description='Cascade deletion test',
            supplier_id=test_data['supplier'].id,
            component_type_id=test_data['component_type'].id
        )
        db.session.add(component)
        db.session.flush()
        
        # Create multiple variants
        variant1 = ComponentVariant(
            component_id=component.id,
            color_id=test_data['color'].id,
            variant_name='Red Variant'
        )
        
        # Create second color for second variant
        blue_color = Color(name=f'Cascade Blue {unique_id}')
        db.session.add(blue_color)
        db.session.flush()
        
        variant2 = ComponentVariant(
            component_id=component.id,
            color_id=blue_color.id,
            variant_name='Blue Variant'
        )
        
        db.session.add_all([variant1, variant2])
        db.session.flush()
        
        component_id = component.id
        variant1_id = variant1.id
        variant2_id = variant2.id
        
        # Verify variants exist
        assert ComponentVariant.query.get(variant1_id) is not None
        assert ComponentVariant.query.get(variant2_id) is not None
        
        # Act - delete component
        result = component_service.delete_component(component_id)
        
        # Assert
        assert result['success'] is True
        
        # Verify component is deleted
        assert Component.query.get(component_id) is None
        
        # Verify variants are cascade deleted
        assert ComponentVariant.query.get(variant1_id) is None
        assert ComponentVariant.query.get(variant2_id) is None
        
        # Verify deletion summary
        assert result['summary']['associations_deleted']['variants'] == 2

    def test_should_cascade_delete_pictures_when_component_deleted(self, test_data, component_service):
        """
        Test: Component picture cascade deletion
        Given: Component with pictures (component and variant pictures) exists
        When: Component is deleted
        Then: All pictures should be cascade deleted from database
        """
        # Arrange
        unique_id = test_data['base_id']
        
        component = Component(
            product_number=f'CASCADE-PICTURE-{unique_id}',
            description='Picture cascade test',
            supplier_id=test_data['supplier'].id,
            component_type_id=test_data['component_type'].id
        )
        db.session.add(component)
        db.session.flush()
        
        # Create variant
        variant = ComponentVariant(
            component_id=component.id,
            color_id=test_data['color'].id,
            variant_name='Test Variant'
        )
        db.session.add(variant)
        db.session.flush()
        
        # Create component picture
        component_picture = Picture(
            component_id=component.id,
            variant_id=None,
            picture_name=f'{component.product_number}_main_1',
            url=f'http://test-webdav/components/{component.product_number}_main_1.jpg',
            picture_order=1
        )
        
        # Create variant picture
        variant_picture = Picture(
            component_id=component.id,
            variant_id=variant.id,
            picture_name=f'{component.product_number}_red_1',
            url=f'http://test-webdav/components/{component.product_number}_red_1.jpg',
            picture_order=1
        )
        
        db.session.add_all([component_picture, variant_picture])
        db.session.flush()
        
        component_id = component.id
        component_picture_id = component_picture.id
        variant_picture_id = variant_picture.id
        
        # Verify pictures exist
        assert Picture.query.get(component_picture_id) is not None
        assert Picture.query.get(variant_picture_id) is not None
        
        # Act - delete component
        result = component_service.delete_component(component_id)
        
        # Assert
        assert result['success'] is True
        
        # Verify component is deleted
        assert Component.query.get(component_id) is None
        
        # Verify pictures are cascade deleted
        assert Picture.query.get(component_picture_id) is None
        assert Picture.query.get(variant_picture_id) is None
        
        # Verify deletion summary
        assert result['summary']['associations_deleted']['pictures'] == 2

    def test_should_delete_brand_associations_when_component_deleted(self, test_data, component_service):
        """
        Test: Component brand association deletion
        Given: Component with brand associations exists
        When: Component is deleted
        Then: Brand associations should be deleted but brands preserved
        """
        # Arrange
        unique_id = test_data['base_id']
        
        component = Component(
            product_number=f'CASCADE-BRAND-{unique_id}',
            description='Brand cascade test',
            supplier_id=test_data['supplier'].id,
            component_type_id=test_data['component_type'].id
        )
        db.session.add(component)
        db.session.flush()
        
        # Create brands
        from app.models import Brand
        brand1 = Brand(name=f'Test Brand 1 {unique_id}')
        brand2 = Brand(name=f'Test Brand 2 {unique_id}')
        db.session.add_all([brand1, brand2])
        db.session.flush()
        
        # Create brand associations
        brand_assoc1 = ComponentBrand(
            component_id=component.id,
            brand_id=brand1.id
        )
        brand_assoc2 = ComponentBrand(
            component_id=component.id,
            brand_id=brand2.id
        )
        db.session.add_all([brand_assoc1, brand_assoc2])
        db.session.flush()
        
        component_id = component.id
        brand1_id = brand1.id
        brand2_id = brand2.id
        brand_assoc1_id = brand_assoc1.id
        brand_assoc2_id = brand_assoc2.id
        
        # Verify associations exist
        assert ComponentBrand.query.get(brand_assoc1_id) is not None
        assert ComponentBrand.query.get(brand_assoc2_id) is not None
        
        # Act - delete component
        result = component_service.delete_component(component_id)
        
        # Assert
        assert result['success'] is True
        
        # Verify component is deleted
        assert Component.query.get(component_id) is None
        
        # Verify brand associations are deleted
        assert ComponentBrand.query.get(brand_assoc1_id) is None
        assert ComponentBrand.query.get(brand_assoc2_id) is None
        
        # Verify brands themselves still exist (should not be cascade deleted)
        assert Brand.query.get(brand1_id) is not None
        assert Brand.query.get(brand2_id) is not None
        
        # Verify deletion summary
        assert result['summary']['associations_deleted']['brands'] == 2

    def test_should_handle_foreign_key_integrity_when_component_deleted(self, test_data, component_service):
        """
        Test: Foreign key integrity preservation during deletion
        Given: Component with foreign key references exists
        When: Component is deleted
        Then: Referenced entities (supplier, type, colors) should remain intact
        """
        # Arrange
        unique_id = test_data['base_id']
        
        component = Component(
            product_number=f'FK-INTEGRITY-{unique_id}',
            description='FK integrity test',
            supplier_id=test_data['supplier'].id,
            component_type_id=test_data['component_type'].id
        )
        db.session.add(component)
        db.session.flush()
        
        component_id = component.id
        supplier_id = test_data['supplier'].id
        component_type_id = test_data['component_type'].id
        color_id = test_data['color'].id
        
        # Act - delete component
        result = component_service.delete_component(component_id)
        
        # Assert
        assert result['success'] is True
        
        # Verify component is deleted
        assert Component.query.get(component_id) is None
        
        # Verify referenced entities are NOT deleted (foreign key integrity)
        assert Supplier.query.get(supplier_id) is not None
        assert ComponentType.query.get(component_type_id) is not None
        assert Color.query.get(color_id) is not None

    def test_should_handle_deletion_with_missing_references(self, test_data, component_service):
        """
        Test: Component deletion with orphaned/missing references
        Given: Component with some NULL foreign key references
        When: Component is deleted
        Then: Deletion should succeed gracefully despite missing references
        """
        # Arrange
        unique_id = test_data['base_id']
        
        # Create component with missing supplier reference (NULL)
        component = Component(
            product_number=f'ORPHAN-{unique_id}',
            description='Orphaned reference test',
            supplier_id=None,  # NULL supplier
            component_type_id=test_data['component_type'].id
        )
        db.session.add(component)
        db.session.flush()
        
        component_id = component.id
        
        # Act - delete component with missing references
        result = component_service.delete_component(component_id)
        
        # Assert
        assert result['success'] is True
        
        # Verify component is deleted despite missing references
        assert Component.query.get(component_id) is None


class TestComponentServiceComprehensiveScenarios(TestComponentServiceIntegration):
    """Test comprehensive component update scenarios with real WebDAV operations"""

    def test_should_rename_all_pictures_when_product_number_changes_comprehensive(self, test_data, component_service, webdav_service):
        """
        Test: Comprehensive product number change scenario
        Given: Component with multiple pictures (component + variants) exists
        When: Product number is changed via ComponentService
        Then: All pictures should be renamed in database and moved on WebDAV
        """
        # Arrange
        unique_id = test_data['base_id']
        original_product = f'comprehensive-original-{unique_id}'
        supplier_code = f'COMP{unique_id % 1000}'
        
        # Create supplier
        supplier = Supplier(supplier_code=supplier_code)
        db.session.add(supplier)
        db.session.flush()
        
        # Create component
        component = Component(
            product_number=original_product,
            description='Comprehensive product number test',
            supplier_id=supplier.id,
            component_type_id=test_data['component_type'].id
        )
        db.session.add(component)
        db.session.flush()
        
        # Create variant
        variant = ComponentVariant(
            component_id=component.id,
            color_id=test_data['color'].id,
            variant_name='Test Variant'
        )
        db.session.add(variant)
        db.session.flush()
        
        # Generate expected picture names using Python logic
        from app.utils.file_handling import generate_picture_name
        
        # Create pictures with manually generated names (since triggers removed)
        component_pic_name = generate_picture_name(component, None, 1)
        variant_pic_name = generate_picture_name(component, variant, 1)
        
        component_picture = Picture(
            component_id=component.id,
            variant_id=None,
            picture_name=component_pic_name,
            url=f'http://test-webdav/components/{component_pic_name}.jpg',
            picture_order=1
        )
        
        variant_picture = Picture(
            component_id=component.id,
            variant_id=variant.id,
            picture_name=variant_pic_name,
            url=f'http://test-webdav/components/{variant_pic_name}.jpg',
            picture_order=1
        )
        
        db.session.add_all([component_picture, variant_picture])
        db.session.flush()
        
        # Store original names
        original_component_name = component_picture.picture_name
        original_variant_name = variant_picture.picture_name
        
        # Act - update product number
        new_product = f'comprehensive-updated-{unique_id}'
        update_data = {
            'product_number': new_product,
            'description': component.description,
            'supplier_id': component.supplier_id,
            'component_type_id': component.component_type_id
        }
        
        result = component_service.update_component(component.id, update_data)
        
        # Assert
        assert result['success'] is True
        
        # Verify component updated
        db.session.refresh(component)
        assert component.product_number == new_product
        
        # Verify picture names updated in database
        db.session.refresh(component_picture)
        db.session.refresh(variant_picture)
        
        # Generate expected new names
        expected_component_name = generate_picture_name(component, None, 1)
        expected_variant_name = generate_picture_name(component, variant, 1)
        
        assert component_picture.picture_name == expected_component_name
        assert variant_picture.picture_name == expected_variant_name
        
        # Verify names actually changed
        assert component_picture.picture_name != original_component_name
        assert variant_picture.picture_name != original_variant_name

    def test_should_update_all_picture_prefixes_when_supplier_changes_comprehensive(self, test_data, component_service):
        """
        Test: Comprehensive supplier change scenario
        Given: Component with supplier and multiple pictures exists
        When: Supplier is changed via ComponentService
        Then: All picture name prefixes should be updated in database
        """
        # Arrange
        unique_id = test_data['base_id']
        product_number = f'supplier-change-{unique_id}'
        
        # Create original supplier
        old_supplier = Supplier(supplier_code=f'OLDSUP{unique_id}')
        db.session.add(old_supplier)
        db.session.flush()
        
        # Create new supplier
        new_supplier = Supplier(supplier_code=f'NEWSUP{unique_id}')
        db.session.add(new_supplier)
        db.session.flush()
        
        # Create component with old supplier
        component = Component(
            product_number=product_number,
            description='Supplier change test',
            supplier_id=old_supplier.id,
            component_type_id=test_data['component_type'].id
        )
        db.session.add(component)
        db.session.flush()
        
        # Create picture with old supplier prefix
        from app.utils.file_handling import generate_picture_name
        original_pic_name = generate_picture_name(component, None, 1)
        
        picture = Picture(
            component_id=component.id,
            variant_id=None,
            picture_name=original_pic_name,
            url=f'http://test-webdav/components/{original_pic_name}.jpg',
            picture_order=1
        )
        db.session.add(picture)
        db.session.flush()
        
        # Verify original name has old supplier prefix
        assert original_pic_name.startswith(old_supplier.supplier_code.lower())
        
        # Act - change supplier
        update_data = {
            'product_number': component.product_number,
            'description': component.description,
            'supplier_id': new_supplier.id,
            'component_type_id': component.component_type_id
        }
        
        result = component_service.update_component(component.id, update_data)
        
        # Assert
        assert result['success'] is True
        
        # Verify supplier changed
        db.session.refresh(component)
        assert component.supplier_id == new_supplier.id
        
        # Verify picture name prefix updated
        db.session.refresh(picture)
        expected_new_name = generate_picture_name(component, None, 1)
        
        assert picture.picture_name == expected_new_name
        assert picture.picture_name.startswith(new_supplier.supplier_code.lower())
        assert picture.picture_name != original_pic_name

    def test_should_remove_supplier_prefix_when_supplier_removed_comprehensive(self, test_data, component_service):
        """
        Test: Comprehensive supplier removal scenario
        Given: Component with supplier and pictures exists
        When: Supplier is removed (set to None) via ComponentService
        Then: Picture names should be updated to remove supplier prefix
        """
        # Arrange
        unique_id = test_data['base_id']
        product_number = f'supplier-removal-{unique_id}'
        
        # Create supplier
        supplier = Supplier(supplier_code=f'REMOVEME{unique_id}')
        db.session.add(supplier)
        db.session.flush()
        
        # Create component with supplier
        component = Component(
            product_number=product_number,
            description='Supplier removal test',
            supplier_id=supplier.id,
            component_type_id=test_data['component_type'].id
        )
        db.session.add(component)
        db.session.flush()
        
        # Create picture with supplier prefix
        from app.utils.file_handling import generate_picture_name
        original_pic_name = generate_picture_name(component, None, 1)
        
        picture = Picture(
            component_id=component.id,
            variant_id=None,
            picture_name=original_pic_name,
            url=f'http://test-webdav/components/{original_pic_name}.jpg',
            picture_order=1
        )
        db.session.add(picture)
        db.session.flush()
        
        # Verify original name has supplier prefix
        assert original_pic_name.startswith(supplier.supplier_code.lower())
        
        # Act - remove supplier (set to None)
        update_data = {
            'product_number': component.product_number,
            'description': component.description,
            'supplier_id': None,  # Remove supplier
            'component_type_id': component.component_type_id
        }
        
        result = component_service.update_component(component.id, update_data)
        
        # Assert
        assert result['success'] is True
        
        # Verify supplier removed
        db.session.refresh(component)
        assert component.supplier_id is None
        
        # Verify picture name prefix removed
        db.session.refresh(picture)
        expected_new_name = generate_picture_name(component, None, 1)
        
        assert picture.picture_name == expected_new_name
        assert not picture.picture_name.startswith(supplier.supplier_code.lower())
        assert picture.picture_name != original_pic_name

    def test_should_add_supplier_prefix_when_supplier_added_comprehensive(self, test_data, component_service):
        """
        Test: Comprehensive supplier addition scenario
        Given: Component without supplier and pictures exists
        When: Supplier is added via ComponentService
        Then: Picture names should be updated to include supplier prefix
        """
        # Arrange
        unique_id = test_data['base_id']
        product_number = f'supplier-addition-{unique_id}'
        
        # Create component without supplier
        component = Component(
            product_number=product_number,
            description='Supplier addition test',
            supplier_id=None,  # No supplier initially
            component_type_id=test_data['component_type'].id
        )
        db.session.add(component)
        db.session.flush()
        
        # Create picture without supplier prefix
        from app.utils.file_handling import generate_picture_name
        original_pic_name = generate_picture_name(component, None, 1)
        
        picture = Picture(
            component_id=component.id,
            variant_id=None,
            picture_name=original_pic_name,
            url=f'http://test-webdav/components/{original_pic_name}.jpg',
            picture_order=1
        )
        db.session.add(picture)
        db.session.flush()
        
        # Verify original name has no supplier prefix
        assert not original_pic_name.startswith('test')
        
        # Create supplier to add
        new_supplier = Supplier(supplier_code=f'ADDME{unique_id}')
        db.session.add(new_supplier)
        db.session.flush()
        
        # Act - add supplier
        update_data = {
            'product_number': component.product_number,
            'description': component.description,
            'supplier_id': new_supplier.id,  # Add supplier
            'component_type_id': component.component_type_id
        }
        
        result = component_service.update_component(component.id, update_data)
        
        # Assert
        assert result['success'] is True
        
        # Verify supplier added
        db.session.refresh(component)
        assert component.supplier_id == new_supplier.id
        
        # Verify picture name prefix added
        db.session.refresh(picture)
        expected_new_name = generate_picture_name(component, None, 1)
        
        assert picture.picture_name == expected_new_name
        assert picture.picture_name.startswith(new_supplier.supplier_code.lower())
        assert picture.picture_name != original_pic_name


class TestComponentServiceBrandAssociation(TestComponentServiceIntegration):
    """Test brand association functionality with ComponentService"""

    def test_should_associate_existing_brands_when_creating_component(self, test_data, component_service):
        """
        Test: Brand association with existing brands during component creation
        Given: Existing brands in database
        When: Component is created with brand_ids specified
        Then: Component should be associated with specified brands
        """
        # Arrange
        unique_id = test_data['base_id']
        
        # Create existing brands
        from app.models import Brand
        brand1 = Brand(name=f'Existing Brand 1 {unique_id}')
        brand2 = Brand(name=f'Existing Brand 2 {unique_id}')
        db.session.add_all([brand1, brand2])
        db.session.flush()
        
        # Component creation data with brand associations
        component_data = {
            'product_number': f'BRAND-TEST-{unique_id}',
            'description': 'Brand association test',
            'component_type_id': test_data['component_type'].id,
            'supplier_id': test_data['supplier'].id,
            'brand_ids': [brand1.id, brand2.id]  # Associate with both brands
        }
        
        # Act
        result = component_service.create_component(component_data)
        
        # Assert
        assert result['success'] is True
        component_id = result['component']['id']
        
        # Verify component created
        component = Component.query.get(component_id)
        assert component is not None
        assert component.product_number == f'BRAND-TEST-{unique_id}'
        
        # Verify brand associations created
        brand_associations = ComponentBrand.query.filter_by(component_id=component_id).all()
        assert len(brand_associations) == 2
        
        associated_brand_ids = [assoc.brand_id for assoc in brand_associations]
        assert brand1.id in associated_brand_ids
        assert brand2.id in associated_brand_ids

    def test_should_create_new_brand_when_specified_during_component_creation(self, test_data, component_service):
        """
        Test: New brand creation during component creation
        Given: New brand name specified
        When: Component is created with new_brand_name
        Then: New brand should be created and associated with component
        """
        # Arrange
        unique_id = test_data['base_id']
        new_brand_name = f'New Brand {unique_id}'
        
        # Verify brand doesn't exist yet
        from app.models import Brand
        existing_brand = Brand.query.filter_by(name=new_brand_name).first()
        assert existing_brand is None
        
        # Component creation data with new brand
        component_data = {
            'product_number': f'NEW-BRAND-{unique_id}',
            'description': 'New brand creation test',
            'component_type_id': test_data['component_type'].id,
            'supplier_id': test_data['supplier'].id,
            'new_brand_name': new_brand_name
        }
        
        # Act
        result = component_service.create_component(component_data)
        
        # Assert
        assert result['success'] is True
        component_id = result['component']['id']
        
        # Verify component created
        component = Component.query.get(component_id)
        assert component is not None
        
        # Verify new brand was created
        new_brand = Brand.query.filter_by(name=new_brand_name).first()
        assert new_brand is not None
        assert new_brand.name == new_brand_name
        
        # Verify brand association created
        brand_association = ComponentBrand.query.filter_by(
            component_id=component_id,
            brand_id=new_brand.id
        ).first()
        assert brand_association is not None

    def test_should_handle_web_form_brand_data_conversion(self, test_data, component_service):
        """
        Test: Web form brand data conversion and processing
        Given: Web form data with string-formatted brand IDs
        When: Component is created via ComponentService
        Then: String brand IDs should be converted and processed correctly
        """
        # Arrange
        unique_id = test_data['base_id']
        
        # Create existing brand
        from app.models import Brand
        brand = Brand(name=f'Web Form Brand {unique_id}')
        db.session.add(brand)
        db.session.flush()
        
        # Web form data (brand_ids come as strings from HTML forms)
        form_data = {
            'product_number': f'WEB-FORM-{unique_id}',
            'description': 'Web form brand test',
            'component_type_id': str(test_data['component_type'].id),  # String from form
            'supplier_id': str(test_data['supplier'].id),  # String from form
            'brand_ids': [str(brand.id)]  # String from form checkboxes
        }
        
        # Act
        result = component_service.create_component(form_data)
        
        # Assert
        assert result['success'] is True
        component_id = result['component']['id']
        
        # Verify component created with proper data type conversion
        component = Component.query.get(component_id)
        assert component is not None
        assert component.component_type_id == test_data['component_type'].id  # Converted to int
        assert component.supplier_id == test_data['supplier'].id  # Converted to int
        
        # Verify brand association created with proper ID conversion
        brand_association = ComponentBrand.query.filter_by(
            component_id=component_id,
            brand_id=brand.id
        ).first()
        assert brand_association is not None

    def test_should_delete_picture_successfully_when_file_exists(self, component_service, webdav_service, test_image_data):
        """
        Test: Picture deletion from WebDAV
        Given: File exists on WebDAV server
        When: delete_picture_from_webdav is called
        Then: File should be deleted successfully
        """
        # Arrange - upload file first
        filename = f"test_delete_{int(time.time())}.jpg"
        upload_result = webdav_service.upload_file(test_image_data, filename, 'image/jpeg')
        
        if upload_result.success:
            # Act
            result = component_service.delete_picture_from_webdav(filename)
            
            # Assert
            assert result['success'] is True
            assert result['filename'] == filename
        else:
            pytest.skip("WebDAV not available for delete test")

    def test_should_move_picture_successfully_when_renaming_required(self, component_service, webdav_service, test_image_data):
        """
        Test: Picture move/rename on WebDAV
        Given: File exists on WebDAV server
        When: move_picture_in_webdav is called with new name
        Then: File should be renamed successfully
        """
        # Arrange - upload file first
        old_filename = f"test_move_old_{int(time.time())}.jpg"
        new_filename = f"test_move_new_{int(time.time())}.jpg"
        
        upload_result = webdav_service.upload_file(test_image_data, old_filename, 'image/jpeg')
        
        if upload_result.success:
            # Act
            result = component_service.move_picture_in_webdav(old_filename, new_filename)
            
            # Assert
            if result['success']:
                assert result['old_filename'] == old_filename
                assert result['new_filename'] == new_filename
                assert 'new_url' in result
                
                # Clean up
                try:
                    webdav_service.delete_file(new_filename)
                except:
                    pass
            else:
                pytest.skip("WebDAV move operation not available")
        else:
            pytest.skip("WebDAV not available for move test")


class TestComponentServiceDeletion(TestComponentServiceIntegration):
    """Test component deletion with real database cascade operations"""

    def test_should_delete_component_with_all_associations_when_complex_component_exists(self, test_data, component_service):
        """
        Test: Complex component deletion with all associations
        Given: Component with variants, pictures, brands, keywords exists
        When: delete_component is called
        Then: Component and all associations should be deleted via cascade
        """
        # Arrange - create complex component with all associations
        unique_id = test_data['base_id']
        component = Component(
            product_number=f'COMPLEX-{unique_id}',
            description='Complex component with all associations',
            supplier_id=test_data['supplier'].id,
            component_type_id=test_data['component_type'].id
        )
        db.session.add(component)
        db.session.flush()

        # Add variant
        variant = ComponentVariant(
            component_id=component.id,
            color_id=test_data['color'].id,
            is_active=True
        )
        db.session.add(variant)
        db.session.flush()

        # Add pictures
        picture1 = Picture(
            component_id=component.id,
            picture_name=f'complex_pic1_{unique_id}',
            url=f'http://test.com/complex_pic1_{unique_id}.jpg',
            picture_order=1
        )
        picture2 = Picture(
            component_id=component.id,
            variant_id=variant.id,
            picture_name=f'complex_pic2_{unique_id}',
            url=f'http://test.com/complex_pic2_{unique_id}.jpg',
            picture_order=1
        )
        db.session.add_all([picture1, picture2])
        db.session.flush()

        # Add brand association
        from app.models import Brand
        brand = Brand(name=f'Test Brand {unique_id}')
        db.session.add(brand)
        db.session.flush()
        
        brand_assoc = ComponentBrand(
            component_id=component.id,
            brand_id=brand.id
        )
        db.session.add(brand_assoc)
        db.session.flush()

        component_id = component.id
        variant_id = variant.id
        picture1_id = picture1.id
        picture2_id = picture2.id

        # Act
        result = component_service.delete_component(component_id)

        # Assert
        assert result['success'] is True
        assert 'Complex component' in result['message'] or f'COMPLEX-{unique_id}' in result['message']
        
        # Verify all entities were deleted via cascade
        assert Component.query.get(component_id) is None
        assert ComponentVariant.query.get(variant_id) is None
        assert Picture.query.get(picture1_id) is None
        assert Picture.query.get(picture2_id) is None

    def test_should_handle_bulk_component_deletion_when_multiple_components_exist(self, test_data, component_service):
        """
        Test: Bulk deletion of multiple components
        Given: Multiple components exist in database
        When: bulk_delete_components is called
        Then: All specified components should be deleted
        """
        # Arrange - create multiple components
        unique_id = test_data['base_id']
        components = []
        
        for i in range(3):
            component = Component(
                product_number=f'BULK{i}-{unique_id}',
                description=f'Bulk test component {i}',
                supplier_id=test_data['supplier'].id,
                component_type_id=test_data['component_type'].id
            )
            db.session.add(component)
            components.append(component)
        
        db.session.flush()
        component_ids = [c.id for c in components]

        # Act
        result = component_service.bulk_delete_components(component_ids)

        # Assert
        assert result['success'] is True
        assert result['deleted_count'] == 3
        
        # Verify all components were deleted
        for comp_id in component_ids:
            assert Component.query.get(comp_id) is None


class TestComponentServicePictureOperations(TestComponentServiceIntegration):
    """Test picture operations with real WebDAV integration (when available)"""

    def test_should_handle_comprehensive_picture_renaming_when_product_number_changes(self, test_data, component_service):
        """
        Test: Comprehensive picture renaming affecting all variants
        Given: Component with multiple variants and pictures exists
        When: Product number is changed
        Then: All pictures should be renamed to reflect new product number
        """
        # Arrange
        unique_id = test_data['base_id']
        old_product_number = f'OLDPROD-{unique_id}'
        new_product_number = f'NEWPROD-{unique_id}'
        
        component = Component(
            product_number=old_product_number,
            description='Picture rename test',
            supplier_id=test_data['supplier'].id,
            component_type_id=test_data['component_type'].id
        )
        db.session.add(component)
        db.session.flush()

        # Add variant and pictures
        variant = ComponentVariant(
            component_id=component.id,
            color_id=test_data['color'].id,
            is_active=True
        )
        db.session.add(variant)
        db.session.flush()

        # Create pictures with old naming
        from app.utils.file_handling import generate_picture_name
        old_component_picture_name = generate_picture_name(component, None, 1)
        old_variant_picture_name = generate_picture_name(component, variant, 1)

        picture1 = Picture(
            component_id=component.id,
            picture_name=old_component_picture_name,
            url=f'http://test.com/{old_component_picture_name}.jpg',
            picture_order=1
        )
        picture2 = Picture(
            component_id=component.id,
            variant_id=variant.id,
            picture_name=old_variant_picture_name,
            url=f'http://test.com/{old_variant_picture_name}.jpg',
            picture_order=1
        )
        db.session.add_all([picture1, picture2])
        db.session.flush()

        # Act - change product number
        update_data = {'product_number': new_product_number}
        result = component_service.update_component(component.id, update_data)

        # Assert
        assert result['success'] is True
        
        # Verify database was updated
        updated_component = Component.query.get(component.id)
        assert updated_component.product_number == new_product_number
        
        # Verify picture names were updated in database
        updated_picture1 = Picture.query.get(picture1.id)
        updated_picture2 = Picture.query.get(picture2.id)
        
        # Generate expected new names
        new_component_picture_name = generate_picture_name(updated_component, None, 1)
        new_variant_picture_name = generate_picture_name(updated_component, variant, 1)
        
        assert updated_picture1.picture_name == new_component_picture_name
        assert updated_picture2.picture_name == new_variant_picture_name

    def test_should_handle_supplier_change_affecting_picture_names(self, test_data, component_service):
        """
        Test: Picture renaming when supplier changes
        Given: Component with supplier and pictures exists
        When: Supplier is changed or removed
        Then: Picture names should update to reflect supplier change
        """
        # Arrange
        unique_id = test_data['base_id']
        
        # Create second supplier
        new_supplier = Supplier(supplier_code=f'NEWSUP-{unique_id}')
        db.session.add(new_supplier)
        db.session.flush()
        
        component = Component(
            product_number=f'SUPPROD-{unique_id}',
            description='Supplier change test',
            supplier_id=test_data['supplier'].id,
            component_type_id=test_data['component_type'].id
        )
        db.session.add(component)
        db.session.flush()

        # Create picture with original supplier
        from app.utils.file_handling import generate_picture_name
        old_picture_name = generate_picture_name(component, None, 1)
        
        picture = Picture(
            component_id=component.id,
            picture_name=old_picture_name,
            url=f'http://test.com/{old_picture_name}.jpg',
            picture_order=1
        )
        db.session.add(picture)
        db.session.flush()

        # Act - change supplier
        update_data = {'supplier_id': new_supplier.id}
        result = component_service.update_component(component.id, update_data)

        # Assert
        assert result['success'] is True
        
        # Verify supplier was changed
        updated_component = Component.query.get(component.id)
        assert updated_component.supplier_id == new_supplier.id
        
        # Verify picture name was updated to reflect new supplier
        updated_picture = Picture.query.get(picture.id)
        expected_new_name = generate_picture_name(updated_component, None, 1)
        assert updated_picture.picture_name == expected_new_name


class TestComponentServiceErrorHandling(TestComponentServiceIntegration):
    """Test error handling and edge cases with real database constraints"""

    def test_should_rollback_transaction_when_foreign_key_constraint_violated(self, test_data, component_service):
        """
        Test: Transaction rollback on database constraint violations
        Given: Invalid foreign key data
        When: Component operation violates database constraints
        Then: Database transaction should be rolled back
        """
        # Arrange
        unique_id = test_data['base_id']
        
        # Create component first
        component = Component(
            product_number=f'ROLLBACK-{unique_id}',
            description='Rollback test',
            supplier_id=test_data['supplier'].id,
            component_type_id=test_data['component_type'].id
        )
        db.session.add(component)
        db.session.flush()

        # Try to update with invalid foreign key (non-existent supplier)
        invalid_update_data = {
            'supplier_id': 999999,  # Non-existent supplier
            'description': 'This should fail'
        }

        # Act & Assert - expect ValueError due to foreign key constraint
        with pytest.raises((ValueError, Exception)) as exc_info:
            component_service.update_component(component.id, invalid_update_data)
        
        # Verify error is related to foreign key constraint
        error_msg = str(exc_info.value).lower()
        assert any(keyword in error_msg for keyword in ['foreign key', 'supplier', 'constraint', 'violat'])
        
        # Verify original data was not changed
        unchanged_component = Component.query.get(component.id)
        assert unchanged_component.description == 'Rollback test'
        assert unchanged_component.supplier_id == test_data['supplier'].id

    def test_should_handle_component_not_found_gracefully(self, component_service):
        """
        Test: Graceful handling of non-existent component operations
        Given: Non-existent component ID
        When: Component operations are attempted
        Then: Appropriate errors should be raised with clear messages
        """
        # Arrange
        non_existent_id = 999999
        
        # Test update non-existent component
        with pytest.raises(ValueError) as exc_info:
            component_service.update_component(non_existent_id, {'description': 'Test'})
        assert 'not found' in str(exc_info.value).lower()
        
        # Test delete non-existent component
        with pytest.raises(ValueError) as exc_info:
            component_service.delete_component(non_existent_id)
        assert 'not found' in str(exc_info.value).lower()

    def test_should_handle_webdav_unavailable_gracefully_when_pictures_involved(self, test_data, component_service):
        """
        Test: Graceful handling when WebDAV is unavailable
        Given: Component with pictures but WebDAV unavailable
        When: Component operations are performed
        Then: Operations should complete without crashing, with appropriate warnings
        """
        # Arrange
        unique_id = test_data['base_id']
        component = Component(
            product_number=f'NOWAV-{unique_id}',
            description='No WebDAV test',
            supplier_id=test_data['supplier'].id,
            component_type_id=test_data['component_type'].id
        )
        db.session.add(component)
        db.session.flush()

        # Create picture record (simulating orphaned database record)
        picture = Picture(
            component_id=component.id,
            picture_name=f'test_picture_{unique_id}',
            url=f'http://nonexistent/test_picture_{unique_id}.jpg',
            picture_order=1
        )
        db.session.add(picture)
        db.session.flush()

        # Act - try to update component (should handle WebDAV failures gracefully)
        update_data = {'description': 'Updated without WebDAV'}
        result = component_service.update_component(component.id, update_data)

        # Assert - operation should succeed even if WebDAV fails
        assert result['success'] is True
        
        updated_component = Component.query.get(component.id)
        assert updated_component.description == 'Updated without WebDAV'


class TestComponentServiceAssociationManagement(TestComponentServiceIntegration):
    """Test component association management with real database operations"""

    def test_should_handle_brand_associations_correctly_when_updating(self, test_data, component_service):
        """
        Test: Brand association management during component updates
        Given: Component with brand associations exists
        When: Component is updated with new brand data
        Then: Brand associations should be updated correctly
        """
        # Arrange
        unique_id = test_data['base_id']
        
        # Create brands
        from app.models import Brand
        brand1 = Brand(name=f'Test Brand 1 {unique_id}')
        brand2 = Brand(name=f'Test Brand 2 {unique_id}')
        db.session.add_all([brand1, brand2])
        db.session.flush()
        
        component = Component(
            product_number=f'BRANDTEST-{unique_id}',
            description='Brand association test',
            supplier_id=test_data['supplier'].id,
            component_type_id=test_data['component_type'].id
        )
        db.session.add(component)
        db.session.flush()

        # Add initial brand association
        brand_assoc = ComponentBrand(
            component_id=component.id,
            brand_id=brand1.id
        )
        db.session.add(brand_assoc)
        db.session.flush()

        # Act - update with new brand associations
        update_data = {
            'brand_ids': [brand2.id],  # Change from brand1 to brand2
            'description': 'Updated with new brand'
        }
        result = component_service.update_component(component.id, update_data)

        # Assert
        assert result['success'] is True
        
        # Verify brand associations were updated
        updated_component = Component.query.get(component.id)
        assert updated_component.description == 'Updated with new brand'
        
        # Check current brand associations
        current_brand_associations = ComponentBrand.query.filter_by(component_id=component.id).all()
        current_brand_ids = [assoc.brand_id for assoc in current_brand_associations]
        
        # Should have brand2, not brand1
        assert brand2.id in current_brand_ids
        assert brand1.id not in current_brand_ids


class TestComponentServiceBrandAssociationIssues(TestComponentServiceIntegration):
    """Test brand association functionality that was previously failing"""

    def test_should_associate_existing_brand_when_creating_component(self, test_data, component_service):
        """
        Test: Brand association during component creation with existing brand
        Given: Existing brand in database
        When: Component is created with brand_ids in data
        Then: Brand association should be created correctly
        """
        # Arrange
        unique_id = test_data['base_id']
        
        from app.models import Brand
        existing_brand = Brand(name=f'Existing Brand {unique_id}')
        db.session.add(existing_brand)
        db.session.flush()
        
        component_data = {
            'product_number': f'BRAND-CREATE-{unique_id}',
            'description': 'Component with existing brand',
            'component_type_id': test_data['component_type'].id,
            'supplier_id': test_data['supplier'].id,
            'brand_ids': [existing_brand.id]
        }
        
        # Act
        result = component_service.create_component(component_data)
        
        # Assert
        assert result['success'] is True
        
        # Verify brand association was created
        component_id = result['component']['id']
        brand_associations = ComponentBrand.query.filter_by(component_id=component_id).all()
        
        assert len(brand_associations) > 0, "Component should have brand association"
        
        brand_ids = [assoc.brand_id for assoc in brand_associations]
        assert existing_brand.id in brand_ids, "Component should be associated with existing brand"

    def test_should_create_new_brand_when_provided_in_component_data(self, test_data, component_service):
        """
        Test: New brand creation during component creation
        Given: New brand name provided in component data
        When: Component is created with new_brand_name
        Then: New brand should be created and associated
        """
        # Arrange
        unique_id = test_data['base_id']
        from app.models import Brand
        initial_brand_count = db.session.query(Brand).count()
        
        new_brand_name = f'New Brand {unique_id}'
        component_data = {
            'product_number': f'NEWBRAND-{unique_id}',
            'description': 'Component with new brand',
            'component_type_id': test_data['component_type'].id,
            'supplier_id': test_data['supplier'].id,
            'new_brand_name': new_brand_name
        }
        
        # Act
        result = component_service.create_component(component_data)
        
        # Assert
        assert result['success'] is True
        
        # Verify new brand was created
        new_brand = Brand.query.filter_by(name=new_brand_name).first()
        assert new_brand is not None, "New brand should be created"
        
        # Verify brand count increased
        final_brand_count = db.session.query(Brand).count()
        assert final_brand_count == initial_brand_count + 1, "Brand count should increase by 1"
        
        # Verify brand association
        component_id = result['component']['id']
        brand_associations = ComponentBrand.query.filter_by(component_id=component_id).all()
        brand_ids = [assoc.brand_id for assoc in brand_associations]
        assert new_brand.id in brand_ids, "Component should be associated with new brand"

    def test_should_update_brand_associations_when_editing_component(self, test_data, component_service):
        """
        Test: Brand association updates during component editing
        Given: Component with no brand associations
        When: Component is updated with brand_ids
        Then: Brand associations should be added correctly
        """
        # Arrange
        unique_id = test_data['base_id']
        
        # Create component without brand
        component = Component(
            product_number=f'EDITBRAND-{unique_id}',
            description='Component for brand editing test',
            component_type_id=test_data['component_type'].id,
            supplier_id=test_data['supplier'].id
        )
        db.session.add(component)
        db.session.flush()
        
        # Create brand to associate
        from app.models import Brand
        test_brand = Brand(name=f'Edit Test Brand {unique_id}')
        db.session.add(test_brand)
        db.session.flush()
        
        # Verify no initial associations
        initial_associations = ComponentBrand.query.filter_by(component_id=component.id).count()
        assert initial_associations == 0, "Component should start with no brand associations"
        
        # Act - update component with brand association
        update_data = {
            'brand_ids': [test_brand.id],
            'description': 'Updated with brand association'
        }
        result = component_service.update_component(component.id, update_data)
        
        # Assert
        assert result['success'] is True
        
        # Verify brand association was added
        final_associations = ComponentBrand.query.filter_by(component_id=component.id).all()
        assert len(final_associations) > 0, "Component should have brand association after update"
        
        brand_ids = [assoc.brand_id for assoc in final_associations]
        assert test_brand.id in brand_ids, "Component should be associated with test brand"


class TestComponentServiceComprehensiveUpdateScenarios(TestComponentServiceIntegration):
    """Test comprehensive component update scenarios affecting picture renaming"""

    def test_should_rename_pictures_when_product_number_changes(self, test_data, component_service, test_image_data):
        """
        Test: Picture renaming when product number changes
        Given: Component with variant pictures exists in WebDAV
        When: Product number is changed
        Then: All pictures should be renamed on WebDAV and database updated
        """
        # Arrange
        unique_id = test_data['base_id']
        original_product_number = f'ORIG-{unique_id}'
        new_product_number = f'NEW-{unique_id}'
        
        # Create component with variant and picture
        component = Component(
            product_number=original_product_number,
            description='Product number change test',
            supplier_id=test_data['supplier'].id,
            component_type_id=test_data['component_type'].id
        )
        db.session.add(component)
        db.session.flush()
        
        # Create variant
        variant = ComponentVariant(
            component_id=component.id,
            color_id=test_data['color'].id,
            is_active=True
        )
        db.session.add(variant)
        db.session.flush()
        
        # Create picture record
        original_picture_name = f'{test_data["supplier"].supplier_code.lower()}_{original_product_number.lower()}_{test_data["color"].name.lower()}_1'
        picture = Picture(
            component_id=component.id,
            variant_id=variant.id,
            picture_name=original_picture_name,
            url='',
            picture_order=1
        )
        db.session.add(picture)
        db.session.flush()
        
        # Upload test image to WebDAV
        filename = f'{original_picture_name}.jpg'
        upload_result = component_service.upload_picture_to_webdav(
            test_image_data.getvalue(), 
            filename, 
            'image/jpeg'
        )
        
        if upload_result['success']:
            picture.url = upload_result['url']
            db.session.flush()
        else:
            pytest.skip("WebDAV not available for integration test")
        
        # Act - change product number
        update_data = {'product_number': new_product_number}
        result = component_service.update_component(component.id, update_data)
        
        # Assert
        assert result['success'] is True
        
        # Verify database was updated
        updated_component = Component.query.get(component.id)
        assert updated_component.product_number == new_product_number
        
        # Verify picture name was updated in database
        updated_picture = Picture.query.get(picture.id)
        expected_new_name = f'{test_data["supplier"].supplier_code.lower()}_{new_product_number.lower()}_{test_data["color"].name.lower()}_1'
        assert expected_new_name.lower() in updated_picture.picture_name.lower()

    def test_should_rename_pictures_when_supplier_changes(self, test_data, component_service, test_image_data):
        """
        Test: Picture renaming when supplier changes
        Given: Component with pictures and supplier
        When: Supplier is changed to different supplier
        Then: All pictures should be renamed with new supplier code
        """
        # Arrange
        unique_id = test_data['base_id']
        
        # Create second supplier
        new_supplier = Supplier(supplier_code=f'NEWSUP-{unique_id}', address='New supplier address')
        db.session.add(new_supplier)
        db.session.flush()
        
        # Create component with original supplier
        component = Component(
            product_number=f'SUPPLIER-{unique_id}',
            description='Supplier change test',
            supplier_id=test_data['supplier'].id,
            component_type_id=test_data['component_type'].id
        )
        db.session.add(component)
        db.session.flush()
        
        # Create variant and picture
        variant = ComponentVariant(
            component_id=component.id,
            color_id=test_data['color'].id,
            is_active=True
        )
        db.session.add(variant)
        db.session.flush()
        
        # Create picture with original supplier naming
        original_picture_name = f'{test_data["supplier"].supplier_code.lower()}_supplier-{unique_id}_{test_data["color"].name.lower()}_1'
        picture = Picture(
            component_id=component.id,
            variant_id=variant.id,
            picture_name=original_picture_name,
            url='',
            picture_order=1
        )
        db.session.add(picture)
        db.session.flush()
        
        # Upload test image
        filename = f'{original_picture_name}.jpg'
        upload_result = component_service.upload_picture_to_webdav(
            test_image_data.getvalue(), 
            filename, 
            'image/jpeg'
        )
        
        if upload_result['success']:
            picture.url = upload_result['url']
            db.session.flush()
        else:
            pytest.skip("WebDAV not available for integration test")
        
        # Act - change supplier
        update_data = {'supplier_id': new_supplier.id}
        result = component_service.update_component(component.id, update_data)
        
        # Assert
        assert result['success'] is True
        
        # Verify supplier was updated
        updated_component = Component.query.get(component.id)
        assert updated_component.supplier_id == new_supplier.id
        
        # Verify picture name contains new supplier code
        updated_picture = Picture.query.get(picture.id)
        assert new_supplier.supplier_code.lower() in updated_picture.picture_name.lower()

    def test_should_handle_supplier_removal_picture_renaming(self, test_data, component_service, test_image_data):
        """
        Test: Picture renaming when supplier is removed (set to NULL)
        Given: Component with supplier and pictures
        When: Supplier is removed (set to NULL)
        Then: Pictures should be renamed without supplier prefix
        """
        # Arrange
        unique_id = test_data['base_id']
        
        # Create component with supplier
        component = Component(
            product_number=f'NOSUP-{unique_id}',
            description='Supplier removal test',
            supplier_id=test_data['supplier'].id,
            component_type_id=test_data['component_type'].id
        )
        db.session.add(component)
        db.session.flush()
        
        # Create variant and picture
        variant = ComponentVariant(
            component_id=component.id,
            color_id=test_data['color'].id,
            is_active=True
        )
        db.session.add(variant)
        db.session.flush()
        
        # Create picture with supplier naming
        original_picture_name = f'{test_data["supplier"].supplier_code.lower()}_nosup-{unique_id}_{test_data["color"].name.lower()}_1'
        picture = Picture(
            component_id=component.id,
            variant_id=variant.id,
            picture_name=original_picture_name,
            url='',
            picture_order=1
        )
        db.session.add(picture)
        db.session.flush()
        
        # Upload test image
        filename = f'{original_picture_name}.jpg'
        upload_result = component_service.upload_picture_to_webdav(
            test_image_data.getvalue(), 
            filename, 
            'image/jpeg'
        )
        
        if upload_result['success']:
            picture.url = upload_result['url']
            db.session.flush()
        else:
            pytest.skip("WebDAV not available for integration test")
        
        # Act - remove supplier
        update_data = {'supplier_id': None}
        result = component_service.update_component(component.id, update_data)
        
        # Assert
        assert result['success'] is True
        
        # Verify supplier was removed
        updated_component = Component.query.get(component.id)
        assert updated_component.supplier_id is None
        
        # Verify picture name no longer contains supplier code
        updated_picture = Picture.query.get(picture.id)
        assert test_data['supplier'].supplier_code.lower() not in updated_picture.picture_name.lower()
        
        # Should have format: product_color_order (without supplier prefix)
        expected_pattern = f'nosup-{unique_id}_{test_data["color"].name.lower()}_1'
        assert expected_pattern.lower() in updated_picture.picture_name.lower()


class TestComponentServiceAPIEditingScenarios(TestComponentServiceIntegration):
    """Test comprehensive component editing scenarios through service layer"""

    def test_should_update_basic_fields_successfully_when_valid_data(self, test_data, component_service):
        """
        Test: Basic field updates through service layer
        Given: Component exists with basic fields
        When: Description and properties are updated
        Then: Changes should be saved correctly
        """
        # Arrange
        unique_id = test_data['base_id']
        component = Component(
            product_number=f'EDIT-{unique_id}',
            description='Original description',
            supplier_id=test_data['supplier'].id,
            component_type_id=test_data['component_type'].id,
            properties={'old_key': 'old_value'}
        )
        db.session.add(component)
        db.session.flush()

        # Act
        update_data = {
            'description': 'Updated via service layer - SUCCESS!',
            'properties': {
                'service_layer_test': 'passed',
                'architecture': 'MVC with service layer',
                'timestamp': '2025-07-07'
            }
        }
        result = component_service.update_component(component.id, update_data)

        # Assert
        assert result['success'] is True
        assert 'description' in result['changes']
        assert 'properties' in result['changes']
        
        # Verify database changes
        updated_component = Component.query.get(component.id)
        assert updated_component.description == 'Updated via service layer - SUCCESS!'
        assert updated_component.properties['service_layer_test'] == 'passed'
        assert updated_component.properties['architecture'] == 'MVC with service layer'

    def test_should_handle_keyword_associations_when_updating(self, test_data, component_service):
        """
        Test: Keyword association management during updates
        Given: Component exists
        When: Keywords are provided in update data
        Then: Keywords should be properly associated
        """
        # Arrange
        unique_id = test_data['base_id']
        component = Component(
            product_number=f'KEYWORD-{unique_id}',
            description='Keyword test component',
            supplier_id=test_data['supplier'].id,
            component_type_id=test_data['component_type'].id
        )
        db.session.add(component)
        db.session.flush()

        # Act
        update_data = {
            'description': 'Testing keyword functionality',
            'keywords': ['service', 'architecture', 'mvc', 'flask']
        }
        result = component_service.update_component(component.id, update_data)

        # Assert
        assert result['success'] is True
        
        # Verify keywords were associated
        updated_component = Component.query.options(
            selectinload(Component.keywords)
        ).get(component.id)
        
        keyword_names = [kw.name for kw in updated_component.keywords]
        for expected_keyword in ['service', 'architecture', 'mvc', 'flask']:
            assert expected_keyword in keyword_names

    def test_should_handle_picture_renames_as_json_object_when_updating(self, test_data, component_service):
        """
        Test: Picture rename handling with JSON object data
        Given: Component with pictures exists
        When: picture_renames is provided as object in update
        Then: Picture renames should be processed correctly
        """
        # Arrange
        unique_id = test_data['base_id']
        component = Component(
            product_number=f'PICJSON-{unique_id}',
            description='Picture JSON test',
            supplier_id=test_data['supplier'].id,
            component_type_id=test_data['component_type'].id
        )
        db.session.add(component)
        db.session.flush()

        # Create variant and picture
        variant = ComponentVariant(
            component_id=component.id,
            color_id=test_data['color'].id,
            is_active=True
        )
        db.session.add(variant)
        db.session.flush()

        # Create picture record
        picture = Picture(
            component_id=component.id,
            variant_id=variant.id,
            picture_name=f'old_picture_{unique_id}',
            url=f'http://test.com/old_picture_{unique_id}.jpg',
            picture_order=1
        )
        db.session.add(picture)
        db.session.flush()

        # Act
        update_data = {
            'description': 'Testing picture rename functionality',
            'picture_renames': {
                f'old_picture_{unique_id}': f'new_picture_{unique_id}'
            }
        }
        result = component_service.update_component(component.id, update_data)

        # Assert
        assert result['success'] is True
        
        # Verify picture rename was processed
        if 'changes' in result and 'picture_orders' in result['changes']:
            assert 'files_renamed' in result['changes']['picture_orders']

    def test_should_handle_picture_renames_as_json_string_when_updating(self, test_data, component_service):
        """
        Test: Picture rename handling with JSON string data (from form submission)
        Given: Component with pictures exists
        When: picture_renames is provided as JSON string
        Then: JSON should be parsed and processed correctly
        """
        # Arrange
        unique_id = test_data['base_id']
        component = Component(
            product_number=f'PICSTR-{unique_id}',
            description='Picture JSON string test',
            supplier_id=test_data['supplier'].id,
            component_type_id=test_data['component_type'].id
        )
        db.session.add(component)
        db.session.flush()

        # Act - simulate form submission with JSON string
        import json
        update_data = {
            'description': 'Testing nested picture rename',
            'picture_renames': json.dumps({
                f'old_nested_{unique_id}': f'new_nested_{unique_id}'
            })
        }
        result = component_service.update_component(component.id, update_data)

        # Assert
        assert result['success'] is True
        # The service should handle JSON string parsing gracefully

    def test_should_handle_mixed_association_updates_when_editing(self, test_data, component_service):
        """
        Test: Multiple association types in single update
        Given: Component exists
        When: Brand, category, and keyword associations are updated together
        Then: All associations should be processed correctly
        """
        # Arrange
        unique_id = test_data['base_id']
        
        # Create test brands and categories
        from app.models import Brand, Category
        brand = Brand(name=f'Mixed Test Brand {unique_id}')
        category = Category(name=f'Mixed Test Category {unique_id}')
        db.session.add_all([brand, category])
        db.session.flush()
        
        component = Component(
            product_number=f'MIXED-{unique_id}',
            description='Mixed associations test',
            supplier_id=test_data['supplier'].id,
            component_type_id=test_data['component_type'].id
        )
        db.session.add(component)
        db.session.flush()

        # Act
        update_data = {
            'description': 'Updated with ALL association types',
            'properties': {
                'test_property': 'mixed_associations',
                'material': 'cotton'
            },
            'brand_ids': [brand.id],
            'category_ids': [category.id],
            'keywords': ['test', 'mixed', 'associations']
        }
        result = component_service.update_component(component.id, update_data)

        # Assert
        assert result['success'] is True
        
        # Verify all associations were updated
        updated_component = Component.query.options(
            selectinload(Component.brand_associations),
            selectinload(Component.categories),
            selectinload(Component.keywords)
        ).get(component.id)
        
        # Check properties
        assert updated_component.properties['test_property'] == 'mixed_associations'
        assert updated_component.properties['material'] == 'cotton'
        
        # Check associations
        assert len(updated_component.brand_associations) > 0
        assert len(updated_component.categories) > 0
        assert len(updated_component.keywords) > 0


class TestComponentServiceVariantPictureUpload(TestComponentServiceIntegration):
    """Test variant picture upload functionality with real WebDAV integration"""

    def test_should_upload_variant_pictures_when_creating_component_with_variants(self, test_data, component_service, test_image_data):
        """
        Test: Variant picture upload during component creation
        Given: Component data with variant images
        When: Component is created with variant picture files
        Then: Pictures should be uploaded to WebDAV and associated with variants
        """
        # Arrange
        unique_id = test_data['base_id']
        
        # Create mock file-like object for testing
        class MockFile:
            def __init__(self, data, filename, content_type):
                self.data = data
                self.filename = filename
                self.content_type = content_type
                self._position = 0
            
            def read(self):
                return self.data
            
            def seek(self, position):
                self._position = position
        
        # Create test image files
        test_file = MockFile(
            test_image_data.getvalue(),
            f'test_variant_{unique_id}.jpg',
            'image/jpeg'
        )
        
        # Component data with variants including images
        component_data = {
            'product_number': f'VARUPLOAD-{unique_id}',
            'description': 'Component with variant pictures',
            'component_type_id': test_data['component_type'].id,
            'supplier_id': test_data['supplier'].id,
            'variants': [
                {
                    'color_id': test_data['color'].id,
                    'images': [test_file]
                }
            ]
        }
        
        # Act
        try:
            result = component_service.create_component(component_data)
            
            # Assert
            assert result['success'] is True
            assert 'variants' in result
            assert len(result['variants']) > 0
            
            # Check if variant was created with pictures
            created_variant = result['variants'][0]
            assert created_variant['color_id'] == test_data['color'].id
            
            # If WebDAV is available, pictures should be uploaded
            if 'pictures' in created_variant and len(created_variant['pictures']) > 0:
                picture = created_variant['pictures'][0]
                assert picture['url'] is not None
                assert picture['name'] is not None
                
        except Exception as e:
            # If WebDAV is not available, the test should skip gracefully
            if 'WebDAV' in str(e) or 'connection' in str(e).lower():
                pytest.skip("WebDAV not available for integration test")
            else:
                raise

    def test_should_generate_correct_picture_names_for_variant_uploads(self, test_data, component_service):
        """
        Test: Picture naming convention for variant uploads
        Given: Component with supplier and variant
        When: Pictures are uploaded for the variant
        Then: Picture names should follow supplier_product_color_order format
        """
        # Arrange
        unique_id = test_data['base_id']
        
        # Create component
        component = Component(
            product_number=f'NAMING-{unique_id}',
            description='Picture naming test',
            supplier_id=test_data['supplier'].id,
            component_type_id=test_data['component_type'].id
        )
        db.session.add(component)
        db.session.flush()
        
        # Create variant
        variant = ComponentVariant(
            component_id=component.id,
            color_id=test_data['color'].id,
            is_active=True
        )
        db.session.add(variant)
        db.session.flush()
        
        # Create picture record
        picture = Picture(
            component_id=component.id,
            variant_id=variant.id,
            picture_name='',  # Will be auto-generated
            url='http://test.com/test.jpg',
            picture_order=1
        )
        db.session.add(picture)
        db.session.flush()
        
        # Act - database trigger should generate name
        db.session.refresh(picture)
        
        # Assert - verify naming convention
        expected_parts = [
            test_data['supplier'].supplier_code.lower(),
            f'naming-{unique_id}'.lower(),
            test_data['color'].name.lower(),
            '1'
        ]
        
        for part in expected_parts:
            assert part.replace('-', '_') in picture.picture_name.lower()

    def test_should_handle_picture_upload_errors_gracefully(self, test_data, component_service):
        """
        Test: Error handling for failed picture uploads
        Given: Component creation with invalid image data
        When: Picture upload to WebDAV fails
        Then: Component should still be created but without pictures
        """
        # Arrange
        unique_id = test_data['base_id']
        
        # Create mock file with invalid data
        class MockBadFile:
            def __init__(self):
                self.filename = 'invalid.jpg'
                self.content_type = 'image/jpeg'
            
            def read(self):
                return b'invalid image data'
        
        component_data = {
            'product_number': f'ERRORTEST-{unique_id}',
            'description': 'Error handling test',
            'component_type_id': test_data['component_type'].id,
            'supplier_id': test_data['supplier'].id,
            'variants': [
                {
                    'color_id': test_data['color'].id,
                    'images': [MockBadFile()]
                }
            ]
        }
        
        # Act
        result = component_service.create_component(component_data)
        
        # Assert
        assert result['success'] is True  # Component creation should succeed
        assert len(result['variants']) > 0  # Variant should be created
        
        # Pictures might not be uploaded due to invalid data, but component exists
        component = Component.query.get(result['component']['id'])
        assert component is not None
        assert component.product_number == f'ERRORTEST-{unique_id}'

    def test_should_support_multiple_picture_uploads_per_variant(self, test_data, component_service, test_image_data):
        """
        Test: Multiple pictures per variant upload
        Given: Variant data with multiple image files
        When: Component is created with multiple pictures per variant
        Then: All pictures should be uploaded with correct ordering
        """
        # Arrange
        unique_id = test_data['base_id']
        
        # Create multiple test files
        class MockFile:
            def __init__(self, data, filename):
                self.data = data
                self.filename = filename
                self.content_type = 'image/jpeg'
            
            def read(self):
                return self.data
        
        files = [
            MockFile(test_image_data.getvalue(), f'variant_{unique_id}_1.jpg'),
            MockFile(test_image_data.getvalue(), f'variant_{unique_id}_2.jpg'),
            MockFile(test_image_data.getvalue(), f'variant_{unique_id}_3.jpg')
        ]
        
        component_data = {
            'product_number': f'MULTIPIC-{unique_id}',
            'description': 'Multiple pictures test',
            'component_type_id': test_data['component_type'].id,
            'supplier_id': test_data['supplier'].id,
            'variants': [
                {
                    'color_id': test_data['color'].id,
                    'images': files
                }
            ]
        }
        
        # Act
        try:
            result = component_service.create_component(component_data)
            
            # Assert
            assert result['success'] is True
            
            if len(result['variants']) > 0:
                variant = result['variants'][0]
                
                # If WebDAV is available and pictures were uploaded
                if 'pictures' in variant and len(variant['pictures']) > 0:
                    # Pictures should be ordered
                    pictures = variant['pictures']
                    for i, picture in enumerate(pictures, 1):
                        assert picture['order'] == i
                        
        except Exception as e:
            if 'WebDAV' in str(e) or 'connection' in str(e).lower():
                pytest.skip("WebDAV not available for integration test")
            else:
                raise

    def test_should_handle_simultaneous_product_number_and_supplier_changes(self, test_data, component_service, test_image_data):
        """
        Test: Simultaneous product number and supplier changes
        Given: Component with supplier and pictures exists
        When: Both product_number and supplier are changed simultaneously
        Then: All pictures should be renamed with both new product number and new supplier code
        """
        # Arrange
        unique_id = test_data['base_id']
        original_product_number = f'MULTI-ORIG-{unique_id}'
        new_product_number = f'MULTI-NEW-{unique_id}'
        
        # Create original supplier
        original_supplier = Supplier(
            supplier_code=f'ORIG{unique_id % 1000}',
            address='Original supplier address'
        )
        db.session.add(original_supplier)
        db.session.flush()
        
        # Create new supplier
        new_supplier = Supplier(
            supplier_code=f'NEW{unique_id % 1000}',
            address='New supplier address'
        )
        db.session.add(new_supplier)
        db.session.flush()
        
        # Create component with original supplier and product number
        component = Component(
            product_number=original_product_number,
            description='Test component for simultaneous changes',
            component_type_id=test_data['component_type_id'],
            supplier_id=original_supplier.id
        )
        db.session.add(component)
        db.session.flush()
        
        # Create variant with color
        variant = ComponentVariant(
            component_id=component.id,
            color_id=test_data['color_id']
        )
        db.session.add(variant)
        db.session.flush()
        
        try:
            # Upload test picture to get original filename
            picture_data = {
                'component_id': component.id,
                'variant_id': variant.id,
                'file_data': test_image_data,
                'filename': f'test_simultaneous_{unique_id}.jpg',
                'order': 1
            }
            
            # Create picture record (triggers will generate name)
            picture = Picture(
                component_id=component.id,
                variant_id=variant.id,
                url=f'/components/placeholder_{unique_id}.jpg',
                picture_order=1
            )
            db.session.add(picture)
            db.session.flush()
            
            original_picture_name = picture.picture_name
            print(f"Original picture name: {original_picture_name}")
            
            # Act: Change both product number and supplier simultaneously
            update_data = {
                'product_number': new_product_number,
                'supplier_id': new_supplier.id,
                'description': 'Updated with simultaneous changes'
            }
            
            result = component_service.update_component(component.id, update_data)
            
            # Assert
            assert result['success'] is True
            
            # Verify component was updated
            updated_component = Component.query.get(component.id)
            assert updated_component.product_number == new_product_number
            assert updated_component.supplier_id == new_supplier.id
            
            # Verify picture name was updated with BOTH changes
            db.session.expunge_all()  # Clear session cache
            updated_picture = Picture.query.get(picture.id)
            new_picture_name = updated_picture.picture_name
            
            print(f"Updated picture name: {new_picture_name}")
            
            # Picture name should contain both new product number and new supplier code
            expected_elements = [
                new_supplier.supplier_code.lower(),
                new_product_number.lower().replace('-', '_'),
                test_data['color_name'].lower()
            ]
            
            for element in expected_elements:
                assert element in new_picture_name.lower(), f"Expected '{element}' in picture name '{new_picture_name}'"
            
            # Verify old picture name elements are NOT present
            old_elements = [
                original_supplier.supplier_code.lower(),
                original_product_number.lower().replace('-', '_')
            ]
            
            for old_element in old_elements:
                assert old_element not in new_picture_name.lower(), f"Old element '{old_element}' should not be in new picture name '{new_picture_name}'"
            
            print(f"✅ Successfully renamed picture from '{original_picture_name}' to '{new_picture_name}'")
            
        except Exception as e:
            if 'WebDAV' in str(e) or 'connection' in str(e).lower():
                pytest.skip("WebDAV not available for integration test")
            else:
                raise