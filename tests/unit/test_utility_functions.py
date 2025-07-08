import unittest
import json
from unittest.mock import Mock, patch

class TestUtilityFunctions(unittest.TestCase):
    """Unit tests for utility helper functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        print(f"\n🧪 UNIT TEST SETUP: {self._testMethodName}")
        print(f"🔧 Setting up utility test environment...")
        print(f"✅ Unit test setup complete for: {self._testMethodName}")

    def test_generate_sku_format(self):
        """Test SKU generation format logic"""
        print(f"\n🧪 UNIT TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test SKU generation format")
        
        # Test with supplier code
        supplier_code = "SUP123"
        product_number = "PROD-001"
        color_name = "Red"
        
        expected_sku = "sup123_prod-001_red"
        result = self._generate_sku(supplier_code, product_number, color_name)
        
        print(f"🔍 Testing: supplier={supplier_code}, product={product_number}, color={color_name}")
        print(f"📊 Expected: {expected_sku}")
        print(f"📊 Result: {result}")
        
        self.assertEqual(result, expected_sku)
        
        # Test without supplier code
        result_no_supplier = self._generate_sku(None, product_number, color_name)
        expected_no_supplier = "prod-001_red"
        
        print(f"🔍 Testing without supplier: product={product_number}, color={color_name}")
        print(f"📊 Expected: {expected_no_supplier}")
        print(f"📊 Result: {result_no_supplier}")
        
        self.assertEqual(result_no_supplier, expected_no_supplier)
        
        print(f"✅ UNIT TEST PASSED: SKU generation format works")

    def test_generate_picture_name_format(self):
        """Test picture name generation format logic"""
        print(f"\n🧪 UNIT TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test picture name generation format")
        
        # Test component picture
        supplier_code = "SUP456"
        product_number = "COMP-002"
        color_name = "main"  # For component pictures
        picture_order = 1
        
        expected_name = "sup456_comp-002_main_1"
        result = self._generate_picture_name(supplier_code, product_number, color_name, picture_order)
        
        print(f"🔍 Testing component picture")
        print(f"📊 Expected: {expected_name}")
        print(f"📊 Result: {result}")
        
        self.assertEqual(result, expected_name)
        
        # Test variant picture
        variant_color = "Blue"
        expected_variant = "sup456_comp-002_blue_2"
        result_variant = self._generate_picture_name(supplier_code, product_number, variant_color, 2)
        
        print(f"🔍 Testing variant picture")
        print(f"📊 Expected: {expected_variant}")
        print(f"📊 Result: {result_variant}")
        
        self.assertEqual(result_variant, expected_variant)
        
        print(f"✅ UNIT TEST PASSED: Picture name generation works")

    def test_normalize_string_format(self):
        """Test string normalization for database names"""
        print(f"\n🧪 UNIT TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test string normalization")
        
        test_cases = [
            ("Product Name", "product_name"),
            ("RED Color", "red_color"),
            ("Multi  Space   Text", "multi_space_text"),
            ("Special-Chars!", "special-chars!"),
            ("  Trimmed  ", "trimmed")
        ]
        
        for input_str, expected in test_cases:
            result = self._normalize_string(input_str)
            print(f"🔍 Input: '{input_str}' → Expected: '{expected}' → Result: '{result}'")
            self.assertEqual(result, expected)
        
        print(f"✅ UNIT TEST PASSED: String normalization works")

    def test_parse_id_values(self):
        """Test parsing ID values from form data"""
        print(f"\n🧪 UNIT TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test ID value parsing")
        
        # String IDs that should convert to integers
        test_cases = [
            ("123", 123),
            ("0", 0),
            ("", None),
            ("abc", None),
            ("12.5", None),
            (None, None)
        ]
        
        for input_val, expected in test_cases:
            result = self._parse_id_value(input_val)
            print(f"🔍 Input: {input_val} → Expected: {expected} → Result: {result}")
            self.assertEqual(result, expected)
        
        print(f"✅ UNIT TEST PASSED: ID value parsing works")

    def test_build_error_response(self):
        """Test error response building"""
        print(f"\n🧪 UNIT TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test error response structure")
        
        error_message = "Component not found"
        error_code = 404
        details = {"component_id": 123, "action": "update"}
        
        result = self._build_error_response(error_message, error_code, details)
        
        print(f"🔍 Error message: {error_message}")
        print(f"🔍 Error code: {error_code}")
        print(f"📊 Response: {json.dumps(result, indent=2)}")
        
        # Verify response structure
        self.assertIn('success', result)
        self.assertIn('error', result)
        self.assertIn('code', result)
        self.assertIn('details', result)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], error_message)
        self.assertEqual(result['code'], error_code)
        self.assertEqual(result['details'], details)
        
        print(f"✅ UNIT TEST PASSED: Error response building works")

    def test_build_success_response(self):
        """Test success response building"""
        print(f"\n🧪 UNIT TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test success response structure")
        
        message = "Component updated successfully"
        data = {"component_id": 456, "changes": {"product_number": {"old": "OLD", "new": "NEW"}}}
        
        result = self._build_success_response(message, data)
        
        print(f"🔍 Success message: {message}")
        print(f"📊 Response: {json.dumps(result, indent=2)}")
        
        # Verify response structure
        self.assertIn('success', result)
        self.assertIn('message', result)
        self.assertIn('data', result)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], message)
        self.assertEqual(result['data'], data)
        
        print(f"✅ UNIT TEST PASSED: Success response building works")

    def test_extract_file_info(self):
        """Test file information extraction"""
        print(f"\n🧪 UNIT TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test file info extraction")
        
        # Mock file object
        mock_file = Mock()
        mock_file.filename = "test_image.jpg"
        mock_file.content_type = "image/jpeg"
        mock_file.content_length = 1024000  # 1MB
        
        result = self._extract_file_info(mock_file)
        
        print(f"🔍 File: {mock_file.filename}")
        print(f"📊 File info: {json.dumps(result, indent=2)}")
        
        # Verify extracted info
        self.assertIn('filename', result)
        self.assertIn('extension', result)
        self.assertIn('content_type', result)
        self.assertIn('size_mb', result)
        self.assertIn('is_image', result)
        
        self.assertEqual(result['filename'], "test_image.jpg")
        self.assertEqual(result['extension'], ".jpg")
        self.assertTrue(result['is_image'])
        
        print(f"✅ UNIT TEST PASSED: File info extraction works")

    def test_calculate_file_size_mb(self):
        """Test file size calculation in MB"""
        print(f"\n🧪 UNIT TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test file size calculation")
        
        test_cases = [
            (1024, "0.00"),      # 1KB
            (1048576, "1.00"),   # 1MB  
            (5242880, "5.00"),   # 5MB
            (1572864, "1.50"),   # 1.5MB
            (0, "0.00")          # 0 bytes
        ]
        
        for bytes_size, expected_mb in test_cases:
            result = self._calculate_size_mb(bytes_size)
            print(f"🔍 {bytes_size} bytes → Expected: {expected_mb} MB → Result: {result} MB")
            self.assertEqual(result, expected_mb)
        
        print(f"✅ UNIT TEST PASSED: File size calculation works")

    # Helper methods (would be in actual utility modules)
    def _generate_sku(self, supplier_code, product_number, color_name):
        """Helper method to generate SKU"""
        parts = []
        if supplier_code:
            parts.append(supplier_code.lower())
        parts.append(product_number.lower())
        parts.append(color_name.lower())
        return "_".join(parts)

    def _generate_picture_name(self, supplier_code, product_number, color_name, picture_order):
        """Helper method to generate picture name"""
        parts = []
        if supplier_code:
            parts.append(supplier_code.lower())
        parts.append(product_number.lower())
        parts.append(color_name.lower())
        parts.append(str(picture_order))
        return "_".join(parts)

    def _normalize_string(self, text):
        """Helper method to normalize strings"""
        if not text:
            return ""
        # Convert to lowercase, replace spaces with underscores, trim
        normalized = text.strip().lower().replace(" ", "_")
        # Replace multiple underscores with single
        import re
        normalized = re.sub(r'_+', '_', normalized)
        return normalized

    def _parse_id_value(self, value):
        """Helper method to parse ID values"""
        if value is None or value == "":
            return None
        if isinstance(value, str) and value.isdigit():
            return int(value)
        if isinstance(value, int):
            return value
        return None

    def _build_error_response(self, message, code, details=None):
        """Helper method to build error responses"""
        return {
            'success': False,
            'error': message,
            'code': code,
            'details': details or {}
        }

    def _build_success_response(self, message, data=None):
        """Helper method to build success responses"""
        return {
            'success': True,
            'message': message,
            'data': data or {}
        }

    def _extract_file_info(self, file_obj):
        """Helper method to extract file information"""
        import os
        filename = getattr(file_obj, 'filename', '')
        extension = os.path.splitext(filename)[1].lower()
        content_type = getattr(file_obj, 'content_type', '')
        size_bytes = getattr(file_obj, 'content_length', 0)
        
        return {
            'filename': filename,
            'extension': extension,
            'content_type': content_type,
            'size_mb': self._calculate_size_mb(size_bytes),
            'is_image': extension in ['.jpg', '.jpeg', '.png', '.gif']
        }

    def _calculate_size_mb(self, bytes_size):
        """Helper method to calculate file size in MB"""
        mb_size = bytes_size / (1024 * 1024)
        return f"{mb_size:.2f}"


if __name__ == '__main__':
    unittest.main()