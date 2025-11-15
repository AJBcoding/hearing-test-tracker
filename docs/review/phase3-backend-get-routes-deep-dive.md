# Deep Dive: Backend GET Routes

**Flow:** Backend Data Retrieval (GET endpoints)
**Files:** `backend/api/routes.py:165-267`
**Severity Summary:** 2 High + 5 Medium + 2 Low = 9 total issues

---

## Architecture & Design Patterns

### Issue 1: No Authentication/Authorization on Health Data

**Severity:** 🔴 CRITICAL (High)
**Location:** `backend/api/routes.py:165-202` (list_tests), `routes.py:205-267` (get_test)
**Category:** Security / Privacy

**Description:**

Both GET endpoints are completely unauthenticated and return health data (hearing test results) to anyone who makes a request. This is a critical privacy violation for medical data.

**Current Code:**

```python
@api_bp.route('/tests', methods=['GET'])
def list_tests():
    """List all hearing tests."""
    conn = _get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, test_date, source_type, location, ocr_confidence
        FROM hearing_test
        ORDER BY test_date DESC
    """)

    # Returns ALL tests to anyone who asks
    tests = []
    for row in cursor.fetchall():
        tests.append({...})

    conn.close()
    return jsonify(tests)

@api_bp.route('/tests/<test_id>', methods=['GET'])
def get_test(test_id):
    """Get specific test with all measurements."""
    # No ownership check - returns any test to anyone
```

**Impact:**
- **HIPAA violation:** Health data exposed without authorization
- **GDPR violation:** Personal health information accessible to unauthorized parties
- No user ownership - everyone sees everyone's data
- Cannot support multi-user scenarios
- Legal liability for healthcare data breach

**Alternatives:**

**Option 1: JWT Authentication with Per-User Data Filtering** ⭐ Recommended

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
            return jsonify({'error': 'Authentication required'}), 401

        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            g.user_id = payload['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid authentication token'}), 401

        return f(*args, **kwargs)
    return decorated_function

@api_bp.route('/tests', methods=['GET'])
@require_auth
def list_tests():
    """List all hearing tests for authenticated user."""
    conn = _get_db_connection()
    cursor = conn.cursor()

    # CRITICAL: Filter by user_id from token
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
    """Get specific test - only if owned by authenticated user."""
    conn = _get_db_connection()
    cursor = conn.cursor()

    # Check ownership
    cursor.execute("""
        SELECT * FROM hearing_test
        WHERE id = ? AND user_id = ?
    """, (test_id, g.user_id))

    test = cursor.fetchone()

    if not test:
        conn.close()
        # Don't reveal whether test exists or just not authorized
        return jsonify({'error': 'Test not found'}), 404

    # ... rest of response
```

- **Pro:** Industry standard, stateless authentication
- **Pro:** Explicit per-user data isolation
- **Pro:** Prevents both unauthorized access and cross-user data leakage
- **Pro:** Supports mobile apps and SPAs
- **Con:** Requires user table and authentication flow
- **Con:** Must implement token refresh mechanism

**Option 2: Session-Based Authentication**

```python
from flask_login import LoginManager, login_required, current_user

login_manager = LoginManager()

@api_bp.route('/tests', methods=['GET'])
@login_required
def list_tests():
    """List tests for logged-in user."""
    conn = _get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, test_date, source_type, location, ocr_confidence
        FROM hearing_test
        WHERE user_id = ?
        ORDER BY test_date DESC
    """, (current_user.id,))

    # ... rest of implementation
```

- **Pro:** Simpler setup than JWT
- **Pro:** Built-in session management
- **Con:** Stateful (requires server-side sessions)
- **Con:** Not ideal for API-first applications
- **Con:** CORS complexity for separate frontend

**Option 3: IP-Based Restriction (Development/Single User Only)**

```python
import os

ALLOWED_IPS = os.getenv('ALLOWED_IPS', 'localhost,127.0.0.1').split(',')

def require_local_access(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.remote_addr

        if client_ip not in ALLOWED_IPS:
            return jsonify({'error': 'Access denied'}), 403

        return f(*args, **kwargs)
    return decorated_function

@api_bp.route('/tests', methods=['GET'])
@require_local_access
def list_tests():
    # Returns all tests (no user filtering)
    # Assumes single-user deployment
```

- **Pro:** Very simple implementation
- **Pro:** Adequate for personal/single-user tool
- **Con:** Not suitable for multi-user deployment
- **Con:** Weak security (IP spoofing possible)
- **Con:** Doesn't support remote access

**Recommendation:** Option 1 (JWT) for any deployment that might have multiple users. Option 3 (IP restriction) only if this will always be a single-user personal tool.

---

### Issue 2: No Pagination on list_tests Endpoint

**Severity:** 🟡 MEDIUM
**Location:** `backend/api/routes.py:165-202`
**Category:** Performance / Scalability

**Description:**

The list_tests endpoint returns ALL tests in the database with no pagination. As the dataset grows (years of hearing tests), this will cause performance issues and excessive data transfer.

**Current Code:**

```python
@api_bp.route('/tests', methods=['GET'])
def list_tests():
    """List all hearing tests."""
    # ...
    cursor.execute("""
        SELECT id, test_date, source_type, location, ocr_confidence
        FROM hearing_test
        ORDER BY test_date DESC
    """)  # No LIMIT or OFFSET

    tests = []
    for row in cursor.fetchall():  # Returns ALL rows
        tests.append({...})

    return jsonify(tests)
```

**Impact:**
- Slow response times with large datasets (1000+ tests)
- Excessive memory usage on server
- Unnecessary network bandwidth
- Poor frontend performance rendering large lists
- Database locks held longer

**Alternatives:**

**Option 1: Offset-Based Pagination** ⭐ Recommended

```python
@api_bp.route('/tests', methods=['GET'])
@require_auth
def list_tests():
    """List hearing tests with pagination."""

    # Parse pagination parameters
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))

        if page < 1:
            return jsonify({'error': 'page must be >= 1'}), 400
        if page_size < 1 or page_size > 100:
            return jsonify({'error': 'page_size must be 1-100'}), 400

    except ValueError:
        return jsonify({'error': 'Invalid pagination parameters'}), 400

    conn = _get_db_connection()
    cursor = conn.cursor()

    # Get total count
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM hearing_test
        WHERE user_id = ?
    """, (g.user_id,))
    total = cursor.fetchone()['total']

    # Get paginated results
    offset = (page - 1) * page_size
    cursor.execute("""
        SELECT id, test_date, source_type, location, ocr_confidence
        FROM hearing_test
        WHERE user_id = ?
        ORDER BY test_date DESC
        LIMIT ? OFFSET ?
    """, (g.user_id, page_size, offset))

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

    # Return with pagination metadata
    return jsonify({
        'data': tests,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total_items': total,
            'total_pages': (total + page_size - 1) // page_size,
            'has_next': offset + page_size < total,
            'has_prev': page > 1
        }
    })
```

- **Pro:** Simple to implement and understand
- **Pro:** Frontend can jump to any page
- **Pro:** Shows total count (good for UI)
- **Con:** OFFSET performance degrades with large offsets
- **Con:** Inconsistent results if data changes between requests

**Option 2: Cursor-Based Pagination (Keyset Pagination)**

```python
@api_bp.route('/tests', methods=['GET'])
@require_auth
def list_tests():
    """List tests with cursor-based pagination."""

    # Cursor is the test_date of last item from previous page
    cursor_date = request.args.get('cursor')
    page_size = min(int(request.args.get('page_size', 20)), 100)

    conn = _get_db_connection()
    cursor_db = conn.cursor()

    if cursor_date:
        # Get next page after cursor
        cursor_db.execute("""
            SELECT id, test_date, source_type, location, ocr_confidence
            FROM hearing_test
            WHERE user_id = ? AND test_date < ?
            ORDER BY test_date DESC
            LIMIT ?
        """, (g.user_id, cursor_date, page_size + 1))  # +1 to check if more
    else:
        # First page
        cursor_db.execute("""
            SELECT id, test_date, source_type, location, ocr_confidence
            FROM hearing_test
            WHERE user_id = ?
            ORDER BY test_date DESC
            LIMIT ?
        """, (g.user_id, page_size + 1))

    rows = cursor_db.fetchall()
    conn.close()

    has_next = len(rows) > page_size
    tests = rows[:page_size]  # Remove the +1 extra item

    response = {
        'data': [
            {
                'id': row['id'],
                'test_date': row['test_date'],
                'source_type': row['source_type'],
                'location': row['location'],
                'confidence': row['ocr_confidence']
            }
            for row in tests
        ],
        'pagination': {
            'page_size': page_size,
            'has_next': has_next,
            'next_cursor': tests[-1]['test_date'] if has_next and tests else None
        }
    }

    return jsonify(response)
```

- **Pro:** Consistent performance even with large datasets
- **Pro:** Stable results (no phantom reads from concurrent inserts)
- **Pro:** Ideal for infinite scroll UIs
- **Con:** Cannot jump to arbitrary page (no page numbers)
- **Con:** More complex to implement
- **Con:** Requires index on sort column (test_date)

**Option 3: Keep Current Approach with Frontend Pagination**

Keep backend as-is but add virtual pagination in frontend.

```typescript
// Frontend only
const [page, setPage] = useState(1);
const pageSize = 20;

const paginatedTests = useMemo(() => {
  const start = (page - 1) * pageSize;
  return tests.slice(start, start + pageSize);
}, [tests, page, pageSize]);
```

- **Pro:** No backend changes needed
- **Pro:** Instant page switching (no network delay)
- **Con:** Still loads all data from server
- **Con:** Memory usage grows with dataset
- **Con:** Slow initial load

**Recommendation:** Option 1 (Offset Pagination) for typical use cases. Option 2 (Cursor Pagination) if you expect very large datasets (10,000+ tests) or real-time updates.

---

## Error Handling & Edge Cases

### Issue 3: No Input Validation on test_id Parameter

**Severity:** 🔴 CRITICAL (High)
**Location:** `backend/api/routes.py:205-226`
**Category:** Security / Input Validation

**Description:**

The get_test endpoint accepts test_id from URL path without validating its format. While SQL injection is prevented by parameterized queries, invalid inputs cause unnecessary database queries and poor error messages.

**Current Code:**

```python
@api_bp.route('/tests/<test_id>', methods=['GET'])
def get_test(test_id):
    """Get specific test with all measurements."""
    conn = _get_db_connection()
    cursor = conn.cursor()

    # No validation - test_id could be anything
    cursor.execute("""
        SELECT * FROM hearing_test WHERE id = ?
    """, (test_id,))
    # ... "not found" for both invalid format and non-existent ID
```

**Impact:**
- Wasted database queries for obviously invalid IDs
- Generic "not found" errors for malformed vs. missing IDs
- Potential information disclosure (timing attacks)
- Poor developer experience debugging API calls

**Alternatives:**

**Option 1: UUID Format Validation** ⭐ Recommended

```python
import uuid

def validate_uuid(uuid_string: str) -> bool:
    """Validate that string is properly formatted UUID."""
    try:
        uuid.UUID(uuid_string)
        return True
    except (ValueError, AttributeError):
        return False

@api_bp.route('/tests/<test_id>', methods=['GET'])
@require_auth
def get_test(test_id):
    """Get specific test with all measurements."""

    # Validate UUID format before database query
    if not validate_uuid(test_id):
        return jsonify({
            'error': 'Invalid test ID format',
            'message': 'Test ID must be a valid UUID'
        }), 400  # Bad Request, not 404

    conn = _get_db_connection()
    cursor = conn.cursor()

    # Now query only if format is valid
    cursor.execute("""
        SELECT * FROM hearing_test
        WHERE id = ? AND user_id = ?
    """, (test_id, g.user_id))

    test = cursor.fetchone()

    if not test:
        conn.close()
        return jsonify({'error': 'Test not found'}), 404

    # ... rest of implementation
```

- **Pro:** Fails fast on invalid input
- **Pro:** Clear error messages (400 vs 404)
- **Pro:** Prevents unnecessary database queries
- **Pro:** Standard UUID validation
- **Con:** Slight code overhead

**Option 2: Flask URL Converter**

```python
# Custom UUID converter
from werkzeug.routing import BaseConverter, ValidationError

class UUIDConverter(BaseConverter):
    """URL converter for UUID parameters."""
    def to_python(self, value):
        try:
            return str(uuid.UUID(value))
        except ValueError:
            raise ValidationError()

    def to_url(self, value):
        return str(value)

# Register in app factory (app.py)
def create_app(db_path: Path = None):
    app = Flask(__name__)
    app.url_map.converters['uuid'] = UUIDConverter
    # ...

# Use in route
@api_bp.route('/tests/<uuid:test_id>', methods=['GET'])
@require_auth
def get_test(test_id):
    """Get specific test - test_id is already validated as UUID."""
    # Flask will return 404 if test_id is not valid UUID
    # test_id is guaranteed to be valid UUID string here
```

- **Pro:** Validation happens at routing layer (very clean)
- **Pro:** Automatic 404 for invalid UUIDs
- **Pro:** Reusable across all UUID routes
- **Con:** Less control over error message
- **Con:** Returns 404 for invalid format (not technically RESTful)

**Option 3: Pydantic Path Parameter Validation (Flask-Pydantic)**

```python
from flask_pydantic import validate
from pydantic import BaseModel, Field, validator

class GetTestPath(BaseModel):
    test_id: str

    @validator('test_id')
    def validate_uuid(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('test_id must be valid UUID')
        return v

@api_bp.route('/tests/<test_id>', methods=['GET'])
@require_auth
@validate()
def get_test(path: GetTestPath):
    """Get specific test."""
    test_id = path.test_id

    # test_id is validated by this point
```

- **Pro:** Consistent with request body validation
- **Pro:** Clear validation errors
- **Con:** Additional dependency (flask-pydantic)
- **Con:** Less common pattern for path params

**Recommendation:** Option 1 (Manual Validation) for simplicity. Option 2 (URL Converter) if you have many UUID routes and want automatic validation.

---

### Issue 4: No Database Connection Error Handling

**Severity:** 🟡 MEDIUM
**Location:** `backend/api/routes.py:182-183, 219-220`
**Category:** Error Handling / Reliability

**Description:**

Both GET endpoints call `_get_db_connection()` without handling potential connection failures. Database unavailability results in uncaught exceptions and generic 500 errors.

**Current Code:**

```python
@api_bp.route('/tests', methods=['GET'])
def list_tests():
    """List all hearing tests."""
    conn = _get_db_connection()  # Could raise exception
    cursor = conn.cursor()
    # ...
```

**Impact:**
- Generic 500 errors don't indicate database issue
- No retry logic for transient failures
- No graceful degradation
- Difficult to debug in production

**Alternatives:**

**Option 1: Try/Except with Specific Error Response** ⭐ Recommended

```python
import sqlite3

@api_bp.route('/tests', methods=['GET'])
@require_auth
def list_tests():
    """List all hearing tests with pagination."""

    try:
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

        return jsonify({'data': tests})

    except sqlite3.OperationalError as e:
        # Database locked, disk I/O error, etc.
        current_app.logger.error(f"Database error in list_tests: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Database temporarily unavailable',
            'message': 'Please try again in a moment',
            'retry_after': 5
        }), 503  # Service Unavailable

    except Exception as e:
        current_app.logger.error(f"Unexpected error in list_tests: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500

    finally:
        if 'conn' in locals():
            conn.close()
```

- **Pro:** Specific error messages for different failure types
- **Pro:** Proper HTTP status codes (503 vs 500)
- **Pro:** Includes retry guidance for clients
- **Pro:** Logs errors for debugging
- **Con:** Verbose (need to wrap every endpoint)

**Option 2: Global Error Handler**

```python
# backend/app.py
@app.errorhandler(sqlite3.OperationalError)
def handle_database_error(e):
    """Handle database operational errors globally."""
    current_app.logger.error(f"Database error: {str(e)}", exc_info=True)
    return jsonify({
        'error': 'Database temporarily unavailable',
        'message': 'Please try again in a moment'
    }), 503

# Routes can now just let exceptions bubble up
@api_bp.route('/tests', methods=['GET'])
@require_auth
def list_tests():
    """List all hearing tests."""
    conn = _get_db_connection()  # Errors caught by global handler
    # ...
```

- **Pro:** DRY - single error handling implementation
- **Pro:** Clean route code
- **Con:** Less control per-endpoint
- **Con:** All database errors get same response

**Option 3: Database Connection Context Manager with Retry**

```python
# backend/database/db_utils.py
from contextlib import contextmanager
import time

@contextmanager
def get_db_connection_with_retry(db_path: Optional[Path] = None, retries: int = 3):
    """Get database connection with automatic retry on lock."""
    if db_path is None:
        from backend.config import DB_PATH
        db_path = DB_PATH

    last_error = None

    for attempt in range(retries):
        try:
            conn = sqlite3.connect(db_path, timeout=10.0)
            conn.row_factory = sqlite3.Row
            yield conn
            conn.close()
            return
        except sqlite3.OperationalError as e:
            last_error = e
            if attempt < retries - 1:
                time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                continue
            raise  # Last attempt failed

# Usage in routes
@api_bp.route('/tests', methods=['GET'])
@require_auth
def list_tests():
    try:
        with get_db_connection_with_retry() as conn:
            cursor = conn.cursor()
            # ... queries
    except sqlite3.OperationalError:
        return jsonify({'error': 'Database unavailable'}), 503
```

- **Pro:** Automatic retry for transient issues
- **Pro:** Reusable pattern
- **Con:** More complexity
- **Con:** May hide underlying issues

**Recommendation:** Option 1 (Try/Except per endpoint) for explicit control. Option 2 (Global Handler) if you want consistent error handling across all endpoints.

---

### Issue 5: Inconsistent Metadata Handling

**Severity:** 🟡 MEDIUM
**Location:** `backend/api/routes.py:262-266`
**Category:** Data Consistency / API Design

**Description:**

The get_test endpoint constructs a metadata object with fields that may be NULL in the database. Frontend receives `null` values without clear documentation of which fields are optional.

**Current Code:**

```python
return jsonify({
    'id': test['id'],
    'test_date': test['test_date'],
    'source_type': test['source_type'],
    'location': test['location'],  # May be NULL
    'left_ear': left_ear,
    'right_ear': right_ear,
    'metadata': {
        'device': test['device_name'],      # May be NULL
        'technician': test['technician_name'],  # May be NULL
        'notes': test['notes']              # May be NULL
    }
})
```

**Impact:**
- Frontend must check every field for null
- Inconsistent between tests (some have device, some don't)
- No clear API contract for required vs optional fields
- TypeScript types don't match reality

**Alternatives:**

**Option 1: Normalize NULL to Empty String or Default** ⭐ Recommended

```python
return jsonify({
    'id': test['id'],
    'test_date': test['test_date'],
    'source_type': test['source_type'],
    'location': test['location'] or '',  # Empty string instead of null
    'left_ear': left_ear,
    'right_ear': right_ear,
    'metadata': {
        'device': test['device_name'] or 'Unknown',
        'technician': test['technician_name'] or '',
        'notes': test['notes'] or ''
    }
})
```

- **Pro:** Frontend never sees null for strings
- **Pro:** Simpler frontend code (no null checks)
- **Pro:** Clear defaults documented in code
- **Con:** Loses distinction between "not provided" and "empty"
- **Con:** "Unknown" as default could be misleading

**Option 2: Exclude Null Fields from Response**

```python
# Construct metadata, excluding null values
metadata = {}
if test['device_name']:
    metadata['device'] = test['device_name']
if test['technician_name']:
    metadata['technician'] = test['technician_name']
if test['notes']:
    metadata['notes'] = test['notes']

response = {
    'id': test['id'],
    'test_date': test['test_date'],
    'source_type': test['source_type'],
    'left_ear': left_ear,
    'right_ear': right_ear,
}

if test['location']:
    response['location'] = test['location']

if metadata:
    response['metadata'] = metadata

return jsonify(response)
```

- **Pro:** Smaller response payload
- **Pro:** Clear "not provided" (field absent)
- **Con:** Frontend must check field existence
- **Con:** Inconsistent response shape

**Option 3: Explicit Optional Fields with TypeScript Interface**

```python
# Keep nulls but document clearly
return jsonify({
    'id': test['id'],
    'test_date': test['test_date'],
    'source_type': test['source_type'],
    'location': test['location'],  # Can be null
    'left_ear': left_ear,
    'right_ear': right_ear,
    'metadata': {
        'device': test['device_name'],  # Can be null
        'technician': test['technician_name'],  # Can be null
        'notes': test['notes']  # Can be null
    }
})

# Document in API schema or OpenAPI
# And match in TypeScript:
# type TestMetadata = {
#   device: string | null;
#   technician: string | null;
#   notes: string | null;
# }
```

- **Pro:** Accurate representation of data
- **Pro:** TypeScript can enforce null checks
- **Con:** More verbose frontend code
- **Con:** Requires good documentation

**Recommendation:** Option 1 (Normalize to Empty String) for simpler frontend code. Option 3 (Explicit Nulls) if you want strict type safety and distinction between "not provided" and "empty".

---

## Readability & Maintainability

### Issue 6: No Query Result Validation

**Severity:** 🟡 MEDIUM
**Location:** `backend/api/routes.py:232-251`
**Category:** Data Validation / Error Handling

**Description:**

The get_test endpoint fetches measurements but doesn't validate the results. If a test has no measurements (database corruption, partial insert), it returns empty arrays without indication.

**Current Code:**

```python
# Get measurements
cursor.execute("""
    SELECT ear, frequency_hz, threshold_db
    FROM audiogram_measurement
    WHERE id_hearing_test = ?
    ORDER BY frequency_hz
""", (test_id,))

left_ear = []
right_ear = []

for row in cursor.fetchall():  # What if no rows?
    measurement = {
        'frequency_hz': row['frequency_hz'],
        'threshold_db': row['threshold_db']
    }
    if row['ear'] == 'left':
        left_ear.append(measurement)
    else:
        right_ear.append(measurement)

# Returns empty arrays - is this expected or error?
return jsonify({
    # ...
    'left_ear': left_ear,  # Could be []
    'right_ear': right_ear   # Could be []
})
```

**Impact:**
- Tests with missing measurements appear valid
- Frontend shows empty audiograms without error
- Difficult to distinguish between intentionally empty and database corruption

**Alternatives:**

**Option 1: Validate Minimum Measurements** ⭐ Recommended

```python
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

# Validate that we have measurements for both ears
# (Hearing tests should always have both ears)
if not left_ear or not right_ear:
    current_app.logger.warning(
        f"Test {test_id} has incomplete measurements: "
        f"left={len(left_ear)}, right={len(right_ear)}"
    )
    # Return with warning flag
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
        },
        'warnings': ['Incomplete measurement data - some frequencies missing']
    })
```

- **Pro:** Alerts about data quality issues
- **Pro:** Logs for investigation
- **Pro:** Still returns data (graceful degradation)
- **Con:** Response shape changes (adds warnings field)

**Option 2: Return Error for Incomplete Data**

```python
if not left_ear or not right_ear:
    conn.close()
    return jsonify({
        'error': 'Incomplete test data',
        'message': 'This test has missing measurements and cannot be displayed'
    }), 500
```

- **Pro:** Forces data integrity
- **Pro:** Clear error to user
- **Con:** User cannot view test at all
- **Con:** Harsh for minor data issues

**Option 3: Return Data Quality Metrics**

```python
return jsonify({
    'id': test['id'],
    # ... other fields
    'left_ear': left_ear,
    'right_ear': right_ear,
    'data_quality': {
        'left_measurements': len(left_ear),
        'right_measurements': len(right_ear),
        'is_complete': len(left_ear) >= 5 and len(right_ear) >= 5,
        'completeness_percentage': (
            (len(left_ear) + len(right_ear)) / 14 * 100  # Assuming 7 freq per ear
        )
    }
})
```

- **Pro:** Provides detailed quality information
- **Pro:** Frontend can decide how to handle
- **Con:** More complex response structure

**Recommendation:** Option 1 (Validate with Warnings). Provides visibility without breaking functionality.

---

### Issue 7: Generic Error Responses

**Severity:** 🟡 MEDIUM
**Location:** `backend/api/routes.py:228-230`
**Category:** Error Handling / Developer Experience

**Description:**

The 404 error response is a simple string with no context. Difficult to debug whether the test doesn't exist, was deleted, or ID is malformed.

**Current Code:**

```python
if not test:
    conn.close()
    return jsonify({'error': 'Test not found'}), 404
```

**Impact:**
- Poor debugging experience
- Cannot implement client-side retry logic
- No request tracking
- No differentiation between error types

**Solution:**

See **Issue 8 (Standardized Error Responses)** below for comprehensive solution.

---

### Issue 8: Inconsistent Response Formats

**Severity:** 🟢 LOW
**Location:** `backend/api/routes.py:192-202, 255-267`
**Category:** API Design / Consistency

**Description:**

list_tests returns a bare array while get_test returns an object. No consistent envelope pattern or error codes.

**Current Code:**

```python
# list_tests returns array directly
return jsonify([
    {'id': '...', 'test_date': '...'},
    {'id': '...', 'test_date': '...'}
])

# get_test returns object
return jsonify({
    'id': '...',
    'test_date': '...'
})
```

**Impact:**
- Inconsistent client-side parsing
- Difficult to add metadata (pagination, etc.)
- No standard error structure

**Alternatives:**

**Option 1: Consistent Envelope Pattern** ⭐ Recommended

```python
# Standardized response helpers
def success_response(data=None, message=None, **kwargs):
    """Create standardized success response."""
    response = {'success': True}
    if data is not None:
        response['data'] = data
    if message:
        response['message'] = message
    response.update(kwargs)
    return jsonify(response)

def error_response(error_code, message, status_code, **kwargs):
    """Create standardized error response."""
    response = {
        'success': False,
        'error': {
            'code': error_code,
            'message': message,
            **kwargs
        }
    }
    return jsonify(response), status_code

# Usage in endpoints
@api_bp.route('/tests', methods=['GET'])
@require_auth
def list_tests():
    # ... query logic

    return success_response(
        data=tests,
        pagination={
            'page': page,
            'page_size': page_size,
            'total': total
        }
    )

@api_bp.route('/tests/<test_id>', methods=['GET'])
@require_auth
def get_test(test_id):
    if not validate_uuid(test_id):
        return error_response(
            'INVALID_ID_FORMAT',
            'Test ID must be a valid UUID',
            400
        )

    # ... query logic

    if not test:
        return error_response(
            'TEST_NOT_FOUND',
            f'Test with ID {test_id} not found',
            404,
            test_id=test_id
        )

    return success_response(data={
        'id': test['id'],
        # ... test data
    })
```

- **Pro:** Consistent response structure
- **Pro:** Easy to add metadata
- **Pro:** Clear success/error indication
- **Pro:** Machine-readable error codes
- **Con:** More verbose

**Option 2: Keep Simple, Add Documentation**

Keep current format but document it clearly in API specification (OpenAPI/Swagger).

- **Pro:** Minimal code changes
- **Con:** Still inconsistent

**Recommendation:** Option 1 (Envelope Pattern) for API consistency and future extensibility.

---

### Issue 9: No Logging of Database Queries

**Severity:** 🟢 LOW
**Location:** `backend/api/routes.py:165-267`
**Category:** Observability

**Description:**

No logging of incoming requests, query parameters, or database query performance. Difficult to debug slow queries or track usage patterns.

**Current Code:**

```python
@api_bp.route('/tests', methods=['GET'])
def list_tests():
    # No logging
    conn = _get_db_connection()
    # ...
```

**Impact:**
- Cannot identify slow queries
- No usage analytics
- Difficult to debug production issues
- No audit trail

**Solution:**

```python
import logging
import time

logger = logging.getLogger(__name__)

@api_bp.route('/tests', methods=['GET'])
@require_auth
def list_tests():
    """List all hearing tests."""
    start_time = time.time()

    logger.info(f"list_tests called by user {g.user_id}")

    try:
        # ... implementation

        duration = time.time() - start_time
        logger.info(f"list_tests completed in {duration:.2f}s, returned {len(tests)} tests")

        return success_response(data=tests)

    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"list_tests failed after {duration:.2f}s for user {g.user_id}: {str(e)}",
            exc_info=True
        )
        raise
```

- **Pro:** Visibility into performance
- **Pro:** Error tracking
- **Pro:** Usage analytics

---

## Summary & Recommendations

### Critical Priority (Implement First)

1. **Add Authentication/Authorization** (Issue 1)
   - JWT-based auth with user_id filtering
   - Prevents unauthorized access to health data

2. **Add Input Validation** (Issue 3)
   - Validate UUID format before database queries
   - Clear error messages for invalid inputs

### High Priority (Implement Soon)

3. **Add Pagination** (Issue 2)
   - Offset-based pagination with metadata
   - Prevents performance issues with large datasets

4. **Add Database Error Handling** (Issue 4)
   - Try/except with specific error responses
   - Graceful degradation for database issues

5. **Standardize Response Format** (Issue 8)
   - Consistent envelope pattern
   - Machine-readable error codes

### Medium Priority (Nice to Have)

6. **Validate Query Results** (Issue 6) - Warn about incomplete data
7. **Normalize Metadata Handling** (Issue 5) - Consistent null handling
8. **Add Request Logging** (Issue 9) - Observability and debugging

### Code Changes Summary

**Files to Modify:**
- `backend/api/routes.py` - Add auth, validation, pagination, error handling
- `backend/database/schema.sql` - Add user_id column to hearing_test table
- `backend/app.py` - Register error handlers, configure logging

**New Files to Create:**
- `backend/api/auth.py` - JWT authentication decorators
- `backend/api/responses.py` - Standardized response helpers
- `backend/api/validators.py` - Input validation utilities

**Estimated Effort:** 4-6 hours for critical + high priority issues
