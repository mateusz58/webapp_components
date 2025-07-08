import unittest
import json
from unittest.mock import Mock, patch

class TestServiceHelpers(unittest.TestCase):
    """Unit tests for service helper methods"""
    
    def setUp(self):
        """Set up test fixtures"""
        print(f"\n🧪 UNIT TEST SETUP: {self._testMethodName}")
        print(f"🔧 Setting up service helper test environment...")
        print(f"✅ Unit test setup complete for: {self._testMethodName}")

    def test_detect_field_changes(self):
        """Test field change detection logic"""
        print(f"\n🧪 UNIT TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test field change detection")
        
        # Original values
        original = {
            'product_number': 'OLD-001',
            'description': 'Old description',
            'supplier_id': 1
        }
        
        # New values with changes
        updated = {
            'product_number': 'NEW-001',
            'description': 'Old description',  # No change
            'supplier_id': 2
        }
        
        print(f"🔍 Original: {json.dumps(original, indent=2)}")
        print(f"🔍 Updated: {json.dumps(updated, indent=2)}")
        
        changes = self._detect_changes(original, updated)
        
        print(f"📊 Detected changes: {json.dumps(changes, indent=2)}")
        
        # Should detect product_number and supplier_id changes
        self.assertIn('product_number', changes)
        self.assertIn('supplier_id', changes)
        self.assertNotIn('description', changes)  # No change
        
        # Verify change structure
        self.assertEqual(changes['product_number']['old'], 'OLD-001')
        self.assertEqual(changes['product_number']['new'], 'NEW-001')
        
        print(f"✅ UNIT TEST PASSED: Field change detection works")

    def test_validate_required_fields(self):
        """Test required field validation logic"""
        print(f"\n🧪 UNIT TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test required field validation")
        
        required_fields = ['product_number', 'component_type_id']
        
        # Valid data with all required fields
        valid_data = {
            'product_number': 'TEST-001',
            'component_type_id': 1,
            'description': 'Optional field'
        }
        
        print(f"🔍 Testing valid data: {json.dumps(valid_data, indent=2)}")
        result = self._validate_required_fields(valid_data, required_fields)
        print(f"📊 Validation result: {result}")
        
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['missing']), 0)
        
        # Invalid data missing required fields
        invalid_data = {
            'description': 'Missing required fields'
        }
        
        print(f"🔍 Testing invalid data: {json.dumps(invalid_data, indent=2)}")
        result = self._validate_required_fields(invalid_data, required_fields)
        print(f"📊 Validation result: {result}")
        
        self.assertFalse(result['valid'])
        self.assertEqual(len(result['missing']), 2)
        self.assertIn('product_number', result['missing'])
        self.assertIn('component_type_id', result['missing'])
        
        print(f"✅ UNIT TEST PASSED: Required field validation works")

    def test_build_association_data(self):
        """Test association data building logic"""
        print(f"\n🧪 UNIT TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test association data building")
        
        # Mock form data
        form_data = {
            'brand_ids[]': ['1', '2', '3'],
            'categories[]': ['10', '20'],
            'keywords': 'tag1,tag2,tag3'
        }
        
        print(f"🔍 Testing form data: {json.dumps(form_data, indent=2)}")
        
        result = self._build_association_data(form_data)
        
        print(f"📊 Association data: {json.dumps(result, indent=2)}")
        
        # Verify structure
        self.assertIn('brands', result)
        self.assertIn('categories', result)
        self.assertIn('keywords', result)
        
        # Verify converted data
        self.assertEqual(result['brands'], [1, 2, 3])
        self.assertEqual(result['categories'], [10, 20])
        self.assertEqual(result['keywords'], ['tag1', 'tag2', 'tag3'])
        
        print(f"✅ UNIT TEST PASSED: Association data building works")

    def test_calculate_component_score(self):
        """Test component completeness scoring"""
        print(f"\n🧪 UNIT TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test component completeness scoring")
        
        # Complete component
        complete_component = {
            'product_number': 'COMPLETE-001',
            'description': 'Complete component',
            'supplier_id': 1,
            'component_type_id': 1,
            'properties': {'color': 'red'},
            'variant_count': 3,
            'picture_count': 5,
            'brand_count': 2,
            'keyword_count': 4
        }
        
        print(f"🔍 Testing complete component")
        score = self._calculate_component_score(complete_component)
        print(f"📊 Completeness score: {score}/100")
        
        self.assertGreaterEqual(score, 85)  # Should be high score
        
        # Minimal component
        minimal_component = {
            'product_number': 'MINIMAL-001'
        }
        
        print(f"🔍 Testing minimal component")
        score = self._calculate_component_score(minimal_component)
        print(f"📊 Completeness score: {score}/100")
        
        self.assertLessEqual(score, 30)  # Should be low score
        
        print(f"✅ UNIT TEST PASSED: Component scoring works")

    def test_format_api_response(self):
        """Test API response formatting"""
        print(f"\n🧪 UNIT TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test API response formatting")
        
        # Success response
        success_data = {
            'component_id': 123,
            'changes': {'product_number': {'old': 'OLD', 'new': 'NEW'}}
        }
        
        success_response = self._format_api_response(
            success=True,
            message="Component updated successfully",
            data=success_data
        )
        
        print(f"🔍 Success response: {json.dumps(success_response, indent=2)}")
        
        # Verify success response structure
        self.assertTrue(success_response['success'])
        self.assertIn('message', success_response)
        self.assertIn('data', success_response)
        self.assertEqual(success_response['data']['component_id'], 123)
        
        # Error response
        error_response = self._format_api_response(
            success=False,
            message="Component not found",
            error_code=404,
            error_details={'component_id': 999}
        )
        
        print(f"🔍 Error response: {json.dumps(error_response, indent=2)}")
        
        # Verify error response structure
        self.assertFalse(error_response['success'])
        self.assertIn('error', error_response)
        self.assertIn('code', error_response)
        self.assertEqual(error_response['code'], 404)
        
        print(f"✅ UNIT TEST PASSED: API response formatting works")

    def test_parse_picture_order_changes(self):
        """Test picture order change parsing"""
        print(f"\n🧪 UNIT TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test picture order change parsing")
        
        # Form data with picture order changes
        form_data = {
            'picture_order_1': '3',
            'picture_order_2': '1', 
            'picture_order_3': '2',
            'other_field': 'ignored'
        }
        
        print(f"🔍 Testing form data: {json.dumps(form_data, indent=2)}")
        
        result = self._parse_picture_order_changes(form_data)
        
        print(f"📊 Picture order changes: {json.dumps(result, indent=2)}")
        
        # Verify parsed changes
        expected_changes = {
            '1': 3,  # Picture 1 should be order 3
            '2': 1,  # Picture 2 should be order 1
            '3': 2   # Picture 3 should be order 2
        }
        
        self.assertEqual(result, expected_changes)
        
        print(f"✅ UNIT TEST PASSED: Picture order parsing works")

    def test_validate_picture_file_data(self):
        """Test picture file validation logic"""
        print(f"\n🧪 UNIT TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test picture file validation")
        
        # Valid image file
        valid_file = Mock()
        valid_file.filename = "test_image.jpg"
        valid_file.content_type = "image/jpeg"
        valid_file.content_length = 2048000  # 2MB
        
        print(f"🔍 Testing valid file: {valid_file.filename}")
        result = self._validate_picture_file(valid_file)
        print(f"📊 Validation result: {result}")
        
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)
        
        # Invalid file - too large
        invalid_file = Mock()
        invalid_file.filename = "huge_image.jpg"
        invalid_file.content_type = "image/jpeg"
        invalid_file.content_length = 20480000  # 20MB
        
        print(f"🔍 Testing invalid file: {invalid_file.filename}")
        result = self._validate_picture_file(invalid_file)
        print(f"📊 Validation result: {result}")
        
        self.assertFalse(result['valid'])
        self.assertGreater(len(result['errors']), 0)
        
        print(f"✅ UNIT TEST PASSED: Picture file validation works")

    # Helper methods (would be in actual service modules)
    def _detect_changes(self, original, updated):
        """Helper method to detect field changes"""
        changes = {}
        for key, new_value in updated.items():
            old_value = original.get(key)
            if old_value != new_value:
                changes[key] = {'old': old_value, 'new': new_value}
        return changes

    def _validate_required_fields(self, data, required_fields):
        """Helper method to validate required fields"""
        missing = []
        for field in required_fields:
            if field not in data or not data[field]:
                missing.append(field)
        
        return {
            'valid': len(missing) == 0,
            'missing': missing
        }

    def _build_association_data(self, form_data):
        """Helper method to build association data"""
        result = {}
        
        # Parse brand IDs
        brand_ids = form_data.get('brand_ids[]', [])
        result['brands'] = [int(id) for id in brand_ids if id.isdigit()]
        
        # Parse category IDs
        category_ids = form_data.get('categories[]', [])
        result['categories'] = [int(id) for id in category_ids if id.isdigit()]
        
        # Parse keywords
        keywords_str = form_data.get('keywords', '')
        result['keywords'] = [kw.strip() for kw in keywords_str.split(',') if kw.strip()]
        
        return result

    def _calculate_component_score(self, component_data):
        """Helper method to calculate component completeness score"""
        score = 0
        max_score = 100
        
        # Core fields (50 points)
        if component_data.get('product_number'):
            score += 15
        if component_data.get('description'):
            score += 10
        if component_data.get('supplier_id'):
            score += 10
        if component_data.get('component_type_id'):
            score += 15
        
        # Properties (10 points)
        if component_data.get('properties'):
            score += 10
        
        # Variants (15 points)
        variant_count = component_data.get('variant_count', 0)
        score += min(variant_count * 5, 15)
        
        # Pictures (15 points)
        picture_count = component_data.get('picture_count', 0)
        score += min(picture_count * 3, 15)
        
        # Associations (10 points)
        brand_count = component_data.get('brand_count', 0)
        keyword_count = component_data.get('keyword_count', 0)
        score += min((brand_count + keyword_count) * 2, 10)
        
        return min(score, max_score)

    def _format_api_response(self, success, message, data=None, error_code=None, error_details=None):
        """Helper method to format API responses"""
        response = {
            'success': success,
        }
        
        if success:
            response['message'] = message
            response['data'] = data or {}
        else:
            response['error'] = message
            if error_code:
                response['code'] = error_code
            if error_details:
                response['details'] = error_details
        
        return response

    def _parse_picture_order_changes(self, form_data):
        """Helper method to parse picture order changes"""
        changes = {}
        for key, value in form_data.items():
            if key.startswith('picture_order_') and value.isdigit():
                picture_id = key.replace('picture_order_', '')
                changes[picture_id] = int(value)
        return changes

    def _validate_picture_file(self, file_obj):
        """Helper method to validate picture files"""
        errors = []
        
        # Check file size (max 16MB)
        max_size = 16 * 1024 * 1024  # 16MB
        if hasattr(file_obj, 'content_length') and file_obj.content_length > max_size:
            errors.append(f"File too large: {file_obj.content_length / (1024*1024):.1f}MB (max 16MB)")
        
        # Check file extension
        if hasattr(file_obj, 'filename'):
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            import os
            ext = os.path.splitext(file_obj.filename)[1].lower()
            if ext not in valid_extensions:
                errors.append(f"Invalid file type: {ext}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }


if __name__ == '__main__':
    unittest.main()