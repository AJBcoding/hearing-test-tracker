import os
import pytest
from backend.config import DevelopmentConfig, ProductionConfig, get_config


def test_development_config_loads():
    """Test development config has expected defaults."""
    config = DevelopmentConfig()
    assert config.DEBUG is True
    assert config.TESTING is False
    assert config.SECRET_KEY is not None


def test_production_config_requires_secret_key():
    """Test production config fails without SECRET_KEY."""
    os.environ.pop('SECRET_KEY', None)
    with pytest.raises(ValueError, match="SECRET_KEY must be set"):
        ProductionConfig()


def test_production_config_disables_debug():
    """Test production config has DEBUG=False."""
    os.environ['SECRET_KEY'] = 'test-secret-key-12345'
    os.environ['CORS_ALLOWED_ORIGINS'] = 'http://example.com'
    config = ProductionConfig()
    assert config.DEBUG is False
    os.environ.pop('SECRET_KEY')
    os.environ.pop('CORS_ALLOWED_ORIGINS')


def test_get_config_returns_correct_class():
    """Test get_config returns right config for environment."""
    os.environ['FLASK_ENV'] = 'development'
    config = get_config()
    assert isinstance(config, DevelopmentConfig)

    os.environ['FLASK_ENV'] = 'production'
    os.environ['SECRET_KEY'] = 'test-secret'
    os.environ['CORS_ALLOWED_ORIGINS'] = 'http://example.com'
    config = get_config()
    assert isinstance(config, ProductionConfig)

    # Cleanup
    os.environ.pop('FLASK_ENV', None)
    os.environ.pop('SECRET_KEY', None)
    os.environ.pop('CORS_ALLOWED_ORIGINS', None)
