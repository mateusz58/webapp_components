"""
WebDAV Storage Service Implementation

Professional WebDAV client implementation following SOLID principles.
Provides CRUD operations on WebDAV storage for file management.
"""

import requests
import logging
from typing import BinaryIO, Optional, Dict, Any, List
from urllib.parse import urljoin, quote
import re
from io import BytesIO
import xml.etree.ElementTree as ET
from datetime import datetime

from .interfaces.file_storage_interface import (
    IFileStorageService, 
    IFileStorageFactory,
    StorageOperationResult, 
    FileInfo, 
    FileOperationResult
)


class WebDAVStorageConfig:
    """Configuration class for WebDAV storage service"""
    
    def __init__(
        self,
        base_url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 30,
        verify_ssl: bool = True,
        max_retries: int = 3,
        chunk_size: int = 8192
    ):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.max_retries = max_retries
        self.chunk_size = chunk_size


class WebDAVStorageService(IFileStorageService):
    """
    WebDAV implementation of IFileStorageService.
    
    Follows Single Responsibility Principle by focusing solely on WebDAV operations.
    Implements all abstract methods from the interface (Liskov Substitution Principle).
    """

    def __init__(self, config: WebDAVStorageConfig, logger: Optional[logging.Logger] = None):
        """
        Initialize WebDAV storage service.
        
        Args:
            config: WebDAV configuration
            logger: Optional logger instance for dependency injection
        """
        self._config = config
        self._logger = logger or logging.getLogger(__name__)
        self._session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create and configure HTTP session for WebDAV operations"""
        session = requests.Session()
        
        if self._config.username and self._config.password:
            session.auth = (self._config.username, self._config.password)
        
        session.verify = self._config.verify_ssl
        
        # Configure retry strategy
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=self._config.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session

    def _build_url(self, filename: str) -> str:
        """Build full URL for a file"""
        # Ensure filename is properly URL encoded
        encoded_filename = quote(filename, safe='')
        return f"{self._config.base_url}/{encoded_filename}"

    def _handle_request_exception(self, operation: str, e: Exception) -> StorageOperationResult:
        """Handle and classify request exceptions"""
        self._logger.error(f"WebDAV {operation} failed: {str(e)}")
        
        if isinstance(e, requests.exceptions.ConnectionError):
            return StorageOperationResult(
                success=False,
                result=FileOperationResult.NETWORK_ERROR,
                message=f"Network connection failed during {operation}: {str(e)}"
            )
        elif isinstance(e, requests.exceptions.Timeout):
            return StorageOperationResult(
                success=False,
                result=FileOperationResult.NETWORK_ERROR,
                message=f"Request timeout during {operation}: {str(e)}"
            )
        else:
            return StorageOperationResult(
                success=False,
                result=FileOperationResult.UNKNOWN_ERROR,
                message=f"Unexpected error during {operation}: {str(e)}"
            )

    def _handle_http_response(self, response: requests.Response, operation: str) -> Optional[StorageOperationResult]:
        """
        Handle HTTP response codes and return appropriate result if error.
        Returns None if response indicates success.
        """
        if response.status_code == 404:
            return StorageOperationResult(
                success=False,
                result=FileOperationResult.NOT_FOUND,
                message=f"File not found during {operation}"
            )
        elif response.status_code == 403:
            return StorageOperationResult(
                success=False,
                result=FileOperationResult.PERMISSION_DENIED,
                message=f"Permission denied during {operation}"
            )
        elif response.status_code == 409:
            return StorageOperationResult(
                success=False,
                result=FileOperationResult.ALREADY_EXISTS,
                message=f"Resource already exists during {operation}"
            )
        elif response.status_code == 507:
            return StorageOperationResult(
                success=False,
                result=FileOperationResult.STORAGE_FULL,
                message=f"Storage full during {operation}"
            )
        elif not (200 <= response.status_code < 300):
            return StorageOperationResult(
                success=False,
                result=FileOperationResult.UNKNOWN_ERROR,
                message=f"HTTP {response.status_code} error during {operation}: {response.text}"
            )
        
        return None  # Success

    def upload_file(
        self, 
        file_data: BinaryIO, 
        filename: str, 
        content_type: Optional[str] = None
    ) -> StorageOperationResult:
        """Upload a file to WebDAV storage using PUT method"""
        if not self.validate_filename(filename):
            return StorageOperationResult(
                success=False,
                result=FileOperationResult.INVALID_PATH,
                message=f"Invalid filename: {filename}"
            )

        url = self._build_url(filename)
        headers = {}
        
        if content_type:
            headers['Content-Type'] = content_type

        try:
            self._logger.info(f"Uploading file: {filename} to {url}")
            
            # Reset file pointer to beginning
            file_data.seek(0)
            
            response = self._session.put(
                url,
                data=file_data,
                headers=headers,
                timeout=self._config.timeout
            )
            
            # Handle HTTP errors
            error_result = self._handle_http_response(response, "upload")
            if error_result:
                return error_result

            # Success - get file info
            file_info = FileInfo(
                name=filename,
                path=url,
                url=url,
                exists=True,
                content_type=content_type
            )

            self._logger.info(f"Successfully uploaded file: {filename}")
            
            return StorageOperationResult(
                success=True,
                result=FileOperationResult.SUCCESS,
                message=f"File {filename} uploaded successfully",
                file_info=file_info
            )

        except Exception as e:
            return self._handle_request_exception("upload", e)

    def download_file(self, filename: str) -> StorageOperationResult:
        """Download a file from WebDAV storage using GET method"""
        url = self._build_url(filename)

        try:
            self._logger.info(f"Downloading file: {filename} from {url}")
            
            response = self._session.get(
                url,
                timeout=self._config.timeout,
                stream=True
            )
            
            # Handle HTTP errors
            error_result = self._handle_http_response(response, "download")
            if error_result:
                return error_result

            # Read file data
            file_data = BytesIO()
            for chunk in response.iter_content(chunk_size=self._config.chunk_size):
                if chunk:
                    file_data.write(chunk)
            
            file_data.seek(0)

            # Get file info
            file_info = FileInfo(
                name=filename,
                path=url,
                url=url,
                exists=True,
                size=len(file_data.getvalue()),
                content_type=response.headers.get('Content-Type')
            )

            self._logger.info(f"Successfully downloaded file: {filename}")
            
            return StorageOperationResult(
                success=True,
                result=FileOperationResult.SUCCESS,
                message=f"File {filename} downloaded successfully",
                data=file_data,
                file_info=file_info
            )

        except Exception as e:
            return self._handle_request_exception("download", e)

    def delete_file(self, filename: str) -> StorageOperationResult:
        """Delete a file from WebDAV storage using DELETE method"""
        url = self._build_url(filename)

        try:
            self._logger.info(f"Deleting file: {filename} from {url}")
            
            response = self._session.delete(
                url,
                timeout=self._config.timeout
            )
            
            # Handle HTTP errors
            error_result = self._handle_http_response(response, "delete")
            if error_result:
                return error_result

            self._logger.info(f"Successfully deleted file: {filename}")
            
            return StorageOperationResult(
                success=True,
                result=FileOperationResult.SUCCESS,
                message=f"File {filename} deleted successfully"
            )

        except Exception as e:
            return self._handle_request_exception("delete", e)

    def move_file(self, old_filename: str, new_filename: str) -> StorageOperationResult:
        """Move/rename a file using WebDAV MOVE method"""
        if not self.validate_filename(old_filename) or not self.validate_filename(new_filename):
            return StorageOperationResult(
                success=False,
                result=FileOperationResult.INVALID_PATH,
                message=f"Invalid filename: {old_filename} or {new_filename}"
            )

        old_url = self._build_url(old_filename)
        new_url = self._build_url(new_filename)

        try:
            self._logger.info(f"Moving file: {old_filename} to {new_filename}")
            
            headers = {
                'Destination': new_url,
                'Overwrite': 'F'  # Don't overwrite existing files
            }
            
            response = self._session.request(
                'MOVE',
                old_url,
                headers=headers,
                timeout=self._config.timeout
            )
            
            # Handle HTTP errors
            error_result = self._handle_http_response(response, "move")
            if error_result:
                return error_result

            # Get info about moved file
            file_info = FileInfo(
                name=new_filename,
                path=new_url,
                url=new_url,
                exists=True
            )

            self._logger.info(f"Successfully moved file: {old_filename} to {new_filename}")
            
            return StorageOperationResult(
                success=True,
                result=FileOperationResult.SUCCESS,
                message=f"File moved from {old_filename} to {new_filename}",
                file_info=file_info
            )

        except Exception as e:
            return self._handle_request_exception("move", e)

    def copy_file(self, source_filename: str, dest_filename: str) -> StorageOperationResult:
        """Copy a file using WebDAV COPY method"""
        if not self.validate_filename(source_filename) or not self.validate_filename(dest_filename):
            return StorageOperationResult(
                success=False,
                result=FileOperationResult.INVALID_PATH,
                message=f"Invalid filename: {source_filename} or {dest_filename}"
            )

        source_url = self._build_url(source_filename)
        dest_url = self._build_url(dest_filename)

        try:
            self._logger.info(f"Copying file: {source_filename} to {dest_filename}")
            
            headers = {
                'Destination': dest_url,
                'Overwrite': 'F'  # Don't overwrite existing files
            }
            
            response = self._session.request(
                'COPY',
                source_url,
                headers=headers,
                timeout=self._config.timeout
            )
            
            # Handle HTTP errors
            error_result = self._handle_http_response(response, "copy")
            if error_result:
                return error_result

            # Get info about copied file
            file_info = FileInfo(
                name=dest_filename,
                path=dest_url,
                url=dest_url,
                exists=True
            )

            self._logger.info(f"Successfully copied file: {source_filename} to {dest_filename}")
            
            return StorageOperationResult(
                success=True,
                result=FileOperationResult.SUCCESS,
                message=f"File copied from {source_filename} to {dest_filename}",
                file_info=file_info
            )

        except Exception as e:
            return self._handle_request_exception("copy", e)

    def file_exists(self, filename: str) -> StorageOperationResult:
        """Check if a file exists using WebDAV HEAD method"""
        url = self._build_url(filename)

        try:
            self._logger.debug(f"Checking existence of file: {filename}")
            
            response = self._session.head(
                url,
                timeout=self._config.timeout
            )
            
            exists = response.status_code == 200
            
            file_info = FileInfo(
                name=filename,
                path=url,
                url=url,
                exists=exists
            )

            return StorageOperationResult(
                success=True,
                result=FileOperationResult.SUCCESS,
                message=f"File {filename} {'exists' if exists else 'does not exist'}",
                data=exists,
                file_info=file_info
            )

        except Exception as e:
            return self._handle_request_exception("file_exists", e)

    def get_file_info(self, filename: str) -> StorageOperationResult:
        """Get detailed file information using WebDAV PROPFIND method"""
        url = self._build_url(filename)

        try:
            self._logger.debug(f"Getting file info for: {filename}")
            
            # First check if file exists
            head_response = self._session.head(url, timeout=self._config.timeout)
            
            if head_response.status_code == 404:
                return StorageOperationResult(
                    success=False,
                    result=FileOperationResult.NOT_FOUND,
                    message=f"File {filename} not found"
                )

            # Get basic info from HEAD response
            file_info = FileInfo(
                name=filename,
                path=url,
                url=url,
                exists=True,
                content_type=head_response.headers.get('Content-Type'),
                size=int(head_response.headers.get('Content-Length', 0)) or None,
                last_modified=head_response.headers.get('Last-Modified')
            )

            self._logger.debug(f"Retrieved file info for: {filename}")
            
            return StorageOperationResult(
                success=True,
                result=FileOperationResult.SUCCESS,
                message=f"File info retrieved for {filename}",
                file_info=file_info
            )

        except Exception as e:
            return self._handle_request_exception("get_file_info", e)

    def list_files(
        self, 
        pattern: Optional[str] = None,
        limit: Optional[int] = None
    ) -> StorageOperationResult:
        """List files using WebDAV PROPFIND method"""
        try:
            self._logger.debug(f"Listing files with pattern: {pattern}, limit: {limit}")
            
            # Use PROPFIND to list directory contents
            headers = {
                'Depth': '1',
                'Content-Type': 'application/xml; charset=utf-8'
            }
            
            # Basic PROPFIND body to get file properties
            propfind_body = '''<?xml version="1.0" encoding="utf-8"?>
            <D:propfind xmlns:D="DAV:">
                <D:prop>
                    <D:resourcetype/>
                    <D:getcontentlength/>
                    <D:getcontenttype/>
                    <D:getlastmodified/>
                    <D:displayname/>
                </D:prop>
            </D:propfind>'''
            
            response = self._session.request(
                'PROPFIND',
                self._config.base_url,
                headers=headers,
                data=propfind_body,
                timeout=self._config.timeout
            )
            
            # Handle HTTP errors
            error_result = self._handle_http_response(response, "list_files")
            if error_result:
                return error_result

            # Parse XML response
            files = self._parse_propfind_response(response.text, pattern, limit)

            self._logger.debug(f"Listed {len(files)} files")
            
            return StorageOperationResult(
                success=True,
                result=FileOperationResult.SUCCESS,
                message=f"Listed {len(files)} files",
                data=files
            )

        except Exception as e:
            return self._handle_request_exception("list_files", e)

    def _parse_propfind_response(
        self, 
        xml_content: str, 
        pattern: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[FileInfo]:
        """Parse PROPFIND XML response and extract file information"""
        files = []
        
        try:
            root = ET.fromstring(xml_content)
            
            # Define XML namespaces
            namespaces = {'D': 'DAV:'}
            
            for response in root.findall('.//D:response', namespaces):
                href = response.find('D:href', namespaces)
                if href is None:
                    continue
                
                href_text = href.text.strip()
                
                # Skip directories and the base directory itself
                if href_text.endswith('/'):
                    continue
                
                # Extract filename from href
                filename = href_text.split('/')[-1]
                if not filename:
                    continue
                
                # Apply pattern filter if specified
                if pattern and not re.search(pattern, filename):
                    continue
                
                # Get file properties
                propstat = response.find('D:propstat', namespaces)
                if propstat is None:
                    continue
                
                prop = propstat.find('D:prop', namespaces)
                if prop is None:
                    continue
                
                # Extract properties
                size_elem = prop.find('D:getcontentlength', namespaces)
                content_type_elem = prop.find('D:getcontenttype', namespaces)
                last_modified_elem = prop.find('D:getlastmodified', namespaces)
                
                file_info = FileInfo(
                    name=filename,
                    path=self._build_url(filename),
                    url=self._build_url(filename),
                    exists=True,
                    size=int(size_elem.text) if size_elem is not None and size_elem.text else None,
                    content_type=content_type_elem.text if content_type_elem is not None else None,
                    last_modified=last_modified_elem.text if last_modified_elem is not None else None
                )
                
                files.append(file_info)
                
                # Apply limit if specified
                if limit and len(files) >= limit:
                    break
        
        except ET.ParseError as e:
            self._logger.warning(f"Failed to parse PROPFIND response: {e}")
        
        return files

    def get_file_url(self, filename: str) -> StorageOperationResult:
        """Get URL for accessing a file"""
        if not self.validate_filename(filename):
            return StorageOperationResult(
                success=False,
                result=FileOperationResult.INVALID_PATH,
                message=f"Invalid filename: {filename}"
            )

        url = self._build_url(filename)
        
        return StorageOperationResult(
            success=True,
            result=FileOperationResult.SUCCESS,
            message=f"URL generated for {filename}",
            data=url
        )

    def validate_filename(self, filename: str) -> bool:
        """Validate filename for WebDAV storage"""
        if not filename or not isinstance(filename, str):
            return False
        
        # Check for invalid characters
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        if any(char in filename for char in invalid_chars):
            return False
        
        # Check for reserved names (Windows compatibility)
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
        # Check the base name (without extension) for reserved names
        base_name = filename.split('.')[0].upper()
        if base_name in reserved_names:
            return False
        
        # Check length
        if len(filename) > 255:
            return False
        
        return True

    def get_storage_info(self) -> StorageOperationResult:
        """Get storage information (basic connectivity check)"""
        try:
            self._logger.debug("Getting storage info")
            
            # Simple OPTIONS request to check server capabilities
            response = self._session.options(
                self._config.base_url,
                timeout=self._config.timeout
            )
            
            info = {
                'base_url': self._config.base_url,
                'connected': response.status_code == 200,
                'server': response.headers.get('Server'),
                'dav_capabilities': response.headers.get('DAV'),
                'last_checked': datetime.now().isoformat()
            }
            
            return StorageOperationResult(
                success=True,
                result=FileOperationResult.SUCCESS,
                message="Storage info retrieved",
                data=info
            )

        except Exception as e:
            return self._handle_request_exception("get_storage_info", e)


class WebDAVStorageFactory(IFileStorageFactory):
    """
    Factory for creating WebDAV storage service instances.
    
    Follows Factory Pattern and Dependency Inversion Principle.
    """

    def create_storage_service(self, config: Dict[str, Any]) -> IFileStorageService:
        """
        Create WebDAV storage service from configuration.
        
        Args:
            config: Dictionary containing WebDAV configuration
            
        Returns:
            WebDAV storage service instance
        """
        webdav_config = WebDAVStorageConfig(
            base_url=config['base_url'],
            username=config.get('username'),
            password=config.get('password'),
            timeout=config.get('timeout', 30),
            verify_ssl=config.get('verify_ssl', True),
            max_retries=config.get('max_retries', 3),
            chunk_size=config.get('chunk_size', 8192)
        )
        
        logger = config.get('logger')
        
        return WebDAVStorageService(webdav_config, logger)