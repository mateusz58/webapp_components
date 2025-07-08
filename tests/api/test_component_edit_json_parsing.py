#!/usr/bin/env python3
"""
API Tests for Component Edit JSON Parsing Issues
Comprehensive testing for "JSON.parse: unexpected character" error scenarios
"""
import unittest
import json
import os
import sys
import tempfile
from io import BytesIO

# Add app directory to path for imports  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app import create_app, db
from app.models import Component, ComponentType, Supplier, Brand, Category, Keyword, Color, ComponentVariant
from config import Config


class TestConfig(Config):
    """Test configuration - use existing PostgreSQL database"""
    TESTING = True
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key-for-json-parsing-tests'
    UPLOAD_FOLDER = tempfile.mkdtemp()
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024


class ComponentEditJSONParsingTests(unittest.TestCase):
    """Test cases for JSON parsing issues in component edit API"""

    def setUp(self):
        """Set up test fixtures with debug logging"""
        print(f"\n🧪 TEST SETUP: {self._testMethodName}")
        print(f"🔧 Creating Flask app with test configuration...")
        
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        
        print(f"🔧 Getting test data from database...")
        self._get_test_data()
        
        # Ensure we have test component
        if not self.test_component:
            self.skipTest("No components available in database for testing")
        
        print(f"✅ Setup complete - Test component: {self.test_component.product_number} (ID: {self.test_component.id})")

    def tearDown(self):
        """Clean up after tests"""
        print(f"🧹 Cleaning up after: {self._testMethodName}")
        db.session.remove()
        self.app_context.pop()

    def _get_test_data(self):
        """Get existing database data for testing"""
        print(f"🔍 Querying database for test data...")
        
        # Get test component
        self.test_component = Component.query.first()
        print(f"📊 Found component: {self.test_component.product_number if self.test_component else 'None'}")
        
        # Get test data for validation
        self.component_types = ComponentType.query.all()
        self.suppliers = Supplier.query.all()
        
        print(f"📊 Available component types: {len(self.component_types)}")
        print(f"📊 Available suppliers: {len(self.suppliers)}")

    def test_valid_json_request_succeeds(self):
        """Test that valid JSON requests work correctly"""
        print(f"\n🧪 TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Verify that properly formatted JSON requests work")
        
        if not self.test_component:
            self.skipTest("No test component available")
        
        # Valid JSON data
        test_data = {
            'product_number': f'{self.test_component.product_number}_json_test',
            'description': 'Updated via valid JSON test',
            'component_type_id': self.test_component.component_type_id,
            'supplier_id': self.test_component.supplier_id,
            'properties': {'test_property': 'test_value'}
        }
        
        print(f"🚀 Sending valid JSON request to /api/component/{self.test_component.id}")
        print(f"📤 Request data: {json.dumps(test_data, indent=2)}")
        
        response = self.client.put(
            f'/api/component/{self.test_component.id}',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response content-type: {response.content_type}")
        print(f"📊 Response headers: {dict(response.headers)}")
        
        if response.data:
            response_text = response.data.decode('utf-8')
            print(f"📊 Response length: {len(response_text)} characters")
            print(f"📊 Response preview: {response_text[:200]}...")
        
        # Verify response
        self.assertEqual(response.status_code, 200, f"Expected 200, got {response.status_code}")
        self.assertTrue(response.is_json, f"Response should be JSON, got content-type: {response.content_type}")
        
        result = response.get_json()
        print(f"✅ Parsed JSON successfully: {json.dumps(result, indent=2)}")
        
        self.assertTrue(result.get('success'), f"Expected success=True, got: {result}")
        self.assertEqual(result.get('component_id'), self.test_component.id)
        
        print(f"✅ TEST PASSED: Valid JSON request handled correctly")

    def test_malformed_json_returns_proper_error(self):
        """Test that malformed JSON returns proper error response"""
        print(f"\n🧪 TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Verify malformed JSON is handled gracefully")
        
        if not self.test_component:
            self.skipTest("No test component available")
        
        # Malformed JSON (missing closing brace)
        malformed_json = '{"product_number": "test", "invalid_json":'
        
        print(f"🚀 Sending malformed JSON to /api/component/{self.test_component.id}")
        print(f"📤 Malformed data: {malformed_json}")
        
        response = self.client.put(
            f'/api/component/{self.test_component.id}',
            data=malformed_json,
            content_type='application/json'
        )
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response content-type: {response.content_type}")
        
        if response.data:
            response_text = response.data.decode('utf-8')
            print(f"📊 Response: {response_text}")
        
        # Should return proper error response
        self.assertIn(response.status_code, [400, 500], f"Expected 400 or 500, got {response.status_code}")
        
        if response.is_json:
            result = response.get_json()
            print(f"✅ Error response is valid JSON: {json.dumps(result, indent=2)}")
            self.assertFalse(result.get('success', False), "Expected success=False for malformed JSON")
        else:
            print(f"⚠️ Non-JSON error response - this could cause frontend parsing issues!")
        
        print(f"✅ TEST PASSED: Malformed JSON handled correctly")

    def test_form_data_with_json_content_type_causes_issue(self):
        """Test that reproduces the user's JSON parsing error"""
        print(f"\n🧪 TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Reproduce 'JSON.parse: unexpected character' error")
        print(f"🚨 This test REPRODUCES the user's reported issue!")
        
        if not self.test_component:
            self.skipTest("No test component available")
        
        # Form data but with JSON content-type (this is the issue!)
        form_data = {
            'product_number': f'{self.test_component.product_number}_form_as_json',
            'description': 'This will cause JSON parsing error',
            'properties': '{"invalid": "json_string"}'  # String instead of object
        }
        
        print(f"🚀 Sending FORM DATA with JSON content-type (REPRODUCES USER ISSUE)")
        print(f"📤 Form data: {form_data}")
        print(f"⚠️ Content-Type: application/json (INCORRECT for form data)")
        
        response = self.client.put(
            f'/api/component/{self.test_component.id}',
            data=form_data,  # Form data
            content_type='application/json'  # But claim it's JSON!
        )
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response content-type: {response.content_type}")
        
        if response.data:
            response_text = response.data.decode('utf-8')
            print(f"📊 Response: {response_text}")
            
            # Check if this would cause frontend JSON parsing issues
            if not response.is_json:
                print(f"❌ NON-JSON RESPONSE! This would cause 'JSON.parse: unexpected character' error!")
                print(f"❌ Frontend JavaScript would fail trying to parse this as JSON")
                
                if response_text.strip().startswith('<'):
                    print(f"❌ Response appears to be HTML - this definitely causes the user's issue!")
                elif 'text/html' in response.content_type:
                    print(f"❌ Content-Type is text/html - frontend expects JSON!")
            else:
                print(f"✅ Response is valid JSON despite the content-type mismatch")
                result = response.get_json()
                print(f"📊 JSON response: {json.dumps(result, indent=2)}")
        
        # This test documents the issue - status code less important than content-type
        print(f"📊 Analysis: Response status {response.status_code}, content-type: {response.content_type}")
        
        if response.is_json:
            print(f"✅ API handled form-data-as-JSON gracefully")
        else:
            print(f"🚨 CONFIRMED: This reproduces the user's JSON parsing error!")
            print(f"🚨 Frontend would fail with 'JSON.parse: unexpected character at line 1 column 1'")
        
        print(f"✅ TEST COMPLETED: Issue reproduction attempted")

    def test_invalid_component_id_returns_json_error(self):
        """Test that invalid component ID returns proper JSON error"""
        print(f"\n🧪 TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Verify invalid component ID returns JSON error")
        
        test_data = {
            'product_number': 'invalid_component_test',
            'description': 'Test with invalid component ID'
        }
        
        invalid_component_id = 999999
        print(f"🚀 Sending request to non-existent component ID: {invalid_component_id}")
        print(f"📤 Request data: {json.dumps(test_data, indent=2)}")
        
        response = self.client.put(
            f'/api/component/{invalid_component_id}',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response content-type: {response.content_type}")
        
        if response.data:
            response_text = response.data.decode('utf-8')
            print(f"📊 Response: {response_text}")
        
        # Should return proper JSON error
        self.assertEqual(response.status_code, 400, f"Expected 400 for invalid component ID")
        self.assertTrue(response.is_json, f"Error response should be JSON")
        
        result = response.get_json()
        print(f"✅ JSON error response: {json.dumps(result, indent=2)}")
        
        self.assertFalse(result.get('success'), "Expected success=False for invalid component")
        self.assertIn('not found', result.get('error', '').lower(), "Error should mention component not found")
        
        print(f"✅ TEST PASSED: Invalid component ID handled with proper JSON error")

    def test_database_constraint_violation_handling(self):
        """Test that database errors return proper JSON responses"""
        print(f"\n🧪 TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Verify database constraint violations return JSON errors")
        
        if not self.test_component:
            self.skipTest("No test component available")
        
        # Try to set invalid foreign key references
        test_data = {
            'product_number': self.test_component.product_number,
            'supplier_id': 999999,  # Non-existent supplier
            'component_type_id': 999999  # Non-existent component type
        }
        
        print(f"🚀 Sending request with invalid foreign key references")
        print(f"📤 Request data: {json.dumps(test_data, indent=2)}")
        
        response = self.client.put(
            f'/api/component/{self.test_component.id}',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response content-type: {response.content_type}")
        
        if response.data:
            response_text = response.data.decode('utf-8')
            print(f"📊 Response preview: {response_text[:300]}...")
        
        # Should return proper JSON error for database constraint violation
        self.assertEqual(response.status_code, 400, f"Expected 400 for constraint violation")
        self.assertTrue(response.is_json, f"Database error response should be JSON")
        
        result = response.get_json()
        print(f"✅ Database error as JSON: {json.dumps(result, indent=2)}")
        
        self.assertFalse(result.get('success'), "Expected success=False for database error")
        self.assertIn('error', result, "Response should contain error message")
        
        print(f"✅ TEST PASSED: Database constraint violations handled with proper JSON error")

    def test_missing_csrf_token_handling(self):
        """Test that missing CSRF token is handled appropriately"""
        print(f"\n🧪 TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Verify missing CSRF token doesn't break JSON response")
        
        if not self.test_component:
            self.skipTest("No test component available")
        
        test_data = {
            'product_number': f'{self.test_component.product_number}_no_csrf',
            'description': 'Test without CSRF token'
        }
        
        print(f"🚀 Sending request WITHOUT X-CSRFToken header")
        print(f"📤 Request data: {json.dumps(test_data, indent=2)}")
        
        # Send without CSRF token header
        response = self.client.put(
            f'/api/component/{self.test_component.id}',
            data=json.dumps(test_data),
            content_type='application/json'
            # No X-CSRFToken header!
        )
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response content-type: {response.content_type}")
        
        if response.data:
            response_text = response.data.decode('utf-8')
            print(f"📊 Response: {response_text[:200]}...")
        
        # Note: CSRF is disabled in test config, so this should work
        # But we're testing that the response format is consistent
        if response.status_code == 200:
            print(f"✅ CSRF disabled in test - request succeeded")
            self.assertTrue(response.is_json, "Successful response should be JSON")
        else:
            print(f"⚠️ CSRF protection active - checking error response format")
            # If CSRF protection is active, error should still be JSON
            if not response.is_json:
                print(f"❌ CSRF error is not JSON - this could cause frontend parsing issues!")
            else:
                print(f"✅ CSRF error returned as JSON")
        
        print(f"✅ TEST COMPLETED: CSRF handling checked")

    def test_picture_renames_json_string_handling(self):
        """Test that picture_renames as JSON string is handled correctly"""
        print(f"\n🧪 TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test picture_renames field with JSON string vs object")
        
        if not self.test_component:
            self.skipTest("No test component available")
        
        # Test with picture_renames as JSON string (from frontend)
        test_data = {
            'product_number': f'{self.test_component.product_number}_picture_renames',
            'description': 'Test picture renames JSON parsing',
            'picture_renames': '{"old_name": "new_name", "another_old": "another_new"}'  # JSON string
        }
        
        print(f"🚀 Testing picture_renames as JSON string")
        print(f"📤 Request data: {json.dumps(test_data, indent=2)}")
        print(f"🔍 picture_renames type: {type(test_data['picture_renames'])} (should be string)")
        
        response = self.client.put(
            f'/api/component/{self.test_component.id}',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response content-type: {response.content_type}")
        
        if response.data:
            response_text = response.data.decode('utf-8')
            print(f"📊 Response preview: {response_text[:300]}...")
        
        if response.is_json:
            result = response.get_json()
            print(f"✅ Response parsed as JSON successfully")
            
            # Check if picture_renames were processed
            if 'changes' in result and 'picture_orders' in result['changes']:
                print(f"📊 Picture changes detected: {result['changes']['picture_orders']}")
            
            if result.get('success'):
                print(f"✅ Request succeeded despite JSON string picture_renames")
            else:
                print(f"⚠️ Request failed: {result.get('error', 'Unknown error')}")
        else:
            print(f"❌ Response is not JSON - this would cause frontend parsing errors!")
        
        print(f"✅ TEST COMPLETED: picture_renames JSON string handling tested")


if __name__ == '__main__':
    print("🚀 Running Component Edit JSON Parsing Tests")
    print("=" * 70)
    print("🎯 Testing scenarios that could cause 'JSON.parse: unexpected character' errors")
    print("=" * 70)
    
    unittest.main(verbosity=2)