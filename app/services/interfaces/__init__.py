"""
Interfaces package for service layer abstractions.

This package contains abstract interfaces following SOLID principles
for dependency injection and testability.
"""

from .file_storage_interface import (
    IFileStorageService,
    IFileStorageFactory,
    FileInfo,
    StorageOperationResult,
    FileOperationResult
)

__all__ = [
    'IFileStorageService',
    'IFileStorageFactory', 
    'FileInfo',
    'StorageOperationResult',
    'FileOperationResult'
]