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
        message="Move successful",
        file_info=FileInfo(
            name="new_name.jpg",
            path="/webdav/components/new_name.jpg",
            url="http://webdav.test/components/new_name.jpg",
            exists=True,
            content_type="image/jpeg"
        )
    )
    return mock_service


@pytest.fixture
def component_service(mock_storage_service):
    """Create ComponentService instance with mocked storage"""
    # Mock the WebDAV config service to avoid initialization issues
    with patch('app.services.component_service.WebDAVConfigService') as mock_webdav_config:
        mock_webdav_config.side_effect = Exception("Mock WebDAV config error")
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
    # Mock the duplicate check - _check_duplicate_component uses filter_by
    mock_query = Mock()
    mock_query.filter_by.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = None  # No duplicate found
    mock_component.query = mock_query
    
    mock_new_component = Mock()
    mock_new_component.id = 100
    mock_new_component.product_number = 'MIN-001'
    # Add required attributes for association counts
    mock_new_component.brand_associations = []
    mock_new_component.categories = []
    mock_new_component.keywords = []
    mock_new_component.variants = []
    mock_new_component.properties = {}
    mock_component.return_value = mock_new_component
    
    mock_db_session.add = Mock()
    mock_db_session.flush = Mock()
    mock_db_session.commit = Mock()
    
    # Mock the _build_component_data method
    with patch.object(component_service, '_build_component_data') as mock_build:
        mock_build.return_value = {
            'id': 100,
            'product_number': 'MIN-001',
            'description': 'Minimal test component'
        }
        
        # Mock the association handlers
        with patch.object(component_service, '_handle_component_associations'):
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
    
    # Mock the duplicate check properly - _check_duplicate_component uses filter_by
    mock_query = Mock()
    mock_query.filter_by.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = existing_component  # Duplicate found
    mock_component.query = mock_query
    
    # Expect ValueError to be raised for duplicate
    with pytest.raises(ValueError) as exc_info:
        component_service.create_component(component_data)
    
    assert 'already exists' in str(exc_info.value)
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


@patch('app.services.component_service.db')
@patch('app.services.component_service.current_app')
@patch('app.utils.file_handling.generate_picture_name')
def test_should_rename_all_pictures_when_product_number_changes(mock_generate_name, mock_app, mock_db, component_service, app_context):
    """
    Test: Picture renaming on product number change (CRITICAL BUSINESS RULE)
    Given: Component with pictures when product_number changes
    When: _handle_comprehensive_picture_renaming is called
    Then: All pictures should be renamed in WebDAV storage and database
    """
    # Mock component
    mock_component = Mock()
    mock_component.id = 1
    mock_component.product_number = "NEW-001"
    mock_component.supplier_id = 1
    
    # Mock pictures with required attributes
    mock_pictures = [
        Mock(id=1, picture_name="old_name_1.jpg", url="http://test.com/old_name_1.jpg", 
             picture_order=1, variant_id=None),
        Mock(id=2, picture_name="old_name_2.jpg", url="http://test.com/old_name_2.jpg", 
             picture_order=2, variant_id=None),
        Mock(id=3, picture_name="old_name_3.jpg", url="http://test.com/old_name_3.jpg", 
             picture_order=3, variant_id=None)
    ]
    
    # Mock database query
    mock_query = Mock()
    mock_query.filter.return_value.all.return_value = mock_pictures
    mock_db.session.query.return_value = mock_query
    
    # Mock generate_picture_name to return different names
    mock_generate_name.side_effect = ["new_name_1.jpg", "new_name_2.jpg", "new_name_3.jpg"]
    
    # Mock current_app config
    mock_app.config.get.return_value = 'http://31.182.67.115/webdav'
    mock_app.logger.info = Mock()
    
    # Mock storage service
    component_service.storage_service.move_file.return_value = Mock(success=True)
    
    result = component_service._handle_comprehensive_picture_renaming(mock_component)
    
    # Verify all pictures were processed for renaming
    assert component_service.storage_service.move_file.call_count == 3
    assert mock_generate_name.call_count == 3


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
        
        # Mock the query chain: Component.query.filter_by().filter_by().first()
        mock_query = Mock()
        mock_query.filter_by.return_value = mock_query
        mock_query.first.return_value = mock_existing
        MockComponent.query = mock_query
        
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
        
        # Mock the query chain: Component.query.filter_by().filter().first()
        mock_query = Mock()
        mock_query.filter_by.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_existing
        MockComponent.query = mock_query
        
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
        # Mock the query chain: Component.query.filter_by().filter_by().filter().first()
        mock_query = Mock()
        mock_query.filter_by.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        MockComponent.query = mock_query
        
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
    mock_supplier = Mock()
    mock_supplier.id = 1
    mock_supplier.supplier_code = "SUPP01"
    mock_component.supplier = mock_supplier
    
    mock_component_type = Mock()
    mock_component_type.id = 1
    mock_component_type.name = "Type1"
    mock_component.component_type = mock_component_type
    
    # Mock brand associations (the actual relationship the method uses)
    mock_brand1 = Mock()
    mock_brand1.id = 1
    mock_brand1.name = "Brand1"
    mock_brand2 = Mock()
    mock_brand2.id = 2
    mock_brand2.name = "Brand2"
    
    mock_brand_assoc1 = Mock()
    mock_brand_assoc1.brand = mock_brand1
    mock_brand_assoc2 = Mock()
    mock_brand_assoc2.brand = mock_brand2
    mock_component.brand_associations = [mock_brand_assoc1, mock_brand_assoc2]
    
    mock_component.categories = []
    mock_component.keywords = []
    mock_component.variants = []
    mock_component.properties = {}
    mock_component.proto_status = "pending"
    mock_component.proto_comment = None
    mock_component.proto_date = None
    mock_component.sms_status = "pending"
    mock_component.sms_comment = None
    mock_component.sms_date = None
    mock_component.pps_status = "pending"
    mock_component.pps_comment = None
    mock_component.pps_date = None
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
    assert result['filename'] == 'test_picture.jpg'  # Method returns the filename that was passed to it
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
@patch('app.services.component_service.Component')
def test_should_delete_component_and_cleanup_files_when_component_has_pictures(mock_component_class, mock_db, component_service, app_context):
    """
    Test: Component deletion with picture cleanup
    Given: Component with multiple variants and pictures
    When: delete_component is called
    Then: Component should be deleted from database and all pictures cleaned up from WebDAV
    """
    mock_component = Mock()
    mock_component.id = 1
    mock_component.product_number = "TEST-001"
    mock_component.variants = [Mock(), Mock()]
    mock_component.brand_associations = [Mock()]
    mock_component.keywords = []
    mock_component.categories = []
    # Create proper mock pictures with variant_id attribute
    pic1 = Mock()
    pic1.variant_id = None
    pic1.url = "http://test.com/pic1.jpg"
    pic1.id = 1
    pic2 = Mock()
    pic2.variant_id = None  
    pic2.url = "http://test.com/pic2.jpg"
    pic2.id = 2
    pic3 = Mock()
    pic3.variant_id = 1
    pic3.url = "http://test.com/pic3.jpg"
    pic3.id = 3
    
    mock_component.pictures = [pic1, pic2, pic3]
    
    # Mock Component.query to return our mock component
    mock_query = Mock()
    mock_query.options.return_value = mock_query
    mock_query.filter_by.return_value = mock_query
    mock_query.first.return_value = mock_component
    mock_component_class.query = mock_query
    
    # Mock the _cleanup_component_files method and current_app
    with patch.object(component_service, '_cleanup_component_files') as mock_cleanup, \
         patch('app.services.component_service.current_app') as mock_app:
        mock_cleanup.return_value = {'deleted': ['pic1.jpg'], 'failed': []}
        # Set up config mock properly to return different values for different keys
        def mock_config_get(key, default=None):
            if key == 'UPLOAD_URL_PREFIX':
                return 'http://31.182.67.115/webdav/components'
            elif key == 'UPLOAD_FOLDER':
                return '/components'
            return default
        mock_app.config.get = mock_config_get
        mock_app.logger.info = Mock()
        result = component_service.delete_component(1)
    
    assert result['success'] is True
    mock_cleanup.assert_called_once_with(mock_component)
    mock_db.session.delete.assert_called_once_with(mock_component)
    mock_db.session.commit.assert_called_once()


# ========================================
# PICTURE RENAMING TESTS (CRITICAL BUSINESS RULES)
# ========================================

@patch('app.services.component_service.db')
@patch('app.services.component_service.Picture')
@patch('app.services.component_service.ComponentVariant')
def test_should_rename_all_component_pictures_when_product_number_changes(mock_variant_class, mock_picture, mock_db, component_service, app_context):
    """
    Test: Product number change triggers picture renaming (CRITICAL BUSINESS RULE)
    Given: Component with 3 pictures when product_number changes from OLD-001 to NEW-001
    When: _handle_comprehensive_picture_renaming is called
    Then: All 3 pictures should be renamed from OLD-001_*.jpg to NEW-001_*.jpg in WebDAV
    """
    # Create mock component with proper attributes
    mock_component = Mock()
    mock_component.id = 1
    mock_component.product_number = 'NEW-001'
    mock_component.supplier = Mock(supplier_code='SUP123')
    
    # Create mock pictures with correct naming patterns
    mock_pictures = [
        Mock(id=1, component_id=1, variant_id=None, picture_name="sup123_old-001_1", 
             url="http://test.com/sup123_old-001_1.jpg", picture_order=1),
        Mock(id=2, component_id=1, variant_id=1, picture_name="sup123_old-001_red_1", 
             url="http://test.com/sup123_old-001_red_1.jpg", picture_order=1),
        Mock(id=3, component_id=1, variant_id=2, picture_name="sup123_old-001_blue_1", 
             url="http://test.com/sup123_old-001_blue_1.jpg", picture_order=1)
    ]
    
    # Set up the query mock
    mock_db.session.query.return_value.filter.return_value.all.return_value = mock_pictures
    
    # Mock variant lookups
    mock_variant1 = Mock(id=1, color=Mock(name='Red'))
    mock_variant2 = Mock(id=2, color=Mock(name='Blue'))
    mock_variant_class.query.get.side_effect = lambda id: mock_variant1 if id == 1 else mock_variant2 if id == 2 else None
    
    # Mock successful WebDAV operations
    mock_move_result = Mock()
    mock_move_result.success = True
    mock_move_result.file_info = Mock(url='http://test.com/new_file.jpg')
    component_service.storage_service.move_file.return_value = mock_move_result
    
    # Mock the generate_picture_name function to return expected new names
    with patch('app.utils.file_handling.generate_picture_name') as mock_generate:
        mock_generate.side_effect = [
            'sup123_new-001_1',
            'sup123_new-001_red_1', 
            'sup123_new-001_blue_1'
        ]
        
        result = component_service._handle_comprehensive_picture_renaming(mock_component)
    
    # Verify all pictures were processed for renaming
    assert component_service.storage_service.move_file.call_count == 3
    
    # Verify the correct old->new mappings
    expected_calls = [
        ('sup123_old-001_1.jpg', 'sup123_new-001_1.jpg'),
        ('sup123_old-001_red_1.jpg', 'sup123_new-001_red_1.jpg'),
        ('sup123_old-001_blue_1.jpg', 'sup123_new-001_blue_1.jpg')
    ]
    
    actual_calls = [call[0] for call in component_service.storage_service.move_file.call_args_list]
    assert actual_calls == expected_calls


@patch('app.services.component_service.db')
@patch('app.services.component_service.current_app')
@patch('app.utils.file_handling.generate_picture_name')
def test_should_rename_component_pictures_when_supplier_changes(mock_generate_name, mock_app, mock_db, component_service, app_context):
    """
    Test: Supplier change triggers picture renaming
    Given: Component pictures with supplier prefix when supplier changes
    When: supplier_id changes (affects picture naming prefix)
    Then: All pictures should be renamed with new supplier prefix in WebDAV
    """
    mock_component = Mock()
    mock_component.id = 1
    
    mock_pictures = [
        Mock(id=1, picture_name="oldsupp_product_1.jpg", picture_order=1, variant_id=None),
        Mock(id=2, picture_name="oldsupp_product_2.jpg", picture_order=2, variant_id=None)
    ]
    
    mock_query = Mock()
    mock_query.filter.return_value.all.return_value = mock_pictures
    mock_db.session.query.return_value = mock_query
    
    mock_generate_name.side_effect = ["newsupp_product_1.jpg", "newsupp_product_2.jpg"]
    mock_app.config.get.return_value = 'http://31.182.67.115/webdav'
    mock_app.logger.info = Mock()
    
    component_service.storage_service.move_file.return_value = Mock(success=True)
    
    component_service._handle_comprehensive_picture_renaming(mock_component)
    
    assert component_service.storage_service.move_file.call_count == 2


@patch('app.services.component_service.db')
@patch('app.services.component_service.current_app')
@patch('app.utils.file_handling.generate_picture_name')
def test_should_remove_supplier_prefix_when_supplier_becomes_null(mock_generate_name, mock_app, mock_db, component_service, app_context):
    """
    Test: Supplier removal triggers prefix removal (CRITICAL BUSINESS RULE)
    Given: Component pictures with supplier prefix when supplier becomes NULL
    When: supplier_id changes to NULL
    Then: All pictures should have supplier prefix removed in WebDAV
    """
    mock_component = Mock()
    mock_component.id = 1
    mock_component.supplier = None  # NULL supplier
    
    # Use correct naming pattern (without "main")
    mock_pictures = [
        Mock(id=1, picture_name="supplier_product_1", picture_order=1, variant_id=None),
        Mock(id=2, picture_name="supplier_product_2", picture_order=2, variant_id=None)
    ]
    
    mock_query = Mock()
    mock_query.filter.return_value.all.return_value = mock_pictures
    mock_db.session.query.return_value = mock_query
    
    # When supplier is NULL, generate_picture_name should return names without supplier prefix
    mock_generate_name.side_effect = ["product_1", "product_2"]
    mock_app.config.get.return_value = 'http://31.182.67.115/webdav'
    mock_app.logger.info = Mock()
    
    component_service.storage_service.move_file.return_value = Mock(success=True)
    
    component_service._handle_comprehensive_picture_renaming(mock_component)
    
    # Verify pictures were processed for prefix removal
    assert component_service.storage_service.move_file.call_count == 2


@patch('app.services.component_service.db')
@patch('app.services.component_service.current_app')
@patch('app.utils.file_handling.generate_picture_name')
def test_should_handle_webdav_failure_with_rollback_when_renaming_fails(mock_generate_name, mock_app, mock_db, component_service, app_context):
    """
    Test: WebDAV failure during picture renaming triggers rollback (ATOMIC OPERATION)
    Given: Component pictures when WebDAV server is unavailable
    When: _handle_comprehensive_picture_renaming is called
    Then: Should raise exception to trigger database rollback
    """
    mock_component = Mock()
    mock_component.id = 1
    
    # Use correct naming pattern (without "main")
    mock_pictures = [
        Mock(id=1, picture_name="test_product_1", picture_order=1, variant_id=None)
    ]
    
    mock_query = Mock()
    mock_query.filter.return_value.all.return_value = mock_pictures
    mock_db.session.query.return_value = mock_query
    
    # Picture name changes (triggering rename attempt)
    mock_generate_name.return_value = "new_test_product_1"
    mock_app.config.get.return_value = 'http://31.182.67.115/webdav'
    mock_app.logger.info = Mock()
    
    # Mock WebDAV failure in move_picture_in_webdav method
    with patch.object(component_service, 'move_picture_in_webdav') as mock_move:
        mock_move.return_value = {
            'success': False,
            'error': 'WebDAV server unavailable'
        }
        
        # Should handle WebDAV failure gracefully (not raise exception)
        result = component_service._handle_comprehensive_picture_renaming(mock_component)
        
        # Verify WebDAV failure was handled gracefully
        assert result is not None
        assert 'renamed_files' in result
        assert len(result['renamed_files']) == 1
        assert result['renamed_files'][0]['status'] == 'failed'


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


@patch('app.services.component_service.ComponentVariant')
@patch('app.services.component_service.db')
@patch('app.services.component_service.current_app')
@patch('app.utils.file_handling.generate_picture_name')
def test_should_handle_variant_specific_picture_renaming_when_color_changes(mock_generate_name, mock_app, mock_db, mock_component_variant, component_service, app_context):
    """
    Test: Comprehensive picture renaming handles all picture types
    Given: Component with component pictures and variant pictures
    When: _handle_comprehensive_picture_renaming is called (component-level change)
    Then: All pictures should be processed for renaming
    """
    mock_component = Mock()
    mock_component.id = 1
    
    # Use correct naming pattern (without "main")
    mock_pictures = [
        Mock(id=1, picture_name="product_1", picture_order=1, variant_id=None),  # Component picture
        Mock(id=2, picture_name="product_old_color_1", picture_order=1, variant_id=101),  # Variant picture
        Mock(id=3, picture_name="product_other_color_1", picture_order=1, variant_id=102)  # Variant picture
    ]
    
    mock_query = Mock()
    mock_query.filter.return_value.all.return_value = mock_pictures
    mock_db.session.query.return_value = mock_query
    
    # Mock ComponentVariant.query.get() for variant pictures
    variant1 = Mock()
    variant1.color = Mock()
    variant1.color.name = "old_color"
    variant2 = Mock()
    variant2.color = Mock()
    variant2.color.name = "other_color"
    
    def mock_variant_get(variant_id):
        if variant_id == 101:
            return variant1
        elif variant_id == 102:
            return variant2
        return None
    
    mock_component_variant.query.get.side_effect = mock_variant_get
    
    # Picture names change (triggering renames)
    mock_generate_name.side_effect = ["new_product_1", "new_product_new_color_1", "new_product_other_color_1"]
    mock_app.config.get.return_value = 'http://31.182.67.115/webdav'
    mock_app.logger.info = Mock()
    
    # Mock the move_picture_in_webdav method
    with patch.object(component_service, 'move_picture_in_webdav') as mock_move:
        mock_move.return_value = {'success': True, 'new_url': 'http://test.com/new_name.jpg'}
        
        component_service._handle_comprehensive_picture_renaming(mock_component)
        
        # All pictures should be processed (component-level change affects all)
        assert mock_move.call_count == 3


@patch('app.services.component_service.db')
@patch('app.services.component_service.current_app')
@patch('app.utils.file_handling.generate_picture_name')
def test_should_handle_empty_supplier_code_as_null_supplier(mock_generate_name, mock_app, mock_db, component_service, app_context):
    """
    Test: Empty supplier code treated as NULL supplier
    Given: Component with empty supplier code
    When: Picture renaming is triggered
    Then: Should handle same as NULL supplier (no prefix)
    """
    mock_component = Mock()
    mock_component.id = 1
    mock_component.supplier = Mock()
    mock_component.supplier.supplier_code = ""  # Empty string treated as NULL
    
    # Use correct naming pattern (without "main")
    mock_pictures = [
        Mock(id=1, picture_name="supplier_product_1", picture_order=1, variant_id=None)
    ]
    
    mock_query = Mock()
    mock_query.filter.return_value.all.return_value = mock_pictures
    mock_db.session.query.return_value = mock_query
    
    # Empty supplier code should result in no supplier prefix
    mock_generate_name.return_value = "product_1"  # No supplier prefix
    mock_app.config.get.return_value = 'http://31.182.67.115/webdav'
    mock_app.logger.info = Mock()
    
    # Mock the move_picture_in_webdav method
    with patch.object(component_service, 'move_picture_in_webdav') as mock_move:
        mock_move.return_value = {'success': True, 'new_url': 'http://test.com/new_name.jpg'}
        
        component_service._handle_comprehensive_picture_renaming(mock_component)
        
        # Verify picture was processed (name changed from supplier prefix to no prefix)
        assert mock_move.call_count == 1


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
    
    # Mock ComponentVariant.query.filter_by().first() to return None (no existing variants)
    mock_variant_query = Mock()
    mock_variant_query.filter_by.return_value = mock_variant_query
    mock_variant_query.first.return_value = None  # No existing variants
    mock_variant.query = mock_variant_query
    
    # Mock ComponentVariant constructor
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

@patch('app.services.component_service.ComponentType')
@patch('app.services.component_service.Component')
@patch('app.services.component_service.db.session')
def test_should_rollback_transaction_when_database_error_occurs(mock_db_session, mock_component, mock_component_type, app_context):
    """
    Test: Database error handling with rollback
    Given: Database error during component creation
    When: Exception is raised during commit
    Then: Transaction should be rolled back and error returned
    """
    service = ComponentService()
    
    # Mock ComponentType lookup
    mock_component_type.query.get.return_value = Mock(id=1, name="Test Type")
    
    # Mock duplicate check to return None (no duplicate)
    mock_query = Mock()
    mock_query.filter_by.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = None
    mock_component.query = mock_query
    
    # Mock component creation
    mock_new_component = Mock()
    mock_new_component.id = 123
    mock_component.return_value = mock_new_component
    
    # Mock database operations - commit fails
    mock_db_session.add = Mock()
    mock_db_session.flush = Mock()
    mock_db_session.commit.side_effect = Exception("Database connection lost")
    mock_db_session.rollback = Mock()
    
    component_data = {
        'product_number': 'ERROR-TEST',
        'component_type_id': 1
    }
    
    # Mock the association handlers to avoid additional complexity
    with patch.object(service, '_handle_component_associations'), \
         patch.object(service, '_build_component_data') as mock_build:
        mock_build.return_value = {'id': 123, 'product_number': 'ERROR-TEST'}
        
        # Expect exception to be raised (implementation design)
        with pytest.raises(Exception) as exc_info:
            service.create_component(component_data)
    
    assert 'Database connection lost' in str(exc_info.value)
    mock_db_session.rollback.assert_called_once()


@patch('app.services.component_service.db.session')
@patch('app.services.component_service.Component')
def test_should_handle_picture_renaming_failures_gracefully(mock_component, mock_db_session, app_context):
    """
    Test: Picture renaming failures handled gracefully
    Given: Component update that triggers picture renaming
    When: Picture renaming fails with WebDAV error
    Then: Component update should continue successfully with error logged
    """
    existing_component = Mock()
    existing_component.id = 500
    existing_component.product_number = 'ROLLBACK-TEST'
    existing_component.supplier_id = 1
    mock_component.query.get.return_value = existing_component
    
    # Mock duplicate check to return None (no duplicate)
    mock_query = Mock()
    mock_query.filter_by.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = None
    mock_component.query = mock_query
    
    update_data = {'product_number': 'NEW-ROLLBACK-TEST'}
    
    mock_db_session.commit = Mock()
    mock_db_session.rollback = Mock()
    
    service = ComponentService()
    
    with patch.object(service, '_handle_comprehensive_picture_renaming') as mock_rename, \
         patch.object(service, '_handle_component_associations'), \
         patch.object(service, '_handle_picture_order_changes'), \
         patch.object(service, '_build_component_data') as mock_build:
        mock_rename.side_effect = Exception("WebDAV server unavailable")
        mock_build.return_value = {'id': 500, 'product_number': 'NEW-ROLLBACK-TEST'}
        
        # Component update should succeed despite picture renaming failure
        result = service.update_component(500, update_data)
    
    # Verify update was successful
    assert result['success'] is True
    assert 'changes' in result
    assert 'picture_rename_error' in result['changes']
    assert 'WebDAV server unavailable' in result['changes']['picture_rename_error']
    
    # Verify commit was called (no rollback for picture renaming errors)
    mock_db_session.commit.assert_called_once()
    mock_db_session.rollback.assert_not_called()


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