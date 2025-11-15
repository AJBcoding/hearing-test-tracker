import pytest
from backend.app import create_app


@pytest.fixture
def app():
    """Create test app."""
    app = create_app()
    app.config['CORS_ALLOWED_ORIGINS'] = ['http://localhost:5173']
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


def test_allowed_origin_accepted(client):
    """Test requests from allowed origins succeed."""
    response = client.get('/api/health',
                         headers={'Origin': 'http://localhost:5173'})

    assert response.status_code == 200
    assert response.headers.get('Access-Control-Allow-Origin') == 'http://localhost:5173'


def test_disallowed_origin_rejected(client):
    """Test requests from disallowed origins don't get CORS headers."""
    response = client.get('/api/health',
                         headers={'Origin': 'http://evil.com'})

    assert response.status_code == 200  # Request succeeds
    # But CORS header should not include evil.com
    cors_origin = response.headers.get('Access-Control-Allow-Origin')
    assert cors_origin != 'http://evil.com'


def test_cors_credentials_supported(client):
    """Test CORS allows credentials."""
    response = client.options('/api/tests',
                             headers={
                                 'Origin': 'http://localhost:5173',
                                 'Access-Control-Request-Method': 'POST',
                                 'Access-Control-Request-Headers': 'Authorization'
                             })

    assert response.headers.get('Access-Control-Allow-Credentials') == 'true'
    assert 'Authorization' in response.headers.get('Access-Control-Allow-Headers', '')


def test_production_requires_explicit_origins():
    """Test production config requires CORS origins."""
    import os
    os.environ['FLASK_ENV'] = 'production'
    os.environ['SECRET_KEY'] = 'test-key'
    os.environ.pop('CORS_ALLOWED_ORIGINS', None)

    with pytest.raises(ValueError, match="CORS_ALLOWED_ORIGINS must be set"):
        create_app()

    # Cleanup
    os.environ.pop('FLASK_ENV', None)
    os.environ.pop('SECRET_KEY', None)
    os.environ.pop('CORS_ALLOWED_ORIGINS', None)
