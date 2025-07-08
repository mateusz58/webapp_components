#!/usr/bin/env python3
"""
Frontend JavaScript Scenario Tests
Tests that simulate exact frontend behavior that could cause JSON parsing errors
"""
import unittest
import json
import os
import sys
import tempfile
from urllib.parse import urlencode

# Add app directory to path for imports  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app import create_app, db
from app.models import Component, ComponentType, Supplier, Brand, Category, Keyword, Color, ComponentVariant
from config import Config


class TestConfig(Config):
    """Test configuration - use existing PostgreSQL database"""
    TESTING = True
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key-frontend-scenarios'
    UPLOAD_FOLDER = tempfile.mkdtemp()
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024


class FrontendJavaScriptScenarioTests(unittest.TestCase):
    """Test cases that simulate exact frontend JavaScript behavior"""

    def setUp(self):
        """Set up test fixtures with debug logging"""
        print(f"\n🧪 FRONTEND SCENARIO TEST SETUP: {self._testMethodName}")
        print(f"🔧 Simulating frontend JavaScript behavior...")
        
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        
        self._get_test_data()
        
        if not self.test_component:
            self.skipTest("No components available in database for testing")
        
        print(f"✅ Frontend test setup complete - Component: {self.test_component.product_number} (ID: {self.test_component.id})")

    def tearDown(self):
        """Clean up after tests"""
        print(f"🧹 Frontend test cleanup: {self._testMethodName}")
        db.session.remove()
        self.app_context.pop()

    def _get_test_data(self):
        """Get existing database data for testing"""
        self.test_component = Component.query.first()
        self.component_types = ComponentType.query.all()
        self.suppliers = Supplier.query.all()

    def test_javascript_form_submission_simulation(self):
        """Simulate exact JavaScript form submission from component_edit_form.html"""
        print(f"\n🧪 FRONTEND TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Simulate JavaScript form submission from form-handler.js")
        print(f"📝 This mimics the submitViaAPI() function behavior")
        
        if not self.test_component:
            self.skipTest("No test component available")
        
        # Simulate the exact data structure from gatherFormDataForAPI()
        form_simulation = {
            'product_number': f'{self.test_component.product_number}_js_sim',
            'description': 'JavaScript form submission simulation',
            'component_type_id': self.test_component.component_type_id,
            'supplier_id': self.test_component.supplier_id,
            'properties': {'test_property': 'from_js_simulation'},
            'brand_ids': [1, 2] if self.test_component.brands else [],
            'category_ids': [1] if self.test_component.categories else [],
            'keywords': ['test', 'frontend', 'simulation'],
            # This is what might cause issues - picture data from frontend
            'picture_renames': {'old_pic_name': 'new_pic_name'},
            'picture_order_123': 1,
            'picture_order_124': 2
        }
        
        print(f"🚀 Simulating frontend JavaScript API call")
        print(f"📤 Simulated form data: {json.dumps(form_simulation, indent=2)}")
        print(f"🔍 Content-Type: application/json (as set by JavaScript)")
        print(f"🔍 Method: PUT (as used by submitViaAPI)")
        
        # Simulate the exact fetch() call from form-handler.js
        response = self.client.put(
            f'/api/component/{self.test_component.id}',
            data=json.dumps(form_simulation),
            content_type='application/json',
            headers={
                'X-CSRFToken': 'fake-csrf-token',
                'X-Requested-With': 'XMLHttpRequest'
            }
        )
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response content-type: {response.content_type}")
        print(f"📊 Response headers: {dict(response.headers)}")
        
        if response.data:
            response_text = response.data.decode('utf-8')
            print(f"📊 Response length: {len(response_text)} characters")
            print(f"📊 Response starts with: '{response_text[:50]}...'")
        
        # This is what the frontend JavaScript would do
        print(f"\n🔍 FRONTEND JAVASCRIPT ANALYSIS:")
        print(f"   if (response.ok) {{ // {response.status_code >= 200 and response.status_code < 300}")
        print(f"       const result = await response.json(); // This is where parsing might fail")
        print(f"   }}")
        
        if response.status_code >= 200 and response.status_code < 300:
            print(f"✅ JavaScript would consider this response 'ok'")
            
            try:
                # Simulate JavaScript response.json() parsing
                result = response.get_json()
                print(f"✅ JavaScript response.json() would succeed")
                print(f"📊 Parsed result: {json.dumps(result, indent=2)}")
                
                # Check for the structure frontend expects
                if result.get('success'):
                    print(f"✅ Frontend would see success=True")
                else:
                    print(f"⚠️ Frontend would see success=False: {result.get('error', 'No error message')}")
                    
            except Exception as e:
                print(f"❌ JavaScript response.json() would FAIL!")
                print(f"❌ This would cause: JSON.parse: unexpected character at line 1 column 1")
                print(f"❌ Error: {str(e)}")
                
        else:
            print(f"⚠️ JavaScript would catch this in error handling")
            
            try:
                error_data = response.get_json()
                print(f"✅ Error response is valid JSON: {json.dumps(error_data, indent=2)}")
            except Exception as e:
                print(f"❌ Error response is not valid JSON - this causes the user's issue!")
                print(f"❌ Frontend would fail parsing error response")
        
        print(f"✅ FRONTEND SIMULATION COMPLETED")

    def test_picture_order_changes_exact_frontend_format(self):
        """Test picture order changes in exact format sent by variant-manager.js"""
        print(f"\n🧪 FRONTEND TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test picture order changes as sent by variant-manager.js")
        print(f"📝 This mimics getPictureOrderChanges() function behavior")
        
        if not self.test_component:
            self.skipTest("No test component available")
        
        # Simulate exact data structure from variant-manager.js getPictureOrderChanges()
        frontend_picture_data = {
            'product_number': self.test_component.product_number,
            'description': self.test_component.description,
            # Picture order changes (as sent by frontend)
            'picture_order_1': 2,
            'picture_order_2': 1,
            'picture_order_3': 3,
            # Picture renames (as sent by frontend) - this could be the issue
            'picture_renames': json.dumps({
                'old_picture_name_1': 'new_picture_name_1',
                'old_picture_name_2': 'new_picture_name_2'
            })  # Frontend sends this as JSON STRING, not object!
        }
        
        print(f"🚀 Testing picture changes as sent by frontend")
        print(f"📤 Frontend picture data: {json.dumps(frontend_picture_data, indent=2)}")
        print(f"🔍 picture_renames type: {type(frontend_picture_data['picture_renames'])}")
        print(f"🔍 picture_renames value: {frontend_picture_data['picture_renames']}")
        
        response = self.client.put(
            f'/api/component/{self.test_component.id}',
            data=json.dumps(frontend_picture_data),
            content_type='application/json'
        )
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response content-type: {response.content_type}")
        
        if response.data:
            response_text = response.data.decode('utf-8')
            print(f"📊 Response preview: {response_text[:200]}...")
        
        # Check if this causes issues
        if response.is_json:
            result = response.get_json()
            print(f"✅ Picture changes handled correctly")
            
            # Check for picture processing results
            if 'changes' in result and 'picture_orders' in result['changes']:
                picture_changes = result['changes']['picture_orders']
                print(f"📊 Picture order changes: {json.dumps(picture_changes, indent=2)}")
                
                if 'files_renamed' in picture_changes:
                    renamed_files = picture_changes['files_renamed']
                    print(f"📊 Files renamed: {len(renamed_files)} files")
                    for file_info in renamed_files:
                        print(f"   - {file_info.get('old_name', 'unknown')} → {file_info.get('new_name', 'unknown')} ({file_info.get('status', 'unknown')})")
                        
        else:
            print(f"❌ Picture changes caused non-JSON response!")
            print(f"❌ This would definitely cause frontend JSON parsing errors!")
        
        print(f"✅ PICTURE CHANGES TEST COMPLETED")

    def test_form_data_vs_json_content_type_mismatch(self):
        """Test the exact mismatch that causes JSON parsing errors"""
        print(f"\n🧪 FRONTEND TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test form data sent with application/json content-type")
        print(f"🚨 This is the EXACT scenario that causes user's JSON parsing error!")
        
        if not self.test_component:
            self.skipTest("No test component available")
        
        # This simulates when frontend form submission goes wrong
        # Form collects data as form fields but sends with JSON content-type
        form_data_as_string = urlencode({
            'product_number': f'{self.test_component.product_number}_form_mismatch',
            'description': 'Form data with JSON content-type mismatch',
            'component_type_id': str(self.test_component.component_type_id),
            'properties': '{"test": "value"}',  # This becomes a string in form data
            'picture_renames': '{"old": "new"}'  # This also becomes a string
        })
        
        print(f"🚀 Sending FORM DATA with application/json content-type")
        print(f"📤 Form data string: {form_data_as_string}")
        print(f"⚠️ Content-Type: application/json (WRONG for form data)")
        print(f"🚨 This is what causes 'JSON.parse: unexpected character' errors!")
        
        response = self.client.put(
            f'/api/component/{self.test_component.id}',
            data=form_data_as_string,  # URL-encoded form data
            content_type='application/json',  # But claiming it's JSON!
            headers={'Content-Length': str(len(form_data_as_string))}
        )
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response content-type: {response.content_type}")
        
        if response.data:
            response_text = response.data.decode('utf-8')
            print(f"📊 Response: {response_text}")
        
        # Analyze what frontend JavaScript would experience
        print(f"\n🔍 FRONTEND JAVASCRIPT EXPERIENCE:")
        if response.status_code >= 200 and response.status_code < 300:
            print(f"   JavaScript: response.ok = true")
        else:
            print(f"   JavaScript: response.ok = false")
        
        print(f"   JavaScript: await response.json() would...")
        
        if response.is_json:
            try:
                result = response.get_json()
                print(f"   ✅ SUCCEED and return: {json.dumps(result, indent=6)}")
            except Exception as e:
                print(f"   ❌ FAIL with error: {str(e)}")
        else:
            print(f"   ❌ FAIL with 'JSON.parse: unexpected character at line 1 column 1'")
            print(f"   ❌ Because content-type is: {response.content_type}")
            print(f"   ❌ And response starts with: '{response_text[:50]}...'")
        
        print(f"✅ CONTENT-TYPE MISMATCH TEST COMPLETED")

    def test_network_error_simulation(self):
        """Test what happens when API returns non-JSON due to server error"""
        print(f"\n🧪 FRONTEND TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Simulate server error that returns HTML instead of JSON")
        
        # Test with completely invalid data that might cause server error
        invalid_data = "This is not JSON at all, just plain text"
        
        print(f"🚀 Sending invalid data to trigger server error")
        print(f"📤 Invalid data: {invalid_data}")
        
        response = self.client.put(
            f'/api/component/999999',  # Invalid component + invalid data
            data=invalid_data,
            content_type='application/json'
        )
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response content-type: {response.content_type}")
        
        if response.data:
            response_text = response.data.decode('utf-8')
            print(f"📊 Response starts: '{response_text[:100]}...'")
            
            # Check if this looks like HTML
            if response_text.strip().startswith('<!DOCTYPE') or response_text.strip().startswith('<html'):
                print(f"❌ FOUND HTML RESPONSE!")
                print(f"❌ This would cause 'JSON.parse: unexpected character' in frontend!")
                print(f"❌ Frontend expects JSON but got HTML error page")
            elif response_text.strip().startswith('<'):
                print(f"❌ FOUND HTML-like RESPONSE!")
                print(f"❌ This would cause JSON parsing errors in frontend!")
            elif 'text/html' in response.content_type:
                print(f"❌ CONTENT-TYPE IS HTML!")
                print(f"❌ Frontend would try to parse HTML as JSON and fail!")
        
        print(f"✅ NETWORK ERROR SIMULATION COMPLETED")


if __name__ == '__main__':
    print("🚀 Running Frontend JavaScript Scenario Tests")
    print("=" * 70)
    print("🎯 Testing exact scenarios that cause frontend JSON parsing errors")
    print("=" * 70)
    
    unittest.main(verbosity=2)