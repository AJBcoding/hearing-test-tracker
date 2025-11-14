"""Tests for audiogram marker detection."""
import numpy as np
import cv2
import pytest
from backend.ocr.marker_detector import detect_markers_by_color


def test_detect_red_markers():
    """Test detection of red circular markers (right ear)."""
    # Create test image with red circles
    image = np.zeros((500, 500, 3), dtype=np.uint8)

    # Draw red circles at known positions
    cv2.circle(image, (100, 100), 10, (0, 0, 255), -1)
    cv2.circle(image, (200, 200), 10, (0, 0, 255), -1)
    cv2.circle(image, (300, 300), 10, (0, 0, 255), -1)

    markers = detect_markers_by_color(image, 'red')

    assert len(markers) == 3
    assert all('x' in m and 'y' in m for m in markers)
    # Check approximate positions (allow some tolerance)
    positions = [(m['x'], m['y']) for m in markers]
    assert any(abs(x - 100) < 15 and abs(y - 100) < 15 for x, y in positions)


def test_detect_blue_markers():
    """Test detection of blue X markers (left ear)."""
    # Create test image with blue X markers
    image = np.zeros((500, 500, 3), dtype=np.uint8)

    # Draw blue X markers at known positions
    for x, y in [(100, 100), (200, 200), (300, 300)]:
        cv2.line(image, (x-10, y-10), (x+10, y+10), (255, 0, 0), 2)
        cv2.line(image, (x-10, y+10), (x+10, y-10), (255, 0, 0), 2)

    markers = detect_markers_by_color(image, 'blue')

    assert len(markers) == 3
    positions = [(m['x'], m['y']) for m in markers]
    assert any(abs(x - 100) < 15 and abs(y - 100) < 15 for x, y in positions)
