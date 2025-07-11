"""
Unit Tests for WebDAV Storage Service

Following TDD approach with comprehensive test coverage for all CRUD operations.
Tests are written first to define expected behavior.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import io
import requests
from typing import Dict, Any

from app.services.webdav_storage_service import (
    WebDAVStorageService, 
    WebDAVStorageConfig,
    WebDAVStorageFactory
)
from app.services.interfaces import (
    FileOperationResult,
    StorageOperationResult,
    FileInfo
)


class TestWebDAVStorageConfig(unittest.TestCase):
    """Test WebDAV configuration class"""

    def test_config_initialization_with_defaults(self):
        """Test configuration initialization with default values"""
        config = WebDAVStorageConfig("http://example.com/webdav/components")
        
        self.assertEqual(config.base_url, "http://example.com/webdav/components")
        self.assertIsNone(config.username)
        self.assertIsNone(config.password)
        self.assertEqual(config.timeout, 30)
        self.assertTrue(config.verify_ssl)
        self.assertEqual(config.max_retries, 3)
        self.assertEqual(config.chunk_size, 8192)

    def test_config_initialization_with_custom_values(self):
        """Test configuration initialization with custom values"""
        config = WebDAVStorageConfig(
            base_url="http://example.com/webdav/components/",
            username="testuser",
            password="testpass",
            timeout=60,
            verify_ssl=False,
            max_retries=5,
            chunk_size=4096
        )
        
        # Should strip trailing slash
        self.assertEqual(config.base_url, "http://example.com/webdav/components")
        self.assertEqual(config.username, "testuser")
        self.assertEqual(config.password, "testpass")
        self.assertEqual(config.timeout, 60)
        self.assertFalse(config.verify_ssl)
        self.assertEqual(config.max_retries, 5)
        self.assertEqual(config.chunk_size, 4096)


class TestWebDAVStorageService(unittest.TestCase):
    """Test WebDAV storage service implementation"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = WebDAVStorageConfig(
            base_url="http://31.182.67.115/webdav/components",
            timeout=30
        )
        self.mock_logger = Mock()
        self.service = WebDAVStorageService(self.config, self.mock_logger)

    def test_initialization(self):
        """Test service initialization"""
        self.assertEqual(self.service._config, self.config)
        self.assertEqual(self.service._logger, self.mock_logger)
        self.assertIsNotNone(self.service._session)

    def test_build_url(self):
        """Test URL building for files within components folder"""
        # Test normal filename
        url = self.service._build_url("test.jpg")
        self.assertEqual(url, "http://31.182.67.115/webdav/components/test.jpg")
        
        # Test filename with spaces
        url = self.service._build_url("test file.jpg")
        self.assertEqual(url, "http://31.182.67.115/webdav/components/test%20file.jpg")
        
        # Test filename with special characters
        url = self.service._build_url("test&file.jpg")
        self.assertEqual(url, "http://31.182.67.115/webdav/components/test%26file.jpg")

    def test_validate_filename_valid_cases(self):
        """Test filename validation for valid cases"""
        valid_filenames = [
            "test.jpg",
            "image_001.png", 
            "component-pic.jpeg",
            "file123.gif",
            "test-file_v2.webp"
        ]
        
        for filename in valid_filenames:
            with self.subTest(filename=filename):
                self.assertTrue(self.service.validate_filename(filename))

    def test_validate_filename_invalid_cases(self):
        """Test filename validation for invalid cases"""
        invalid_filenames = [
            "",                    # Empty
            None,                  # None
            "file/with/slash.jpg", # Contains slash
            "file\\with\\backslash.jpg", # Contains backslash
            "file:with:colon.jpg", # Contains colon
            "file*with*asterisk.jpg", # Contains asterisk
            "file?with?question.jpg", # Contains question mark
            "file\"with\"quote.jpg", # Contains quote
            "file<with<less.jpg",  # Contains less than
            "file>with>greater.jpg", # Contains greater than
            "file|with|pipe.jpg",  # Contains pipe
            "CON.jpg",             # Reserved name
            "PRN.txt",             # Reserved name
            "a" * 256              # Too long
        ]
        
        for filename in invalid_filenames:
            with self.subTest(filename=filename):
                self.assertFalse(self.service.validate_filename(filename))

    @patch('requests.Session.put')
    def test_upload_file_success(self, mock_put):
        """Test successful file upload"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 201
        mock_put.return_value = mock_response
        
        file_data = io.BytesIO(b"test file content")
        filename = "test.jpg"
        content_type = "image/jpeg"
        
        # Act
        result = self.service.upload_file(file_data, filename, content_type)
        
        # Assert
        self.assertTrue(result.success)
        self.assertEqual(result.result, FileOperationResult.SUCCESS)
        self.assertIsNotNone(result.file_info)
        self.assertEqual(result.file_info.name, filename)
        self.assertEqual(result.file_info.content_type, content_type)
        self.assertTrue(result.file_info.exists)
        
        # Verify PUT request was made correctly
        expected_url = "http://31.182.67.115/webdav/components/test.jpg"
        mock_put.assert_called_once()
        args, kwargs = mock_put.call_args
        self.assertEqual(args[0], expected_url)
        self.assertEqual(kwargs['headers']['Content-Type'], content_type)

    @patch('requests.Session.put')
    def test_upload_file_invalid_filename(self, mock_put):
        """Test file upload with invalid filename"""
        file_data = io.BytesIO(b"test content")
        invalid_filename = "file/with/slash.jpg"
        
        result = self.service.upload_file(file_data, invalid_filename)
        
        self.assertFalse(result.success)
        self.assertEqual(result.result, FileOperationResult.INVALID_PATH)
        mock_put.assert_not_called()

    @patch('requests.Session.put')
    def test_upload_file_http_error(self, mock_put):
        """Test file upload with HTTP error"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 403
        mock_put.return_value = mock_response
        
        file_data = io.BytesIO(b"test content")
        filename = "test.jpg"
        
        # Act
        result = self.service.upload_file(file_data, filename)
        
        # Assert
        self.assertFalse(result.success)
        self.assertEqual(result.result, FileOperationResult.PERMISSION_DENIED)

    @patch('requests.Session.put')
    def test_upload_file_network_error(self, mock_put):
        """Test file upload with network error"""
        # Arrange
        mock_put.side_effect = requests.exceptions.ConnectionError("Network error")
        
        file_data = io.BytesIO(b"test content")
        filename = "test.jpg"
        
        # Act
        result = self.service.upload_file(file_data, filename)
        
        # Assert
        self.assertFalse(result.success)
        self.assertEqual(result.result, FileOperationResult.NETWORK_ERROR)

    @patch('requests.Session.get')
    def test_download_file_success(self, mock_get):
        """Test successful file download"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {
            'Content-Type': 'image/jpeg',
            'Content-Length': '12'
        }
        mock_response.iter_content.return_value = [b"test", b" file", b" content"]
        mock_get.return_value = mock_response
        
        filename = "test.jpg"
        
        # Act
        result = self.service.download_file(filename)
        
        # Assert
        self.assertTrue(result.success)
        self.assertEqual(result.result, FileOperationResult.SUCCESS)
        self.assertIsNotNone(result.data)
        self.assertIsNotNone(result.file_info)
        
        # Check downloaded content
        downloaded_data = result.data.getvalue()
        self.assertEqual(downloaded_data, b"test file content")
        
        # Check file info
        self.assertEqual(result.file_info.name, filename)
        self.assertEqual(result.file_info.content_type, "image/jpeg")
        self.assertEqual(result.file_info.size, 17)  # Actual content length

    @patch('requests.Session.get')
    def test_download_file_not_found(self, mock_get):
        """Test file download when file not found"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        filename = "nonexistent.jpg"
        
        # Act
        result = self.service.download_file(filename)
        
        # Assert
        self.assertFalse(result.success)
        self.assertEqual(result.result, FileOperationResult.NOT_FOUND)

    @patch('requests.Session.delete')
    def test_delete_file_success(self, mock_delete):
        """Test successful file deletion"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response
        
        filename = "test.jpg"
        
        # Act
        result = self.service.delete_file(filename)
        
        # Assert
        self.assertTrue(result.success)
        self.assertEqual(result.result, FileOperationResult.SUCCESS)
        
        # Verify DELETE request was made
        expected_url = "http://31.182.67.115/webdav/components/test.jpg"
        mock_delete.assert_called_once()
        args, kwargs = mock_delete.call_args
        self.assertEqual(args[0], expected_url)

    @patch('requests.Session.request')
    def test_move_file_success(self, mock_request):
        """Test successful file move/rename"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 201
        mock_request.return_value = mock_response
        
        old_filename = "old.jpg"
        new_filename = "new.jpg"
        
        # Act
        result = self.service.move_file(old_filename, new_filename)
        
        # Assert
        self.assertTrue(result.success)
        self.assertEqual(result.result, FileOperationResult.SUCCESS)
        self.assertIsNotNone(result.file_info)
        self.assertEqual(result.file_info.name, new_filename)
        
        # Verify MOVE request was made correctly
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], 'MOVE')
        self.assertEqual(args[1], "http://31.182.67.115/webdav/components/old.jpg")
        self.assertEqual(kwargs['headers']['Destination'], "http://31.182.67.115/webdav/components/new.jpg")

    @patch('requests.Session.request')
    def test_copy_file_success(self, mock_request):
        """Test successful file copy"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 201
        mock_request.return_value = mock_response
        
        source_filename = "source.jpg"
        dest_filename = "dest.jpg"
        
        # Act
        result = self.service.copy_file(source_filename, dest_filename)
        
        # Assert
        self.assertTrue(result.success)
        self.assertEqual(result.result, FileOperationResult.SUCCESS)
        self.assertIsNotNone(result.file_info)
        self.assertEqual(result.file_info.name, dest_filename)
        
        # Verify COPY request was made correctly
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], 'COPY')
        self.assertEqual(args[1], "http://31.182.67.115/webdav/components/source.jpg")
        self.assertEqual(kwargs['headers']['Destination'], "http://31.182.67.115/webdav/components/dest.jpg")

    @patch('requests.Session.head')
    def test_file_exists_true(self, mock_head):
        """Test file existence check when file exists"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response
        
        filename = "existing.jpg"
        
        # Act
        result = self.service.file_exists(filename)
        
        # Assert
        self.assertTrue(result.success)
        self.assertEqual(result.result, FileOperationResult.SUCCESS)
        self.assertTrue(result.data)  # File exists
        self.assertTrue(result.file_info.exists)

    @patch('requests.Session.head')
    def test_file_exists_false(self, mock_head):
        """Test file existence check when file does not exist"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 404
        mock_head.return_value = mock_response
        
        filename = "nonexistent.jpg"
        
        # Act
        result = self.service.file_exists(filename)
        
        # Assert
        self.assertTrue(result.success)
        self.assertEqual(result.result, FileOperationResult.SUCCESS)
        self.assertFalse(result.data)  # File does not exist
        self.assertFalse(result.file_info.exists)

    @patch('requests.Session.head')
    def test_get_file_info_success(self, mock_head):
        """Test successful file info retrieval"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {
            'Content-Type': 'image/jpeg',
            'Content-Length': '1024',
            'Last-Modified': 'Wed, 21 Oct 2015 07:28:00 GMT'
        }
        mock_head.return_value = mock_response
        
        filename = "test.jpg"
        
        # Act
        result = self.service.get_file_info(filename)
        
        # Assert
        self.assertTrue(result.success)
        self.assertEqual(result.result, FileOperationResult.SUCCESS)
        self.assertIsNotNone(result.file_info)
        
        file_info = result.file_info
        self.assertEqual(file_info.name, filename)
        self.assertEqual(file_info.content_type, "image/jpeg")
        self.assertEqual(file_info.size, 1024)
        self.assertEqual(file_info.last_modified, "Wed, 21 Oct 2015 07:28:00 GMT")
        self.assertTrue(file_info.exists)

    def test_get_file_url(self):
        """Test file URL generation"""
        filename = "test.jpg"
        
        result = self.service.get_file_url(filename)
        
        self.assertTrue(result.success)
        self.assertEqual(result.result, FileOperationResult.SUCCESS)
        self.assertEqual(result.data, "http://31.182.67.115/webdav/components/test.jpg")

    def test_get_file_url_invalid_filename(self):
        """Test file URL generation with invalid filename"""
        invalid_filename = "file/with/slash.jpg"
        
        result = self.service.get_file_url(invalid_filename)
        
        self.assertFalse(result.success)
        self.assertEqual(result.result, FileOperationResult.INVALID_PATH)

    @patch('requests.Session.options')
    def test_get_storage_info_success(self, mock_options):
        """Test successful storage info retrieval"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {
            'Server': 'Apache/2.4.41',
            'DAV': '1, 2'
        }
        mock_options.return_value = mock_response
        
        # Act
        result = self.service.get_storage_info()
        
        # Assert
        self.assertTrue(result.success)
        self.assertEqual(result.result, FileOperationResult.SUCCESS)
        self.assertIsNotNone(result.data)
        
        info = result.data
        self.assertEqual(info['base_url'], "http://31.182.67.115/webdav/components")
        self.assertTrue(info['connected'])
        self.assertEqual(info['server'], "Apache/2.4.41")
        self.assertEqual(info['dav_capabilities'], "1, 2")


class TestWebDAVStorageFactory(unittest.TestCase):
    """Test WebDAV storage factory"""

    def test_create_storage_service_basic_config(self):
        """Test factory creation with basic configuration"""
        factory = WebDAVStorageFactory()
        config = {
            'base_url': 'http://31.182.67.115/webdav/components'
        }
        
        service = factory.create_storage_service(config)
        
        self.assertIsInstance(service, WebDAVStorageService)
        self.assertEqual(service._config.base_url, 'http://31.182.67.115/webdav/components')

    def test_create_storage_service_full_config(self):
        """Test factory creation with full configuration"""
        factory = WebDAVStorageFactory()
        mock_logger = Mock()
        
        config = {
            'base_url': 'http://31.182.67.115/webdav/components',
            'username': 'testuser',
            'password': 'testpass',
            'timeout': 60,
            'verify_ssl': False,
            'max_retries': 5,
            'chunk_size': 4096,
            'logger': mock_logger
        }
        
        service = factory.create_storage_service(config)
        
        self.assertIsInstance(service, WebDAVStorageService)
        self.assertEqual(service._config.base_url, 'http://31.182.67.115/webdav/components')
        self.assertEqual(service._config.username, 'testuser')
        self.assertEqual(service._config.password, 'testpass')
        self.assertEqual(service._config.timeout, 60)
        self.assertFalse(service._config.verify_ssl)
        self.assertEqual(service._config.max_retries, 5)
        self.assertEqual(service._config.chunk_size, 4096)
        self.assertEqual(service._logger, mock_logger)


class TestWebDAVStorageServiceIntegration(unittest.TestCase):
    """Integration tests for WebDAV storage service"""

    def setUp(self):
        """Set up integration test fixtures"""
        self.config = WebDAVStorageConfig(
            base_url="http://31.182.67.115/webdav/components",
            timeout=30
        )
        self.service = WebDAVStorageService(self.config)

    @unittest.skip("Integration test - requires live WebDAV server")
    def test_integration_file_lifecycle(self):
        """
        Integration test for complete file lifecycle.
        
        Note: This test is skipped by default as it requires a live WebDAV server.
        Enable by removing @unittest.skip decorator when testing against real server.
        """
        # Test file upload
        test_content = b"This is a test file for integration testing"
        file_data = io.BytesIO(test_content)
        filename = "integration_test.txt"
        
        # Upload
        upload_result = self.service.upload_file(file_data, filename, "text/plain")
        self.assertTrue(upload_result.success)
        
        # Check if file exists
        exists_result = self.service.file_exists(filename)
        self.assertTrue(exists_result.success)
        self.assertTrue(exists_result.data)
        
        # Get file info
        info_result = self.service.get_file_info(filename)
        self.assertTrue(info_result.success)
        self.assertEqual(info_result.file_info.name, filename)
        
        # Download
        download_result = self.service.download_file(filename)
        self.assertTrue(download_result.success)
        self.assertEqual(download_result.data.getvalue(), test_content)
        
        # Rename
        new_filename = "integration_test_renamed.txt"
        move_result = self.service.move_file(filename, new_filename)
        self.assertTrue(move_result.success)
        
        # Verify old file doesn't exist
        old_exists_result = self.service.file_exists(filename)
        self.assertTrue(old_exists_result.success)
        self.assertFalse(old_exists_result.data)
        
        # Verify new file exists
        new_exists_result = self.service.file_exists(new_filename)
        self.assertTrue(new_exists_result.success)
        self.assertTrue(new_exists_result.data)
        
        # Delete
        delete_result = self.service.delete_file(new_filename)
        self.assertTrue(delete_result.success)
        
        # Verify file is deleted
        final_exists_result = self.service.file_exists(new_filename)
        self.assertTrue(final_exists_result.success)
        self.assertFalse(final_exists_result.data)


if __name__ == '__main__':
    unittest.main()