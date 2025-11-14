"""API routes for hearing test application."""
from flask import Blueprint, request, jsonify, current_app
from pathlib import Path
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

    # Insert measurements
    for ear_name, ear_data in [('left', ocr_result['left_ear']),
                                ('right', ocr_result['right_ear'])]:
        for measurement in ear_data:
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
