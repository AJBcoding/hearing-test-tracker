# Deep Dive: Upload (Single) Flow

**Flow:** Single Audiogram Image Upload and OCR Processing
**Files:**
- Frontend: `frontend/src/components/UploadForm.tsx`
- Backend: `backend/api/routes.py:20-163`
- API Client: `frontend/src/lib/api.ts:32-41`

**Severity Summary:** 5 High + 8 Medium + 3 Low = 16 total issues

---

## Architecture & Design Patterns

### Issue 1: No File Upload Security Controls

**Severity:** 🔴 CRITICAL (High)
**Location:** `backend/app.py` (missing config), `backend/api/routes.py:37-42, 131-139`
**Category:** Security - File Upload Vulnerabilities

**Description:**

The upload endpoint has NO security controls for file uploads: no size limits, no MIME type validation, no filename sanitization. This creates multiple attack vectors including DoS, path traversal, and malicious file storage.

**Current Code:**

```python
# backend/app.py
def create_app(db_path: Path = None):
    app = Flask(__name__)
    # NO MAX_CONTENT_LENGTH configured!
    # Accepts unlimited file sizes

# backend/api/routes.py
@api_bp.route('/tests/upload', methods=['POST'])
def upload_test():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    # NO file type validation!
    # NO MIME type checking!
    # NO size validation!

    # Filename used directly - path traversal vulnerability!
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    filename = f"{timestamp}_{file.filename}"  # file.filename could be "../../../etc/passwd"
    filepath = AUDIOGRAMS_DIR / filename

    try:
        file.save(filepath)  # Saves any file type, any size!
```

**Impact:**
- **DoS Attack:** Upload 10GB file → disk exhaustion, server crash
- **Path Traversal:** Upload filename `../../../etc/cron.d/backdoor` → arbitrary file write
- **Malicious Files:** Upload `malware.exe.jpg` → stored on server, could be served to users
- **Resource Exhaustion:** Unlimited concurrent uploads → memory/disk exhaustion

**Attack Examples:**

```bash
# DoS via large file
curl -F "file=@/dev/zero" http://api.example.com/api/tests/upload

# Path traversal
curl -F "file=@malicious.jpg;filename=../../../tmp/backdoor.sh" \
     http://api.example.com/api/tests/upload
```

**Alternatives:**

**Option 1: Comprehensive File Upload Security** ⭐ Recommended

```python
# backend/app.py
import os

def create_app(db_path: Path = None):
    app = Flask(__name__)

    # File upload security
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_UPLOAD_SIZE', 16 * 1024 * 1024))  # 16MB
    app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png'}
    app.config['UPLOAD_FOLDER'] = AUDIOGRAMS_DIR

    # ... other config

# backend/api/routes.py
import magic  # python-magic for MIME type detection
import secrets
from werkzeug.utils import secure_filename

def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def validate_file_type(file_path: Path, allowed_mimes: set) -> bool:
    """Validate file type using magic numbers (not just extension)."""
    try:
        mime = magic.from_file(str(file_path), mime=True)
        return mime in allowed_mimes
    except Exception:
        return False

@api_bp.route('/tests/upload', methods=['POST'])
@require_auth
def upload_test():
    """Upload and process audiogram image with security controls."""

    # Check if file present
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    # Check filename not empty
    if file.filename == '' or file.filename is None:
        return jsonify({'error': 'Invalid filename'}), 400

    # Validate file extension (first line of defense)
    if not allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
        return jsonify({
            'error': 'Invalid file type',
            'message': 'Only JPEG and PNG images are accepted',
            'allowed_types': list(current_app.config['ALLOWED_EXTENSIONS'])
        }), 400

    # Sanitize filename and use UUID for uniqueness
    secure_name = secure_filename(file.filename)  # Removes path traversal chars
    file_ext = secure_name.rsplit('.', 1)[1].lower()
    unique_filename = f"{secrets.token_hex(16)}.{file_ext}"  # UUID-based name
    filepath = current_app.config['UPLOAD_FOLDER'] / unique_filename

    # Save file temporarily
    try:
        file.save(filepath)
    except Exception as e:
        current_app.logger.error(f"File save failed: {str(e)}")
        return jsonify({'error': 'Failed to save file'}), 500

    # Validate MIME type using magic numbers (second line of defense)
    ALLOWED_MIMES = {'image/jpeg', 'image/png'}
    if not validate_file_type(filepath, ALLOWED_MIMES):
        filepath.unlink()  # Delete invalid file
        return jsonify({
            'error': 'Invalid file content',
            'message': 'File content does not match image format'
        }), 400

    # Additional validation: check image can be opened
    try:
        from PIL import Image
        with Image.open(filepath) as img:
            # Verify it's actually an image
            img.verify()
            # Check dimensions are reasonable (e.g., not 100000x100000 decompression bomb)
            if img.width > 10000 or img.height > 10000:
                filepath.unlink()
                return jsonify({
                    'error': 'Image dimensions too large',
                    'message': f'Maximum dimensions: 10000x10000, got {img.width}x{img.height}'
                }), 400
    except Exception as e:
        filepath.unlink()
        return jsonify({
            'error': 'Invalid image file',
            'message': 'Could not process image'
        }), 400

    # File is validated - proceed with OCR
    try:
        result = _process_single_file_content(filepath)
        return jsonify(result)
    except Exception as e:
        # Cleanup happens in _process_single_file_content
        current_app.logger.error(f"OCR processing failed: {str(e)}", exc_info=True)
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

# Handle file too large (413)
@api_bp.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        'error': 'File too large',
        'message': f'Maximum file size is {current_app.config["MAX_CONTENT_LENGTH"] // 1024 // 1024}MB',
        'max_size_bytes': current_app.config['MAX_CONTENT_LENGTH']
    }), 413
```

- **Pro:** Comprehensive defense-in-depth
- **Pro:** Prevents all known file upload attacks
- **Pro:** Clear error messages for users
- **Pro:** Industry-standard security practices
- **Con:** Requires additional dependencies (python-magic, Pillow)
- **Con:** More complex implementation (~80 lines vs 10)

**Option 2: Basic Security with Flask-Uploads**

```python
from flask_uploads import UploadSet, configure_uploads, IMAGES

# backend/app.py
photos = UploadSet('photos', IMAGES)

def create_app(db_path: Path = None):
    app = Flask(__name__)
    app.config['UPLOADED_PHOTOS_DEST'] = AUDIOGRAMS_DIR
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    configure_uploads(app, photos)

# backend/api/routes.py
from werkzeug.utils import secure_filename

@api_bp.route('/tests/upload', methods=['POST'])
def upload_test():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    # Flask-Uploads handles validation
    if file and photos.file_allowed(file, file.filename):
        filename = photos.save(file)
        filepath = photos.path(filename)
        # ... process file
    else:
        return jsonify({'error': 'Invalid file type'}), 400
```

- **Pro:** Simple, uses Flask extension
- **Pro:** Handles basic security
- **Con:** External dependency (flask-uploads)
- **Con:** Less control over validation

**Option 3: Minimal Frontend + Backend Validation**

```typescript
// Frontend validation (UploadForm.tsx)
const handleUpload = () => {
  if (!file) return;

  // Client-side validation
  const MAX_SIZE = 16 * 1024 * 1024; // 16MB
  const ALLOWED_TYPES = ['image/jpeg', 'image/png'];

  if (file.size > MAX_SIZE) {
    notifications.show({
      title: 'File Too Large',
      message: `Maximum file size is 16MB. Your file is ${(file.size / 1024 / 1024).toFixed(1)}MB`,
      color: 'red'
    });
    return;
  }

  if (!ALLOWED_TYPES.includes(file.type)) {
    notifications.show({
      title: 'Invalid File Type',
      message: 'Only JPEG and PNG images are accepted',
      color: 'red'
    });
    return;
  }

  uploadMutation.mutate(file);
};
```

```python
# Backend still needs validation (don't trust client!)
from werkzeug.utils import secure_filename

@api_bp.route('/tests/upload', methods=['POST'])
def upload_test():
    # ... basic checks

    # Sanitize filename
    secure_name = secure_filename(file.filename)
    file_ext = secure_name.rsplit('.', 1)[1].lower() if '.' in secure_name else ''

    if file_ext not in {'jpg', 'jpeg', 'png'}:
        return jsonify({'error': 'Invalid file type'}), 400

    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}.{file_ext}"
    filepath = AUDIOGRAMS_DIR / unique_filename

    file.save(filepath)
    # ... process
```

- **Pro:** Better UX (instant client feedback)
- **Pro:** Reduces unnecessary server requests
- **Con:** Client-side validation can be bypassed
- **Con:** Still needs full server-side validation

**Recommendation:** Option 1 (Comprehensive Security). File uploads are a critical attack vector - invest in proper security. Option 3 for UX improvement alongside server validation.

---

### Issue 2: Non-Atomic Database Transaction (File + DB Not Transactional)

**Severity:** 🔴 CRITICAL (High)
**Location:** `backend/api/routes.py:136-162`
**Category:** Data Integrity

**Description:**

File is saved to disk BEFORE database insertion. If database insert fails (constraint violation, disk full, etc.), the file remains on disk orphaned. If OCR fails, file is deleted but partial state may remain.

**Current Code:**

```python
def _process_single_file(file):
    # Save file FIRST
    try:
        file.save(filepath)  # File now on disk
    except Exception as e:
        return {'error': f'Failed to save file: {str(e)}'}

    try:
        # Run OCR
        ocr_result = parse_jacoti_audiogram(filepath)

        # Save to database (if this fails, file is orphaned!)
        test_id = _save_test_to_database(ocr_result, filepath)

        return {
            'test_id': test_id,
            'confidence': ocr_result['confidence'],
            # ...
        }

    except Exception as e:
        # Cleanup on failure
        if filepath.exists():
            filepath.unlink()
        return {'error': str(e)}
```

**Impact:**
- Orphaned files accumulate on disk (storage leak)
- Database shows tests that don't have image files
- Partial uploads create inconsistent state
- No way to retry failed uploads (file already consumed)

**Alternatives:**

**Option 1: Two-Phase Commit (Temporary → Permanent)** ⭐ Recommended

```python
import shutil

def _process_single_file(file):
    """Process uploaded file with two-phase commit pattern."""

    # Phase 1: Save to temporary location
    temp_dir = current_app.config['DATA_DIR'] / 'temp'
    temp_dir.mkdir(exist_ok=True)

    temp_filename = f"temp_{secrets.token_hex(16)}.jpg"
    temp_filepath = temp_dir / temp_filename

    try:
        file.save(temp_filepath)
    except Exception as e:
        return {'error': f'Failed to save file: {str(e)}'}

    try:
        # Run OCR on temporary file
        ocr_result = parse_jacoti_audiogram(temp_filepath)

        # Generate final filename
        final_filename = f"{secrets.token_hex(16)}.jpg"
        final_filepath = AUDIOGRAMS_DIR / final_filename

        # Phase 2: Database transaction with file move
        with get_transaction() as (conn, cursor):
            # Insert into database (inside transaction)
            test_id = generate_uuid()
            cursor.execute("""
                INSERT INTO hearing_test (
                    id, test_date, source_type, location, device_name,
                    image_path, ocr_confidence, user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                test_id,
                ocr_result['test_date'] or datetime.now().isoformat(),
                'home',
                ocr_result['metadata']['location'],
                ocr_result['metadata']['device'],
                str(final_filepath),
                ocr_result['confidence'],
                g.user_id
            ))

            # Insert measurements
            for ear_name, ear_data in [('left', ocr_result['left_ear']),
                                        ('right', ocr_result['right_ear'])]:
                deduplicated = _deduplicate_measurements(ear_data)
                for measurement in deduplicated:
                    cursor.execute("""
                        INSERT INTO audiogram_measurement (
                            id, id_hearing_test, ear, frequency_hz, threshold_db
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (
                        generate_uuid(), test_id, ear_name,
                        measurement['frequency_hz'], measurement['threshold_db']
                    ))

            # Transaction commits here - now safe to move file

        # Database commit succeeded - move file from temp to permanent
        shutil.move(str(temp_filepath), str(final_filepath))

        return {
            'test_id': test_id,
            'confidence': ocr_result['confidence'],
            'needs_review': ocr_result['confidence'] < OCR_CONFIDENCE_THRESHOLD,
            'left_ear': ocr_result['left_ear'],
            'right_ear': ocr_result['right_ear']
        }

    except Exception as e:
        # Cleanup temp file on any failure
        if temp_filepath.exists():
            temp_filepath.unlink()

        current_app.logger.error(f"Upload processing failed: {str(e)}", exc_info=True)
        return {'error': str(e)}
```

- **Pro:** Atomic - both file and DB succeed or both fail
- **Pro:** No orphaned files
- **Pro:** Can retry on failure
- **Pro:** Temporary files isolated (can clean up on restart)
- **Con:** Requires temp directory management
- **Con:** Two file operations (save + move)

**Option 2: Database-First with Cleanup on Failure**

```python
def _process_single_file(file):
    """Save to database first, then file."""

    # Save file temporarily for OCR
    temp_filepath = ...
    file.save(temp_filepath)

    try:
        ocr_result = parse_jacoti_audiogram(temp_filepath)

        # Database transaction FIRST
        with get_transaction() as (conn, cursor):
            test_id = generate_uuid()
            final_filename = f"{test_id}.jpg"
            final_filepath = AUDIOGRAMS_DIR / final_filename

            # Insert into database
            cursor.execute("INSERT INTO hearing_test ...")
            # ... measurements

            # Transaction will commit here

        # Database succeeded - now move file
        shutil.move(str(temp_filepath), str(final_filepath))

        return {'test_id': test_id, ...}

    except Exception as e:
        # Database failed - just delete temp file
        if temp_filepath.exists():
            temp_filepath.unlink()
        return {'error': str(e)}
```

- **Pro:** Database is source of truth
- **Pro:** Simpler than two-phase commit
- **Con:** If file move fails after DB commit, DB has orphaned reference
- **Con:** Requires cleanup job to find and fix orphaned references

**Option 3: Accept Files Can Be Orphaned, Add Cleanup Job**

```python
# Keep current approach but add periodic cleanup

# backend/maintenance/cleanup.py
def cleanup_orphaned_files():
    """Remove files that don't have database records."""
    conn = get_connection()
    cursor = conn.cursor()

    # Get all image paths from database
    cursor.execute("SELECT image_path FROM hearing_test")
    db_files = {Path(row['image_path']) for row in cursor.fetchall()}
    conn.close()

    # Get all files on disk
    disk_files = set(AUDIOGRAMS_DIR.glob('*'))

    # Find orphans
    orphaned = disk_files - db_files

    # Delete orphaned files (older than 1 hour to avoid race conditions)
    import time
    current_time = time.time()
    for orphan in orphaned:
        if current_time - orphan.stat().st_mtime > 3600:  # 1 hour old
            orphan.unlink()
            print(f"Deleted orphaned file: {orphan}")

# Run as cron job or on startup
```

- **Pro:** Simple - keep current code
- **Pro:** Eventual consistency
- **Con:** Storage leak until cleanup runs
- **Con:** Requires background job infrastructure

**Recommendation:** Option 1 (Two-Phase Commit). Prevents orphaned files at source with minimal complexity.

---

### Issue 3: Production Stack Trace Disclosure

**Severity:** 🔴 CRITICAL (High)
**Location:** `backend/api/routes.py:157-158`
**Category:** Security - Information Disclosure

**Description:**

`traceback.print_exc()` in exception handler prints full stack trace to console. In production, this exposes file paths, library versions, and internal logic to logs that may be accessible to attackers.

**Current Code:**

```python
except Exception as e:
    import traceback
    traceback.print_exc()  # Exposes full stack trace!
    # Clean up the file if processing failed
    if filepath.exists():
        filepath.unlink()
    return {'error': str(e)}  # Also exposes error details to client
```

**Impact:**
- File paths exposed (`/var/app/backend/ocr/parser.py`)
- Library versions exposed (`tesseract 5.0.1`)
- Internal logic exposed (what functions failed, why)
- Helps attackers craft targeted exploits

**Solution:**

```python
except Exception as e:
    # Log with full traceback for debugging (server-side only)
    current_app.logger.error(
        f"Upload processing failed for user {g.user_id}: {str(e)}",
        exc_info=True  # Includes traceback in logs
    )

    # Clean up temp file
    if temp_filepath and temp_filepath.exists():
        temp_filepath.unlink()

    # Return generic error to client (no details in production)
    if current_app.debug:
        # Development: include details
        return {'error': f'Processing failed: {str(e)}'}
    else:
        # Production: generic message
        return {
            'error': 'Processing failed',
            'message': 'An error occurred while processing your upload. Please try again or contact support.',
            'request_id': generate_uuid()  # For support to trace in logs
        }
```

- **Pro:** No information disclosure to clients
- **Pro:** Full debugging info in server logs
- **Pro:** Request ID enables support to trace issues
- **Con:** Less helpful error messages for users (trade-off for security)

---

## Error Handling & Edge Cases

### Issue 4: No Rate Limiting on Upload Endpoint

**Severity:** 🟡 MEDIUM
**Location:** `backend/api/routes.py:20`
**Category:** Security - DoS Prevention

**Description:**

Upload endpoint has no rate limiting. Single user can spam uploads and exhaust server resources (CPU for OCR, disk for storage, bandwidth).

**Current Code:**

```python
@api_bp.route('/tests/upload', methods=['POST'])
def upload_test():
    # No rate limiting - can be called unlimited times
```

**Impact:**
- DoS attack: 1000 uploads/second → server crash
- Resource exhaustion: OCR is CPU-intensive
- Storage exhaustion: Even with size limits, many files add up
- Cost increase: Cloud storage/compute costs spike

**Alternatives:**

**Option 1: Flask-Limiter (Per-User Rate Limit)** ⭐ Recommended

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# backend/app.py
def create_app(db_path: Path = None):
    app = Flask(__name__)

    # Configure rate limiter
    limiter = Limiter(
        app=app,
        key_func=lambda: g.user_id if hasattr(g, 'user_id') else get_remote_address(),
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"  # or redis://localhost:6379
    )

    return app, limiter

# backend/api/routes.py
@api_bp.route('/tests/upload', methods=['POST'])
@require_auth
@limiter.limit("10 per minute")  # Max 10 uploads per minute per user
@limiter.limit("100 per day")    # Max 100 uploads per day per user
def upload_test():
    """Upload and process audiogram image."""
    # ... implementation
```

- **Pro:** Industry-standard rate limiting
- **Pro:** Per-user limits prevent abuse
- **Pro:** Configurable limits per endpoint
- **Pro:** Can use Redis for distributed limiting
- **Con:** Additional dependency

**Option 2: Custom Rate Limit Decorator**

```python
from functools import wraps
from time import time
from collections import defaultdict

# Simple in-memory rate limiter
upload_tracker = defaultdict(list)

def rate_limit(max_per_minute: int):
    """Decorator for rate limiting."""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            user_id = g.user_id
            now = time()

            # Clean old entries (older than 1 minute)
            upload_tracker[user_id] = [
                t for t in upload_tracker[user_id]
                if now - t < 60
            ]

            # Check rate limit
            if len(upload_tracker[user_id]) >= max_per_minute:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Maximum {max_per_minute} uploads per minute',
                    'retry_after': 60
                }), 429  # Too Many Requests

            # Record this request
            upload_tracker[user_id].append(now)

            return f(*args, **kwargs)
        return wrapped
    return decorator

@api_bp.route('/tests/upload', methods=['POST'])
@require_auth
@rate_limit(max_per_minute=10)
def upload_test():
    # ...
```

- **Pro:** No external dependencies
- **Pro:** Simple to understand
- **Con:** In-memory (lost on restart)
- **Con:** Not suitable for multi-server deployments
- **Con:** Memory grows with users

**Option 3: Token Bucket with Database**

```python
# Store rate limit tokens in database
def check_rate_limit(user_id: str, max_tokens: int, refill_rate: float) -> bool:
    """Token bucket algorithm using database."""
    conn = get_connection()
    cursor = conn.cursor()

    # Get or create bucket
    cursor.execute("""
        INSERT OR IGNORE INTO rate_limit_buckets (user_id, tokens, last_refill)
        VALUES (?, ?, ?)
    """, (user_id, max_tokens, time.time()))

    cursor.execute("""
        SELECT tokens, last_refill FROM rate_limit_buckets WHERE user_id = ?
    """, (user_id,))

    row = cursor.fetchone()
    tokens = row['tokens']
    last_refill = row['last_refill']

    # Refill tokens based on time elapsed
    now = time.time()
    elapsed = now - last_refill
    tokens = min(max_tokens, tokens + elapsed * refill_rate)

    # Check if token available
    if tokens < 1:
        conn.close()
        return False

    # Consume token
    cursor.execute("""
        UPDATE rate_limit_buckets
        SET tokens = ?, last_refill = ?
        WHERE user_id = ?
    """, (tokens - 1, now, user_id))

    conn.commit()
    conn.close()
    return True

@api_bp.route('/tests/upload', methods=['POST'])
@require_auth
def upload_test():
    # Check rate limit (10 tokens, refill 1 per 6 seconds = 10/min)
    if not check_rate_limit(g.user_id, max_tokens=10, refill_rate=1/6):
        return jsonify({'error': 'Rate limit exceeded'}), 429

    # ... upload logic
```

- **Pro:** Persistent across restarts
- **Pro:** Smooth rate limiting (token bucket)
- **Con:** Database overhead on every request
- **Con:** More complex implementation

**Recommendation:** Option 1 (Flask-Limiter) for production. Option 2 (Custom Decorator) for simple/personal deployments.

---

### Issue 5: Frontend Error Handling Assumes Error Structure

**Severity:** 🟡 MEDIUM
**Location:** `frontend/src/components/UploadForm.tsx:57-61`
**Category:** Error Handling

**Description:**

Frontend assumes `uploadMutation.error.message` exists. Axios errors have structure `.response.data.error` or `.message`. Displaying wrong property shows `undefined` or crashes.

**Current Code:**

```tsx
{uploadMutation.isError && (
  <Alert color="red" title="Upload Failed">
    {uploadMutation.error.message}  {/* May be undefined! */}
  </Alert>
)}
```

**Impact:**
- Shows "undefined" to users on some errors
- Potential crashes if error is unexpected shape
- Poor user experience

**Alternatives:**

**Option 1: Axios Error Interceptor** ⭐ Recommended

```typescript
// frontend/src/lib/api.ts
import axios, { AxiosError } from 'axios'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
})

// Error interceptor to normalize error structure
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // Create normalized error
    const normalizedError = new Error();

    if (error.response) {
      // Server responded with error status
      const data = error.response.data as any;
      normalizedError.message = data?.error || data?.message || `Server error: ${error.response.status}`;
    } else if (error.request) {
      // Request made but no response
      normalizedError.message = 'Network error - please check your connection';
    } else {
      // Something else happened
      normalizedError.message = error.message || 'An unexpected error occurred';
    }

    return Promise.reject(normalizedError);
  }
);
```

```tsx
// UploadForm.tsx - now error.message is always defined
{uploadMutation.isError && (
  <Alert color="red" title="Upload Failed">
    {uploadMutation.error.message}  {/* Always a string */}
  </Alert>
)}
```

- **Pro:** Centralized error handling
- **Pro:** All components benefit
- **Pro:** Consistent error messages
- **Con:** Hides original error structure (may need for debugging)

**Option 2: Safe Error Display Utility**

```typescript
// frontend/src/lib/error-utils.ts
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  if (typeof error === 'object' && error !== null) {
    // Axios error
    const axiosError = error as any;
    if (axiosError.response?.data) {
      return axiosError.response.data.error ||
             axiosError.response.data.message ||
             `Error: ${axiosError.response.status}`;
    }
    if (axiosError.message) {
      return axiosError.message;
    }
  }

  return 'An unexpected error occurred';
}

// UploadForm.tsx
import { getErrorMessage } from '../lib/error-utils'

{uploadMutation.isError && (
  <Alert color="red" title="Upload Failed">
    {getErrorMessage(uploadMutation.error)}
  </Alert>
)}
```

- **Pro:** Works with any error type
- **Pro:** No global changes needed
- **Con:** Must import and use in every component

**Option 3: Optional Chaining with Fallback**

```tsx
{uploadMutation.isError && (
  <Alert color="red" title="Upload Failed">
    {uploadMutation.error?.message ||
     (uploadMutation.error as any)?.response?.data?.error ||
     'Upload failed. Please try again.'}
  </Alert>
)}
```

- **Pro:** Simple, no dependencies
- **Pro:** Inline fallback
- **Con:** Verbose
- **Con:** Repeated in every component

**Recommendation:** Option 1 (Error Interceptor) for clean, centralized error handling.

---

### Issue 6: Frontend Lacks File Size Validation

**Severity:** 🟡 MEDIUM
**Location:** `frontend/src/components/UploadForm.tsx:41-47`
**Category:** UX / Performance

**Description:**

Frontend doesn't validate file size before upload. Users can select 100MB+ files and only discover the error after wasting bandwidth and time on upload.

**Current Code:**

```tsx
<FileInput
  label="Select Audiogram Image"
  placeholder="Click to select a JPEG file"
  accept="image/jpeg,image/jpg,image/png"
  value={file}
  onChange={setFile}  // No size validation
/>
```

**Impact:**
- Poor UX: Long upload only to fail
- Wasted bandwidth for large files
- Mobile users hit data caps
- Server load from doomed uploads

**Solution:**

```tsx
import { useState } from 'react'
import { notifications } from '@mantine/notifications'

const MAX_FILE_SIZE = 16 * 1024 * 1024; // 16MB

export function UploadForm() {
  const [file, setFile] = useState<File | null>(null)

  const handleFileChange = (selectedFile: File | null) => {
    if (!selectedFile) {
      setFile(null);
      return;
    }

    // Validate file size
    if (selectedFile.size > MAX_FILE_SIZE) {
      notifications.show({
        title: 'File Too Large',
        message: `Maximum file size is ${MAX_FILE_SIZE / 1024 / 1024}MB. Selected file is ${(selectedFile.size / 1024 / 1024).toFixed(1)}MB.`,
        color: 'red'
      });
      setFile(null); // Clear invalid selection
      return;
    }

    // Validate file type (additional check beyond accept attribute)
    const validTypes = ['image/jpeg', 'image/png', 'image/jpg'];
    if (!validTypes.includes(selectedFile.type)) {
      notifications.show({
        title: 'Invalid File Type',
        message: 'Please select a JPEG or PNG image',
        color: 'red'
      });
      setFile(null);
      return;
    }

    setFile(selectedFile);
  };

  return (
    <Paper p="md" withBorder>
      <Stack>
        <Title order={3}>Upload Single Audiogram</Title>

        <FileInput
          label="Select Audiogram Image"
          placeholder="Click to select a JPEG file"
          accept="image/jpeg,image/jpg,image/png"
          value={file}
          onChange={handleFileChange}  // Validates before setting
          description={`Maximum file size: ${MAX_FILE_SIZE / 1024 / 1024}MB`}
        />

        {/* ... rest of component */}
      </Stack>
    </Paper>
  )
}
```

- **Pro:** Instant feedback to user
- **Pro:** Prevents wasted uploads
- **Pro:** Better UX

---

## Readability & Maintainability

### Issue 7: Missing Logging

**Severity:** 🟢 LOW
**Location:** `backend/api/routes.py:20-163`
**Category:** Observability

**Description:**

No logging of upload attempts, successes, or failures. Cannot track usage, debug issues, or monitor OCR accuracy.

**Solution:**

```python
import logging

logger = logging.getLogger(__name__)

@api_bp.route('/tests/upload', methods=['POST'])
@require_auth
def upload_test():
    """Upload and process audiogram image."""
    start_time = time.time()

    logger.info(f"Upload attempt by user {g.user_id}")

    # ... validation

    try:
        # ... processing

        duration = time.time() - start_time
        logger.info(
            f"Upload successful for user {g.user_id}: "
            f"test_id={test_id}, confidence={confidence:.2f}, duration={duration:.2f}s"
        )

        return jsonify(result)

    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"Upload failed for user {g.user_id} after {duration:.2f}s: {str(e)}",
            exc_info=True
        )
        return jsonify({'error': 'Processing failed'}), 500
```

---

## Summary & Recommendations

### Critical Priority (Implement First)

1. **Add File Upload Security** (Issue 1)
   - File size limits, MIME validation, filename sanitization
   - Prevents DoS, path traversal, malicious uploads

2. **Fix Transaction Atomicity** (Issue 2)
   - Two-phase commit (temp → permanent after DB)
   - Prevents orphaned files

3. **Remove Stack Trace Disclosure** (Issue 3)
   - Log server-side only, generic errors to client
   - Prevents information disclosure

### High Priority (Implement Soon)

4. **Add Rate Limiting** (Issue 4) - Prevents upload spam/DoS
5. **Fix Frontend Error Handling** (Issue 5) - Better UX
6. **Add Frontend File Validation** (Issue 6) - Prevent wasted uploads

### Medium Priority (Nice to Have)

7. **Add Logging** (Issue 7) - Observability and monitoring

### Code Changes Summary

**Backend Files:**
- `backend/app.py` - Add MAX_CONTENT_LENGTH, rate limiter
- `backend/api/routes.py` - Rewrite upload endpoint with security
- `backend/database/schema.sql` - Add rate_limit_buckets table (if Option 3)

**Frontend Files:**
- `frontend/src/lib/api.ts` - Add error interceptor
- `frontend/src/components/UploadForm.tsx` - Add file validation

**New Files:**
- `backend/api/validators.py` - File validation utilities

**Estimated Effort:** 6-8 hours for critical + high priority issues
