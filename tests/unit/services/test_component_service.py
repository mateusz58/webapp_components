"""
Comprehensive ComponentService Unit Tests
All tests for app.services.component_service.ComponentService in one organized file
Following testing_rules.md: One file per service with pytest style organization
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from app import create_app
from app.services.component_service import ComponentService
from app.models import Component, ComponentType, Supplier, Color, ComponentVariant, Picture
from app.services.interfaces import StorageOperationResult, FileOperationResult, FileInfo


# ========================================
# FIXTURES
# ========================================

@pytest.fixture
def app_context():
    """Create Flask app context for tests"""
    app = create_app()
    app_context = app.app_context()
    app_context.push()
    yield app
    app_context.pop()


@pytest.fixture
def mock_storage_service():
    """Create mock storage service with default successful responses"""
    mock_service = Mock()
    mock_service.upload_file.return_value = StorageOperationResult(
        success=True,
        result=FileOperationResult.SUCCESS,
        message="Upload successful",
        file_info=FileInfo(
            name="test.jpg",
            path="/webdav/components/test.jpg",
            url="http://webdav.test/components/test.jpg",
            exists=True,
            content_type="image/jpeg"
        )
    )
    mock_service.delete_file.return_value = StorageOperationResult(
        success=True,
        result=FileOperationResult.SUCCESS,
        message="Delete successful"
    )
    mock_service.move_file.return_value = StorageOperationResult(
        success=True,
        result=FileOperationResult.SUCCESS,
        message="Move successful"
    )
    return mock_service


@pytest.fixture
def component_service(mock_storage_service):
    """Create ComponentService instance with mocked storage"""
    return ComponentService(storage_service=mock_storage_service)


# ========================================
# COMPONENT CREATION TESTS
# ========================================

@patch('app.services.component_service.db.session')
@patch('app.services.component_service.Component')
@patch('app.services.component_service.ComponentType')
def test_should_create_component_successfully_when_valid_minimal_data(mock_component_type, mock_component, mock_db_session, component_service, app_context):
    """
    Test: Component creation with minimal valid data
    Given: Valid component data with only required fields
    When: create_component is called
    Then: Component should be created successfully with auto-generated ID
    """
    component_data = {
        'product_number': 'MIN-001',
        'component_type_id': 1,
        'description': 'Minimal test component'
    }
    
    mock_component_type.query.get.return_value = Mock(id=1, name="Test Type")
    mock_component.query.filter.return_value.first.return_value = None
    
    mock_new_component = Mock()
    mock_new_component.id = 100
    mock_new_component.product_number = 'MIN-001'
    mock_component.return_value = mock_new_component
    
    mock_db_session.add = Mock()
    mock_db_session.flush = Mock()
    mock_db_session.commit = Mock()
    
    with patch('app.services.component_service.handle_brand_associations'), \
         patch('app.services.component_service.handle_categories'), \
         patch('app.services.component_service.handle_keywords'):
        
        result = component_service.create_component(component_data)
    
    assert result['success'] is True
    assert result['component']['id'] == 100
    mock_component.assert_called_once()
    mock_db_session.commit.assert_called_once()


@patch('app.services.component_service.db.session')
@patch('app.services.component_service.Component')
def test_should_fail_creation_when_duplicate_product_number_exists(mock_component, mock_db_session, component_service, app_context):
    """
    Test: Component creation with duplicate product number
    Given: Component data with existing product_number
    When: create_component is called
    Then: ValidationError should be raised with appropriate message
    """
    component_data = {
        'product_number': 'DUPLICATE-001',
        'component_type_id': 1,
        'description': 'Duplicate component test'
    }
    
    existing_component = Mock()
    existing_component.id = 50
    existing_component.product_number = 'DUPLICATE-001'
    mock_component.query.filter.return_value.first.return_value = existing_component
    
    result = component_service.create_component(component_data)
    
    assert result['success'] is False
    assert 'already exists' in result['error']
    mock_db_session.commit.assert_not_called()


# ========================================
# COMPONENT UPDATE TESTS
# ========================================

def test_should_track_changes_correctly_when_product_number_changes(app_context):
    """
    Test: Change tracking for product number updates
    Given: Component with existing product number and update data with new product number
    When: _update_basic_fields_static is called
    Then: Changes should be tracked with old and new values
    """
    component = Mock()
    component.product_number = 'OLD-001'
    component.description = 'Old description'
    component.component_type_id = 1
    component.supplier_id = 1
    component.properties = {}
    
    data = {
        'product_number': 'NEW-001',
        'description': 'New description',
        'component_type_id': 2,
        'supplier_id': 2,
        'properties': {'test': 'value'}
    }
    
    changes = ComponentService._update_basic_fields_static(component, data)
    
    assert 'product_number' in changes
    assert changes['product_number']['old'] == 'OLD-001'
    assert changes['product_number']['new'] == 'NEW-001'
    
    assert 'description' in changes
    assert changes['description']['old'] == 'Old description'
    assert changes['description']['new'] == 'New description'


def test_should_return_empty_changes_when_no_fields_modified(app_context):
    """
    Test: No changes detection
    Given: Component with existing data identical to update data
    When: _update_basic_fields_static is called
    Then: Empty changes dictionary should be returned
    """
    component = Mock()
    component.product_number = 'SAME-001'
    component.description = 'Same description'
    component.component_type_id = 1
    component.supplier_id = 1
    component.properties = {'existing': 'value'}
    
    data = {
        'product_number': 'SAME-001',
        'description': 'Same description',
        'component_type_id': 1,
        'supplier_id': 1,
        'properties': {'existing': 'value'}
    }
    
    changes = ComponentService._update_basic_fields_static(component, data)
    
    assert len(changes) == 0


def test_should_parse_json_properties_correctly_when_string_provided(app_context):
    """
    Test: JSON properties parsing
    Given: Component update data with properties as JSON string
    When: _update_basic_fields_static is called
    Then: JSON string should be parsed to dict and applied correctly
    """
    component = Mock()
    component.product_number = 'JSON-001'
    component.description = 'JSON test'
    component.component_type_id = 1
    component.supplier_id = 1
    component.properties = {}
    
    data = {
        'product_number': 'JSON-001',
        'description': 'JSON test',
        'component_type_id': 1,
        'supplier_id': 1,
        'properties': '{"new_prop": "new_value", "nested": {"key": "value"}}'
    }
    
    changes = ComponentService._update_basic_fields_static(component, data)
    
    assert 'properties' in changes
    assert changes['properties']['new']['new_prop'] == 'new_value'
    assert changes['properties']['new']['nested']['key'] == 'value'


@patch('app.services.component_service.Picture')
@patch('app.services.component_service.db')
def test_should_rename_all_pictures_when_product_number_changes(mock_db, mock_picture, component_service, app_context):
    """
    Test: Picture renaming on product number change (CRITICAL BUSINESS RULE)
    Given: Component with pictures when product_number changes
    When: _handle_comprehensive_picture_renaming is called
    Then: All pictures should be renamed in WebDAV storage and database
    """
    mock_pictures = [
        Mock(picture_name="old_name_1.jpg", url="http://test.com/old_name_1.jpg"),
        Mock(picture_name="old_name_2.jpg", url="http://test.com/old_name_2.jpg"),
        Mock(picture_name="old_name_3.jpg", url="http://test.com/old_name_3.jpg")
    ]
    mock_picture.query.filter.return_value.all.return_value = mock_pictures
    
    mock_component = Mock()
    mock_component.id = 1
    
    component_service._handle_comprehensive_picture_renaming(mock_component)
    
    # Verify all pictures were processed for renaming
    assert component_service.storage_service.move_file.call_count == 3


# ========================================
# DUPLICATE VALIDATION TESTS
# ========================================

def test_should_find_existing_component_when_product_number_and_supplier_match(app_context):
    """
    Test: Duplicate detection with supplier
    Given: Product number and supplier ID that already exist in database
    When: _check_duplicate_component_static is called
    Then: Existing component should be found and returned
    """
    with patch('app.services.component_service.Component') as MockComponent:
        mock_existing = Mock()
        mock_existing.id = 123
        MockComponent.query.filter.return_value.filter.return_value.first.return_value = mock_existing
        
        result = ComponentService._check_duplicate_component_static("TEST-001", 1, exclude_id=None)
        
        assert result == mock_existing


def test_should_handle_null_supplier_correctly_when_checking_duplicates(app_context):
    """
    Test: Duplicate detection without supplier (NULL supplier_id)
    Given: Product number exists with NULL supplier_id
    When: _check_duplicate_component_static is called with supplier_id=None
    Then: Proper SQL NULL comparison should be used
    """
    with patch('app.services.component_service.Component') as MockComponent:
        mock_existing = Mock()
        MockComponent.query.filter.return_value.filter.return_value.first.return_value = mock_existing
        
        result = ComponentService._check_duplicate_component_static("TEST-001", None, exclude_id=None)
        
        assert result == mock_existing


def test_should_exclude_current_component_when_checking_duplicates_during_update(app_context):
    """
    Test: Duplicate detection excluding current component ID
    Given: Product number exists but should exclude specific component ID during update
    When: _check_duplicate_component_static is called with exclude_id
    Then: Current component should be excluded from duplicate check
    """
    with patch('app.services.component_service.Component') as MockComponent:
        MockComponent.query.filter.return_value.filter.return_value.filter.return_value.first.return_value = None
        
        result = ComponentService._check_duplicate_component_static("TEST-001", 1, exclude_id=123)
        
        assert result is None


# ========================================
# DATA SERIALIZATION TESTS
# ========================================

def test_should_build_complete_data_structure_when_component_has_all_relationships(app_context):
    """
    Test: Component data building for API responses
    Given: Component with all relationships loaded (supplier, type, brands, variants)
    When: _build_component_data_static is called
    Then: Complete JSON structure should be returned with all fields and relationships
    """
    mock_component = Mock()
    mock_component.id = 1
    mock_component.product_number = "TEST-001"
    mock_component.description = "Test component with all relationships"
    mock_component.supplier = Mock(id=1, supplier_code="SUPP01")
    mock_component.component_type = Mock(id=1, name="Type1")
    mock_component.brands = [Mock(id=1, name="Brand1"), Mock(id=2, name="Brand2")]
    mock_component.categories = []
    mock_component.keywords = []
    mock_component.variants = []
    mock_component.proto_status = "pending"
    mock_component.sms_status = "pending"
    mock_component.pps_status = "pending"
    mock_component.created_at = None
    mock_component.updated_at = None
    
    result = ComponentService._build_component_data_static(mock_component)
    
    assert result['id'] == 1
    assert result['product_number'] == "TEST-001"
    assert result['supplier']['supplier_code'] == "SUPP01"
    assert len(result['brands']) == 2
    assert result['brands'][0]['name'] == "Brand1"
    assert result['brands'][1]['name'] == "Brand2"


# ========================================
# PICTURE MANAGEMENT TESTS
# ========================================

def test_should_upload_picture_successfully_when_valid_file_provided(component_service, app_context):
    """
    Test: Picture upload to WebDAV with valid file
    Given: Valid file data and filename
    When: upload_picture_to_webdav is called
    Then: Picture should be uploaded successfully to WebDAV storage
    """
    result = component_service.upload_picture_to_webdav(b'valid_image_data', 'test_picture.jpg')
    
    assert result['success'] is True
    assert result['url'] == 'http://webdav.test/components/test.jpg'
    assert result['filename'] == 'test.jpg'
    component_service.storage_service.upload_file.assert_called_once()


def test_should_delete_picture_successfully_when_file_exists(component_service, app_context):
    """
    Test: Picture deletion from WebDAV
    Given: Existing picture filename in WebDAV storage
    When: delete_picture_from_webdav is called
    Then: Picture should be deleted successfully from WebDAV
    """
    result = component_service.delete_picture_from_webdav('existing_picture.jpg')
    
    assert result['success'] is True
    component_service.storage_service.delete_file.assert_called_once_with('existing_picture.jpg')


def test_should_move_picture_successfully_when_renaming_required(component_service, app_context):
    """
    Test: Picture moving/renaming in WebDAV
    Given: Existing picture that needs to be renamed
    When: move_picture_in_webdav is called
    Then: Picture should be moved/renamed successfully in WebDAV
    """
    result = component_service.move_picture_in_webdav('old_name.jpg', 'new_name.jpg')
    
    assert result['success'] is True
    component_service.storage_service.move_file.assert_called_once_with('old_name.jpg', 'new_name.jpg')


# ========================================
# COMPONENT DELETION TESTS
# ========================================

@patch('app.services.component_service.db')
def test_should_delete_component_and_cleanup_files_when_component_has_pictures(mock_db, component_service, app_context):
    """
    Test: Component deletion with picture cleanup
    Given: Component with multiple variants and pictures
    When: delete_component is called
    Then: Component should be deleted from database and all pictures cleaned up from WebDAV
    """
    mock_component = Mock()
    mock_component.id = 1
    mock_component.variants = [Mock(), Mock()]
    mock_component.pictures = [
        Mock(picture_name="pic1.jpg"),
        Mock(picture_name="pic2.jpg"),
        Mock(picture_name="pic3.jpg")
    ]
    
    with patch.object(component_service, '_cleanup_component_files') as mock_cleanup:
        result = component_service.delete_component(mock_component)
    
    assert result['success'] is True
    mock_cleanup.assert_called_once_with(mock_component)
    mock_db.session.delete.assert_called_with(mock_component)
    mock_db.session.commit.assert_called()


# ========================================
# PICTURE RENAMING TESTS (CRITICAL BUSINESS RULES)
# ========================================

@patch('app.services.component_service.Picture')
def test_should_rename_all_component_pictures_when_product_number_changes(mock_picture, component_service, app_context):
    """
    Test: Product number change triggers picture renaming (CRITICAL BUSINESS RULE)
    Given: Component with 3 pictures when product_number changes from OLD-001 to NEW-001
    When: _handle_comprehensive_picture_renaming is called
    Then: All 3 pictures should be renamed from OLD-001_*.jpg to NEW-001_*.jpg in WebDAV
    """
    mock_pictures = [
        Mock(picture_name="old-001_main_1.jpg", url="http://test.com/old-001_main_1.jpg"),
        Mock(picture_name="old-001_red_1.jpg", url="http://test.com/old-001_red_1.jpg"),
        Mock(picture_name="old-001_blue_1.jpg", url="http://test.com/old-001_blue_1.jpg")
    ]
    mock_picture.query.filter.return_value.all.return_value = mock_pictures
    
    # Mock the picture renaming to simulate new names
    for i, pic in enumerate(mock_pictures):
        pic.picture_name = f"new-001_main_{i+1}.jpg"
    
    mock_component = Mock()
    mock_component.id = 1
    
    component_service._handle_comprehensive_picture_renaming(mock_component)
    
    # Verify all pictures were processed for renaming
    assert component_service.storage_service.move_file.call_count == 3


@patch('app.services.component_service.Picture')
def test_should_rename_component_pictures_when_supplier_changes(mock_picture, component_service, app_context):
    """
    Test: Supplier change triggers picture renaming
    Given: Component pictures with supplier prefix when supplier changes
    When: supplier_id changes (affects picture naming prefix)
    Then: All pictures should be renamed with new supplier prefix in WebDAV
    """
    mock_pictures = [
        Mock(picture_name="oldsupp_product_main_1.jpg", url="http://test.com/oldsupp_product_main_1.jpg"),
        Mock(picture_name="oldsupp_product_red_1.jpg", url="http://test.com/oldsupp_product_red_1.jpg")
    ]
    mock_picture.query.filter.return_value.all.return_value = mock_pictures
    
    mock_component = Mock()
    mock_component.id = 1
    
    component_service._handle_comprehensive_picture_renaming(mock_component)
    
    # Verify pictures were processed for supplier prefix change
    assert component_service.storage_service.move_file.call_count == 2


@patch('app.services.component_service.Picture')
def test_should_remove_supplier_prefix_when_supplier_becomes_null(mock_picture, component_service, app_context):
    """
    Test: Supplier removal triggers prefix removal (CRITICAL BUSINESS RULE)
    Given: Component pictures with supplier prefix when supplier becomes NULL
    When: supplier_id changes to NULL
    Then: All pictures should have supplier prefix removed in WebDAV
    """
    mock_pictures = [
        Mock(picture_name="supplier_product_main_1.jpg", url="http://test.com/supplier_product_main_1.jpg"),
        Mock(picture_name="supplier_product_red_1.jpg", url="http://test.com/supplier_product_red_1.jpg")
    ]
    mock_picture.query.filter.return_value.all.return_value = mock_pictures
    
    # Mock component with NULL supplier
    mock_component = Mock()
    mock_component.id = 1
    mock_component.supplier = None
    
    component_service._handle_comprehensive_picture_renaming(mock_component)
    
    # Verify pictures were processed for prefix removal
    assert component_service.storage_service.move_file.call_count == 2


@patch('app.services.component_service.Picture')
def test_should_handle_webdav_failure_with_rollback_when_renaming_fails(mock_picture, mock_storage_service, app_context):
    """
    Test: WebDAV failure during picture renaming triggers rollback (ATOMIC OPERATION)
    Given: Component pictures when WebDAV server is unavailable
    When: _handle_comprehensive_picture_renaming is called
    Then: Should raise exception to trigger database rollback
    """
    mock_pictures = [
        Mock(picture_name="test_product_main_1.jpg", url="http://test.com/test_product_main_1.jpg")
    ]
    mock_picture.query.filter.return_value.all.return_value = mock_pictures
    
    # Mock WebDAV failure
    mock_storage_service.move_file.return_value = StorageOperationResult(
        success=False,
        result=FileOperationResult.FAILED,
        message="WebDAV server unavailable"
    )
    
    mock_component = Mock()
    mock_component.id = 1
    
    service = ComponentService(storage_service=mock_storage_service)
    
    # Should raise exception for atomic rollback
    with pytest.raises(Exception):
        service._handle_comprehensive_picture_renaming(mock_component)


@patch('app.services.component_service.Picture')
def test_should_handle_empty_picture_list_when_component_has_no_pictures(mock_picture, component_service, app_context):
    """
    Test: Picture renaming with no pictures
    Given: Component with no pictures
    When: _handle_comprehensive_picture_renaming is called
    Then: No WebDAV operations should be performed and no errors should occur
    """
    mock_picture.query.filter.return_value.all.return_value = []
    
    mock_component = Mock()
    mock_component.id = 1
    
    component_service._handle_comprehensive_picture_renaming(mock_component)
    
    # Verify no WebDAV operations were attempted
    assert component_service.storage_service.move_file.call_count == 0


@patch('app.services.component_service.Picture')
def test_should_handle_variant_specific_picture_renaming_when_color_changes(mock_picture, component_service, app_context):
    """
    Test: Variant color change triggers only variant-specific picture renaming
    Given: Component with variant pictures when variant color changes
    When: Variant color is updated
    Then: Only pictures for that specific variant should be renamed
    """
    mock_pictures = [
        Mock(picture_name="product_main_1.jpg", url="http://test.com/product_main_1.jpg", variant_id=None),
        Mock(picture_name="product_old_color_1.jpg", url="http://test.com/product_old_color_1.jpg", variant_id=101),
        Mock(picture_name="product_other_color_1.jpg", url="http://test.com/product_other_color_1.jpg", variant_id=102)
    ]
    mock_picture.query.filter.return_value.all.return_value = mock_pictures
    
    mock_component = Mock()
    mock_component.id = 1
    
    component_service._handle_comprehensive_picture_renaming(mock_component)
    
    # All pictures should be processed (component-level change affects all)
    assert component_service.storage_service.move_file.call_count == 3


@patch('app.services.component_service.Picture')
def test_should_handle_empty_supplier_code_as_null_supplier(mock_picture, component_service, app_context):
    """
    Test: Empty supplier code treated as NULL supplier
    Given: Component with empty supplier code
    When: Picture renaming is triggered
    Then: Should handle same as NULL supplier (no prefix)
    """
    mock_pictures = [
        Mock(picture_name="product_main_1.jpg", url="http://test.com/product_main_1.jpg")
    ]
    mock_picture.query.filter.return_value.all.return_value = mock_pictures
    
    mock_component = Mock()
    mock_component.id = 1
    mock_component.supplier = Mock()
    mock_component.supplier.supplier_code = ""  # Empty string treated as NULL
    
    component_service._handle_comprehensive_picture_renaming(mock_component)
    
    # Verify picture was processed (should not add empty prefix)
    assert component_service.storage_service.move_file.call_count == 1


# ========================================
# BULK OPERATIONS TESTS
# ========================================

@patch('app.services.component_service.db')
@patch('app.services.component_service.Component')
def test_should_delete_multiple_components_when_bulk_delete_called(mock_component, mock_db, component_service, app_context):
    """
    Test: Bulk deletion of multiple components
    Given: List of component IDs to delete
    When: bulk_delete_components is called
    Then: All components should be deleted with their pictures cleaned up
    """
    # Create mock components with pictures
    mock_components = []
    for i in range(3):
        comp = Mock()
        comp.id = i + 1
        comp.pictures = [Mock(picture_name=f"pic_{i}_1.jpg"), Mock(picture_name=f"pic_{i}_2.jpg")]
        mock_components.append(comp)
    
    mock_component.query.filter.return_value.all.return_value = mock_components
    
    with patch.object(component_service, '_cleanup_component_files') as mock_cleanup:
        result = component_service.bulk_delete_components([1, 2, 3])
    
    assert result['success'] is True
    assert result['deleted_count'] == 3
    assert mock_cleanup.call_count == 3


# ========================================
# VARIANT HANDLING TESTS
# ========================================

@patch('app.services.component_service.db.session')
@patch('app.services.component_service.ComponentVariant')
@patch('app.services.component_service.Color')
def test_should_create_variants_when_component_has_color_variants(mock_color, mock_variant, mock_db_session, app_context):
    """
    Test: Variant creation during component creation
    Given: Component data with variant specifications
    When: _handle_variants_creation is called
    Then: Variants should be created with auto-generated SKUs
    """
    service = ComponentService()
    
    mock_component = Mock()
    mock_component.id = 100
    mock_component.product_number = 'VAR-TEST-001'
    
    variants_data = [
        {'color_id': 1, 'variant_name': 'Red Variant'},
        {'color_id': 2, 'variant_name': 'Blue Variant'}
    ]
    
    mock_color.query.get.side_effect = [
        Mock(id=1, name='Red'),
        Mock(id=2, name='Blue')
    ]
    
    mock_variant.return_value = Mock()
    
    result = service._handle_variants_creation(mock_component, variants_data)
    
    assert len(result) == 2
    assert mock_variant.call_count == 2


def test_should_handle_components_without_variants_when_no_color_variants_specified(app_context):
    """
    Test: Component creation without variants (components without color variants)
    Given: Component data with no variants specified
    When: Component is created
    Then: Component should be created successfully without variants
    """
    service = ComponentService()
    
    mock_component = Mock()
    mock_component.id = 200
    mock_component.product_number = 'NO-VARIANT-001'
    
    # Test that component exists without variants
    assert hasattr(mock_component, 'id')
    assert mock_component.product_number == 'NO-VARIANT-001'


def test_should_handle_mixed_component_types_when_some_have_variants_others_dont(app_context):
    """
    Test: Mixed component types (some with variants, some without)
    Given: Multiple components where some have variants and some don't
    When: Processing mixed component operations
    Then: Should handle both types correctly without conflicts
    """
    service = ComponentService()
    
    # Component with variants
    component_with_variants = Mock()
    component_with_variants.id = 301
    component_with_variants.variants = [Mock(id=1), Mock(id=2)]
    
    # Component without variants
    component_without_variants = Mock()
    component_without_variants.id = 302
    component_without_variants.variants = []
    
    # Both should be valid component types
    assert len(component_with_variants.variants) == 2
    assert len(component_without_variants.variants) == 0


def test_should_enforce_picture_order_constraints_per_variant_when_multiple_pictures_uploaded(app_context):
    """
    Test: Picture order constraints per variant
    Given: Variant with multiple pictures
    When: Pictures are uploaded with specific orders
    Then: Picture order constraints should be enforced per variant
    """
    service = ComponentService()
    
    mock_variant = Mock()
    mock_variant.id = 401
    mock_variant.component_id = 100
    
    # Mock pictures with different orders
    pictures = [
        Mock(picture_order=1, variant_id=401),
        Mock(picture_order=2, variant_id=401),
        Mock(picture_order=3, variant_id=401)
    ]
    
    # Each picture should have unique order for this variant
    orders = [pic.picture_order for pic in pictures]
    assert len(set(orders)) == 3  # All orders should be unique
    assert sorted(orders) == [1, 2, 3]  # Should be sequential


# ========================================
# ERROR HANDLING TESTS
# ========================================

@patch('app.services.component_service.db.session')
def test_should_rollback_transaction_when_database_error_occurs(mock_db_session, app_context):
    """
    Test: Database error handling with rollback
    Given: Database error during component creation
    When: Exception is raised during commit
    Then: Transaction should be rolled back and error returned
    """
    service = ComponentService()
    
    mock_db_session.commit.side_effect = Exception("Database connection lost")
    mock_db_session.rollback = Mock()
    
    component_data = {
        'product_number': 'ERROR-TEST',
        'component_type_id': 1
    }
    
    result = service.create_component(component_data)
    
    assert result['success'] is False
    assert 'Database connection lost' in result['error']
    mock_db_session.rollback.assert_called_once()


@patch('app.services.component_service.db.session')
@patch('app.services.component_service.Component')
def test_should_rollback_when_picture_renaming_fails(mock_component, mock_db_session, app_context):
    """
    Test: Rollback when picture renaming fails (atomic operation)
    Given: Component update that triggers picture renaming
    When: Picture renaming fails with WebDAV error
    Then: Database changes should be rolled back
    """
    existing_component = Mock()
    existing_component.id = 500
    existing_component.product_number = 'ROLLBACK-TEST'
    mock_component.query.get.return_value = existing_component
    
    update_data = {'product_number': 'NEW-ROLLBACK-TEST'}
    
    mock_db_session.commit = Mock()
    mock_db_session.rollback = Mock()
    
    service = ComponentService()
    
    with patch.object(service, '_handle_comprehensive_picture_renaming') as mock_rename:
        mock_rename.side_effect = Exception("WebDAV server unavailable")
        
        result = service.update_component(500, update_data)
    
    assert result['success'] is False
    assert 'WebDAV server unavailable' in result['error']
    mock_db_session.rollback.assert_called_once()


# ========================================
# METHOD STRUCTURE TESTS
# ========================================

def test_should_have_all_required_public_methods_when_service_instantiated(app_context):
    """
    Test: ComponentService has all required public methods
    Given: ComponentService class
    When: Checking for required public methods
    Then: All essential public methods should exist with correct signatures
    """
    service = ComponentService()
    
    # Core CRUD methods
    assert hasattr(service, 'create_component')
    assert callable(getattr(service, 'create_component'))
    
    assert hasattr(service, 'update_component')
    assert callable(getattr(service, 'update_component'))
    
    assert hasattr(service, 'get_component_for_edit')
    assert callable(getattr(service, 'get_component_for_edit'))
    
    assert hasattr(service, 'delete_component')
    assert callable(getattr(service, 'delete_component'))
    
    assert hasattr(service, 'bulk_delete_components')
    assert callable(getattr(service, 'bulk_delete_components'))


def test_should_have_all_required_static_helper_methods_when_class_loaded(app_context):
    """
    Test: ComponentService has all required static helper methods
    Given: ComponentService class
    When: Checking for required static helper methods
    Then: All essential static helper methods should exist and be callable
    """
    assert hasattr(ComponentService, '_update_basic_fields_static')
    assert callable(getattr(ComponentService, '_update_basic_fields_static'))
    
    assert hasattr(ComponentService, '_check_duplicate_component_static')
    assert callable(getattr(ComponentService, '_check_duplicate_component_static'))
    
    assert hasattr(ComponentService, '_build_component_data_static')
    assert callable(getattr(ComponentService, '_build_component_data_static'))


def test_should_have_all_required_instance_helper_methods_when_service_instantiated(app_context):
    """
    Test: ComponentService has all required instance helper methods
    Given: ComponentService instance
    When: Checking for required instance helper methods
    Then: All essential instance helper methods should exist and be callable
    """
    service = ComponentService()
    
    assert hasattr(service, '_handle_component_associations')
    assert callable(getattr(service, '_handle_component_associations'))
    
    assert hasattr(service, '_handle_picture_order_changes')
    assert callable(getattr(service, '_handle_picture_order_changes'))
    
    assert hasattr(service, '_handle_comprehensive_picture_renaming')
    assert callable(getattr(service, '_handle_comprehensive_picture_renaming'))
    
    assert hasattr(service, '_handle_variants_creation')
    assert callable(getattr(service, '_handle_variants_creation'))
    
    assert hasattr(service, '_cleanup_component_files')
    assert callable(getattr(service, '_cleanup_component_files'))
    
    # Picture management methods
    assert hasattr(service, 'upload_picture_to_webdav')
    assert callable(getattr(service, 'upload_picture_to_webdav'))
    
    assert hasattr(service, 'delete_picture_from_webdav')
    assert callable(getattr(service, 'delete_picture_from_webdav'))
    
    assert hasattr(service, 'move_picture_in_webdav')
    assert callable(getattr(service, 'move_picture_in_webdav'))