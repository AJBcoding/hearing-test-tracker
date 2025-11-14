"""Parse Jacoti audiogram format using complete OCR pipeline."""
from pathlib import Path
from typing import Dict, List
import cv2
from backend.ocr.image_processor import preprocess_image, extract_graph_region
from backend.ocr.marker_detector import detect_markers_by_color
from backend.ocr.coordinate_transformer import calibrate_axes, pixels_to_audiogram_values


def parse_jacoti_audiogram(image_path: Path) -> Dict:
    """
    Parse Jacoti audiogram JPEG and extract all data.

    Args:
        image_path: Path to Jacoti audiogram JPEG

    Returns:
        Dictionary with extracted data:
        {
            'test_date': str,
            'left_ear': [{'frequency_hz': int, 'threshold_db': float}, ...],
            'right_ear': [{'frequency_hz': int, 'threshold_db': float}, ...],
            'metadata': {'location': str, 'device': str},
            'confidence': float  # 0.0-1.0
        }
    """
    # Load original color image for marker detection
    color_image = cv2.imread(str(image_path))
    if color_image is None:
        raise ValueError(f"Cannot read image: {image_path}")

    # Preprocess for graph region detection
    processed = preprocess_image(image_path)

    # Extract graph boundaries
    graph_bounds = extract_graph_region(processed)

    # Detect markers in color image
    red_markers = detect_markers_by_color(color_image, 'red')
    blue_markers = detect_markers_by_color(color_image, 'blue')

    # Calibrate axes
    h, w = processed.shape[:2]
    calibration = calibrate_axes(graph_bounds, w, h)

    # Convert markers to audiogram values
    right_ear_data = pixels_to_audiogram_values(red_markers, calibration)
    left_ear_data = pixels_to_audiogram_values(blue_markers, calibration)

    # Calculate confidence score
    confidence = _calculate_confidence(
        left_ear_data, right_ear_data,
        expected_count=9
    )

    # Extract metadata (simplified for now)
    metadata = {
        'location': 'Jacoti Hearing Center',
        'device': 'Jacoti'
    }

    return {
        'test_date': None,  # TODO: Add OCR text extraction for date
        'left_ear': left_ear_data,
        'right_ear': right_ear_data,
        'metadata': metadata,
        'confidence': confidence
    }


def _calculate_confidence(
    left_ear: List[Dict],
    right_ear: List[Dict],
    expected_count: int = 9
) -> float:
    """
    Calculate OCR confidence score based on data quality.

    Args:
        left_ear: Extracted left ear measurements
        right_ear: Extracted right ear measurements
        expected_count: Expected number of measurements per ear

    Returns:
        Confidence score (0.0-1.0)
    """
    score = 0.0

    # Check marker count (50% weight)
    left_count = len(left_ear)
    right_count = len(right_ear)
    count_score = (
        (min(left_count, expected_count) / expected_count) * 0.25 +
        (min(right_count, expected_count) / expected_count) * 0.25
    )
    score += count_score

    # Check frequency coverage (25% weight)
    all_freqs = [m['frequency_hz'] for m in left_ear + right_ear]
    unique_freqs = len(set(all_freqs))
    freq_score = min(unique_freqs / expected_count, 1.0) * 0.25
    score += freq_score

    # Check dB value validity (25% weight)
    valid_db = all(
        0 <= m['threshold_db'] <= 120
        for m in left_ear + right_ear
    )
    db_score = 0.25 if valid_db else 0.0
    score += db_score

    return round(score, 2)
