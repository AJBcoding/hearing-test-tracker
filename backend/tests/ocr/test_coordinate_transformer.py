"""Tests for pixel-to-audiogram coordinate transformation."""
import pytest
from backend.ocr.coordinate_transformer import (
    pixels_to_audiogram_values,
    calibrate_axes
)


def test_calibrate_axes_returns_scale_factors():
    """Test axis calibration from graph bounds."""
    graph_bounds = {
        'x_min': 100,
        'x_max': 900,
        'y_min': 50,
        'y_max': 950
    }

    calibration = calibrate_axes(graph_bounds, image_width=1000, image_height=1000)

    assert 'freq_scale' in calibration
    assert 'db_scale' in calibration
    assert calibration['x_min'] == 100
    assert calibration['y_max'] == 950


def test_pixels_to_audiogram_values_converts_correctly():
    """Test pixel coordinate conversion to frequency/dB."""
    markers = [
        {'x': 200, 'y': 100},  # Should be low frequency, low dB (good hearing at low freq)
        {'x': 800, 'y': 800},  # Should be high frequency, high dB (hearing loss at high freq)
    ]

    graph_bounds = {
        'x_min': 100,
        'x_max': 900,
        'y_min': 50,
        'y_max': 950
    }

    calibration = calibrate_axes(graph_bounds, image_width=1000, image_height=1000)
    results = pixels_to_audiogram_values(markers, calibration)

    assert len(results) == 2
    assert all('frequency_hz' in r and 'threshold_db' in r for r in results)

    # First marker (left-top) should be lower frequency, lower dB
    # Second marker (right-bottom) should be higher frequency, higher dB
    assert results[0]['frequency_hz'] < results[1]['frequency_hz']
    assert results[0]['threshold_db'] < results[1]['threshold_db']
