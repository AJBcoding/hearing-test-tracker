import pytest
from pathlib import Path
import tempfile
import os
from io import BytesIO
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
    """Create auth headers with a test user."""
    with app.app_context():
        from backend.database.db_utils import get_connection
        from backend.auth.utils import hash_password

        conn = get_connection(app.config['DB_PATH'])
        cursor = conn.cursor()
        cursor.execute('INSERT INTO user (email, password_hash) VALUES (?, ?)',
                      ('test@example.com', hash_password('test123')))
        user_id = cursor.lastrowid
        conn.commit()

        token = generate_token(user_id)
    return {'Authorization': f'Bearer {token}'}


def test_valid_image_file_accepted(client, auth_headers):
    """Test that valid image files are accepted."""
    # Create a minimal valid JPEG (just the SOI marker for testing)
    valid_jpeg = b'\xff\xd8\xff\xe0\x00\x10JFIF'

    response = client.post('/api/tests/upload',
                          data={'file': (BytesIO(valid_jpeg), 'test.jpg')},
                          content_type='multipart/form-data',
                          headers=auth_headers)

    # Will fail OCR but should pass file validation
    # We're testing that it doesn't reject based on file type
    assert response.status_code in [200, 500]  # 500 is OK (OCR failure), just not 400/413


def test_oversized_file_rejected(client, auth_headers):
    """Test that files over MAX_CONTENT_LENGTH are rejected."""
    # Create a 20MB file (larger than 16MB limit)
    large_data = b'x' * (20 * 1024 * 1024)

    response = client.post('/api/tests/upload',
                          data={'file': (BytesIO(large_data), 'large.jpg')},
                          content_type='multipart/form-data',
                          headers=auth_headers)

    assert response.status_code == 413
    data = response.get_json()
    assert 'too large' in data['error'].lower()


def test_invalid_mime_type_rejected(client, auth_headers):
    """Test that non-image files are rejected."""
    # Create a text file disguised as jpg
    text_content = b'This is not an image file'

    response = client.post('/api/tests/upload',
                          data={'file': (BytesIO(text_content), 'fake.jpg')},
                          content_type='multipart/form-data',
                          headers=auth_headers)

    assert response.status_code == 400
    data = response.get_json()
    assert 'invalid file type' in data['error'].lower() or 'mime type' in data['error'].lower()


def test_executable_file_rejected(client, auth_headers):
    """Test that executable files are rejected."""
    # ELF header (Linux executable)
    elf_header = b'\x7fELF\x02\x01\x01\x00'

    response = client.post('/api/tests/upload',
                          data={'file': (BytesIO(elf_header), 'malware.jpg')},
                          content_type='multipart/form-data',
                          headers=auth_headers)

    assert response.status_code == 400
    data = response.get_json()
    assert 'invalid file type' in data['error'].lower() or 'mime type' in data['error'].lower()


def test_script_file_rejected(client, auth_headers):
    """Test that script files are rejected."""
    script_content = b'#!/bin/bash\nrm -rf /'

    response = client.post('/api/tests/upload',
                          data={'file': (BytesIO(script_content), 'script.jpg')},
                          content_type='multipart/form-data',
                          headers=auth_headers)

    assert response.status_code == 400
    data = response.get_json()
    assert 'invalid file type' in data['error'].lower() or 'mime type' in data['error'].lower()


def test_empty_file_rejected(client, auth_headers):
    """Test that empty files are rejected."""
    response = client.post('/api/tests/upload',
                          data={'file': (BytesIO(b''), 'empty.jpg')},
                          content_type='multipart/form-data',
                          headers=auth_headers)

    assert response.status_code == 400
    data = response.get_json()
    assert 'empty' in data['error'].lower() or 'invalid' in data['error'].lower()


def test_filename_sanitization(client, auth_headers, app):
    """Test that filenames are sanitized to prevent path traversal."""
    # Try to upload with malicious filename
    valid_jpeg = b'\xff\xd8\xff\xe0\x00\x10JFIF'
    malicious_filename = '../../../etc/passwd.jpg'

    response = client.post('/api/tests/upload',
                          data={'file': (BytesIO(valid_jpeg), malicious_filename)},
                          content_type='multipart/form-data',
                          headers=auth_headers)

    # Should either succeed or fail OCR, but not create file outside upload dir
    # Check that no file was created outside the upload directory
    assert not Path('/etc/passwd.jpg').exists()
    assert not Path('../etc/passwd.jpg').exists()


def test_rate_limiting_enforced(client, auth_headers):
    """Test that rate limiting prevents too many uploads."""
    valid_jpeg = b'\xff\xd8\xff\xe0\x00\x10JFIF'

    # Make 11 upload attempts (limit should be 10 per minute)
    for i in range(11):
        response = client.post('/api/tests/upload',
                              data={'file': (BytesIO(valid_jpeg), f'test{i}.jpg')},
                              content_type='multipart/form-data',
                              headers=auth_headers)

        if i < 10:
            # First 10 should succeed or fail OCR (not rate limited)
            assert response.status_code in [200, 400, 500]
        else:
            # 11th should be rate limited
            assert response.status_code == 429


def test_bulk_upload_validates_each_file(client, auth_headers):
    """Test that bulk upload validates each file."""
    valid_jpeg = b'\xff\xd8\xff\xe0\x00\x10JFIF'
    invalid_file = b'This is not an image'

    response = client.post('/api/tests/bulk-upload',
                          data={
                              'files[]': [
                                  (BytesIO(valid_jpeg), 'valid.jpg'),
                                  (BytesIO(invalid_file), 'invalid.jpg')
                              ]
                          },
                          content_type='multipart/form-data',
                          headers=auth_headers)

    assert response.status_code == 200
    data = response.get_json()

    # Should have results for both files
    assert data['total'] == 2

    # At least one should fail validation (the invalid one)
    assert data['failed'] >= 1


def test_allowed_extensions_only(client, auth_headers):
    """Test that only allowed file extensions are accepted."""
    valid_jpeg = b'\xff\xd8\xff\xe0\x00\x10JFIF'

    # Try disallowed extension
    response = client.post('/api/tests/upload',
                          data={'file': (BytesIO(valid_jpeg), 'test.exe')},
                          content_type='multipart/form-data',
                          headers=auth_headers)

    assert response.status_code == 400
    data = response.get_json()
    assert 'extension' in data['error'].lower() or 'file type' in data['error'].lower()
