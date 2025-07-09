#!/usr/bin/env python3
"""
TDD Test for Component Deletion API Integration
Tests that the component deletion API works correctly with proper session handling
Following proper TDD methodology and test organization
"""
import unittest
import sys
import os
import requests
import json
import time

# Add app directory to path for database imports
current_dir = os.path.dirname(os.path.abspath(__file__))
app_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
sys.path.insert(0, app_path)

from app import create_app, db
from app.models import Component
from config import Config

class TestConfig(Config):
    """Test configuration"""
    TESTING = True
    WTF_CSRF_ENABLED = True
    SECRET_KEY = 'test-secret-key'

class ComponentDeletionAPIIntegrationTestCase(unittest.TestCase):
    """Test cases for component deletion API integration following TDD principles"""

    @classmethod
    def setUpClass(cls):
        """Set up Flask app for database verification"""
        cls.app = create_app(TestConfig)
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        cls.base_url = 'http://localhost:6002'

    @classmethod
    def tearDownClass(cls):
        """Clean up Flask app"""
        if hasattr(cls, 'app_context'):
            cls.app_context.pop()

    def setUp(self):
        """Set up each test"""
        self.test_logs = []
        self.session = requests.Session()
        self.add_log("🧪 Starting Component Deletion API Integration Test")

    def add_log(self, message):
        """Add log with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.test_logs.append(log_entry)
        print(log_entry)

    def get_csrf_token(self):
        """Get CSRF token from components page"""
        response = self.session.get(f'{self.base_url}/components')
        response.raise_for_status()
        
        lines = response.text.split('\n')
        for line in lines:
            if 'name="csrf-token"' in line:
                import re
                match = re.search(r'content="([^"]+)"', line)
                if match:
                    return match.group(1)
        
        return None

    def test_csrf_token_availability(self):
        """Test that CSRF token is available for API requests"""
        self.add_log("🔒 Testing CSRF Token Availability")
        
        csrf_token = self.get_csrf_token()
        
        self.assertIsNotNone(csrf_token, "CSRF token should be available")
        self.assertGreater(len(csrf_token), 10, "CSRF token should be substantial")
        
        self.add_log(f"✅ CSRF token obtained: {csrf_token[:20]}...")

    def test_delete_nonexistent_component_returns_404(self):
        """Test that deleting non-existent component returns 404"""
        self.add_log("🎯 Testing Delete Non-existent Component")
        
        csrf_token = self.get_csrf_token()
        self.assertIsNotNone(csrf_token, "CSRF token should be available")
        
        headers = {
            'X-CSRFToken': csrf_token,
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        nonexistent_id = 99999
        self.add_log(f"🌐 Making DELETE request to /api/component/{nonexistent_id}")
        
        response = self.session.delete(
            f'{self.base_url}/api/component/{nonexistent_id}',
            headers=headers,
            timeout=10
        )
        
        self.assertEqual(response.status_code, 404, "Should return 404 for non-existent component")
        
        response_data = response.json()
        self.assertFalse(response_data['success'], "Success should be False")
        self.assertEqual(response_data['code'], 'NOT_FOUND', "Error code should be NOT_FOUND")
        self.assertIn('not found', response_data['error'], "Error message should mention 'not found'")
        
        self.add_log("✅ Non-existent component deletion handled correctly")

    def test_delete_existing_component_success(self):
        """Test successful deletion of existing component"""
        self.add_log("🎯 Testing Delete Existing Component")
        
        # Find a component to delete
        component = Component.query.first()
        if not component:
            self.skipTest("No components available for deletion test")
        
        component_id = component.id
        product_number = component.product_number
        
        self.add_log(f"📋 Testing deletion of component {component_id}: {product_number}")
        
        # Get component count before deletion
        before_count = Component.query.count()
        self.add_log(f"📊 Components before deletion: {before_count}")
        
        # Get CSRF token
        csrf_token = self.get_csrf_token()
        self.assertIsNotNone(csrf_token, "CSRF token should be available")
        
        headers = {
            'X-CSRFToken': csrf_token,
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        self.add_log(f"🌐 Making DELETE request to /api/component/{component_id}")
        
        # Make DELETE request
        response = self.session.delete(
            f'{self.base_url}/api/component/{component_id}',
            headers=headers,
            timeout=10
        )
        
        self.add_log(f"📊 Response status: {response.status_code}")
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200, "Should return 200 for successful deletion")
        
        # Parse response
        response_data = response.json()
        self.assertTrue(response_data['success'], "Success should be True")
        self.assertIn('deleted successfully', response_data['message'], "Should have success message")
        
        # Check response structure
        self.assertIn('summary', response_data, "Response should include summary")
        summary = response_data['summary']
        self.assertEqual(summary['component_id'], component_id, "Should include correct component ID")
        self.assertEqual(summary['product_number'], product_number, "Should include correct product number")
        
        # Log summary details
        self.add_log(f"✅ Response summary: {json.dumps(summary, indent=2)}")
        
        # Verify component count decreased
        after_count = Component.query.count()
        self.assertEqual(after_count, before_count - 1, "Component count should decrease by 1")
        
        self.add_log(f"📊 Components after deletion: {after_count}")
        self.add_log("🎉 Component deletion successful")

    def test_delete_component_with_associations(self):
        """Test deletion of component with variants, pictures, and associations"""
        self.add_log("🎯 Testing Delete Component with Associations")
        
        # Find a component with associations
        component = Component.query.filter(
            Component.variants.any()
        ).first()
        
        if not component:
            self.skipTest("No components with associations available for test")
        
        component_id = component.id
        product_number = component.product_number
        
        # Count associations before deletion
        variants_count = len(component.variants)
        pictures_count = len(component.pictures)
        
        self.add_log(f"📋 Component {component_id} has {variants_count} variants, {pictures_count} pictures")
        
        # Get CSRF token and make request
        csrf_token = self.get_csrf_token()
        headers = {
            'X-CSRFToken': csrf_token,
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        response = self.session.delete(
            f'{self.base_url}/api/component/{component_id}',
            headers=headers,
            timeout=10
        )
        
        self.assertEqual(response.status_code, 200, "Should successfully delete component with associations")
        
        response_data = response.json()
        self.assertTrue(response_data['success'], "Deletion should be successful")
        
        # Verify associations were deleted
        summary = response_data['summary']
        associations_deleted = summary['associations_deleted']
        
        self.assertEqual(associations_deleted['variants'], variants_count, "All variants should be deleted")
        
        self.add_log(f"✅ Associations deleted: {associations_deleted}")
        self.add_log("🎉 Component with associations deleted successfully")

    def test_session_handling_for_csrf(self):
        """Test that session handling works correctly for CSRF validation"""
        self.add_log("🔒 Testing Session Handling for CSRF")
        
        # Test 1: Request without proper session should fail
        headers = {
            'X-CSRFToken': 'invalid-token',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        response = requests.delete(
            f'{self.base_url}/api/component/99999',
            headers=headers,
            timeout=10
        )
        
        self.assertEqual(response.status_code, 400, "Should return 400 for invalid CSRF token")
        
        # Test 2: Request with proper session should work
        csrf_token = self.get_csrf_token()
        headers = {
            'X-CSRFToken': csrf_token,
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        response = self.session.delete(
            f'{self.base_url}/api/component/99999',
            headers=headers,
            timeout=10
        )
        
        self.assertEqual(response.status_code, 404, "Should return 404 (not 400) with proper session")
        
        self.add_log("✅ Session handling for CSRF works correctly")

    def tearDown(self):
        """Print test logs"""
        print("\\n" + "="*70)
        print("COMPONENT DELETION API INTEGRATION TEST LOGS")
        print("="*70)
        for log in self.test_logs:
            print(log)
        print("="*70 + "\\n")

if __name__ == '__main__':
    unittest.main(verbosity=2)