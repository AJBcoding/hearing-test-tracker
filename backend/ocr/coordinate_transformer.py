"""Transform pixel coordinates to audiogram frequency/dB values."""
import numpy as np
from typing import List, Dict
from backend.config import STANDARD_FREQUENCIES


def calibrate_axes(
    graph_bounds: Dict[str, int],
    image_width: int,
    image_height: int
) -> Dict:
    """
    Calibrate frequency and dB scales from graph boundaries.

    Args:
        graph_bounds: Dictionary with x_min, x_max, y_min, y_max
        image_width: Total image width in pixels
        image_height: Total image height in pixels

    Returns:
        Calibration data for coordinate transformation
    """
    # Frequency range (Hz) - logarithmic scale
    freq_min = np.log10(STANDARD_FREQUENCIES[0])
    freq_max = np.log10(STANDARD_FREQUENCIES[-1])

    # dB range - linear scale, inverted (0 at top, 120 at bottom)
    db_min = 0
    db_max = 120

    # Calculate scale factors
    x_range = graph_bounds['x_max'] - graph_bounds['x_min']
    y_range = graph_bounds['y_max'] - graph_bounds['y_min']

    freq_scale = (freq_max - freq_min) / x_range
    db_scale = (db_max - db_min) / y_range

    return {
        'x_min': graph_bounds['x_min'],
        'x_max': graph_bounds['x_max'],
        'y_min': graph_bounds['y_min'],
        'y_max': graph_bounds['y_max'],
        'freq_min': freq_min,
        'freq_scale': freq_scale,
        'db_scale': db_scale
    }


def pixels_to_audiogram_values(
    markers: List[Dict[str, int]],
    calibration: Dict
) -> List[Dict[str, float]]:
    """
    Convert pixel coordinates to frequency (Hz) and threshold (dB).

    Args:
        markers: List of marker positions [{'x': int, 'y': int}, ...]
        calibration: Calibration data from calibrate_axes()

    Returns:
        List of audiogram values [{'frequency_hz': float, 'threshold_db': float}, ...]
    """
    results = []

    for marker in markers:
        # Calculate frequency (logarithmic scale)
        x_offset = marker['x'] - calibration['x_min']
        log_freq = calibration['freq_min'] + (x_offset * calibration['freq_scale'])
        frequency_hz = 10 ** log_freq

        # Calculate dB threshold (linear scale, inverted)
        y_offset = marker['y'] - calibration['y_min']
        threshold_db = y_offset * calibration['db_scale']

        # Round frequency to nearest standard frequency
        frequency_hz = _snap_to_standard_frequency(frequency_hz)

        results.append({
            'frequency_hz': frequency_hz,
            'threshold_db': round(threshold_db, 1)
        })

    return results


def _snap_to_standard_frequency(freq: float) -> int:
    """
    Round frequency to nearest standard audiometric frequency.

    Args:
        freq: Calculated frequency in Hz

    Returns:
        Nearest standard frequency
    """
    # Find closest standard frequency
    differences = [abs(freq - sf) for sf in STANDARD_FREQUENCIES]
    min_index = differences.index(min(differences))
    return STANDARD_FREQUENCIES[min_index]
