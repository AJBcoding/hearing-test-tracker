"""API routes for hearing test application."""
from flask import Blueprint, request, jsonify, current_app, g
from pathlib import Path
from typing import Dict, List
import shutil
from datetime import datetime
from functools import wraps
from backend.config import AUDIOGRAMS_DIR, OCR_CONFIDENCE_THRESHOLD
from backend.database.db_utils import get_connection, generate_uuid
from backend.ocr.jacoti_parser import parse_jacoti_audiogram
from backend.auth.decorators import require_auth
from backend.utils.file_validator import sanitize_filename, validate_upload_file

api_bp = Blueprint('api', __name__, url_prefix='/api')


def rate_limit(limit_string):
    """Apply rate limiting to a route using Flask-Limiter's storage."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask_limiter.util import get_remote_address
            limiter = current_app.limiter

            # Build a unique key for this endpoint and client
            key = f"rate_limit:{request.endpoint}:{get_remote_address()}"

            try:
                # Get the storage backend
                storage = limiter._storage

                # Parse the limit (e.g., "10 per minute")
                parts = limit_string.split()
                if len(parts) == 3 and parts[1] == "per":
                    limit_count = int(parts[0])
                    period_name = parts[2]

                    # Convert period to seconds
                    period_seconds = {
                        "second": 1,
                        "minute": 60,
                        "hour": 3600,
                        "day": 86400
                    }.get(period_name, 60)

                    # Get current count from storage
                    current = storage.get(key) or 0

                    if current >= limit_count:
                        return jsonify({'error': 'Rate limit exceeded. Too many requests.'}), 429

                    # Increment the counter
                    storage.incr(key, expiry=period_seconds)

            except Exception as e:
                # If rate limiting fails, log and allow request (graceful degradation)
                current_app.logger.warning(f"Rate limiting error: {e}")

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def _get_db_connection():
    """Get database connection using app config."""
    db_path = current_app.config.get('DB_PATH')
    return get_connection(db_path)


def _get_limiter():
    """Get limiter from current app."""
    return current_app.limiter


@api_bp.route('/tests/upload', methods=['POST'])
@require_auth
@rate_limit("10 per minute")
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

    result = _process_single_file(file)

    if 'error' in result:
        error_code = result.get('status_code', 500)
        return jsonify({'error': result['error']}), error_code

    return jsonify(result)


@api_bp.route('/tests/bulk-upload', methods=['POST'])
@require_auth
def bulk_upload_tests():
    """
    Bulk upload and process multiple audiogram images.

    Request:
        Multipart form with multiple 'files[]' fields containing JPEG images

    Response:
        {
            'total': int,
            'successful': int,
            'failed': int,
            'results': [
                {
                    'filename': str,
                    'status': 'success' | 'error',
                    'test_id': str (if success),
                    'confidence': float (if success),
                    'needs_review': bool (if success),
                    'error': str (if error)
                },
                ...
            ]
        }
    """
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files provided'}), 400

    files = request.files.getlist('files[]')

    if not files or len(files) == 0:
        return jsonify({'error': 'No files provided'}), 400

    results = []
    successful = 0
    failed = 0

    for file in files:
        if file.filename == '':
            continue

        result = _process_single_file(file)

        if 'error' in result:
            results.append({
                'filename': file.filename,
                'status': 'error',
                'error': result['error']
            })
            failed += 1
        else:
            results.append({
                'filename': file.filename,
                'status': 'success',
                'test_id': result['test_id'],
                'confidence': result['confidence'],
                'needs_review': result['needs_review']
            })
            successful += 1

    return jsonify({
        'total': len(results),
        'successful': successful,
        'failed': failed,
        'results': results
    })


def _process_single_file(file):
    """
    Process a single audiogram file.

    Args:
        file: FileStorage object from request.files

    Returns:
        dict: Result with test_id, confidence, etc. or error message
    """
    # Sanitize filename to prevent path traversal
    safe_filename = sanitize_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    filename = f"{timestamp}_{safe_filename}"
    filepath = AUDIOGRAMS_DIR / filename

    try:
        file.save(filepath)
    except Exception as e:
        return {'error': f'Failed to save file: {str(e)}', 'status_code': 500}

    # Validate uploaded file
    is_valid, error_message = validate_upload_file(filepath, file.filename)
    if not is_valid:
        # Clean up invalid file
        if filepath.exists():
            filepath.unlink()
        return {'error': error_message, 'status_code': 400}

    try:
        # Run OCR
        ocr_result = parse_jacoti_audiogram(filepath)

        # Save to database
        test_id = _save_test_to_database(ocr_result, filepath, g.user_id)

        return {
            'test_id': test_id,
            'confidence': ocr_result['confidence'],
            'needs_review': ocr_result['confidence'] < OCR_CONFIDENCE_THRESHOLD,
            'left_ear': ocr_result['left_ear'],
            'right_ear': ocr_result['right_ear']
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        # Clean up the file if processing failed
        if filepath.exists():
            filepath.unlink()
        return {'error': str(e), 'status_code': 500}


@api_bp.route('/tests', methods=['GET'])
@require_auth
def list_tests():
    """
    List all hearing tests for the authenticated user.

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
        WHERE user_id = ?
        ORDER BY test_date DESC
    """, (g.user_id,))

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
@require_auth
def get_test(test_id):
    """
    Get specific test with all measurements for the authenticated user.

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

    # Get test record (only if it belongs to the user)
    cursor.execute("""
        SELECT * FROM hearing_test WHERE id = ? AND user_id = ?
    """, (test_id, g.user_id))
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
@require_auth
def update_test(test_id):
    """
    Update test data after manual review (user can only update their own tests).

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

    # Verify test exists and belongs to user
    cursor.execute("SELECT id FROM hearing_test WHERE id = ? AND user_id = ?", (test_id, g.user_id))
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
        WHERE id = ? AND user_id = ?
    """, (
        data['test_date'],
        data.get('location'),
        data.get('device_name'),
        data.get('notes'),
        test_id,
        g.user_id
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
@require_auth
def delete_test(test_id):
    """
    Delete a test and its measurements (user can only delete their own tests).

    Response:
        {'success': true}
    """
    conn = _get_db_connection()
    cursor = conn.cursor()

    # Verify test exists and belongs to user
    cursor.execute("SELECT id, image_path FROM hearing_test WHERE id = ? AND user_id = ?", (test_id, g.user_id))
    test = cursor.fetchone()

    if not test:
        conn.close()
        return jsonify({'error': 'Test not found'}), 404

    # Delete measurements (cascade should handle this, but explicit is clear)
    cursor.execute("DELETE FROM audiogram_measurement WHERE id_hearing_test = ?", (test_id,))

    # Delete test (double-check ownership)
    cursor.execute("DELETE FROM hearing_test WHERE id = ? AND user_id = ?", (test_id, g.user_id))

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


def _save_test_to_database(ocr_result: dict, image_path: Path, user_id: int) -> str:
    """Save OCR results to database."""
    conn = _get_db_connection()
    cursor = conn.cursor()

    # Create test record
    test_id = generate_uuid()
    cursor.execute("""
        INSERT INTO hearing_test (
            id, test_date, source_type, location, device_name,
            image_path, ocr_confidence, user_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        test_id,
        ocr_result['test_date'] or datetime.now().isoformat(),
        'home',  # Default for Jacoti
        ocr_result['metadata']['location'],
        ocr_result['metadata']['device'],
        str(image_path),
        ocr_result['confidence'],
        user_id
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
