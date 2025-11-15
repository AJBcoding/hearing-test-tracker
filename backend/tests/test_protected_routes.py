import pytest
from pathlib import Path
import tempfile
import os
from backend.app import create_app
from backend.auth.utils import generate_token


@pytest.fixture
def app():
    """Create test app with temporary database."""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    app = create_app(db_path=Path(db_path))
    yield app
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def auth_headers(app):
    """Create auth headers for user 1."""
    with app.app_context():
        token = generate_token(1)
    return {'Authorization': f'Bearer {token}'}


def test_get_tests_requires_auth(client):
    """Test GET /tests requires authentication."""
    response = client.get('/api/tests')
    assert response.status_code == 401


def test_upload_test_requires_auth(client):
    """Test POST /tests/upload requires authentication."""
    response = client.post('/api/tests/upload',
                          data={'file': (b'fake image data', 'test.jpg')},
                          content_type='multipart/form-data')
    assert response.status_code == 401


def test_bulk_upload_requires_auth(client):
    """Test POST /tests/bulk-upload requires authentication."""
    response = client.post('/api/tests/bulk-upload',
                          data={'files[]': [(b'fake', 'test.jpg')]},
                          content_type='multipart/form-data')
    assert response.status_code == 401


def test_get_test_requires_auth(client):
    """Test GET /tests/<id> requires authentication."""
    response = client.get('/api/tests/test-123')
    assert response.status_code == 401


def test_update_test_requires_auth(client):
    """Test PUT /tests/<id> requires authentication."""
    response = client.put('/api/tests/test-123', json={'notes': 'test'})
    assert response.status_code == 401


def test_delete_test_requires_auth(client):
    """Test DELETE /tests/<id> requires authentication."""
    response = client.delete('/api/tests/test-123')
    assert response.status_code == 401


def test_users_only_see_own_tests(client, app, auth_headers):
    """Test users can only see their own tests."""
    # Create user 1 and user 2
    with app.app_context():
        from backend.database.db_utils import get_connection
        from backend.auth.utils import hash_password

        conn = get_connection(app.config['DB_PATH'])
        cursor = conn.cursor()

        # Create two users
        cursor.execute('INSERT INTO user (email, password_hash) VALUES (?, ?)',
                      ('user1@test.com', hash_password('pass123')))
        user1_id = cursor.lastrowid

        cursor.execute('INSERT INTO user (email, password_hash) VALUES (?, ?)',
                      ('user2@test.com', hash_password('pass123')))
        user2_id = cursor.lastrowid

        # Create a test for user 1
        cursor.execute('''
            INSERT INTO hearing_test (id, test_date, source_type, user_id)
            VALUES (?, ?, ?, ?)
        ''', ('test-user1', '2025-01-01', 'audiologist', user1_id))

        # Create a test for user 2
        cursor.execute('''
            INSERT INTO hearing_test (id, test_date, source_type, user_id)
            VALUES (?, ?, ?, ?)
        ''', ('test-user2', '2025-01-02', 'audiologist', user2_id))

        conn.commit()

        # Get token for user 1
        user1_token = generate_token(user1_id)

    # User 1 should only see their test
    response = client.get('/api/tests',
                         headers={'Authorization': f'Bearer {user1_token}'})

    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['id'] == 'test-user1'


def test_user_cannot_access_another_users_test(client, app):
    """Test user cannot GET another user's test."""
    with app.app_context():
        from backend.database.db_utils import get_connection
        from backend.auth.utils import hash_password, generate_token

        conn = get_connection(app.config['DB_PATH'])
        cursor = conn.cursor()

        # Create two users
        cursor.execute('INSERT INTO user (email, password_hash) VALUES (?, ?)',
                      ('user1@test.com', hash_password('pass123')))
        user1_id = cursor.lastrowid

        cursor.execute('INSERT INTO user (email, password_hash) VALUES (?, ?)',
                      ('user2@test.com', hash_password('pass123')))
        user2_id = cursor.lastrowid

        # Create a test for user 2
        cursor.execute('''
            INSERT INTO hearing_test (id, test_date, source_type, user_id)
            VALUES (?, ?, ?, ?)
        ''', ('test-user2', '2025-01-02', 'audiologist', user2_id))

        conn.commit()

        # Get token for user 1
        user1_token = generate_token(user1_id)

    # User 1 tries to access user 2's test
    response = client.get('/api/tests/test-user2',
                         headers={'Authorization': f'Bearer {user1_token}'})

    assert response.status_code == 404  # Not found (can't see it exists)


def test_user_cannot_update_another_users_test(client, app):
    """Test user cannot UPDATE another user's test."""
    with app.app_context():
        from backend.database.db_utils import get_connection
        from backend.auth.utils import hash_password, generate_token

        conn = get_connection(app.config['DB_PATH'])
        cursor = conn.cursor()

        # Create two users
        cursor.execute('INSERT INTO user (email, password_hash) VALUES (?, ?)',
                      ('user1@test.com', hash_password('pass123')))
        user1_id = cursor.lastrowid

        cursor.execute('INSERT INTO user (email, password_hash) VALUES (?, ?)',
                      ('user2@test.com', hash_password('pass123')))
        user2_id = cursor.lastrowid

        # Create a test for user 2
        cursor.execute('''
            INSERT INTO hearing_test (id, test_date, source_type, user_id)
            VALUES (?, ?, ?, ?)
        ''', ('test-user2', '2025-01-02', 'audiologist', user2_id))

        conn.commit()

        # Get token for user 1
        user1_token = generate_token(user1_id)

    # User 1 tries to update user 2's test
    response = client.put('/api/tests/test-user2',
                         headers={'Authorization': f'Bearer {user1_token}'},
                         json={'notes': 'hacked!'})

    assert response.status_code == 404  # Not found (can't see it exists)


def test_user_cannot_delete_another_users_test(client, app):
    """Test user cannot DELETE another user's test."""
    with app.app_context():
        from backend.database.db_utils import get_connection
        from backend.auth.utils import hash_password, generate_token

        conn = get_connection(app.config['DB_PATH'])
        cursor = conn.cursor()

        # Create two users
        cursor.execute('INSERT INTO user (email, password_hash) VALUES (?, ?)',
                      ('user1@test.com', hash_password('pass123')))
        user1_id = cursor.lastrowid

        cursor.execute('INSERT INTO user (email, password_hash) VALUES (?, ?)',
                      ('user2@test.com', hash_password('pass123')))
        user2_id = cursor.lastrowid

        # Create a test for user 2
        cursor.execute('''
            INSERT INTO hearing_test (id, test_date, source_type, user_id)
            VALUES (?, ?, ?, ?)
        ''', ('test-user2', '2025-01-02', 'audiologist', user2_id))

        conn.commit()

        # Get token for user 1
        user1_token = generate_token(user1_id)

    # User 1 tries to delete user 2's test
    response = client.delete('/api/tests/test-user2',
                            headers={'Authorization': f'Bearer {user1_token}'})

    assert response.status_code == 404  # Not found (can't see it exists)
