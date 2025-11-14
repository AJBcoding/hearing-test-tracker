"""Tests for OCR image processing."""
import numpy as np
import cv2
import pytest
from backend.ocr.image_processor import preprocess_image, extract_graph_region


def test_preprocess_image_converts_to_grayscale(tmp_path):
    """Test that preprocessing converts image to grayscale."""
    # Create a simple color test image
    color_image = np.zeros((100, 100, 3), dtype=np.uint8)
    color_image[:, :, 0] = 255  # Blue channel

    image_path = tmp_path / "test.jpg"
    cv2.imwrite(str(image_path), color_image)

    processed = preprocess_image(image_path)

    # Grayscale images have 2 dimensions (height, width)
    assert len(processed.shape) == 2
    assert processed.shape == (100, 100)


def test_extract_graph_region_returns_bounds():
    """Test that graph region extraction returns valid bounds."""
    # Create test image with a white rectangle (graph region)
    image = np.zeros((1275, 2190), dtype=np.uint8)
    # Draw white rectangle representing graph area
    image[200:1000, 300:1800] = 255

    bounds = extract_graph_region(image)

    assert 'x_min' in bounds
    assert 'x_max' in bounds
    assert 'y_min' in bounds
    assert 'y_max' in bounds
    assert bounds['x_max'] > bounds['x_min']
    assert bounds['y_max'] > bounds['y_min']
