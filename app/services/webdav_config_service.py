"""
WebDAV Configuration Service

Service layer for managing WebDAV configurations stored in PostgreSQL.
Follows repository pattern and provides secure configuration management.
"""

import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
import base64
import hashlib
import os
from datetime import datetime

from app import db
from app.webdav_config import WebDAVConfig, WebDAVUsageLog
from .webdav_storage_service import WebDAVStorageConfig, WebDAVStorageService
from .interfaces import IFileStorageService


class WebDAVConfigurationError(Exception):
    """Custom exception for WebDAV configuration errors"""
    pass


class WebDAVPasswordEncryption:
    """
    Handles simple password encryption/decryption for WebDAV configurations.
    
    Uses basic XOR encryption for demonstration. In production, use proper encryption libraries.
    """

    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize password encryption.
        
        Args:
            encryption_key: Encryption key. If None, generates new key.
        """
        if encryption_key:
            self._key = encryption_key
        else:
            # In production, this should come from environment variables or key management service
            self._key = base64.urlsafe_b64encode(os.urandom(32)).decode()

    def encrypt_password(self, password: str) -> str:
        """
        Encrypt a password using XOR encryption.
        
        Args:
            password: Plain text password
            
        Returns:
            Base64 encoded encrypted password
        """
        if not password:
            return ""
        
        try:
            # Simple XOR encryption (for demo purposes)
            key_bytes = self._key.encode()
            password_bytes = password.encode()
            
            encrypted_bytes = bytearray()
            for i, byte in enumerate(password_bytes):
                encrypted_bytes.append(byte ^ key_bytes[i % len(key_bytes)])
            
            return base64.urlsafe_b64encode(encrypted_bytes).decode()
        except Exception as e:
            raise WebDAVConfigurationError(f"Failed to encrypt password: {str(e)}")

    def decrypt_password(self, encrypted_password: str) -> str:
        """
        Decrypt a password using XOR decryption.
        
        Args:
            encrypted_password: Base64 encoded encrypted password
            
        Returns:
            Plain text password
        """
        if not encrypted_password:
            return ""
        
        try:
            # Simple XOR decryption (same as encryption for XOR)
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_password.encode())
            key_bytes = self._key.encode()
            
            decrypted_bytes = bytearray()
            for i, byte in enumerate(encrypted_bytes):
                decrypted_bytes.append(byte ^ key_bytes[i % len(key_bytes)])
            
            return decrypted_bytes.decode()
        except Exception as e:
            raise WebDAVConfigurationError(f"Failed to decrypt password: {str(e)}")

    def get_key_id(self) -> str:
        """Get a hash of the encryption key for identification"""
        return hashlib.sha256(self._key.encode()).hexdigest()[:16]


class WebDAVConfigRepository:
    """
    Repository for WebDAV configuration data access.
    
    Follows Repository pattern for clean separation of data access.
    """

    def __init__(self, session: Optional[Session] = None, logger: Optional[logging.Logger] = None):
        """
        Initialize repository.
        
        Args:
            session: Database session. If None, uses db.session
            logger: Logger instance for dependency injection
        """
        self._session = session or db.session
        self._logger = logger or logging.getLogger(__name__)

    def get_by_name_and_environment(
        self, 
        config_name: str, 
        environment: str = 'production'
    ) -> Optional[WebDAVConfig]:
        """
        Get configuration by name and environment.
        
        Args:
            config_name: Configuration name
            environment: Environment (dev, staging, production)
            
        Returns:
            WebDAVConfig instance or None if not found
        """
        try:
            return self._session.query(WebDAVConfig).filter(
                and_(
                    WebDAVConfig.config_name == config_name,
                    WebDAVConfig.environment == environment,
                    WebDAVConfig.is_active == True
                )
            ).first()
        except Exception as e:
            self._logger.error(f"Error retrieving config {config_name}/{environment}: {str(e)}")
            return None

    def get_by_id(self, config_id: int) -> Optional[WebDAVConfig]:
        """Get configuration by ID"""
        try:
            return self._session.query(WebDAVConfig).filter_by(id=config_id).first()
        except Exception as e:
            self._logger.error(f"Error retrieving config by ID {config_id}: {str(e)}")
            return None

    def get_all_active(self, environment: Optional[str] = None) -> List[WebDAVConfig]:
        """
        Get all active configurations.
        
        Args:
            environment: Optional environment filter
            
        Returns:
            List of active WebDAVConfig instances
        """
        try:
            query = self._session.query(WebDAVConfig).filter_by(is_active=True)
            
            if environment:
                query = query.filter_by(environment=environment)
            
            return query.order_by(WebDAVConfig.config_name).all()
        except Exception as e:
            self._logger.error(f"Error retrieving active configs: {str(e)}")
            return []

    def create(self, config_data: Dict[str, Any]) -> WebDAVConfig:
        """
        Create new WebDAV configuration.
        
        Args:
            config_data: Configuration data dictionary
            
        Returns:
            Created WebDAVConfig instance
        """
        try:
            config = WebDAVConfig(**config_data)
            self._session.add(config)
            self._session.flush()  # Get ID without committing
            return config
        except Exception as e:
            self._session.rollback()
            self._logger.error(f"Error creating config: {str(e)}")
            raise WebDAVConfigurationError(f"Failed to create configuration: {str(e)}")

    def update(self, config: WebDAVConfig, update_data: Dict[str, Any]) -> WebDAVConfig:
        """
        Update existing configuration.
        
        Args:
            config: WebDAVConfig instance to update
            update_data: Data to update
            
        Returns:
            Updated WebDAVConfig instance
        """
        try:
            for key, value in update_data.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            config.updated_at = datetime.utcnow()
            return config
        except Exception as e:
            self._session.rollback()
            self._logger.error(f"Error updating config {config.id}: {str(e)}")
            raise WebDAVConfigurationError(f"Failed to update configuration: {str(e)}")

    def delete(self, config: WebDAVConfig) -> None:
        """
        Delete configuration (soft delete by setting is_active=False).
        
        Args:
            config: WebDAVConfig instance to delete
        """
        try:
            config.is_active = False
            config.updated_at = datetime.utcnow()
        except Exception as e:
            self._session.rollback()
            self._logger.error(f"Error deleting config {config.id}: {str(e)}")
            raise WebDAVConfigurationError(f"Failed to delete configuration: {str(e)}")

    def log_operation(
        self,
        config_id: int,
        operation: str,
        filename: Optional[str] = None,
        file_size: Optional[int] = None,
        success: bool = True,
        status_code: Optional[int] = None,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None,
        request_id: Optional[str] = None
    ) -> WebDAVUsageLog:
        """
        Log a WebDAV operation.
        
        Args:
            config_id: Configuration ID
            operation: Operation type (upload, download, delete, etc.)
            filename: File name
            file_size: File size in bytes
            success: Whether operation was successful
            status_code: HTTP status code
            error_message: Error message if failed
            duration_ms: Operation duration in milliseconds
            request_id: Request ID for correlation
            
        Returns:
            Created WebDAVUsageLog instance
        """
        try:
            log_entry = WebDAVUsageLog(
                config_id=config_id,
                operation=operation,
                filename=filename,
                file_size=file_size,
                success=success,
                status_code=status_code,
                error_message=error_message,
                duration_ms=duration_ms,
                request_id=request_id
            )
            
            self._session.add(log_entry)
            
            # Update configuration usage stats
            config = self.get_by_id(config_id)
            if config:
                config.last_used_at = datetime.utcnow()
                if success:
                    config.success_count += 1
                else:
                    config.error_count += 1
            
            return log_entry
        except Exception as e:
            self._session.rollback()
            self._logger.error(f"Error logging operation: {str(e)}")
            raise WebDAVConfigurationError(f"Failed to log operation: {str(e)}")

    def commit(self) -> None:
        """Commit current transaction"""
        try:
            self._session.commit()
        except Exception as e:
            self._session.rollback()
            self._logger.error(f"Error committing transaction: {str(e)}")
            raise WebDAVConfigurationError(f"Failed to commit transaction: {str(e)}")


class WebDAVConfigService:
    """
    Service layer for WebDAV configuration management.
    
    Provides high-level operations for managing WebDAV configurations
    with encryption, validation, and logging.
    """

    def __init__(
        self,
        repository: Optional[WebDAVConfigRepository] = None,
        encryption: Optional[WebDAVPasswordEncryption] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize service.
        
        Args:
            repository: Configuration repository for dependency injection
            encryption: Password encryption service for dependency injection
            logger: Logger instance for dependency injection
        """
        self._repository = repository or WebDAVConfigRepository()
        self._encryption = encryption or WebDAVPasswordEncryption()
        self._logger = logger or logging.getLogger(__name__)

    def get_storage_service(
        self, 
        config_name: str, 
        environment: str = 'production'
    ) -> IFileStorageService:
        """
        Get a configured WebDAV storage service.
        
        Args:
            config_name: Configuration name
            environment: Environment
            
        Returns:
            Configured WebDAV storage service
            
        Raises:
            WebDAVConfigurationError: If configuration not found or invalid
        """
        config = self._repository.get_by_name_and_environment(config_name, environment)
        
        if not config:
            raise WebDAVConfigurationError(
                f"WebDAV configuration '{config_name}' not found for environment '{environment}'"
            )

        if not config.is_active:
            raise WebDAVConfigurationError(
                f"WebDAV configuration '{config_name}' is not active"
            )

        # Decrypt password if present
        password = None
        if config.password_encrypted:
            try:
                password = self._encryption.decrypt_password(config.password_encrypted)
            except Exception as e:
                self._logger.error(f"Failed to decrypt password for config {config_name}: {str(e)}")
                raise WebDAVConfigurationError(f"Failed to decrypt password: {str(e)}")

        # Create WebDAV storage config
        storage_config = WebDAVStorageConfig(
            base_url=config.base_url,
            username=config.username,
            password=password,
            timeout=config.timeout_seconds,
            verify_ssl=config.verify_ssl,
            max_retries=config.max_retries,
            chunk_size=config.chunk_size
        )

        # Create storage service with logging wrapper
        storage_service = WebDAVStorageService(storage_config, self._logger)
        
        # Wrap with logging service
        return LoggingWebDAVStorageService(
            storage_service=storage_service,
            config_service=self,
            config_id=config.id,
            logger=self._logger
        )

    def create_configuration(
        self,
        config_name: str,
        base_url: str,
        environment: str = 'production',
        username: Optional[str] = None,
        password: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs
    ) -> WebDAVConfig:
        """
        Create new WebDAV configuration.
        
        Args:
            config_name: Unique configuration name
            base_url: WebDAV base URL
            environment: Environment (dev, staging, production)
            username: Optional username
            password: Optional password (will be encrypted)
            description: Optional description
            **kwargs: Additional configuration options
            
        Returns:
            Created configuration
        """
        # Encrypt password if provided
        password_encrypted = None
        if password:
            password_encrypted = self._encryption.encrypt_password(password)

        config_data = {
            'config_name': config_name,
            'base_url': base_url.rstrip('/'),  # Remove trailing slash
            'environment': environment,
            'username': username,
            'password_encrypted': password_encrypted,
            'description': description,
            'encryption_key_id': self._encryption.get_key_id(),
            'created_by': kwargs.get('created_by', 'system'),
            # Override defaults with provided values
            **{k: v for k, v in kwargs.items() if k in [
                'timeout_seconds', 'verify_ssl', 'max_retries', 'chunk_size',
                'auth_type', 'advanced_settings'
            ]}
        }

        config = self._repository.create(config_data)
        self._repository.commit()
        
        self._logger.info(f"Created WebDAV configuration: {config_name} ({environment})")
        return config

    def update_configuration(
        self,
        config_name: str,
        environment: str = 'production',
        **update_data
    ) -> WebDAVConfig:
        """
        Update existing configuration.
        
        Args:
            config_name: Configuration name
            environment: Environment
            **update_data: Fields to update
            
        Returns:
            Updated configuration
        """
        config = self._repository.get_by_name_and_environment(config_name, environment)
        
        if not config:
            raise WebDAVConfigurationError(
                f"Configuration '{config_name}' not found for environment '{environment}'"
            )

        # Handle password encryption
        if 'password' in update_data:
            password = update_data.pop('password')
            if password:
                update_data['password_encrypted'] = self._encryption.encrypt_password(password)
                update_data['encryption_key_id'] = self._encryption.get_key_id()
            else:
                update_data['password_encrypted'] = None

        updated_config = self._repository.update(config, update_data)
        self._repository.commit()
        
        self._logger.info(f"Updated WebDAV configuration: {config_name} ({environment})")
        return updated_config

    def delete_configuration(self, config_name: str, environment: str = 'production') -> None:
        """
        Delete (deactivate) configuration.
        
        Args:
            config_name: Configuration name
            environment: Environment
        """
        config = self._repository.get_by_name_and_environment(config_name, environment)
        
        if not config:
            raise WebDAVConfigurationError(
                f"Configuration '{config_name}' not found for environment '{environment}'"
            )

        self._repository.delete(config)
        self._repository.commit()
        
        self._logger.info(f"Deleted WebDAV configuration: {config_name} ({environment})")

    def list_configurations(self, environment: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all active configurations.
        
        Args:
            environment: Optional environment filter
            
        Returns:
            List of configuration dictionaries (without sensitive data)
        """
        configs = self._repository.get_all_active(environment)
        return [config.to_dict(include_sensitive=False) for config in configs]

    def test_configuration(self, config_name: str, environment: str = 'production') -> Dict[str, Any]:
        """
        Test WebDAV configuration connectivity.
        
        Args:
            config_name: Configuration name
            environment: Environment
            
        Returns:
            Test result dictionary
        """
        try:
            storage_service = self.get_storage_service(config_name, environment)
            result = storage_service.get_storage_info()
            
            return {
                'success': result.success,
                'message': result.message,
                'data': result.data
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e),
                'data': None
            }

    def log_operation(self, config_id: int, operation: str, **kwargs) -> None:
        """
        Log WebDAV operation.
        
        Args:
            config_id: Configuration ID
            operation: Operation type
            **kwargs: Additional log data
        """
        try:
            self._repository.log_operation(config_id, operation, **kwargs)
            self._repository.commit()
        except Exception as e:
            self._logger.error(f"Failed to log operation: {str(e)}")


class LoggingWebDAVStorageService:
    """
    Wrapper service that adds operation logging to WebDAV storage service.
    
    Follows Decorator pattern to add logging functionality.
    """

    def __init__(
        self,
        storage_service: IFileStorageService,
        config_service: WebDAVConfigService,
        config_id: int,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize logging wrapper.
        
        Args:
            storage_service: Underlying storage service
            config_service: Configuration service for logging
            config_id: Configuration ID
            logger: Logger instance
        """
        self._storage_service = storage_service
        self._config_service = config_service
        self._config_id = config_id
        self._logger = logger or logging.getLogger(__name__)

    def __getattr__(self, name):
        """Delegate all other methods to underlying storage service"""
        return getattr(self._storage_service, name)

    def _log_operation(self, operation: str, result, **kwargs):
        """Log operation with timing and result"""
        try:
            self._config_service.log_operation(
                config_id=self._config_id,
                operation=operation,
                success=result.success,
                error_message=result.message if not result.success else None,
                **kwargs
            )
        except Exception as e:
            self._logger.error(f"Failed to log operation {operation}: {str(e)}")

    def upload_file(self, file_data, filename, content_type=None):
        """Upload file with logging"""
        import time
        start_time = time.time()
        
        result = self._storage_service.upload_file(file_data, filename, content_type)
        
        duration_ms = int((time.time() - start_time) * 1000)
        file_size = len(file_data.getvalue()) if hasattr(file_data, 'getvalue') else None
        
        self._log_operation(
            'upload',
            result,
            filename=filename,
            file_size=file_size,
            duration_ms=duration_ms
        )
        
        return result

    def download_file(self, filename):
        """Download file with logging"""
        import time
        start_time = time.time()
        
        result = self._storage_service.download_file(filename)
        
        duration_ms = int((time.time() - start_time) * 1000)
        file_size = len(result.data.getvalue()) if result.success and result.data else None
        
        self._log_operation(
            'download',
            result,
            filename=filename,
            file_size=file_size,
            duration_ms=duration_ms
        )
        
        return result

    def delete_file(self, filename):
        """Delete file with logging"""
        import time
        start_time = time.time()
        
        result = self._storage_service.delete_file(filename)
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        self._log_operation(
            'delete',
            result,
            filename=filename,
            duration_ms=duration_ms
        )
        
        return result

    def move_file(self, old_filename, new_filename):
        """Move file with logging"""
        import time
        start_time = time.time()
        
        result = self._storage_service.move_file(old_filename, new_filename)
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        self._log_operation(
            'move',
            result,
            filename=f"{old_filename} -> {new_filename}",
            duration_ms=duration_ms
        )
        
        return result

    def copy_file(self, source_filename, dest_filename):
        """Copy file with logging"""
        import time
        start_time = time.time()
        
        result = self._storage_service.copy_file(source_filename, dest_filename)
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        self._log_operation(
            'copy',
            result,
            filename=f"{source_filename} -> {dest_filename}",
            duration_ms=duration_ms
        )
        
        return result