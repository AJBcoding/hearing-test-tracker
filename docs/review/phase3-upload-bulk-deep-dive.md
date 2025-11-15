# Deep Dive: Upload (Bulk) Flow

**Flow:** Bulk Audiogram Image Upload and Batch OCR Processing
**Files:**
- Frontend: `frontend/src/components/BulkUploadForm.tsx`
- Backend: `backend/api/routes.py:52-118`
- API Client: `frontend/src/lib/api.ts:59-71`

**Severity Summary:** 2 High + 6 Medium + 2 Low = 10 total issues

---

## Architecture & Design Patterns

### Issue 1: Inherits All Single Upload Security Vulnerabilities (Amplified)

**Severity:** 🔴 CRITICAL (High)
**Location:** `backend/api/routes.py:90-118`
**Category:** Security - File Upload

**Description:**

Bulk upload endpoint has ALL the same security issues as single upload (no size limits, no MIME validation, no filename sanitization) but AMPLIFIED by bulk nature. Single request can upload hundreds of malicious files.

**Current Code:**

```python
@api_bp.route('/tests/bulk-upload', methods=['POST'])
def bulk_upload_tests():
    """Bulk upload and process multiple audiogram images."""
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files provided'}), 400

    files = request.files.getlist('files[]')  # No limit on count!

    if not files or len(files) == 0:
        return jsonify({'error': 'No files provided'}), 400

    results = []
    successful = 0
    failed = 0

    for file in files:  # Process ALL files, no limits
        if file.filename == '':
            continue

        result = _process_single_file(file)  # Inherits all security issues

        # ... append results

    return jsonify({
        'total': len(results),
        'successful': successful,
        'failed': failed,
        'results': results
    })
```

**Impact:**
- **Amplified DoS:** Upload 1000 files at once → complete server crash
- **Storage Exhaustion:** 1000 × 10MB = 10GB in single request
- **CPU Exhaustion:** OCR on 1000 images simultaneously
- **Multiple Path Traversal:** Plant malicious files across filesystem

**Attack Example:**

```bash
# Upload 1000 large files to crash server
for i in {1..1000}; do
  files+=(-F "files[]=@/dev/zero")
done
curl "${files[@]}" http://api.example.com/api/tests/bulk-upload
```

**Solutions:**

**Option 1: Apply Single Upload Security + Bulk Limits** ⭐ Recommended

```python
MAX_BULK_FILES = 50  # Maximum files per bulk request
MAX_TOTAL_SIZE = 100 * 1024 * 1024  # 100MB total per request

@api_bp.route('/tests/bulk-upload', methods=['POST'])
@require_auth
@limiter.limit("5 per minute")  # Stricter than single upload
@limiter.limit("20 per hour")
def bulk_upload_tests():
    """Bulk upload with security controls."""

    if 'files[]' not in request.files:
        return jsonify({'error': 'No files provided'}), 400

    files = request.files.getlist('files[]')

    # Validate file count
    if not files or len(files) == 0:
        return jsonify({'error': 'No files provided'}), 400

    if len(files) > MAX_BULK_FILES:
        return jsonify({
            'error': 'Too many files',
            'message': f'Maximum {MAX_BULK_FILES} files per bulk upload',
            'provided': len(files)
        }), 400

    # Validate total size (before processing any files)
    total_size = sum(file.content_length or 0 for file in files if file.filename)
    if total_size > MAX_TOTAL_SIZE:
        return jsonify({
            'error': 'Total size exceeds limit',
            'message': f'Maximum total size is {MAX_TOTAL_SIZE // 1024 // 1024}MB',
            'total_size_mb': total_size / 1024 / 1024
        }), 400

    results = []
    successful = 0
    failed = 0

    for file in files:
        if file.filename == '':
            continue

        # Apply same security validations as single upload
        # (from Issue 1 in single upload deep dive)
        validation_result = validate_upload_file(file)
        if validation_result is not None:
            results.append({
                'filename': file.filename,
                'status': 'error',
                'error': validation_result
            })
            failed += 1
            continue

        # Process validated file
        result = _process_single_file_secure(file)

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
```

- **Pro:** Prevents bulk-specific attacks
- **Pro:** Applies all single-upload security
- **Pro:** Clear error messages
- **Con:** Inherits single upload fixes (must fix single first)

**Recommendation:** Fix single upload security (Issue 1 from single upload), then apply same validations to bulk with added count/size limits.

---

### Issue 2: No Transaction Management for Batch Operations

**Severity:** 🔴 CRITICAL (High)
**Location:** `backend/api/routes.py:90-112`
**Category:** Data Integrity

**Description:**

Bulk upload processes files in a loop without transactions. If file 50 of 100 fails, files 1-49 are committed but 50-100 are lost. Partial success creates inconsistent state.

**Current Code:**

```python
for file in files:
    if file.filename == '':
        continue

    result = _process_single_file(file)  # Each file commits independently

    if 'error' in result:
        # File failed, but previous files already committed!
        results.append({...})
        failed += 1
    else:
        # File succeeded and committed
        results.append({...})
        successful += 1

# Returns mix of success/failure with no rollback
```

**Impact:**
- Partial uploads create incomplete batches
- User expects all-or-nothing but gets partial success
- Cannot retry failed batch without duplicating successful files
- Difficult to track which files in a batch were processed

**Alternatives:**

**Option 1: Accept Partial Success (Current Behavior)** ⭐ Recommended

Keep current behavior but make it explicit and add retry support.

```python
@api_bp.route('/tests/bulk-upload', methods=['POST'])
@require_auth
def bulk_upload_tests():
    """
    Bulk upload with partial success support.

    NOTE: Each file is processed independently. If some files fail,
    successful files will still be saved. This allows large batches
    to partially succeed rather than failing entirely.
    """
    # ... validation

    results = []
    successful = 0
    failed = 0
    batch_id = generate_uuid()  # Track this batch

    for index, file in enumerate(files):
        if file.filename == '':
            continue

        try:
            result = _process_single_file_secure(file, batch_id=batch_id)

            results.append({
                'filename': file.filename,
                'file_number': index + 1,
                'status': 'success',
                'test_id': result['test_id'],
                'confidence': result['confidence'],
                'needs_review': result['needs_review']
            })
            successful += 1

        except Exception as e:
            current_app.logger.error(
                f"Bulk upload file {index + 1}/{len(files)} failed: {str(e)}"
            )
            results.append({
                'filename': file.filename,
                'file_number': index + 1,
                'status': 'error',
                'error': str(e),
                'retryable': True  # Can retry just this file
            })
            failed += 1

    return jsonify({
        'batch_id': batch_id,
        'total': len(results),
        'successful': successful,
        'failed': failed,
        'results': results,
        'partial_success': successful > 0 and failed > 0
    })
```

- **Pro:** Large batches can partially succeed
- **Pro:** Retry only failed files (not entire batch)
- **Pro:** Matches user expectation for bulk operations
- **Con:** Not atomic (some succeed, some fail)

**Option 2: All-or-Nothing Transaction**

```python
@api_bp.route('/tests/bulk-upload', methods=['POST'])
@require_auth
def bulk_upload_tests():
    """Bulk upload with all-or-nothing guarantee."""

    # ... validation

    temp_files = []
    ocr_results = []

    try:
        # Phase 1: Save all files to temp and run OCR
        for file in files:
            if file.filename == '':
                continue

            temp_path = save_to_temp(file)
            temp_files.append(temp_path)

            ocr_result = parse_jacoti_audiogram(temp_path)
            ocr_results.append((temp_path, ocr_result))

        # Phase 2: Single transaction for all database inserts
        with get_transaction() as (conn, cursor):
            results = []

            for temp_path, ocr_result in ocr_results:
                # Insert test and measurements
                test_id = _save_test_to_database_transactional(
                    cursor, ocr_result, temp_path, g.user_id
                )

                results.append({
                    'filename': temp_path.name,
                    'status': 'success',
                    'test_id': test_id,
                    # ...
                })

            # Transaction commits here - all succeed or all fail

        # Phase 3: Move files from temp to permanent (all succeeded)
        for temp_path, test_id in zip([t[0] for t in ocr_results], [r['test_id'] for r in results]):
            final_path = AUDIOGRAMS_DIR / f"{test_id}.jpg"
            shutil.move(str(temp_path), str(final_path))

        return jsonify({
            'total': len(results),
            'successful': len(results),
            'failed': 0,
            'results': results
        })

    except Exception as e:
        # Any failure rolls back entire batch
        # Clean up temp files
        for temp_path in temp_files:
            if temp_path.exists():
                temp_path.unlink()

        return jsonify({
            'error': 'Bulk upload failed',
            'message': 'None of the files were saved due to processing error',
            'details': str(e) if current_app.debug else None
        }), 500
```

- **Pro:** Atomic - all files succeed or all fail
- **Pro:** Consistent state
- **Con:** One bad file fails entire batch
- **Con:** Must retry entire batch on failure
- **Con:** Resource intensive (process all before committing)

**Option 3: Batch-Level Transactions with Checkpoints**

```python
BATCH_SIZE = 10  # Commit every 10 files

@api_bp.route('/tests/bulk-upload', methods=['POST'])
@require_auth
def bulk_upload_tests():
    """Bulk upload with batch checkpoints."""

    # ... validation

    results = []
    batch_results = []

    for i in range(0, len(files), BATCH_SIZE):
        batch_files = files[i:i + BATCH_SIZE]

        try:
            # Process batch atomically
            batch_results = process_file_batch(batch_files, g.user_id)
            results.extend(batch_results)

        except Exception as e:
            # This batch failed, but previous batches succeeded
            for file in batch_files:
                results.append({
                    'filename': file.filename,
                    'status': 'error',
                    'error': 'Batch processing failed'
                })

    return jsonify({
        'total': len(results),
        'successful': sum(1 for r in results if r['status'] == 'success'),
        'failed': sum(1 for r in results if r['status'] == 'error'),
        'results': results
    })
```

- **Pro:** Balances atomicity and partial success
- **Pro:** Limits damage from failures
- **Con:** More complex implementation
- **Con:** Batch size is arbitrary

**Recommendation:** Option 1 (Partial Success). Users expect bulk operations to partially succeed. Provide clear status per file and support retrying failures.

---

## Error Handling & UX Improvements

### Issue 3: Indeterminate Progress Bar

**Severity:** 🟡 MEDIUM
**Location:** `frontend/src/components/BulkUploadForm.tsx:98-104`
**Category:** User Experience

**Description:**

Progress bar shows animated 100% while uploading. Doesn't reflect actual upload or processing progress. User has no idea how much is complete or how long to wait.

**Current Code:**

```tsx
{uploadMutation.isPending && (
  <Stack gap="xs">
    <Text size="sm" c="dimmed">
      Processing files, please wait...
    </Text>
    <Progress value={100} animated />  {/* Always 100%! */}
  </Stack>
)}
```

**Impact:**
- User doesn't know progress
- Long uploads feel frozen
- Cannot estimate completion time
- Poor UX for large batches

**Alternatives:**

**Option 1: Server-Sent Events for Real-Time Progress** ⭐ Recommended

```python
# backend/api/routes.py
from flask import Response, stream_with_context
import json

@api_bp.route('/tests/bulk-upload-stream', methods=['POST'])
@require_auth
def bulk_upload_tests_stream():
    """Bulk upload with real-time progress via SSE."""

    def generate_progress():
        files = request.files.getlist('files[]')

        yield f"data: {json.dumps({'type': 'start', 'total': len(files)})}\n\n"

        for index, file in enumerate(files):
            try:
                result = _process_single_file_secure(file)

                yield f"data: {json.dumps({
                    'type': 'progress',
                    'current': index + 1,
                    'total': len(files),
                    'filename': file.filename,
                    'status': 'success',
                    'test_id': result['test_id']
                })}\n\n"

            except Exception as e:
                yield f"data: {json.dumps({
                    'type': 'progress',
                    'current': index + 1,
                    'total': len(files),
                    'filename': file.filename,
                    'status': 'error',
                    'error': str(e)
                })}\n\n"

        yield f"data: {json.dumps({'type': 'complete'})}\n\n"

    return Response(
        stream_with_context(generate_progress()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )
```

```tsx
// BulkUploadForm.tsx
import { useState, useEffect } from 'react'

export function BulkUploadForm() {
  const [uploadProgress, setUploadProgress] = useState({
    current: 0,
    total: 0,
    currentFile: ''
  })

  const handleStreamUpload = async (files: File[]) => {
    const formData = new FormData()
    files.forEach(file => formData.append('files[]', file))

    const response = await fetch('/api/tests/bulk-upload-stream', {
      method: 'POST',
      body: formData
    })

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader!.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6))

          if (data.type === 'start') {
            setUploadProgress({ current: 0, total: data.total, currentFile: '' })
          } else if (data.type === 'progress') {
            setUploadProgress({
              current: data.current,
              total: data.total,
              currentFile: data.filename
            })
          }
        }
      }
    }
  }

  return (
    <Stack gap="lg">
      {uploadProgress.total > 0 && (
        <Stack gap="xs">
          <Text size="sm">
            Processing {uploadProgress.current} of {uploadProgress.total} files...
          </Text>
          <Text size="xs" c="dimmed">{uploadProgress.currentFile}</Text>
          <Progress
            value={(uploadProgress.current / uploadProgress.total) * 100}
          />
        </Stack>
      )}
      {/* ... */}
    </Stack>
  )
}
```

- **Pro:** Real-time progress updates
- **Pro:** Shows which file is processing
- **Pro:** Accurate completion percentage
- **Con:** More complex implementation
- **Con:** Requires SSE support

**Option 2: Simple File Count Progress (Client-Side Estimate)**

```tsx
// Keep existing API, estimate progress client-side
const [uploadProgress, setUploadProgress] = useState(0)

const handleUpload = async () => {
  if (files.length === 0) return

  setUploadProgress(0)

  // This is an estimate - actual server processing time varies
  const estimatedTimePerFile = 2000 // 2 seconds
  const totalEstimatedTime = files.length * estimatedTimePerFile

  // Update progress based on time
  const interval = setInterval(() => {
    setUploadProgress(prev => {
      const newProgress = prev + (100 / (totalEstimatedTime / 100))
      return newProgress >= 95 ? 95 : newProgress // Cap at 95 until actually complete
    })
  }, 100)

  try {
    await uploadMutation.mutateAsync(files)
    setUploadProgress(100)
  } finally {
    clearInterval(interval)
  }
}

{uploadMutation.isPending && (
  <Stack gap="xs">
    <Text size="sm">
      Processing {files.length} files... ({uploadProgress.toFixed(0)}%)
    </Text>
    <Progress value={uploadProgress} />
  </Stack>
)}
```

- **Pro:** Simple, no backend changes
- **Pro:** Better than no progress
- **Con:** Inaccurate (just time-based estimate)
- **Con:** Doesn't reflect actual progress

**Recommendation:** Option 1 (SSE) for accurate progress. Option 2 as quick improvement if SSE not feasible.

---

### Issue 4: No Cancel/Abort Functionality

**Severity:** 🟡 MEDIUM
**Location:** `frontend/src/components/BulkUploadForm.tsx:50-55`
**Category:** User Experience

**Description:**

Once bulk upload starts, user cannot cancel it. Long-running uploads (100 files) lock the UI with no escape.

**Current Code:**

```tsx
const handleUpload = () => {
  if (files.length > 0) {
    setResults(null)
    uploadMutation.mutate(files)  // No way to abort
  }
}
```

**Solution:**

```tsx
import { useState, useRef } from 'react'

export function BulkUploadForm() {
  const abortControllerRef = useRef<AbortController | null>(null)

  const handleUpload = () => {
    if (files.length === 0) return

    // Create abort controller for this upload
    abortControllerRef.current = new AbortController()

    uploadMutation.mutate({
      files,
      signal: abortControllerRef.current.signal
    })
  }

  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      notifications.show({
        title: 'Upload Cancelled',
        message: 'Bulk upload was cancelled by user',
        color: 'orange'
      })
    }
  }

  return (
    <Stack gap="lg">
      {uploadMutation.isPending && (
        <Button
          onClick={handleCancel}
          color="red"
          variant="outline"
        >
          Cancel Upload
        </Button>
      )}
      {/* ... */}
    </Stack>
  )
}

// api.ts
export const bulkUploadAudiograms = async (
  files: File[],
  signal?: AbortSignal
): Promise<BulkUploadResponse> => {
  const formData = new FormData()
  files.forEach(file => formData.append('files[]', file))

  const response = await apiClient.post<BulkUploadResponse>(
    '/tests/bulk-upload',
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      signal  // Pass abort signal to axios
    }
  )

  return response.data
}
```

- **Pro:** User can cancel long uploads
- **Pro:** Frees up UI
- **Con:** Server may continue processing (axios only aborts HTTP request)

---

## Summary & Recommendations

### Critical Priority (Must Fix)

1. **Apply Single Upload Security + Bulk Limits** (Issue 1)
   - Fix single upload security first
   - Add max file count (50) and total size (100MB) limits
   - Apply strict rate limiting

2. **Accept Partial Success with Clear Status** (Issue 2)
   - Document partial success behavior
   - Provide batch_id for tracking
   - Enable retry of failed files only

### High Priority (Important UX)

3. **Add Real-Time Progress** (Issue 3)
   - Server-Sent Events for accurate progress
   - Show current file being processed
   - Display percentage complete

4. **Add Cancel Functionality** (Issue 4)
   - AbortController support
   - Cancel button during upload
   - Clear feedback on cancellation

### Medium Priority (Nice to Have)

5. Frontend file validation (same as single upload)
6. Better error messaging (same as single upload)

### Code Changes Summary

**Inherits from Single Upload:**
- All security validations
- Error handling patterns
- Logging and monitoring

**Bulk-Specific:**
- `backend/api/routes.py` - Add bulk limits, SSE endpoint
- `frontend/src/components/BulkUploadForm.tsx` - Progress UI, cancel button
- `frontend/src/lib/api.ts` - AbortController support

**Estimated Effort:** 4-6 hours (assumes single upload security already implemented)
