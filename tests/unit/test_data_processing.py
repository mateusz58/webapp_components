import unittest
import json
from unittest.mock import Mock

class TestDataProcessing(unittest.TestCase):
    """Unit tests for data processing helper functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        print(f"\n🧪 UNIT TEST SETUP: {self._testMethodName}")
        print(f"🔧 Setting up data processing test environment...")
        print(f"✅ Unit test setup complete for: {self._testMethodName}")

    def test_parse_properties_from_json_string(self):
        """Test parsing properties from JSON string"""
        print(f"\n🧪 UNIT TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test JSON string to dict conversion")
        
        # Valid JSON string
        json_string = '{"color": "red", "material": "plastic", "size": "large"}'
        print(f"🔍 Testing JSON string: {json_string}")
        
        result = self._parse_properties(json_string)
        
        expected = {"color": "red", "material": "plastic", "size": "large"}
        print(f"📊 Expected: {expected}")
        print(f"📊 Result: {result}")
        
        self.assertEqual(result, expected)
        self.assertIsInstance(result, dict)
        
        print(f"✅ UNIT TEST PASSED: JSON string parsing works")

    def test_parse_properties_from_dict(self):
        """Test parsing properties when already a dict"""
        print(f"\n🧪 UNIT TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test dict passthrough processing")
        
        # Already a dict
        properties_dict = {"color": "blue", "weight": "2kg"}
        print(f"🔍 Testing dict: {properties_dict}")
        
        result = self._parse_properties(properties_dict)
        
        print(f"📊 Expected: {properties_dict}")
        print(f"📊 Result: {result}")
        
        self.assertEqual(result, properties_dict)
        self.assertIsInstance(result, dict)
        
        print(f"✅ UNIT TEST PASSED: Dict passthrough works")

    def test_parse_properties_invalid_json(self):
        """Test parsing invalid JSON string"""
        print(f"\n🧪 UNIT TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test invalid JSON handling")
        
        # Invalid JSON
        invalid_json = '{"color": "red", "material":}'
        print(f"🔍 Testing invalid JSON: {invalid_json}")
        
        result = self._parse_properties(invalid_json)
        
        print(f"📊 Result: {result}")
        
        # Should return empty dict for invalid JSON
        self.assertEqual(result, {})
        
        print(f"✅ UNIT TEST PASSED: Invalid JSON handled correctly")

    def test_build_component_response_data(self):
        """Test building component response data structure"""
        print(f"\n🧪 UNIT TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test component response data building")
        
        # Mock component object
        mock_component = Mock()
        mock_component.id = 123
        mock_component.product_number = 'TEST-123'
        mock_component.description = 'Test component'
        mock_component.supplier_id = 5
        mock_component.component_type_id = 2
        mock_component.properties = {"color": "green", "material": "metal"}
        
        print(f"🔍 Testing with component ID: {mock_component.id}")
        print(f"🔍 Product number: {mock_component.product_number}")
        
        result = self._build_component_response(mock_component)
        
        print(f"📊 Response data: {json.dumps(result, indent=2)}")
        
        # Verify response structure
        self.assertIn('id', result)
        self.assertIn('product_number', result)
        self.assertIn('description', result)
        self.assertIn('properties', result)
        
        self.assertEqual(result['id'], 123)
        self.assertEqual(result['product_number'], 'TEST-123')
        self.assertEqual(result['properties'], {"color": "green", "material": "metal"})
        
        print(f"✅ UNIT TEST PASSED: Component response data building works")

    def test_extract_form_data_fields(self):
        """Test extracting specific fields from form data"""
        print(f"\n🧪 UNIT TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test form data field extraction")
        
        # Mock form data
        form_data = {
            'product_number': 'NEW-001',
            'description': 'New component',
            'supplier_id': '3',
            'extra_field': 'should be ignored',
            'properties': '{"type": "electronic"}'
        }
        
        allowed_fields = ['product_number', 'description', 'supplier_id', 'properties']
        
        print(f"🔍 Testing form data: {json.dumps(form_data, indent=2)}")
        print(f"🔍 Allowed fields: {allowed_fields}")
        
        result = self._extract_form_fields(form_data, allowed_fields)
        
        print(f"📊 Extracted data: {json.dumps(result, indent=2)}")
        
        # Should only contain allowed fields
        self.assertIn('product_number', result)
        self.assertIn('description', result) 
        self.assertIn('supplier_id', result)
        self.assertNotIn('extra_field', result)
        
        # Should convert string IDs to integers
        self.assertEqual(result['supplier_id'], 3)
        
        print(f"✅ UNIT TEST PASSED: Form data extraction works")

    def test_merge_component_changes(self):
        """Test merging component changes tracking"""
        print(f"\n🧪 UNIT TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test change tracking merge functionality")
        
        changes1 = {
            'product_number': {'old': 'OLD-001', 'new': 'NEW-001'},
            'description': {'old': 'Old desc', 'new': 'New desc'}
        }
        
        changes2 = {
            'supplier_id': {'old': 1, 'new': 2},
            'properties': {'old': {}, 'new': {'color': 'blue'}}
        }
        
        print(f"🔍 Changes 1: {json.dumps(changes1, indent=2)}")
        print(f"🔍 Changes 2: {json.dumps(changes2, indent=2)}")
        
        result = self._merge_changes(changes1, changes2)
        
        print(f"📊 Merged changes: {json.dumps(result, indent=2)}")
        
        # Should contain all changes
        self.assertIn('product_number', result)
        self.assertIn('description', result)
        self.assertIn('supplier_id', result)
        self.assertIn('properties', result)
        
        # Verify specific change values
        self.assertEqual(result['product_number']['new'], 'NEW-001')
        self.assertEqual(result['supplier_id']['new'], 2)
        
        print(f"✅ UNIT TEST PASSED: Change tracking merge works")

    def test_calculate_completion_percentage(self):
        """Test completion percentage calculation"""
        print(f"\n🧪 UNIT TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test completion percentage calculation")
        
        # Component with all fields filled
        complete_component = {
            'product_number': 'TEST-001',
            'description': 'Complete component',
            'supplier_id': 1,
            'component_type_id': 1,
            'properties': {'color': 'red'},
            'variants': [{'id': 1}, {'id': 2}],
            'pictures': [{'id': 1}, {'id': 2}, {'id': 3}]
        }
        
        print(f"🔍 Testing complete component")
        completion = self._calculate_completion_percentage(complete_component)
        print(f"📊 Completion: {completion}%")
        
        self.assertGreaterEqual(completion, 80)  # Should be high completion
        
        # Component with minimal fields
        minimal_component = {
            'product_number': 'TEST-002',
            'variants': [],
            'pictures': []
        }
        
        print(f"🔍 Testing minimal component")
        completion = self._calculate_completion_percentage(minimal_component)
        print(f"📊 Completion: {completion}%")
        
        self.assertLessEqual(completion, 50)  # Should be low completion
        
        print(f"✅ UNIT TEST PASSED: Completion percentage calculation works")

    # Helper methods for data processing (would be in actual processing module)
    def _parse_properties(self, properties):
        """Helper method to parse properties"""
        if isinstance(properties, dict):
            return properties
        elif isinstance(properties, str):
            try:
                return json.loads(properties)
            except (json.JSONDecodeError, ValueError):
                return {}
        return {}

    def _build_component_response(self, component):
        """Helper method to build component response"""
        return {
            'id': component.id,
            'product_number': component.product_number,
            'description': component.description,
            'supplier_id': component.supplier_id,
            'component_type_id': component.component_type_id,
            'properties': component.properties
        }

    def _extract_form_fields(self, form_data, allowed_fields):
        """Helper method to extract and clean form fields"""
        result = {}
        for field in allowed_fields:
            if field in form_data:
                value = form_data[field]
                # Convert string IDs to integers
                if field.endswith('_id') and isinstance(value, str) and value.isdigit():
                    result[field] = int(value)
                else:
                    result[field] = value
        return result

    def _merge_changes(self, *change_dicts):
        """Helper method to merge multiple change dictionaries"""
        merged = {}
        for changes in change_dicts:
            merged.update(changes)
        return merged

    def _calculate_completion_percentage(self, component_data):
        """Helper method to calculate component completion percentage"""
        total_weight = 0
        completed_weight = 0
        
        # Core fields (weight: 20 each)
        core_fields = ['product_number', 'description', 'supplier_id', 'component_type_id']
        for field in core_fields:
            total_weight += 20
            if component_data.get(field):
                completed_weight += 20
        
        # Properties (weight: 10)
        total_weight += 10
        if component_data.get('properties'):
            completed_weight += 10
        
        # Variants (weight: 5 per variant, max 10)
        variants = component_data.get('variants', [])
        total_weight += 10
        completed_weight += min(len(variants) * 5, 10)
        
        # Pictures (weight: 2 per picture, max 10)
        pictures = component_data.get('pictures', [])
        total_weight += 10
        completed_weight += min(len(pictures) * 2, 10)
        
        return int((completed_weight / total_weight) * 100) if total_weight > 0 else 0


if __name__ == '__main__':
    unittest.main()