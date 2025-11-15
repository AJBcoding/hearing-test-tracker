# Deep Dive: Backend CRUD Routes

**Flow:** Backend CRUD Operations (PUT, DELETE endpoints)
**Files:** `backend/api/routes.py:270-374`
**Severity Summary:** 4 High + 4 Medium + 2 Low = 10 total issues

---

## Architecture & Design Patterns

### Issue 1: No Authentication/Authorization Layer

**Severity:** 🔴 CRITICAL (High)
**Location:** `backend/api/routes.py:270-271` (PUT), `routes.py:340-341` (DELETE)
**Category:** Security / Architecture

**Description:**

Both update and delete endpoints are completely unauthenticated and unauthorized. Any client that knows a test ID can modify or delete that test, regardless of ownership. This is a critical security vulnerability for a medical data application.

**Current Code:**

```python
@api_bp.route('/tests/<test_id>', methods=['PUT'])
def update_test(test_id):
    """Update test data after manual review."""
    data = request.json
    conn = _get_db_connection()
    # ... directly updates without any ownership check

@api_bp.route('/tests/<test_id>', methods=['DELETE'])
def delete_test(test_id):
    """Delete a test and its measurements."""
    conn = _get_db_connection()
    # ... directly deletes without any ownership check
```

**Impact:**
- Unauthorized data modification and deletion
- HIPAA/GDPR compliance violations (health data exposed)
- No audit trail for who made changes
- Cannot support multi-user/multi-tenant scenarios

**Alternatives:**

**Option 1: JWT-Based Authentication with Ownership Checks** ⭐ Recommended

```python
from functools import wraps
from flask import g
import jwt

def require_auth(f):
    """Decorator to require valid JWT token."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'No authentication token'}), 401

        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            g.user_id = payload['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

        return f(*args, **kwargs)
    return decorated_function

def check_test_ownership(test_id: str) -> bool:
    """Verify current user owns the test."""
    conn = _get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM hearing_test WHERE id = ?", (test_id,))
    test = cursor.fetchone()
    conn.close()

    if not test:
        return False
    return test['user_id'] == g.user_id

@api_bp.route('/tests/<test_id>', methods=['PUT'])
@require_auth
def update_test(test_id):
    """Update test data after manual review."""
    if not check_test_ownership(test_id):
        return jsonify({'error': 'Forbidden'}), 403

    # ... proceed with update
```

- **Pro:** Industry standard, stateless, scalable
- **Pro:** Supports role-based access control (RBAC) extension
- **Pro:** Works well with modern frontend frameworks
- **Con:** Requires user table, login/registration endpoints
- **Con:** Adds complexity for token refresh mechanism

**Option 2: Session-Based Authentication**

```python
from flask_login import LoginManager, login_required, current_user

login_manager = LoginManager()

@api_bp.route('/tests/<test_id>', methods=['PUT'])
@login_required
def update_test(test_id):
    """Update test data after manual review."""
    conn = _get_db_connection()
    cursor = conn.cursor()

    # Check ownership
    cursor.execute("""
        SELECT user_id FROM hearing_test WHERE id = ?
    """, (test_id,))
    test = cursor.fetchone()

    if not test or test['user_id'] != current_user.id:
        conn.close()
        return jsonify({'error': 'Forbidden'}), 403

    # ... proceed with update
```

- **Pro:** Simpler to implement than JWT
- **Pro:** Built-in session management
- **Con:** Stateful (requires session storage)
- **Con:** Not ideal for API-first applications
- **Con:** CORS complexity for cross-domain requests

**Option 3: API Key-Based Authentication (Simple)**

```python
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')

        conn = _get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM api_keys WHERE key = ? AND active = 1", (api_key,))
        result = cursor.fetchone()
        conn.close()

        if not result:
            return jsonify({'error': 'Invalid API key'}), 401

        g.user_id = result['user_id']
        return f(*args, **kwargs)
    return decorated_function

@api_bp.route('/tests/<test_id>', methods=['PUT'])
@require_api_key
def update_test(test_id):
    # ... ownership check + update
```

- **Pro:** Very simple to implement
- **Pro:** Good for personal/internal tools
- **Con:** No standard token expiration
- **Con:** Less secure than JWT (keys don't expire automatically)
- **Con:** Key rotation is manual

**Recommendation:** Option 1 (JWT) for production applications. Option 3 (API Key) if this remains a personal tool with single user.

---

### Issue 2: No Transaction Management with Rollback

**Severity:** 🔴 CRITICAL (High)
**Location:** `backend/api/routes.py:289-334` (update), `routes.py:348-366` (delete)
**Category:** Data Integrity / Architecture

**Description:**

Both update and delete operations perform multiple database writes (UPDATE + DELETE + INSERT for updates; multiple DELETEs for delete) but use manual `conn.commit()` without explicit transaction boundaries or rollback handling. If any operation fails mid-sequence, the database is left in an inconsistent state.

**Current Code:**

```python
@api_bp.route('/tests/<test_id>', methods=['PUT'])
def update_test(test_id):
    data = request.json
    conn = _get_db_connection()
    cursor = conn.cursor()

    # Multiple operations with no transaction:
    cursor.execute("UPDATE hearing_test SET ...")  # Operation 1
    cursor.execute("DELETE FROM audiogram_measurement ...")  # Operation 2
    for measurement in ...:
        cursor.execute("INSERT INTO audiogram_measurement ...")  # Operations 3-N

    conn.commit()  # If this fails, some writes may have gone through
    conn.close()

    return get_test(test_id)
```

**Impact:**
- Data corruption if operation fails mid-update
- Partial deletes leave orphaned measurement records
- No way to recover from errors
- Database integrity violations

**Alternatives:**

**Option 1: Context Manager with Explicit Transaction** ⭐ Recommended

```python
# backend/database/db_utils.py
from contextlib import contextmanager

@contextmanager
def get_transaction(db_path: Optional[Path] = None):
    """
    Context manager for database transactions with automatic rollback.

    Usage:
        with get_transaction() as (conn, cursor):
            cursor.execute(...)
            # Automatically commits on success, rolls back on exception
    """
    if db_path is None:
        from backend.config import DB_PATH
        db_path = DB_PATH

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("BEGIN")  # Explicit transaction start
    cursor = conn.cursor()

    try:
        yield conn, cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# backend/api/routes.py
@api_bp.route('/tests/<test_id>', methods=['PUT'])
def update_test(test_id):
    """Update test data after manual review."""
    data = request.json

    try:
        with get_transaction() as (conn, cursor):
            # Verify test exists
            cursor.execute("SELECT id FROM hearing_test WHERE id = ?", (test_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Test not found'}), 404

            # Update metadata
            cursor.execute("""
                UPDATE hearing_test
                SET test_date = ?, location = ?, device_name = ?, notes = ?
                WHERE id = ?
            """, (data['test_date'], data.get('location'),
                  data.get('device_name'), data.get('notes'), test_id))

            # Delete and re-insert measurements
            cursor.execute("DELETE FROM audiogram_measurement WHERE id_hearing_test = ?", (test_id,))

            for ear_name, ear_data in [('left', data['left_ear']), ('right', data['right_ear'])]:
                deduplicated = _deduplicate_measurements(ear_data)
                for measurement in deduplicated:
                    cursor.execute("""
                        INSERT INTO audiogram_measurement (
                            id, id_hearing_test, ear, frequency_hz, threshold_db
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (generate_uuid(), test_id, ear_name,
                          measurement['frequency_hz'], measurement['threshold_db']))

            # Automatically commits here

        # Return updated test
        return get_test(test_id)

    except sqlite3.IntegrityError as e:
        return jsonify({'error': f'Database integrity error: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Update failed: {str(e)}'}), 500
```

- **Pro:** Automatic rollback on any exception
- **Pro:** Clean, Pythonic API with context manager
- **Pro:** Explicit transaction boundaries
- **Pro:** Reusable across all endpoints
- **Con:** Requires refactoring db_utils.py

**Option 2: Try/Except with Manual Rollback**

```python
@api_bp.route('/tests/<test_id>', methods=['PUT'])
def update_test(test_id):
    """Update test data after manual review."""
    data = request.json
    conn = _get_db_connection()
    cursor = conn.cursor()

    try:
        conn.execute("BEGIN")

        # Verify test exists
        cursor.execute("SELECT id FROM hearing_test WHERE id = ?", (test_id,))
        if not cursor.fetchone():
            raise ValueError('Test not found')

        # All operations...
        cursor.execute("UPDATE hearing_test ...")
        cursor.execute("DELETE FROM audiogram_measurement ...")
        # ... inserts

        conn.commit()
        return get_test(test_id)

    except ValueError as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        conn.rollback()
        return jsonify({'error': f'Update failed: {str(e)}'}), 500
    finally:
        conn.close()
```

- **Pro:** No changes to db_utils.py needed
- **Pro:** Easy to understand
- **Con:** Manual rollback in every endpoint (error-prone)
- **Con:** Verbose, repeated pattern
- **Con:** Easy to forget `finally` block

**Option 3: Savepoints for Nested Transactions**

```python
@contextmanager
def savepoint(conn, name: str):
    """Create a savepoint for partial rollback."""
    cursor = conn.cursor()
    cursor.execute(f"SAVEPOINT {name}")
    try:
        yield cursor
        cursor.execute(f"RELEASE SAVEPOINT {name}")
    except Exception:
        cursor.execute(f"ROLLBACK TO SAVEPOINT {name}")
        raise

@api_bp.route('/tests/<test_id>', methods=['PUT'])
def update_test(test_id):
    with get_transaction() as (conn, cursor):
        # Update metadata
        cursor.execute("UPDATE hearing_test ...")

        # Use savepoint for measurements (can rollback just this part)
        with savepoint(conn, 'measurements'):
            cursor.execute("DELETE FROM audiogram_measurement ...")
            # ... inserts
```

- **Pro:** Allows partial rollback without losing entire transaction
- **Pro:** Useful for complex multi-step operations
- **Con:** More complex to reason about
- **Con:** Overkill for current simple operations

**Recommendation:** Option 1 (Context Manager). Clean, reusable, and prevents 90% of transaction bugs.

---

### Issue 3: Inefficient Update Strategy (Delete All + Re-Insert All)

**Severity:** 🟡 MEDIUM
**Location:** `backend/api/routes.py:314-331`
**Category:** Performance / Architecture

**Description:**

The update endpoint deletes ALL measurements for a test and re-inserts ALL measurements, even if only one measurement changed. For a typical audiogram with 18 measurements (9 frequencies × 2 ears), this results in 19 SQL statements (1 DELETE + 18 INSERTs) even for a single-value change.

**Current Code:**

```python
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
        """, (...))
```

**Impact:**
- Unnecessary database writes and disk I/O
- Slower updates (especially noticeable with large datasets)
- More WAL/journal churn in SQLite
- Database bloat from deleted records

**Alternatives:**

**Option 1: Keep Simple Delete-All Approach** ⭐ Recommended

Keep current implementation as-is.

- **Pro:** Simple, easy to understand and maintain
- **Pro:** Avoids complex diff logic
- **Pro:** Always consistent (no partial update bugs)
- **Pro:** Performance impact minimal for typical use (18 measurements)
- **Con:** More database writes than necessary

**Option 2: Differential Update (UPSERT)**

```python
@api_bp.route('/tests/<test_id>', methods=['PUT'])
def update_test(test_id):
    # ...

    with get_transaction() as (conn, cursor):
        # Update metadata
        cursor.execute("UPDATE hearing_test ...")

        # Differential update for measurements
        for ear_name, ear_data in [('left', data['left_ear']), ('right', data['right_ear'])]:
            deduplicated = _deduplicate_measurements(ear_data)

            for measurement in deduplicated:
                # UPSERT: Insert or update if exists
                cursor.execute("""
                    INSERT INTO audiogram_measurement (
                        id, id_hearing_test, ear, frequency_hz, threshold_db
                    ) VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(id_hearing_test, ear, frequency_hz)
                    DO UPDATE SET threshold_db = excluded.threshold_db
                """, (generate_uuid(), test_id, ear_name,
                      measurement['frequency_hz'], measurement['threshold_db']))

        # Delete measurements that are no longer present
        submitted_frequencies = [m['frequency_hz'] for ear_data in [data['left_ear'], data['right_ear']]
                                  for m in _deduplicate_measurements(ear_data)]

        if submitted_frequencies:
            placeholders = ','.join(['?'] * len(submitted_frequencies))
            cursor.execute(f"""
                DELETE FROM audiogram_measurement
                WHERE id_hearing_test = ?
                AND frequency_hz NOT IN ({placeholders})
            """, [test_id] + submitted_frequencies)
```

- **Pro:** Minimal database writes (only changed values)
- **Pro:** Better performance for large datasets
- **Con:** Requires composite unique constraint on (id_hearing_test, ear, frequency_hz)
- **Con:** More complex logic (harder to maintain)
- **Con:** Risk of orphaned records if delete logic has bugs

**Option 3: Fetch-Compare-Update**

```python
# Fetch existing measurements
cursor.execute("""
    SELECT id, ear, frequency_hz, threshold_db
    FROM audiogram_measurement WHERE id_hearing_test = ?
""", (test_id,))
existing = {(row['ear'], row['frequency_hz']): row for row in cursor.fetchall()}

# Compare and update only changed
for ear_name, ear_data in [('left', data['left_ear']), ('right', data['right_ear'])]:
    for measurement in _deduplicate_measurements(ear_data):
        key = (ear_name, measurement['frequency_hz'])

        if key in existing:
            # Update if threshold changed
            if existing[key]['threshold_db'] != measurement['threshold_db']:
                cursor.execute("""
                    UPDATE audiogram_measurement
                    SET threshold_db = ?
                    WHERE id = ?
                """, (measurement['threshold_db'], existing[key]['id']))
            existing.pop(key)  # Mark as processed
        else:
            # Insert new measurement
            cursor.execute("INSERT INTO audiogram_measurement ...", (...))

# Delete measurements that were not in new data
for row in existing.values():
    cursor.execute("DELETE FROM audiogram_measurement WHERE id = ?", (row['id'],))
```

- **Pro:** Minimal writes (only changes)
- **Pro:** No schema changes needed
- **Con:** More complex (50+ lines vs 10)
- **Con:** Extra SELECT query before update
- **Con:** Logic bugs could leave partial state

**Recommendation:** Option 1 (Keep Current). The simplicity outweighs the minor performance cost for typical audiogram data. Only optimize if profiling shows this is a bottleneck.

---

## Error Handling & Edge Cases

### Issue 4: No Input Validation on Request Data

**Severity:** 🔴 CRITICAL (High)
**Location:** `backend/api/routes.py:288`
**Category:** Data Integrity / Security

**Description:**

The update endpoint accepts `request.json` without any validation. No checks for required fields, data types, value ranges, or malicious input. Invalid data will cause database errors or corrupt the data.

**Current Code:**

```python
@api_bp.route('/tests/<test_id>', methods=['PUT'])
def update_test(test_id):
    data = request.json  # No validation!
    # ... directly uses data['test_date'], data['left_ear'], etc.
```

**Impact:**
- Database crashes from missing required fields
- Invalid data inserted (e.g., threshold_db = 999, frequency_hz = -1)
- SQL injection if malformed data interpreted as SQL
- Type errors crash the endpoint
- No user-friendly error messages

**Alternatives:**

**Option 1: Pydantic Schema Validation** ⭐ Recommended

```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime

class MeasurementSchema(BaseModel):
    frequency_hz: int = Field(ge=64, le=16000, description="Frequency in Hz")
    threshold_db: float = Field(ge=-10, le=120, description="Hearing threshold in dB")

    @validator('frequency_hz')
    def validate_frequency(cls, v):
        # Standard audiometric frequencies
        valid_freqs = [64, 125, 250, 500, 750, 1000, 1500, 2000, 3000, 4000, 6000, 8000, 12000, 16000]
        if v not in valid_freqs:
            raise ValueError(f'Frequency {v} Hz is not a standard audiometric frequency')
        return v

class UpdateTestSchema(BaseModel):
    test_date: str  # ISO format datetime string
    location: Optional[str] = None
    device_name: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1000)
    left_ear: List[MeasurementSchema]
    right_ear: List[MeasurementSchema]

    @validator('test_date')
    def validate_date(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError('test_date must be valid ISO format datetime')
        return v

    @validator('left_ear', 'right_ear')
    def validate_ear_data(cls, v):
        if not v or len(v) == 0:
            raise ValueError('Ear data cannot be empty')
        if len(v) > 20:
            raise ValueError('Too many measurements (max 20 per ear)')
        return v

@api_bp.route('/tests/<test_id>', methods=['PUT'])
def update_test(test_id):
    """Update test data after manual review."""

    # Validate request data
    try:
        validated_data = UpdateTestSchema(**request.json)
    except ValidationError as e:
        return jsonify({
            'error': 'Validation failed',
            'details': e.errors()
        }), 400

    # Use validated_data.dict() for database operations
    with get_transaction() as (conn, cursor):
        # ... update using validated_data.test_date, etc.
```

- **Pro:** Comprehensive validation with clear error messages
- **Pro:** Type checking and range validation
- **Pro:** Auto-generated documentation (OpenAPI)
- **Pro:** Reusable schemas across endpoints
- **Con:** Additional dependency (pydantic)
- **Con:** ~50 lines of schema code

**Option 2: Manual Validation Functions**

```python
def validate_update_request(data: dict) -> tuple[bool, Optional[str]]:
    """
    Validate update test request data.

    Returns:
        (is_valid, error_message)
    """
    if not data:
        return False, "Request body is required"

    # Required fields
    required = ['test_date', 'left_ear', 'right_ear']
    for field in required:
        if field not in data:
            return False, f"Missing required field: {field}"

    # Validate date format
    try:
        datetime.fromisoformat(data['test_date'].replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return False, "test_date must be valid ISO format datetime"

    # Validate ear data
    for ear_name in ['left_ear', 'right_ear']:
        ear_data = data[ear_name]

        if not isinstance(ear_data, list):
            return False, f"{ear_name} must be an array"

        if len(ear_data) == 0:
            return False, f"{ear_name} cannot be empty"

        for measurement in ear_data:
            if 'frequency_hz' not in measurement or 'threshold_db' not in measurement:
                return False, f"Measurement missing frequency_hz or threshold_db"

            freq = measurement['frequency_hz']
            threshold = measurement['threshold_db']

            if not isinstance(freq, int) or freq < 64 or freq > 16000:
                return False, f"Invalid frequency: {freq} (must be 64-16000 Hz)"

            if not isinstance(threshold, (int, float)) or threshold < -10 or threshold > 120:
                return False, f"Invalid threshold: {threshold} (must be -10 to 120 dB)"

    # Validate optional fields
    if 'notes' in data and data['notes'] and len(data['notes']) > 1000:
        return False, "notes exceeds maximum length (1000 characters)"

    return True, None

@api_bp.route('/tests/<test_id>', methods=['PUT'])
def update_test(test_id):
    """Update test data after manual review."""

    # Validate request
    is_valid, error_msg = validate_update_request(request.json)
    if not is_valid:
        return jsonify({'error': error_msg}), 400

    data = request.json
    # ... proceed with update
```

- **Pro:** No external dependencies
- **Pro:** Full control over validation logic
- **Con:** Verbose (60+ lines)
- **Con:** Error-prone (easy to miss edge cases)
- **Con:** Less maintainable than Pydantic

**Option 3: Marshmallow Schema**

```python
from marshmallow import Schema, fields, validate, validates, ValidationError

class MeasurementSchema(Schema):
    frequency_hz = fields.Int(required=True, validate=validate.Range(min=64, max=16000))
    threshold_db = fields.Float(required=True, validate=validate.Range(min=-10, max=120))

class UpdateTestSchema(Schema):
    test_date = fields.Str(required=True)
    location = fields.Str(required=False, allow_none=True)
    device_name = fields.Str(required=False, allow_none=True)
    notes = fields.Str(required=False, allow_none=True, validate=validate.Length(max=1000))
    left_ear = fields.List(fields.Nested(MeasurementSchema), required=True, validate=validate.Length(min=1))
    right_ear = fields.List(fields.Nested(MeasurementSchema), required=True, validate=validate.Length(min=1))

    @validates('test_date')
    def validate_date(self, value):
        try:
            datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            raise ValidationError('test_date must be valid ISO format datetime')

update_schema = UpdateTestSchema()

@api_bp.route('/tests/<test_id>', methods=['PUT'])
def update_test(test_id):
    try:
        validated_data = update_schema.load(request.json)
    except ValidationError as e:
        return jsonify({'error': 'Validation failed', 'details': e.messages}), 400

    # ... use validated_data
```

- **Pro:** Common in Flask apps (ecosystem fit)
- **Pro:** Simpler than Pydantic for basic use cases
- **Con:** Less type safety than Pydantic
- **Con:** Additional dependency

**Recommendation:** Option 1 (Pydantic) for type safety and modern Python. Option 3 (Marshmallow) if already using Flask ecosystem libraries.

---

### Issue 5: File Deletion Timing Creates Orphans

**Severity:** 🟡 MEDIUM
**Location:** `backend/api/routes.py:368-372`
**Category:** Data Integrity

**Description:**

The delete endpoint deletes database records first, then deletes the file. If file deletion fails (permissions, disk error, file locked), the database record is lost but the file remains on disk as an orphan.

**Current Code:**

```python
# Delete test
cursor.execute("DELETE FROM hearing_test WHERE id = ?", (test_id,))

conn.commit()
conn.close()

# Delete image file if it exists
if test['image_path']:
    image_path = Path(test['image_path'])
    if image_path.exists():
        image_path.unlink()  # If this fails, DB is already committed!
```

**Impact:**
- Orphaned files accumulate on disk (disk space leak)
- No way to recover test if file deletion fails
- Cannot rollback database changes

**Alternatives:**

**Option 1: Delete File Before Database** ⭐ Recommended

```python
@api_bp.route('/tests/<test_id>', methods=['DELETE'])
def delete_test(test_id):
    """Delete a test and its measurements."""

    with get_transaction() as (conn, cursor):
        # Verify test exists and get file path
        cursor.execute("SELECT id, image_path FROM hearing_test WHERE id = ?", (test_id,))
        test = cursor.fetchone()

        if not test:
            return jsonify({'error': 'Test not found'}), 404

        # Delete file FIRST (before DB commit)
        if test['image_path']:
            image_path = Path(test['image_path'])
            try:
                if image_path.exists():
                    image_path.unlink()
            except (PermissionError, OSError) as e:
                # File deletion failed - abort entire operation
                raise Exception(f'Failed to delete file: {str(e)}')

        # Now delete from database (will rollback if file deletion failed)
        cursor.execute("DELETE FROM audiogram_measurement WHERE id_hearing_test = ?", (test_id,))
        cursor.execute("DELETE FROM hearing_test WHERE id = ?", (test_id,))

        # Transaction commits here

    return jsonify({'success': True})
```

- **Pro:** Prevents orphaned files
- **Pro:** Atomicity - both succeed or both fail
- **Pro:** File can be recovered if DB delete fails
- **Con:** If DB delete fails, file is lost (but DB still has reference)

**Option 2: Two-Phase Delete with Soft Delete**

```python
# Schema change: Add deleted_at column to hearing_test
# ALTER TABLE hearing_test ADD COLUMN deleted_at TEXT;

@api_bp.route('/tests/<test_id>', methods=['DELETE'])
def delete_test(test_id):
    """Soft-delete a test (mark as deleted)."""

    with get_transaction() as (conn, cursor):
        # Mark as deleted
        cursor.execute("""
            UPDATE hearing_test
            SET deleted_at = ?
            WHERE id = ?
        """, (datetime.utcnow().isoformat(), test_id))

    return jsonify({'success': True})

# Separate cleanup job (cron or celery task)
def cleanup_deleted_tests():
    """Physically delete soft-deleted tests and their files."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, image_path
        FROM hearing_test
        WHERE deleted_at IS NOT NULL
        AND deleted_at < datetime('now', '-7 days')
    """)

    for test in cursor.fetchall():
        # Delete file
        if test['image_path']:
            Path(test['image_path']).unlink(missing_ok=True)

        # Delete from DB
        cursor.execute("DELETE FROM audiogram_measurement WHERE id_hearing_test = ?", (test['id'],))
        cursor.execute("DELETE FROM hearing_test WHERE id = ?", (test['id'],))

    conn.commit()
    conn.close()
```

- **Pro:** Can recover from accidental deletes (within 7 days)
- **Pro:** Separates user action from physical cleanup
- **Pro:** Allows async cleanup with retry
- **Con:** Requires schema change
- **Con:** More complexity (soft delete query filtering)
- **Con:** Needs background job infrastructure

**Option 3: Best-Effort File Delete with Logging**

```python
@api_bp.route('/tests/<test_id>', methods=['DELETE'])
def delete_test(test_id):
    """Delete a test and its measurements."""

    with get_transaction() as (conn, cursor):
        # Get file path
        cursor.execute("SELECT id, image_path FROM hearing_test WHERE id = ?", (test_id,))
        test = cursor.fetchone()

        if not test:
            return jsonify({'error': 'Test not found'}), 404

        # Delete from database
        cursor.execute("DELETE FROM audiogram_measurement WHERE id_hearing_test = ?", (test_id,))
        cursor.execute("DELETE FROM hearing_test WHERE id = ?", (test_id,))

        # Transaction commits here

    # Best-effort file delete (log failures)
    if test['image_path']:
        image_path = Path(test['image_path'])
        try:
            if image_path.exists():
                image_path.unlink()
        except Exception as e:
            # Log for manual cleanup
            current_app.logger.error(
                f"Failed to delete file for test {test_id}: {image_path}",
                exc_info=True
            )

    return jsonify({'success': True})
```

- **Pro:** Delete always succeeds from user perspective
- **Pro:** Simple implementation
- **Con:** Orphaned files accumulate (requires manual cleanup)
- **Con:** No rollback if file delete fails

**Recommendation:** Option 1 (Delete File First). Files are easier to recreate than database integrity, and failures are rare.

---

### Issue 6: No Concurrent Modification Protection

**Severity:** 🟡 MEDIUM
**Location:** `backend/api/routes.py:270-337`
**Category:** Data Integrity

**Description:**

If two users edit the same test simultaneously, the last write wins with no conflict detection. User A's changes can be silently overwritten by User B.

**Current Code:**

```python
@api_bp.route('/tests/<test_id>', methods=['PUT'])
def update_test(test_id):
    data = request.json

    # No version checking
    # No modified_at timestamp comparison
    # Last write always wins

    cursor.execute("UPDATE hearing_test SET ...")
```

**Impact:**
- Data loss when multiple users edit simultaneously
- No user notification of conflicts
- Cannot implement collaborative editing
- Difficult to debug data inconsistencies

**Alternatives:**

**Option 1: Optimistic Locking with modified_at Timestamp** ⭐ Recommended

```python
# Schema change: Ensure hearing_test has modified_at column
# ALTER TABLE hearing_test ADD COLUMN modified_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP;
# CREATE TRIGGER update_hearing_test_timestamp
# AFTER UPDATE ON hearing_test
# BEGIN
#   UPDATE hearing_test SET modified_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
# END;

class UpdateTestSchema(BaseModel):
    test_date: str
    location: Optional[str]
    device_name: Optional[str]
    notes: Optional[str]
    left_ear: List[MeasurementSchema]
    right_ear: List[MeasurementSchema]
    modified_at: str  # Client must send last known modified_at

@api_bp.route('/tests/<test_id>', methods=['PUT'])
def update_test(test_id):
    """Update test data with optimistic locking."""

    try:
        validated_data = UpdateTestSchema(**request.json)
    except ValidationError as e:
        return jsonify({'error': 'Validation failed', 'details': e.errors()}), 400

    with get_transaction() as (conn, cursor):
        # Check if test has been modified since client loaded it
        cursor.execute("""
            SELECT modified_at FROM hearing_test WHERE id = ?
        """, (test_id,))
        test = cursor.fetchone()

        if not test:
            return jsonify({'error': 'Test not found'}), 404

        if test['modified_at'] != validated_data.modified_at:
            return jsonify({
                'error': 'Conflict detected',
                'message': 'This test was modified by another user. Please refresh and try again.',
                'current_modified_at': test['modified_at']
            }), 409  # HTTP 409 Conflict

        # Proceed with update (modified_at will auto-update via trigger)
        cursor.execute("""
            UPDATE hearing_test
            SET test_date = ?, location = ?, device_name = ?, notes = ?
            WHERE id = ?
        """, (validated_data.test_date, validated_data.location,
              validated_data.device_name, validated_data.notes, test_id))

        # ... update measurements

    return get_test(test_id)
```

- **Pro:** Standard pattern for optimistic locking
- **Pro:** No locks needed (high concurrency)
- **Pro:** Clear user feedback on conflicts
- **Con:** Requires schema change (modified_at column)
- **Con:** Client must track and send modified_at

**Option 2: Version Number with Auto-Increment**

```python
# Schema: Add version INTEGER DEFAULT 1 to hearing_test

@api_bp.route('/tests/<test_id>', methods=['PUT'])
def update_test(test_id):
    data = request.json
    client_version = data.get('version')

    if not client_version:
        return jsonify({'error': 'version field required for conflict detection'}), 400

    with get_transaction() as (conn, cursor):
        # Update with version check
        cursor.execute("""
            UPDATE hearing_test
            SET test_date = ?,
                location = ?,
                device_name = ?,
                notes = ?,
                version = version + 1
            WHERE id = ? AND version = ?
        """, (data['test_date'], data.get('location'),
              data.get('device_name'), data.get('notes'),
              test_id, client_version))

        if cursor.rowcount == 0:
            # Either not found or version mismatch
            cursor.execute("SELECT version FROM hearing_test WHERE id = ?", (test_id,))
            test = cursor.fetchone()

            if not test:
                return jsonify({'error': 'Test not found'}), 404
            else:
                return jsonify({
                    'error': 'Conflict detected',
                    'message': 'Test was modified by another user',
                    'current_version': test['version']
                }), 409

        # ... update measurements
```

- **Pro:** Simple integer comparison (no date parsing)
- **Pro:** Clear version semantics
- **Con:** Requires schema change
- **Con:** Version number can grow indefinitely

**Option 3: ETag-Based Versioning (HTTP Standard)**

```python
import hashlib
import json

def calculate_etag(test_data: dict) -> str:
    """Calculate ETag hash for test data."""
    serialized = json.dumps(test_data, sort_keys=True)
    return hashlib.sha256(serialized.encode()).hexdigest()[:16]

@api_bp.route('/tests/<test_id>', methods=['GET'])
def get_test(test_id):
    # ... fetch test ...

    response_data = {
        'id': test['id'],
        'test_date': test['test_date'],
        # ... all fields
    }

    etag = calculate_etag(response_data)

    response = jsonify(response_data)
    response.headers['ETag'] = etag
    return response

@api_bp.route('/tests/<test_id>', methods=['PUT'])
def update_test(test_id):
    client_etag = request.headers.get('If-Match')

    if not client_etag:
        return jsonify({'error': 'If-Match header required'}), 428  # Precondition Required

    # Fetch current test and calculate its ETag
    current_test = ...  # fetch current state
    current_etag = calculate_etag(current_test)

    if current_etag != client_etag:
        return jsonify({'error': 'Precondition failed - test was modified'}), 412

    # Proceed with update
```

- **Pro:** HTTP standard (REST best practice)
- **Pro:** No schema changes needed
- **Con:** More complex (ETag calculation)
- **Con:** Not common in simple APIs

**Recommendation:** Option 1 (modified_at timestamp). Standard, simple, and provides good user feedback.

---

## Readability & Maintainability

### Issue 7: No Measurement Range Validation

**Severity:** 🟡 MEDIUM
**Location:** `backend/api/routes.py:318-331`
**Category:** Data Integrity

**Description:**

No validation that frequency_hz and threshold_db values are within valid audiometric ranges. Could insert nonsensical data like `frequency_hz=-999` or `threshold_db=9999`.

**Impact:**
- Invalid audiogram data corrupts visualizations
- Scientific inaccuracy in medical data
- Frontend charts break or show meaningless values

**Solution:**

This is addressed by **Issue 4 (Input Validation)** - the Pydantic schema includes range validation:

```python
class MeasurementSchema(BaseModel):
    frequency_hz: int = Field(ge=64, le=16000)
    threshold_db: float = Field(ge=-10, le=120)
```

No additional changes needed if Option 1 from Issue 4 is implemented.

---

### Issue 8: Hardcoded Error Messages

**Severity:** 🟢 LOW
**Location:** `backend/api/routes.py:296, 357`
**Category:** Maintainability

**Description:**

Error messages are hardcoded strings with no error codes. Difficult for frontend to handle different error types programmatically.

**Current Code:**

```python
return jsonify({'error': 'Test not found'}), 404
```

**Impact:**
- Frontend must parse error strings to determine error type
- Cannot internationalize error messages
- Difficult to track error types in monitoring

**Alternatives:**

**Option 1: Error Codes with Constants** ⭐ Recommended

```python
# backend/api/errors.py
class ErrorCode:
    TEST_NOT_FOUND = 'TEST_NOT_FOUND'
    VALIDATION_FAILED = 'VALIDATION_FAILED'
    UNAUTHORIZED = 'UNAUTHORIZED'
    CONFLICT = 'CONFLICT'

def error_response(code: str, message: str, status: int, **kwargs):
    """Create standardized error response."""
    response = {
        'error': {
            'code': code,
            'message': message,
            **kwargs
        }
    }
    return jsonify(response), status

# backend/api/routes.py
from backend.api.errors import ErrorCode, error_response

@api_bp.route('/tests/<test_id>', methods=['PUT'])
def update_test(test_id):
    # ...
    if not test:
        return error_response(
            ErrorCode.TEST_NOT_FOUND,
            f'Test with ID {test_id} not found',
            404
        )
```

- **Pro:** Frontend can switch on error codes
- **Pro:** Easy to internationalize (code → translated message)
- **Pro:** Consistent error structure
- **Con:** More verbose

**Option 2: Exception-Based Error Handling**

```python
# backend/api/exceptions.py
class APIException(Exception):
    """Base API exception."""
    status_code = 500
    error_code = 'INTERNAL_ERROR'

    def __init__(self, message: str, **kwargs):
        self.message = message
        self.extra = kwargs

class TestNotFound(APIException):
    status_code = 404
    error_code = 'TEST_NOT_FOUND'

class ValidationError(APIException):
    status_code = 400
    error_code = 'VALIDATION_FAILED'

# Register error handler
@api_bp.errorhandler(APIException)
def handle_api_exception(e):
    return jsonify({
        'error': {
            'code': e.error_code,
            'message': e.message,
            **e.extra
        }
    }), e.status_code

# In routes
@api_bp.route('/tests/<test_id>', methods=['PUT'])
def update_test(test_id):
    if not test:
        raise TestNotFound(f'Test {test_id} not found')
```

- **Pro:** Clean route code (just raise exception)
- **Pro:** Centralized error handling
- **Con:** Requires exception class hierarchy
- **Con:** Can make control flow less obvious

**Recommendation:** Option 1 for small APIs, Option 2 if building larger API with many endpoints.

---

### Issue 9: No Request Body Validation for Null/Missing JSON

**Severity:** 🟢 LOW
**Location:** `backend/api/routes.py:288`
**Category:** Error Handling

**Description:**

No check if `request.json` is None before accessing. If client sends invalid JSON or empty body, will raise uncaught exception.

**Impact:**
- 500 Internal Server Error instead of helpful 400 Bad Request
- Poor developer experience when debugging API calls

**Solution:**

Addressed by **Issue 4 (Input Validation)** - Pydantic will handle None/invalid JSON:

```python
try:
    validated_data = UpdateTestSchema(**request.json)
except ValidationError as e:
    return jsonify({'error': 'Validation failed', 'details': e.errors()}), 400
except (TypeError, AttributeError):
    return jsonify({'error': 'Invalid or missing JSON body'}), 400
```

---

## Summary & Recommendations

### Critical Priority (Implement First)

1. **Add Authentication/Authorization** (Issue 1)
   - Implement JWT-based auth with ownership checks
   - Prevents unauthorized data access/modification

2. **Add Transaction Management** (Issue 2)
   - Use context manager for automatic rollback
   - Prevents data corruption

3. **Add Input Validation** (Issue 4)
   - Use Pydantic schemas for comprehensive validation
   - Prevents invalid data insertion

### High Priority (Implement Soon)

4. **Fix File Deletion Order** (Issue 5)
   - Delete files before database records
   - Prevents orphaned files

5. **Add Concurrent Edit Protection** (Issue 6)
   - Use modified_at timestamp for optimistic locking
   - Prevents silent data loss

### Low Priority (Nice to Have)

6. **Optimize Update Strategy** (Issue 3) - Only if performance becomes an issue
7. **Standardize Error Responses** (Issue 8) - For better API consistency
8. **Add Measurement Range Validation** (Issue 7) - Covered by Issue 4

### Code Changes Summary

**Files to Modify:**
- `backend/database/db_utils.py` - Add transaction context manager
- `backend/api/routes.py` - Add auth decorators, validation, transaction usage
- `backend/database/schema.sql` - Add modified_at column and trigger

**New Files to Create:**
- `backend/api/auth.py` - Authentication decorators
- `backend/api/schemas.py` - Pydantic validation schemas
- `backend/api/errors.py` - Error codes and response helpers (optional)

**Estimated Effort:** 3-5 hours for critical issues, 2-3 hours for high priority
