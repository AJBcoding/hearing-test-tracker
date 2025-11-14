"""API routes for hearing test application."""
from flask import Blueprint, request, jsonify, current_app
from pathlib import Path
from typing import Dict, List
import shutil
from datetime import datetime
from backend.config import AUDIOGRAMS_DIR, OCR_CONFIDENCE_THRESHOLD
from backend.database.db_utils import get_connection, generate_uuid
from backend.ocr.jacoti_parser import parse_jacoti_audiogram

api_bp = Blueprint('api', __name__, url_prefix='/api')


def _get_db_connection():
    """Get database connection using app config."""
    db_path = current_app.config.get('DB_PATH')
    return get_connection(db_path)


@api_bp.route('/tests/upload', methods=['POST'])
def upload_test():
    """
    Upload and process audiogram image.

    Request:
        Multipart form with 'file' field containing JPEG image

    Response:
        {
            'test_id': str,
            'confidence': float,
            'needs_review': bool,
            'left_ear': [...],
            'right_ear': [...]
        }
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    # Save uploaded file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{file.filename}"
    filepath = AUDIOGRAMS_DIR / filename
    file.save(filepath)

    try:
        # Run OCR
        ocr_result = parse_jacoti_audiogram(filepath)

        # Save to database
        test_id = _save_test_to_database(ocr_result, filepath)

        return jsonify({
            'test_id': test_id,
            'confidence': ocr_result['confidence'],
            'needs_review': ocr_result['confidence'] < OCR_CONFIDENCE_THRESHOLD,
            'left_ear': ocr_result['left_ear'],
            'right_ear': ocr_result['right_ear']
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/tests', methods=['GET'])
def list_tests():
    """
    List all hearing tests.

    Response:
        [
            {
                'id': str,
                'test_date': str,
                'source_type': str,
                'location': str,
                'confidence': float
            },
            ...
        ]
    """
    conn = _get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, test_date, source_type, location, ocr_confidence
        FROM hearing_test
        ORDER BY test_date DESC
    """)

    tests = []
    for row in cursor.fetchall():
        tests.append({
            'id': row['id'],
            'test_date': row['test_date'],
            'source_type': row['source_type'],
            'location': row['location'],
            'confidence': row['ocr_confidence']
        })

    conn.close()
    return jsonify(tests)


@api_bp.route('/tests/<test_id>', methods=['GET'])
def get_test(test_id):
    """
    Get specific test with all measurements.

    Response:
        {
            'id': str,
            'test_date': str,
            'left_ear': [...],
            'right_ear': [...],
            'metadata': {...}
        }
    """
    conn = _get_db_connection()
    cursor = conn.cursor()

    # Get test record
    cursor.execute("""
        SELECT * FROM hearing_test WHERE id = ?
    """, (test_id,))
    test = cursor.fetchone()

    if not test:
        conn.close()
        return jsonify({'error': 'Test not found'}), 404

    # Get measurements
    cursor.execute("""
        SELECT ear, frequency_hz, threshold_db
        FROM audiogram_measurement
        WHERE id_hearing_test = ?
        ORDER BY frequency_hz
    """, (test_id,))

    left_ear = []
    right_ear = []

    for row in cursor.fetchall():
        measurement = {
            'frequency_hz': row['frequency_hz'],
            'threshold_db': row['threshold_db']
        }
        if row['ear'] == 'left':
            left_ear.append(measurement)
        else:
            right_ear.append(measurement)

    conn.close()

    return jsonify({
        'id': test['id'],
        'test_date': test['test_date'],
        'source_type': test['source_type'],
        'location': test['location'],
        'left_ear': left_ear,
        'right_ear': right_ear,
        'metadata': {
            'device': test['device_name'],
            'technician': test['technician_name'],
            'notes': test['notes']
        }
    })


@api_bp.route('/tests/<test_id>', methods=['PUT'])
def update_test(test_id):
    """
    Update test data after manual review.

    Request:
        {
            'test_date': str,
            'location': str,
            'device_name': str,
            'notes': str,
            'left_ear': [{'frequency_hz': int, 'threshold_db': float}, ...],
            'right_ear': [{'frequency_hz': int, 'threshold_db': float}, ...]
        }

    Response:
        Updated test object (same as GET /tests/:id)
    """
    data = request.json
    conn = _get_db_connection()
    cursor = conn.cursor()

    # Verify test exists
    cursor.execute("SELECT id FROM hearing_test WHERE id = ?", (test_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Test not found'}), 404

    # Update test metadata
    cursor.execute("""
        UPDATE hearing_test
        SET test_date = ?,
            location = ?,
            device_name = ?,
            notes = ?
        WHERE id = ?
    """, (
        data['test_date'],
        data.get('location'),
        data.get('device_name'),
        data.get('notes'),
        test_id
    ))

    # Delete existing measurements
    cursor.execute("DELETE FROM audiogram_measurement WHERE id_hearing_test = ?", (test_id,))

    # Insert new measurements (deduplicated)
    for ear_name, ear_data in [('left', data['left_ear']), ('right', data['right_ear'])]:
        deduplicated = _deduplicate_measurements(ear_data)
        for measurement in deduplicated:
            cursor.execute("""
                INSERT INTO audiogram_measurement (
                    id, id_hearing_test, ear, frequency_hz, threshold_db
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                generate_uuid(),
                test_id,
                ear_name,
                measurement['frequency_hz'],
                measurement['threshold_db']
            ))

    conn.commit()
    conn.close()

    # Return updated test
    return get_test(test_id)


@api_bp.route('/tests/<test_id>', methods=['DELETE'])
def delete_test(test_id):
    """
    Delete a test and its measurements.

    Response:
        {'success': true}
    """
    conn = _get_db_connection()
    cursor = conn.cursor()

    # Verify test exists
    cursor.execute("SELECT id, image_path FROM hearing_test WHERE id = ?", (test_id,))
    test = cursor.fetchone()

    if not test:
        conn.close()
        return jsonify({'error': 'Test not found'}), 404

    # Delete measurements (cascade should handle this, but explicit is clear)
    cursor.execute("DELETE FROM audiogram_measurement WHERE id_hearing_test = ?", (test_id,))

    # Delete test
    cursor.execute("DELETE FROM hearing_test WHERE id = ?", (test_id,))

    conn.commit()
    conn.close()

    # Delete image file if it exists
    if test['image_path']:
        image_path = Path(test['image_path'])
        if image_path.exists():
            image_path.unlink()

    return jsonify({'success': True})


def _deduplicate_measurements(measurements: List[Dict]) -> List[Dict]:
    """
    Deduplicate measurements by frequency, keeping median threshold value.

    Args:
        measurements: List of measurements with frequency_hz and threshold_db

    Returns:
        Deduplicated list with one measurement per frequency
    """
    from collections import defaultdict
    import statistics

    # Group by frequency
    freq_groups = defaultdict(list)
    for m in measurements:
        freq_groups[m['frequency_hz']].append(m['threshold_db'])

    # Take median for each frequency
    result = []
    for freq, thresholds in freq_groups.items():
        median_threshold = statistics.median(thresholds)
        result.append({
            'frequency_hz': freq,
            'threshold_db': median_threshold
        })

    return sorted(result, key=lambda x: x['frequency_hz'])


def _save_test_to_database(ocr_result: dict, image_path: Path) -> str:
    """Save OCR results to database."""
    conn = _get_db_connection()
    cursor = conn.cursor()

    # Create test record
    test_id = generate_uuid()
    cursor.execute("""
        INSERT INTO hearing_test (
            id, test_date, source_type, location, device_name,
            image_path, ocr_confidence
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        test_id,
        ocr_result['test_date'] or datetime.now().isoformat(),
        'home',  # Default for Jacoti
        ocr_result['metadata']['location'],
        ocr_result['metadata']['device'],
        str(image_path),
        ocr_result['confidence']
    ))

    # Insert measurements (deduplicate by frequency first)
    for ear_name, ear_data in [('left', ocr_result['left_ear']),
                                ('right', ocr_result['right_ear'])]:
        # Deduplicate: group by frequency and take median threshold
        deduplicated = _deduplicate_measurements(ear_data)

        for measurement in deduplicated:
            cursor.execute("""
                INSERT INTO audiogram_measurement (
                    id, id_hearing_test, ear, frequency_hz, threshold_db
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                generate_uuid(),
                test_id,
                ear_name,
                measurement['frequency_hz'],
                measurement['threshold_db']
            ))

    conn.commit()
    conn.close()

    return test_id
