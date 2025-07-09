"""
Unit Tests for Component Web Route Logic
Tests the web route layer logic without database dependencies
"""
import unittest
from unittest.mock import patch, MagicMock, Mock
import os
import sys

# Add the app directory to the path so we can import from app
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(os.path.dirname(os.path.dirname(current_dir)))
sys.path.insert(0, app_dir)


class ComponentWebRoutesLogicTestCase(unittest.TestCase):
    """Test cases for component web route logic without database"""

    def setUp(self):
        """Set up test environment"""
        # Import Flask app for context
        from app import create_app
        from config import Config
        
        class TestConfig(Config):
            TESTING = True
            WTF_CSRF_ENABLED = False
        
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        self.mock_app = MagicMock()
        self.mock_request = MagicMock()
        self.mock_component = MagicMock()
        self.mock_component.id = 123
        self.mock_component.product_number = 'TEST_COMPONENT_123'
        
    def tearDown(self):
        """Clean up test environment"""
        self.app_context.pop()

    def test_web_route_calls_api_endpoint(self):
        """Test that web route properly calls API endpoint"""
        with patch('app.web.component_routes.Component') as mock_component_model, \
             patch('app.api.component_api.delete_component_api') as mock_api, \
             patch('app.web.component_routes.current_app') as mock_app, \
             patch('app.web.component_routes.redirect') as mock_redirect, \
             patch('app.web.component_routes.flash') as mock_flash, \
             patch('app.web.component_routes.url_for') as mock_url_for:
            
            # Setup mocks
            mock_component_model.query.get_or_404.return_value = self.mock_component
            
            mock_response = MagicMock()
            mock_response.get_json.return_value = {
                'success': True,
                'message': 'Component deleted successfully',
                'summary': {
                    'component_id': 123,
                    'product_number': 'TEST_COMPONENT_123',
                    'associations_deleted': {
                        'variants': 1,
                        'brands': 1,
                        'keywords': 0,
                        'categories': 0,
                        'pictures': 2
                    },
                    'files_deleted': {
                        'successful': 2,
                        'failed': 0,
                        'total': 2
                    }
                }
            }
            mock_api.return_value = (mock_response, 200)
            mock_url_for.return_value = '/components'
            
            # Import and call the function
            from app.web.component_routes import delete_component
            
            result = delete_component(123)
            
            # Verify API was called
            mock_api.assert_called_once_with(123)
            
            # Verify success flash message was set
            mock_flash.assert_called()
            flash_call_args = mock_flash.call_args[0]
            self.assertIn('TEST_COMPONENT_123', flash_call_args[0])
            self.assertIn('deleted successfully', flash_call_args[0])
            self.assertEqual(flash_call_args[1], 'success')
            
            # Verify redirect was called
            mock_redirect.assert_called_once()

    def test_web_route_handles_api_error(self):
        """Test that web route handles API errors properly"""
        with patch('app.web.component_routes.Component') as mock_component_model, \
             patch('app.api.component_api.delete_component_api') as mock_api, \
             patch('app.web.component_routes.current_app') as mock_app, \
             patch('app.web.component_routes.redirect') as mock_redirect, \
             patch('app.web.component_routes.flash') as mock_flash, \
             patch('app.web.component_routes.url_for') as mock_url_for:
            
            # Setup mocks
            mock_component_model.query.get_or_404.return_value = self.mock_component
            
            mock_error_response = MagicMock()
            mock_error_response.get_json.return_value = {
                'success': False,
                'error': 'Component deletion failed',
                'code': 'DELETE_ERROR'
            }
            mock_api.return_value = (mock_error_response, 500)
            mock_url_for.return_value = '/components'
            
            # Import and call the function
            from app.web.component_routes import delete_component
            
            result = delete_component(123)
            
            # Verify API was called
            mock_api.assert_called_once_with(123)
            
            # Verify error flash message was set
            mock_flash.assert_called()
            flash_call_args = mock_flash.call_args[0]
            self.assertIn('error', flash_call_args[0].lower())
            self.assertEqual(flash_call_args[1], 'error')
            
            # Verify redirect was called
            mock_redirect.assert_called_once()

    def test_web_route_handles_api_not_found(self):
        """Test that web route handles 404 from API"""
        with patch('app.web.component_routes.Component') as mock_component_model, \
             patch('app.api.component_api.delete_component_api') as mock_api, \
             patch('app.web.component_routes.current_app') as mock_app, \
             patch('app.web.component_routes.redirect') as mock_redirect, \
             patch('app.web.component_routes.flash') as mock_flash, \
             patch('app.web.component_routes.url_for') as mock_url_for:
            
            # Setup mocks
            mock_component_model.query.get_or_404.return_value = self.mock_component
            
            mock_not_found_response = MagicMock()
            mock_not_found_response.get_json.return_value = {
                'success': False,
                'error': 'Component 123 not found',
                'code': 'NOT_FOUND'
            }
            mock_api.return_value = (mock_not_found_response, 404)
            mock_url_for.return_value = '/components'
            
            # Import and call the function
            from app.web.component_routes import delete_component
            
            result = delete_component(123)
            
            # Verify API was called
            mock_api.assert_called_once_with(123)
            
            # Verify error flash message was set
            mock_flash.assert_called()
            flash_call_args = mock_flash.call_args[0]
            self.assertIn('not found', flash_call_args[0].lower())
            self.assertEqual(flash_call_args[1], 'error')

    def test_web_route_handles_api_exception(self):
        """Test that web route handles API exceptions"""
        with patch('app.web.component_routes.Component') as mock_component_model, \
             patch('app.api.component_api.delete_component_api') as mock_api, \
             patch('app.web.component_routes.current_app') as mock_app, \
             patch('app.web.component_routes.redirect') as mock_redirect, \
             patch('app.web.component_routes.flash') as mock_flash, \
             patch('app.web.component_routes.url_for') as mock_url_for:
            
            # Setup mocks
            mock_component_model.query.get_or_404.return_value = self.mock_component
            mock_api.side_effect = Exception("API connection error")
            mock_url_for.return_value = '/components'
            
            # Import and call the function
            from app.web.component_routes import delete_component
            
            result = delete_component(123)
            
            # Verify API was called
            mock_api.assert_called_once_with(123)
            
            # Verify error flash message was set
            mock_flash.assert_called()
            flash_call_args = mock_flash.call_args[0]
            self.assertIn('error', flash_call_args[0].lower())
            self.assertEqual(flash_call_args[1], 'error')

    def test_web_route_formats_success_message_with_associations(self):
        """Test that success message includes association details"""
        with patch('app.web.component_routes.Component') as mock_component_model, \
             patch('app.api.component_api.delete_component_api') as mock_api, \
             patch('app.web.component_routes.current_app') as mock_app, \
             patch('app.web.component_routes.redirect') as mock_redirect, \
             patch('app.web.component_routes.flash') as mock_flash, \
             patch('app.web.component_routes.url_for') as mock_url_for:
            
            # Setup mocks
            mock_component_model.query.get_or_404.return_value = self.mock_component
            
            mock_response = MagicMock()
            mock_response.get_json.return_value = {
                'success': True,
                'message': 'Component deleted successfully',
                'summary': {
                    'component_id': 123,
                    'product_number': 'TEST_COMPONENT_123',
                    'associations_deleted': {
                        'variants': 3,
                        'brands': 2,
                        'keywords': 5,
                        'categories': 1,
                        'pictures': 7
                    },
                    'files_deleted': {
                        'successful': 7,
                        'failed': 0,
                        'total': 7
                    }
                }
            }
            mock_api.return_value = (mock_response, 200)
            mock_url_for.return_value = '/components'
            
            # Import and call the function
            from app.web.component_routes import delete_component
            
            result = delete_component(123)
            
            # Verify success flash message includes association details
            mock_flash.assert_called()
            flash_call_args = mock_flash.call_args[0]
            message = flash_call_args[0]
            
            self.assertIn('TEST_COMPONENT_123', message)
            self.assertIn('deleted successfully', message)
            self.assertIn('3 variants', message)
            self.assertIn('2 brand associations', message)
            self.assertIn('5 keyword associations', message)
            self.assertIn('1 category associations', message)
            self.assertIn('7 pictures', message)

    def test_web_route_warns_about_file_deletion_failures(self):
        """Test that web route warns about file deletion failures"""
        with patch('app.web.component_routes.Component') as mock_component_model, \
             patch('app.api.component_api.delete_component_api') as mock_api, \
             patch('app.web.component_routes.current_app') as mock_app, \
             patch('app.web.component_routes.redirect') as mock_redirect, \
             patch('app.web.component_routes.flash') as mock_flash, \
             patch('app.web.component_routes.url_for') as mock_url_for:
            
            # Setup mocks
            mock_component_model.query.get_or_404.return_value = self.mock_component
            
            mock_response = MagicMock()
            mock_response.get_json.return_value = {
                'success': True,
                'message': 'Component deleted successfully',
                'summary': {
                    'component_id': 123,
                    'product_number': 'TEST_COMPONENT_123',
                    'associations_deleted': {
                        'variants': 1,
                        'brands': 0,
                        'keywords': 0,
                        'categories': 0,
                        'pictures': 3
                    },
                    'files_deleted': {
                        'successful': 2,
                        'failed': 1,
                        'total': 3
                    }
                }
            }
            mock_api.return_value = (mock_response, 200)
            mock_url_for.return_value = '/components'
            
            # Import and call the function
            from app.web.component_routes import delete_component
            
            result = delete_component(123)
            
            # Verify flash was called multiple times (success + warning)
            self.assertEqual(mock_flash.call_count, 2)
            
            # Check calls
            calls = mock_flash.call_args_list
            success_call = calls[0]
            warning_call = calls[1]
            
            # Verify success message
            self.assertEqual(success_call[0][1], 'success')
            
            # Verify warning message about file failures
            self.assertIn('warning', warning_call[0][0].lower())
            self.assertIn('file', warning_call[0][0].lower())
            self.assertEqual(warning_call[0][1], 'warning')

    def test_web_route_logging(self):
        """Test that web route logs appropriately"""
        with patch('app.web.component_routes.Component') as mock_component_model, \
             patch('app.api.component_api.delete_component_api') as mock_api, \
             patch('app.web.component_routes.current_app') as mock_app, \
             patch('app.web.component_routes.redirect') as mock_redirect, \
             patch('app.web.component_routes.flash') as mock_flash, \
             patch('app.web.component_routes.url_for') as mock_url_for:
            
            # Setup mocks
            mock_component_model.query.get_or_404.return_value = self.mock_component
            mock_logger = MagicMock()
            mock_app.logger = mock_logger
            
            mock_response = MagicMock()
            mock_response.get_json.return_value = {
                'success': True,
                'message': 'Component deleted successfully',
                'summary': {
                    'component_id': 123,
                    'product_number': 'TEST_COMPONENT_123',
                    'associations_deleted': {'variants': 0, 'brands': 0, 'keywords': 0, 'categories': 0, 'pictures': 0},
                    'files_deleted': {'successful': 0, 'failed': 0, 'total': 0}
                }
            }
            mock_api.return_value = (mock_response, 200)
            mock_url_for.return_value = '/components'
            
            # Import and call the function
            from app.web.component_routes import delete_component
            
            result = delete_component(123)
            
            # Verify logging was called
            mock_logger.info.assert_called()
            
            # Check all log calls to find the expected messages
            all_calls = mock_logger.info.call_args_list
            log_messages = [call[0][0] for call in all_calls]
            
            # Find the deletion start message
            deletion_start_msg = next((msg for msg in log_messages if 'Web route: Deleting component' in msg), None)
            self.assertIsNotNone(deletion_start_msg, "Expected 'Web route: Deleting component' message not found")
            self.assertIn('123', deletion_start_msg)
            self.assertIn('TEST_COMPONENT_123', deletion_start_msg)


if __name__ == '__main__':
    unittest.main()