import pytest
import jwt
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import os
from backend.app import create_app
from backend.database.db_utils import get_connection


@pytest.fixture
def app():
    """Create test app with temporary database."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')

    app = create_app(db_path=Path(db_path))

    yield app

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


def test_user_registration_success(client):
    """Test user can register with valid email/password."""
    response = client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'password': 'SecurePassword123!'
    })

    assert response.status_code == 201
    data = response.get_json()
    assert 'user_id' in data
    assert 'token' in data
    assert data['email'] == 'test@example.com'


def test_user_registration_duplicate_email_rejected(client):
    """Test duplicate email registration rejected."""
    # Register first user
    client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'password': 'Password123!'
    })

    # Try to register again with same email
    response = client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'password': 'DifferentPassword123!'
    })

    assert response.status_code == 409
    data = response.get_json()
    assert 'already exists' in data['error'].lower()


def test_login_with_valid_credentials_returns_token(client):
    """Test login returns valid JWT token."""
    # Register user
    client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'password': 'Password123!'
    })

    # Login
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'Password123!'
    })

    assert response.status_code == 200
    data = response.get_json()
    assert 'token' in data
    assert 'user_id' in data

    # Verify token is valid JWT
    token = data['token']
    decoded = jwt.decode(token, options={"verify_signature": False})
    assert 'user_id' in decoded
    assert 'exp' in decoded


def test_login_with_invalid_password_rejected(client):
    """Test wrong password rejected."""
    # Register user
    client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'password': 'CorrectPassword123!'
    })

    # Try to login with wrong password
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'WrongPassword123!'
    })

    assert response.status_code == 401
    data = response.get_json()
    assert 'invalid' in data['error'].lower()


def test_login_with_nonexistent_email_rejected(client):
    """Test login with unknown email rejected."""
    response = client.post('/api/auth/login', json={
        'email': 'nonexistent@example.com',
        'password': 'Password123!'
    })

    assert response.status_code == 401
    data = response.get_json()
    assert 'invalid' in data['error'].lower()


def test_expired_token_rejected(client, app):
    """Test expired tokens return 401."""
    from backend.auth.decorators import require_auth
    from flask import jsonify, g

    # Add a test protected route
    @client.application.route('/test-protected')
    @require_auth
    def test_protected():
        return jsonify({'message': 'success', 'user_id': g.user_id})

    # Create expired token
    user_id = 1
    expired_time = datetime.utcnow() - timedelta(hours=1)
    token = jwt.encode({
        'user_id': user_id,
        'exp': expired_time
    }, app.config['JWT_SECRET_KEY'], algorithm='HS256')

    response = client.get('/test-protected',
                         headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 401
    data = response.get_json()
    assert 'expired' in data['error'].lower()


def test_invalid_token_rejected(client):
    """Test malformed tokens return 401."""
    from backend.auth.decorators import require_auth
    from flask import jsonify, g

    # Add a test protected route
    @client.application.route('/test-protected-2')
    @require_auth
    def test_protected():
        return jsonify({'message': 'success', 'user_id': g.user_id})

    response = client.get('/test-protected-2',
                         headers={'Authorization': 'Bearer invalid-token-12345'})

    assert response.status_code == 401
    data = response.get_json()
    assert 'invalid' in data['error'].lower()


def test_missing_token_rejected(client):
    """Test requests without token return 401."""
    from backend.auth.decorators import require_auth
    from flask import jsonify, g

    # Add a test protected route
    @client.application.route('/test-protected-3')
    @require_auth
    def test_protected():
        return jsonify({'message': 'success', 'user_id': g.user_id})

    response = client.get('/test-protected-3')

    assert response.status_code == 401
    data = response.get_json()
    assert 'required' in data['error'].lower()
