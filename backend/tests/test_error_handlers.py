import pytest
from flask import Flask
from backend.app import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_404_returns_json(client):
    """Test 404 errors return JSON, not HTML."""
    response = client.get('/nonexistent-route')

    assert response.status_code == 404
    assert response.content_type == 'application/json'

    data = response.get_json()
    assert 'error' in data
    assert 'status' in data
    assert data['status'] == 404


def test_405_method_not_allowed(client):
    """Test 405 errors return JSON."""
    response = client.post('/api/health')  # Health only accepts GET

    assert response.status_code == 405
    assert response.content_type == 'application/json'

    data = response.get_json()
    assert 'error' in data
    assert data['status'] == 405


def test_500_hides_stack_trace(client, monkeypatch):
    """Test 500 errors don't leak stack traces."""
    # We'll add a route that raises an exception for testing
    @client.application.route('/test-error')
    def trigger_error():
        raise Exception("Test exception")

    response = client.get('/test-error')

    assert response.status_code == 500
    assert response.content_type == 'application/json'

    data = response.get_json()
    assert 'error' in data
    assert data['status'] == 500
    # Should NOT contain stack trace details
    assert 'Test exception' not in data['error']
    assert 'Traceback' not in str(data)


def test_413_file_too_large(client):
    """Test 413 errors for oversized uploads."""
    # Directly test the 413 error handler by triggering it
    from werkzeug.exceptions import RequestEntityTooLarge

    @client.application.route('/test-413')
    def trigger_413():
        raise RequestEntityTooLarge()

    response = client.get('/test-413')

    assert response.status_code == 413
    assert response.content_type == 'application/json'

    data = response.get_json()
    assert 'error' in data
    assert data['status'] == 413
    assert 'too large' in data['error'].lower()
