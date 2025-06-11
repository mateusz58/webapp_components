# tests/test_config.py
"""
Test configuration loading and environment variables.
"""

import pytest
import os
from config import Config, DevelopmentConfig, ProductionConfig, TestingConfig

class TestConfiguration:
    """Test configuration classes."""

    def test_config_has_secret_key(self):
        """Test that configuration has a secret key."""
        config = Config()
        assert hasattr(config, 'SECRET_KEY')
        assert config.SECRET_KEY is not None

    def test_development_config(self):
        """Test development configuration."""
        config = DevelopmentConfig()
        assert config.DEBUG is True

    def test_production_config(self):
        """Test production configuration."""
        config = ProductionConfig()
        assert config.DEBUG is False

    def test_testing_config(self):
        """Test testing configuration."""
        config = TestingConfig()
        assert config.TESTING is True
        assert 'sqlite' in config.SQLALCHEMY_DATABASE_URI

    def test_environment_variable_override(self):
        """Test that environment variables override defaults."""
        # Set environment variable
        test_secret = 'test-secret-from-env'
        os.environ['SECRET_KEY'] = test_secret

        config = Config()
        assert config.SECRET_KEY == test_secret

        # Clean up
        del os.environ['SECRET_KEY']
