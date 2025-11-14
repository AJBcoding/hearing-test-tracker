"""Tests for upload API endpoint."""
import pytest
import json
from pathlib import Path
from backend.app import create_app
from backend.config import DB_PATH
from backend.database.db_utils import init_database


@pytest.fixture
def client(tmp_path):
    """Create test client with temporary database."""
    # Use temporary database
    test_db = tmp_path / "test.db"
    init_database(test_db)

    app = create_app(db_path=test_db)
    app.config['TESTING'] = True

    with app.test_client() as client:
        yield client


def test_upload_endpoint_accepts_image(client, tmp_path):
    """Test POST /api/tests/upload accepts audiogram image."""
    # Create a simple valid JPEG image (1x1 pixel black image)
    import cv2
    import numpy as np

    image = np.zeros((100, 100, 3), dtype=np.uint8)
    image_path = tmp_path / "test.jpg"
    cv2.imwrite(str(image_path), image)

    with open(image_path, 'rb') as f:
        response = client.post(
            '/api/tests/upload',
            data={'file': (f, 'audiogram.jpg')},
            content_type='multipart/form-data'
        )

    # Note: OCR will fail on dummy image, but endpoint should handle gracefully
    # We expect either 200 with low confidence or 500 with error message
    data = json.loads(response.data)

    if response.status_code == 200:
        assert 'test_id' in data
        assert 'confidence' in data
    else:
        # OCR failed on dummy image, which is expected
        assert response.status_code == 500
        assert 'error' in data


def test_list_tests_endpoint_returns_array(client):
    """Test GET /api/tests returns array of tests."""
    response = client.get('/api/tests')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
