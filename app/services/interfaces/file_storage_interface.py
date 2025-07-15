"""
File Storage Interface

Abstract interface for file storage operations following SOLID principles.
This interface can be implemented by different storage backends (WebDAV, S3, local filesystem, etc.)
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, BinaryIO
from dataclasses import dataclass
from enum import Enum


class FileOperationResult(Enum):
    """Enumeration of possible file operation results"""
    SUCCESS = "success"
    NOT_FOUND = "not_found"
    PERMISSION_DENIED = "permission_denied"
    NETWORK_ERROR = "network_error"
    INVALID_PATH = "invalid_path"
    ALREADY_EXISTS = "already_exists"
    STORAGE_FULL = "storage_full"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class FileInfo:
    """Data class representing file information"""
    name: str
    path: str
    size: Optional[int] = None
    content_type: Optional[str] = None
    last_modified: Optional[str] = None
    exists: bool = False
    url: Optional[str] = None


@dataclass
class StorageOperationResult:
    """Result of a storage operation"""
    success: bool
    result: FileOperationResult
    message: str
    data: Optional[Any] = None
    file_info: Optional[FileInfo] = None


class IFileStorageService(ABC):
    """
    Abstract interface for file storage operations.
    
    Follows Interface Segregation Principle (ISP) by providing focused,
    specific methods for file operations.
    """

    @abstractmethod
    def upload_file(
        self, 
        file_data: BinaryIO, 
        filename: str, 
        content_type: Optional[str] = None
    ) -> StorageOperationResult:
        """
        Upload a file to storage.
        
        Args:
            file_data: Binary file data to upload
            filename: Target filename
            content_type: MIME type of the file
            
        Returns:
            StorageOperationResult with operation details
        """
        pass

    @abstractmethod
    def download_file(self, filename: str) -> StorageOperationResult:
        """
        Download a file from storage.
        
        Args:
            filename: Name of file to download
            
        Returns:
            StorageOperationResult with file data
        """
        pass

    @abstractmethod
    def delete_file(self, filename: str) -> StorageOperationResult:
        """
        Delete a file from storage.
        
        Args:
            filename: Name of file to delete
            
        Returns:
            StorageOperationResult with operation details
        """
        pass

    @abstractmethod
    def move_file(self, old_filename: str, new_filename: str) -> StorageOperationResult:
        """
        Move/rename a file in storage.
        
        Args:
            old_filename: Current filename
            new_filename: New filename
            
        Returns:
            StorageOperationResult with operation details
        """
        pass

    @abstractmethod
    def copy_file(self, source_filename: str, dest_filename: str) -> StorageOperationResult:
        """
        Copy a file in storage.
        
        Args:
            source_filename: Source filename
            dest_filename: Destination filename
            
        Returns:
            StorageOperationResult with operation details
        """
        pass

    @abstractmethod
    def file_exists(self, filename: str) -> StorageOperationResult:
        """
        Check if a file exists in storage.
        
        Args:
            filename: Name of file to check
            
        Returns:
            StorageOperationResult with existence status
        """
        pass

    @abstractmethod
    def get_file_info(self, filename: str) -> StorageOperationResult:
        """
        Get detailed information about a file.
        
        Args:
            filename: Name of file to get info for
            
        Returns:
            StorageOperationResult with FileInfo data
        """
        pass

    @abstractmethod
    def list_files(
        self, 
        pattern: Optional[str] = None,
        limit: Optional[int] = None
    ) -> StorageOperationResult:
        """
        List files in storage.
        
        Args:
            pattern: Optional filename pattern to filter by
            limit: Optional limit on number of results
            
        Returns:
            StorageOperationResult with list of FileInfo objects
        """
        pass

    @abstractmethod
    def get_file_url(self, filename: str) -> StorageOperationResult:
        """
        Get a URL for accessing a file.
        
        Args:
            filename: Name of file to get URL for
            
        Returns:
            StorageOperationResult with file URL
        """
        pass

    @abstractmethod
    def validate_filename(self, filename: str) -> bool:
        """
        Validate that a filename is acceptable for this storage backend.
        
        Args:
            filename: Filename to validate
            
        Returns:
            True if filename is valid, False otherwise
        """
        pass

    @abstractmethod
    def get_storage_info(self) -> StorageOperationResult:
        """
        Get information about the storage backend (capacity, usage, etc.).
        
        Returns:
            StorageOperationResult with storage information
        """
        pass


class IFileStorageFactory(ABC):
    """
    Factory interface for creating file storage services.
    
    Follows Dependency Inversion Principle (DIP) by depending on abstractions.
    """

    @abstractmethod
    def create_storage_service(self, config: Dict[str, Any]) -> IFileStorageService:
        """
        Create a file storage service instance.
        
        Args:
            config: Configuration parameters for the storage service
            
        Returns:
            IFileStorageService implementation
        """
        pass