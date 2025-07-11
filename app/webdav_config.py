"""
WebDAV Configuration Models

SQLAlchemy models for managing WebDAV configuration settings stored in PostgreSQL.
Follows the existing model patterns and schema structure.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, func
from sqlalchemy.dialects.postgresql import INET
from app import db
from datetime import datetime
from typing import Dict, Any, Optional


class WebDAVConfig(db.Model):
    """
    Model for WebDAV configuration settings.
    
    Stores connection details, timeouts, and other settings for WebDAV storage.
    """
    __tablename__ = 'webdav_config'
    __table_args__ = {'schema': 'component_app', 'extend_existing': True}

    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Configuration identity
    config_name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text)
    environment = Column(String(50), nullable=False, default='production', index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    
    # WebDAV connection settings
    base_url = Column(Text, nullable=False)
    username = Column(String(255))
    password_encrypted = Column(Text)  # Always encrypted, never plain text
    
    # Connection settings
    timeout_seconds = Column(Integer, nullable=False, default=30)
    verify_ssl = Column(Boolean, nullable=False, default=True)
    max_retries = Column(Integer, nullable=False, default=3)
    chunk_size = Column(Integer, nullable=False, default=8192)
    
    # Security settings
    encryption_key_id = Column(String(100))
    auth_type = Column(String(50), nullable=False, default='basic')
    
    # Advanced settings (stored as JSON)
    advanced_settings = Column(JSON, default={})
    
    # Usage tracking
    last_used_at = Column(DateTime)
    success_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.current_timestamp())
    updated_at = Column(DateTime, nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp())
    created_by = Column(String(100))
    updated_by = Column(String(100))

    def __repr__(self):
        return f'<WebDAVConfig {self.config_name} ({self.environment})>'

    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """
        Convert model to dictionary.
        
        Args:
            include_sensitive: Whether to include sensitive data (encrypted password)
            
        Returns:
            Dictionary representation of the model
        """
        data = {
            'id': self.id,
            'config_name': self.config_name,
            'description': self.description,
            'environment': self.environment,
            'is_active': self.is_active,
            'base_url': self.base_url,
            'username': self.username,
            'timeout_seconds': self.timeout_seconds,
            'verify_ssl': self.verify_ssl,
            'max_retries': self.max_retries,
            'chunk_size': self.chunk_size,
            'auth_type': self.auth_type,
            'advanced_settings': self.advanced_settings,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'updated_by': self.updated_by
        }
        
        if include_sensitive:
            data['password_encrypted'] = self.password_encrypted
            data['encryption_key_id'] = self.encryption_key_id
        
        return data

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage"""
        total_operations = self.success_count + self.error_count
        if total_operations == 0:
            return 0.0
        return (self.success_count / total_operations) * 100.0

    def is_healthy(self) -> bool:
        """Check if configuration is considered healthy (>90% success rate with some usage)"""
        total_operations = self.success_count + self.error_count
        if total_operations < 10:  # Not enough data
            return True
        return self.success_rate >= 90.0


class WebDAVUsageLog(db.Model):
    """
    Model for logging WebDAV operations.
    
    Tracks all operations for monitoring, debugging, and performance analysis.
    """
    __tablename__ = 'webdav_usage_log'
    __table_args__ = {'schema': 'component_app', 'extend_existing': True}

    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Foreign key to config
    config_id = Column(Integer, db.ForeignKey('component_app.webdav_config.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Operation details
    operation = Column(String(50), nullable=False, index=True)
    filename = Column(String(500))
    file_size = Column(Integer)
    
    # Result
    success = Column(Boolean, nullable=False, index=True)
    status_code = Column(Integer)
    error_message = Column(Text)
    
    # Performance
    duration_ms = Column(Integer)  # Operation duration in milliseconds
    
    # Context
    user_agent = Column(String(500))
    ip_address = Column(INET)
    request_id = Column(String(100))  # For correlating with application logs
    
    # Timestamp
    created_at = Column(DateTime, nullable=False, default=func.current_timestamp(), index=True)

    # Relationship  
    config = db.relationship('WebDAVConfig', backref='usage_logs')

    def __repr__(self):
        return f'<WebDAVUsageLog {self.operation} {self.filename} success={self.success}>'

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'config_id': self.config_id,
            'operation': self.operation,
            'filename': self.filename,
            'file_size': self.file_size,
            'success': self.success,
            'status_code': self.status_code,
            'error_message': self.error_message,
            'duration_ms': self.duration_ms,
            'user_agent': self.user_agent,
            'ip_address': str(self.ip_address) if self.ip_address else None,
            'request_id': self.request_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }